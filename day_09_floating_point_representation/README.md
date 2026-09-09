# Floating Point Representation

## Introduction

Floating-point representation is a method for representing real-valued quantities in a finite number of bits. It is fundamental to scientific computing, engineering, graphics, simulation, statistics, numerical optimization, embedded systems, databases, and many general-purpose software applications.

A floating-point format provides a practical compromise between **range**, **precision**, **storage**, and **computational cost**. Unlike exact real numbers, a floating-point format contains only a finite set of representable values. Consequently, many mathematically valid real numbers must be rounded to the nearest representable value.

The Python script accompanying this README develops floating-point representation from elementary binary fractions through IEEE 754 structure, numerical error, special values, stable algorithms, exact alternatives, and production considerations.

The primary floating-point format used by Python's `float` is IEEE 754 binary64 on standard Python implementations.

---

## 1. Fixed-Point and Floating-Point Representation

### Fixed-point representation

In fixed-point arithmetic, the location of the binary or decimal point is predetermined.

For example, if an integer stores cents, the integer `1999` can represent:

`1999 cents = 19.99 currency units`

The scale is fixed.

Fixed-point arithmetic is useful when:

- The number of decimal places is known in advance.
- Exact fixed-scale arithmetic is required.
- Values represent quantities such as currency.
- Predictable storage and arithmetic are important.

### Floating-point representation

Floating-point representation stores a number using a significand and an exponent.

Conceptually:

`value = sign × significand × base^exponent`

For binary floating point:

`value = sign × significand × 2^exponent`

The exponent allows the binary point to move, providing a large dynamic range.

Floating-point arithmetic is particularly useful when values may vary across many orders of magnitude.

---

## 2. Scientific Notation and Binary Scientific Notation

Decimal scientific notation represents a number using powers of ten.

For example:

`602200000000000000000000 = 6.022 × 10^23`

Binary floating point uses powers of two.

For example:

`101.101₂ = 1.01101₂ × 2²`

The normalized binary form has a single nonzero bit before the binary point.

This normalized structure is central to IEEE 754 normal numbers.

---

## 3. Binary Fractions

Binary fractional positions represent negative powers of two.

For example:

`0.101₂`

means:

`1 × 2^-1 + 0 × 2^-2 + 1 × 2^-3`

Therefore:

`0.101₂ = 1/2 + 1/8 = 5/8`

The Python script implements exact binary-fraction conversion using `Fraction`.

This is important because it demonstrates why some decimal fractions are exactly representable in binary while others are not.

---

## 4. Why 0.1 Is Not Exactly Representable in Binary

The decimal value:

`0.1 = 1/10`

has a reduced denominator of `10`.

Because:

`10 = 2 × 5`

the denominator contains a factor other than 2.

A rational number has a finite binary expansion only when its reduced denominator contains no prime factors other than 2.

Therefore:

- `1/2` is exactly representable.
- `1/4` is exactly representable.
- `3/8` is exactly representable.
- `1/10` is not exactly representable.
- `1/3` is not exactly representable.

A binary floating-point implementation therefore stores the nearest representable approximation to `0.1`.

This is a representation issue rather than a failure of arithmetic.

---

# 5. IEEE 754

IEEE 754 is the widely used standard defining floating-point formats and arithmetic behavior.

Important concepts specified or addressed by IEEE 754 include:

- Floating-point formats
- Sign representation
- Exponents
- Significands
- Normal numbers
- Subnormal numbers
- Positive and negative zero
- Positive and negative infinity
- NaN
- Rounding
- Exceptional conditions
- Numerical operations

The Python script focuses primarily on binary32 and binary64.

---

## 6. Binary32

Binary32 is commonly called single precision.

Its structure is:

| Component | Bits |
|---|---:|
| Sign | 1 |
| Exponent | 8 |
| Fraction | 23 |
| Total | 32 |

The exponent uses a bias of:

`127`

Normal binary32 values effectively have:

`24 significant binary bits`

because the leading `1` of the normalized significand is implicit.

---

## 7. Binary64

Binary64 is commonly called double precision.

Its structure is:

| Component | Bits |
|---|---:|
| Sign | 1 |
| Exponent | 11 |
| Fraction | 52 |
| Total | 64 |

The exponent bias is:

`1023`

A normal binary64 value has:

`53 significant binary bits`

The additional bit comes from the implicit leading `1`.

This is why binary64 is often described as having approximately 15 to 17 decimal significant digits of practical precision.

---

# 8. Binary64 Encoding

For a normal binary64 number:

`(-1)^sign × (1.fraction)₂ × 2^(E - 1023)`

where:

- `sign` is the sign bit.
- `E` is the stored exponent field.
- `fraction` is the 52-bit stored fraction.
- `1023` is the exponent bias.
- The leading `1` is implicit.

The physical bit layout is:

`[sign][exponent][fraction]`

The script uses Python's `struct` module to inspect the actual 64-bit representation of a Python `float`.

---

## 9. The Sign Bit

The sign field contains one bit.

- `0` represents a positive sign.
- `1` represents a negative sign.

The sign bit participates in normal values, infinities, zeros, and NaNs.

An important consequence is that IEEE 754 has both:

- `+0`
- `-0`

These values compare equal numerically but retain different sign information.

---

# 10. The Exponent Field

The exponent field is stored using a biased representation.

For binary64:

`bias = 1023`

For a normal number:

`actual exponent = stored exponent - 1023`

The exponent field is not interpreted as an ordinary signed integer because special exponent encodings are reserved.

Two exponent-field values are particularly important:

- All exponent bits zero
- All exponent bits one

These values identify special cases.

---

# 11. The Fraction Field

The fraction field stores the bits following the implicit leading `1` for normal values.

For binary64:

`fraction field = 52 bits`

A normal significand therefore has the conceptual form:

`1.fraction`

The leading `1` does not need to be stored because normalized binary numbers have it by definition.

This is sometimes called the **hidden bit** or **implicit bit**.

---

# 12. Normal Numbers

Normal numbers use:

- A nonzero exponent field
- An exponent field that is not all ones

Their mathematical representation is:

`(-1)^s × (1 + fraction/2^52) × 2^(E-1023)`

Normal numbers provide the main range and precision of binary64.

The script reconstructs normal binary64 values directly from their fields to demonstrate how the encoding corresponds to the mathematical formula.

---

# 13. Subnormal Numbers

Subnormal numbers are also called denormal numbers in some older terminology.

They use:

- Exponent field = 0
- Fraction field ≠ 0

They do not have the implicit leading `1`.

Instead, their significand has the form:

`0.fraction`

Subnormals allow a gradual transition toward zero.

For binary64:

- Smallest positive normal ≈ `2^-1022`
- Smallest positive subnormal = `2^-1074`

This behavior is known as **gradual underflow**.

---

# 14. Zero

IEEE 754 represents zero using:

- Exponent field = 0
- Fraction field = 0

There are two encodings:

- Positive zero
- Negative zero

Their numerical comparison gives:

`+0 == -0`

but their signs can be distinguished using operations such as `math.copysign`.

Signed zero can matter in numerical algorithms involving directional limits, complex arithmetic, branch-sensitive mathematical functions, and certain numerical transformations.

---

# 15. Infinity

Infinity is represented using:

- Exponent field = all ones
- Fraction field = zero

There are:

- `+∞`
- `-∞`

Infinity can arise from overflow or from operations involving already infinite operands.

Examples include:

- `∞ + finite = ∞`
- `∞ × positive = ∞`
- `∞ × negative = -∞`

Some operations involving infinity are undefined and produce NaN under IEEE-style arithmetic.

---

# 16. NaN

NaN means **Not a Number**.

A NaN encoding has:

- Exponent field = all ones
- Fraction field ≠ zero

NaN represents an undefined or invalid numerical result.

Important NaN behavior includes:

`NaN != NaN`

Therefore this is not a suitable way to test for NaN:

`value == value`

The appropriate Python operation is:

`math.isnan(value)`

NaN can propagate through subsequent arithmetic operations.

---

# 17. NaN Payloads

The fraction bits of a NaN are not required to be zero.

Consequently, multiple NaN bit patterns can exist.

The payload can contain diagnostic information in some environments, but portable application code should generally treat NaN as a category rather than depending on a specific payload.

NaN propagation and payload preservation can depend on the operation, platform, compiler, and implementation.

---

# 18. Precision

Precision describes how finely values can be distinguished.

Binary64 has:

`53 significant binary bits`

This includes the implicit leading bit for normal numbers.

The number of decimal digits that can generally be relied upon is around 15 digits, while carefully chosen decimal representations can provide useful round-trip behavior with up to about 17 significant decimal digits.

Precision should not be confused with range.

A number can have a very large magnitude while still having only about 53 significant binary bits.

---

# 19. Range Versus Precision

Two different questions must be distinguished:

### Range

How large or small can the number be?

Binary64 has a maximum finite value of approximately:

`1.7976931348623157 × 10^308`

Its smallest positive subnormal is approximately:

`4.9406564584124654 × 10^-324`

### Precision

How closely can nearby numbers be distinguished?

Binary64 provides 53 significant binary bits for normal values.

A format can have a huge range while still having limited precision.

---

# 20. Machine Epsilon

Machine epsilon is commonly defined as the distance between `1.0` and the next larger representable binary64 number.

For binary64:

`epsilon = 2^-52`

approximately:

`2.220446049250313 × 10^-16`

The Python script computes machine epsilon experimentally by repeatedly halving a value until adding half of it to `1.0` no longer changes the result.

---

# 21. Machine Epsilon Is Not the Smallest Float

A frequent misconception is that machine epsilon represents the smallest possible floating-point value.

It does not.

Machine epsilon describes spacing around `1.0`.

For binary64:

- Machine epsilon = `2^-52`
- Smallest positive normal = `2^-1022`
- Smallest positive subnormal = `2^-1074`

These quantities answer entirely different questions.

---

# 22. Unit Roundoff

Under the standard round-to-nearest model, the **unit roundoff** is commonly represented by:

`u = 2^-53`

This is approximately half the spacing between `1.0` and the next larger binary64 number.

Thus:

`machine epsilon = 2^-52`

while:

`unit roundoff = 2^-53`

The terminology varies somewhat between numerical-analysis texts, so definitions should be checked when interpreting a specific formula.

---

# 23. ULP

ULP means **Unit in the Last Place**.

It describes a local unit of spacing between representable floating-point values.

Unlike machine epsilon, ULP spacing changes with magnitude.

For example, the spacing around:

`1.0`

is much smaller than the spacing around:

`10^16`

This explains why adding `1.0` to a sufficiently large floating-point value may have no effect.

Python's `math.nextafter()` can be used to inspect adjacent representable values.

---

# 24. `math.nextafter`

`math.nextafter(x, direction)` returns the floating-point value immediately adjacent to `x` in the specified direction.

This is useful for:

- Inspecting representable neighbors
- Understanding ULP spacing
- Boundary testing
- Numerical debugging
- Floating-point interval reasoning
- Testing underflow and subnormal behavior

For example, the value immediately above `0.0` is the smallest positive binary64 subnormal.

---

# 25. Rounding

A floating-point format cannot represent every real number.

When an exact result is not representable, it must be rounded.

IEEE 754 defines several rounding-direction concepts, including:

- Round to nearest, ties to even
- Round toward zero
- Round toward positive infinity
- Round toward negative infinity

The default rounding direction in typical IEEE 754 arithmetic is round to nearest, ties to even.

---

# 26. Round-to-Nearest, Ties-to-Even

When an exact result lies exactly halfway between two representable values, ties-to-even selects the one whose least significant retained bit is even.

Python's `round()` demonstrates this behavior for many decimal rounding cases:

- `round(2.5)` gives `2`
- `round(3.5)` gives `4`
- `round(4.5)` gives `4`
- `round(5.5)` gives `6`

This strategy helps reduce systematic rounding bias.

Python's decimal `round()` behavior and hardware floating-point rounding should not be treated as the same mechanism, but they illustrate the same tie-breaking principle.

---

# 27. Representation Error

Suppose the mathematical problem specifies:

`0.1`

The computer cannot represent the exact binary value of `1/10` in binary64.

Therefore it stores a nearby binary64 value.

The difference between the intended mathematical value and the stored value is **representation error**.

The script uses:

`Fraction.from_float(0.1)`

to expose the exact rational value represented by the binary64 float.

This is a useful debugging technique because it distinguishes the displayed decimal representation from the actual stored binary value.

---

# 28. Operation Rounding Error

Representation error is not the only source of floating-point error.

Even when the input operands are already floating-point values, the exact mathematical result of an operation may not be representable.

The result is therefore rounded again.

A computation can consequently involve:

1. Error introduced while representing inputs.
2. Error introduced by arithmetic operations.
3. Error accumulated over many operations.
4. Error magnified by an ill-conditioned mathematical problem.

---

# 29. The `0.1 + 0.2` Example

The expression:

`0.1 + 0.2`

does not produce a binary64 value exactly equal to the separately represented value `0.3`.

This is because:

- `0.1` is an approximation.
- `0.2` is an approximation.
- Their floating-point sum is rounded.
- The resulting binary64 value differs from the binary64 encoding of `0.3`.

Therefore:

`0.1 + 0.2 == 0.3`

evaluates to `False`.

This does not imply that floating-point addition is broken.

It reflects finite binary representation.

---

# 30. Equality Comparisons

Direct equality is appropriate when exact equality is genuinely part of the problem.

For approximate numerical calculations, direct equality can be inappropriate.

Instead, a tolerance-based comparison can be used.

Python provides:

`math.isclose(a, b)`

Its conceptual test is based on both relative and absolute tolerances.

A simplified description is:

`abs(a-b) <= max(rel_tol × max(abs(a), abs(b)), abs_tol)`

---

# 31. Relative Tolerance

Relative tolerance is appropriate when error should scale with the magnitude of the values.

For example, an error of `0.001` may be negligible for a quantity around `1,000,000` but significant for a quantity around `0.001`.

Relative error is commonly expressed as:

`|approximation - reference| / |reference|`

Relative error becomes problematic when the reference value is zero or extremely close to zero.

---

# 32. Absolute Tolerance

Absolute tolerance is useful near zero.

For example, if a numerical solver should produce zero but returns:

`1e-14`

the appropriate interpretation may be that the result is sufficiently close to zero.

A relative error calculation against zero is not meaningful in the ordinary sense.

Therefore numerical algorithms often use both:

- Relative tolerance
- Absolute tolerance

---

# 33. Accumulated Error

Repeated floating-point operations can accumulate rounding errors.

For example, repeatedly adding `0.1` does not necessarily produce the exact mathematical result expected from real-number arithmetic.

The script demonstrates repeated addition and measures the resulting absolute error.

The amount of accumulated error depends on:

- Number of operations
- Operation order
- Magnitudes
- Signs
- Conditioning
- Rounding behavior
- Algorithm structure

---

# 34. Floating-Point Addition Is Not Associative

Real-number addition satisfies:

`(a+b)+c = a+(b+c)`

Floating-point addition generally does not.

For example, with values of substantially different magnitudes:

`(a+b)+c`

may differ from:

`a+(b+c)`

because each intermediate operation is rounded.

This is especially important in:

- Parallel computation
- Distributed systems
- Numerical reductions
- Scientific simulations
- GPU computations
- Multithreaded summation

Different execution orders can therefore produce slightly different numerical results.

---

# 35. Summation Algorithms

A simple sum performs:

`total = total + value`

for each value.

This can accumulate rounding error.

The script demonstrates three approaches:

### Naive summation

Simple and fast, but potentially less accurate.

### Pairwise summation

Combines values in a balanced tree-like structure.

This can reduce error because values are combined at more similar scales.

### Kahan summation

Maintains a compensation value representing low-order information lost during addition.

Kahan summation can substantially reduce accumulated error for some workloads.

---

# 36. `math.fsum`

Python provides:

`math.fsum()`

It is designed to provide higher accuracy than ordinary sequential summation for many inputs.

It is particularly useful when:

- Many floating-point values are being summed.
- Small values may be lost when added to larger values.
- Numerical accuracy matters more than the minimal operation count.

It does not make floating-point arithmetic mathematically exact in every possible situation.

---

# 37. Catastrophic Cancellation

Cancellation occurs when nearly equal quantities are subtracted.

For example:

`a - b`

can be mathematically small even though `a` and `b` are individually large.

If the operands contain small errors, subtracting them can remove many significant digits and leave an answer dominated by error.

This is known as **catastrophic cancellation** when the resulting loss of significance is severe.

---

# 38. Stable Algebraic Reformulation

A numerically unstable expression can sometimes be rewritten into an equivalent but more stable form.

The script uses:

`sqrt(x² + 1) - x`

and its rationalized form:

`1 / (sqrt(x² + 1) + x)`

For large `x`, the first expression subtracts two nearly equal large numbers.

The rationalized version avoids this cancellation.

This illustrates an important principle:

> Algebraic equivalence does not guarantee numerical equivalence.

---

# 39. Absorption

Absorption occurs when a small quantity is added to a much larger floating-point value and the result rounds back to the larger value.

For example, near a sufficiently large magnitude:

`large + 1.0 == large`

can be true.

The issue is not that the addition is mathematically zero.

The issue is that `1.0` is smaller than the local representational spacing.

---

# 40. Overflow

Overflow occurs when a finite mathematical result exceeds the maximum finite value of the floating-point format.

Binary64 has a maximum finite value of approximately:

`1.7976931348623157 × 10^308`

An IEEE-style arithmetic operation that exceeds this range can produce infinity.

Python-level behavior can differ depending on the operation. Some expressions produce infinity, while other operations can raise `OverflowError`.

Production code should explicitly define how overflow should be handled.

---

# 41. Underflow

Underflow occurs when a result becomes too small in magnitude to be represented as a normal floating-point number.

IEEE 754 supports gradual underflow through subnormal values.

For binary64:

`minimum normal ≈ 2^-1022`

while:

`minimum positive subnormal = 2^-1074`

Once values become sufficiently small, they eventually round to zero.

---

# 42. Gradual Underflow

Without subnormal numbers, there would be an abrupt transition:

`smallest normal -> 0`

Subnormal numbers fill the gap between the smallest normal value and zero.

This provides better numerical behavior for certain algorithms because small differences can remain representable for a longer range.

Some specialized hardware environments can operate with subnormals disabled or flushed to zero for performance reasons, so performance-sensitive numerical software should understand the behavior of its target environment.

---

# 43. Special Values

IEEE 754 defines several special categories:

| Exponent | Fraction | Category |
|---|---|---|
| All zero | All zero | Zero |
| All zero | Nonzero | Subnormal |
| Normal | Any | Normal |
| All one | Zero | Infinity |
| All one | Nonzero | NaN |

The sign bit distinguishes positive and negative variants where applicable.

---

# 44. Python's Floating-Point Environment

Python exposes many useful numerical facilities through the standard library:

- `float`
- `math`
- `sys.float_info`
- `struct`
- `decimal`
- `fractions`

The script uses these modules to examine representation, arithmetic behavior, precision, special values, and exact alternatives.

---

# 45. Hexadecimal Floating-Point Representation

Python provides:

`float.hex()`

and:

`float.fromhex()`

A hexadecimal floating-point representation directly reflects the binary structure of a floating-point value.

For example, the hexadecimal form can preserve the exact binary64 value across a round trip.

This is useful for:

- Numerical debugging
- Reproducible diagnostics
- Exact binary floating-point serialization in suitable contexts
- Inspecting exponents and significands

---

# 46. Decimal Display Versus Stored Value

Formatting a float to a certain number of decimal places does not change its internal representation.

For example:

`f"{value:.2f}"`

changes the displayed string.

It does not modify the stored binary64 value.

By contrast:

`round(value, 2)`

creates a numerically rounded result.

This distinction is important when debugging apparent discrepancies between displayed values and calculations.

---

# 47. The `2.675` Example

The decimal value:

`2.675`

is not exactly representable in binary64.

Consequently, the stored value is slightly different from the exact decimal number.

When it is rounded to two decimal places using binary floating-point operations, the result can differ from an intuitive expectation based on exact decimal arithmetic.

Using:

`Decimal("2.675")`

represents the decimal value exactly within Decimal's decimal arithmetic model.

This illustrates why decimal-sensitive applications should not assume binary floating-point has decimal rounding semantics.

---

# 48. `Decimal`

Python's `decimal.Decimal` implements decimal floating-point arithmetic.

It is useful when decimal semantics matter.

Examples include:

- Financial calculations
- Accounting
- Tax calculations
- Decimal measurement systems
- Applications requiring controlled decimal precision

A critical distinction is:

`Decimal("0.1")`

versus:

`Decimal(0.1)`

The first starts from the exact decimal string.

The second begins with an already rounded binary floating-point value and therefore preserves that binary approximation in Decimal form.

---

# 49. Decimal Context

Decimal arithmetic operates within a context that controls properties such as:

- Precision
- Rounding
- Exceptional conditions

For example, the script demonstrates division by seven at different decimal precisions.

Increasing Decimal precision provides more decimal digits for subsequent operations, but it does not mean that arbitrary mathematical real numbers become exactly representable.

---

# 50. `Fraction`

Python's `fractions.Fraction` provides exact rational arithmetic.

For example:

`Fraction(1, 10) + Fraction(2, 10)`

produces exactly:

`3/10`

This is appropriate when rational exactness is more important than floating-point performance.

`Fraction.from_float(0.1)` reveals the exact rational value of the binary64 float rather than treating `0.1` as exact decimal one-tenth.

---

# 51. Integer Minor Units

An alternative for monetary quantities is integer minor units.

For example:

`1999 cents`

can represent:

`19.99`

This approach is useful when:

- The currency has a fixed minor-unit scale.
- Exact accounting arithmetic is required.
- The domain can be expressed naturally as integers.

The scale must be documented and handled consistently.

---

# 52. Binary32 Versus Binary64

Binary32 uses:

- 32 total bits
- 24 significant binary bits
- 8 exponent bits
- 23 stored fraction bits

Binary64 uses:

- 64 total bits
- 53 significant binary bits
- 11 exponent bits
- 52 stored fraction bits

Binary32 generally provides less precision and a smaller range but requires half the raw storage of binary64.

Binary64 is the conventional general-purpose choice for many scientific and engineering computations.

---

# 53. Precision Trade-Off

Choosing a floating-point format involves trade-offs.

| Property | Lower Precision | Higher Precision |
|---|---|---|
| Storage | Lower | Higher |
| Memory bandwidth | Lower | Higher |
| Precision | Lower | Higher |
| Dynamic range | Usually lower | Usually higher |
| Numerical robustness | Potentially lower | Potentially higher |
| Performance | Can be faster on suitable hardware | May be slower or equivalent |

The best choice depends on the application rather than on precision alone.

---

# 54. Exact Integer Representation

Binary64 can represent every integer exactly up to:

`2^53`

because it has 53 significant binary bits.

The important issue is what happens beyond that point.

Above `2^53`, consecutive integers are no longer all representable.

For example, some integers such as:

`2^53 + 1`

cannot be represented exactly as a binary64 float.

This matters when converting:

- Large identifiers
- Database keys
- High-resolution timestamps
- Large integer counts
- Financial quantities

to floating-point.

---

# 55. Large Integer Conversion

Converting an integer to float can lose information even though the original integer is exact.

For example:

`float(10**20)`

may represent a nearby value rather than the exact integer.

If exact integer semantics are required, retain the value as an integer.

Floating-point should not be used merely because a number is numerically large.

---

# 56. Conditioning

**Conditioning** describes how sensitive a mathematical problem is to small changes in its inputs.

An ill-conditioned problem can amplify small input errors dramatically.

This is different from algorithmic stability.

### Conditioning

A property of the mathematical problem.

### Stability

A property of the numerical method used to solve the problem.

A stable algorithm cannot completely overcome an intrinsically ill-conditioned problem.

---

# 57. Numerical Stability

A numerically stable algorithm attempts to control the effect of floating-point errors.

Typical techniques include:

- Avoiding unnecessary subtraction of nearly equal quantities
- Scaling inputs
- Reordering operations
- Using compensated summation
- Using stable library functions
- Reformulating equations
- Avoiding unnecessary overflow-prone intermediate results

The script demonstrates several of these ideas.

---

# 58. Stable Mathematical Functions

Specialized mathematical functions often exist because direct expressions can lose precision.

Examples include:

- `math.log1p(x)` for `log(1+x)`
- `math.expm1(x)` for `exp(x)-1`
- `math.hypot(x, y)` for Euclidean norms
- `math.fsum(values)` for accurate summation

For small `x`, directly calculating:

`log(1+x)`

can lose information because `1+x` may round to `1`.

`math.log1p(x)` is designed for this numerical situation.

---

# 59. `expm1`

For small `x`:

`exp(x)`

is very close to `1`.

Therefore:

`exp(x) - 1`

can suffer cancellation.

`math.expm1(x)` computes:

`exp(x) - 1`

with improved numerical behavior for small `x`.

This is an example of a library function encoding numerical-analysis knowledge into a reusable operation.

---

# 60. `hypot`

A naive Euclidean norm is:

`sqrt(x*x + y*y)`

For very large values, `x*x` or `y*y` can overflow even when the final Euclidean norm is representable.

`math.hypot(x, y)` uses a more robust algorithm.

This demonstrates that intermediate expressions can overflow even when the final mathematical result lies within the available range.

---

# 61. Log-Sum-Exp

A common computation is:

`log(sum(exp(x_i)))`

Directly calculating the exponentials can overflow for large inputs.

A stable transformation chooses:

`m = max(x_i)`

and computes:

`m + log(sum(exp(x_i - m)))`

Since each `x_i - m` is non-positive, the exponentials remain within a safer range.

The script implements this technique.

---

# 62. Stable Softmax

Softmax is:

`softmax(x_i) = exp(x_i) / sum(exp(x_j))`

Direct exponentiation of large inputs can overflow.

Subtracting the maximum input does not change the mathematical result:

`softmax(x_i) = exp(x_i-m) / sum(exp(x_j-m))`

where:

`m = max(x)`

The script implements stable softmax and verifies that the resulting probabilities sum approximately to one.

---

# 63. Horner's Method

A polynomial such as:

`x² - 3x + 2`

can be evaluated directly using powers or through Horner's method:

`(x - 3)x + 2`

Horner's method generally:

- Uses fewer arithmetic operations.
- Reduces explicit power computations.
- Can provide better numerical behavior.

The exact error properties still depend on the polynomial, coefficient scaling, and evaluation point.

---

# 64. Fused Multiply-Add

A fused multiply-add computes:

`a × b + c`

with a single final rounding rather than necessarily rounding the multiplication and addition separately.

This operation is commonly known as **FMA**.

Its advantages can include:

- Improved accuracy
- Fewer rounding steps
- Better numerical behavior in certain algorithms

The availability of `math.fma()` depends on the Python version and underlying platform.

The script detects whether it is available rather than assuming it exists.

---

# 65. Operation Order

Floating-point operations are not generally associative.

Consequently, changing operation order can change the final result.

This matters in:

- Parallel reductions
- Distributed numerical systems
- GPU kernels
- Scientific simulations
- Numerical optimization
- Matrix and vector computations

If reproducibility is required, the reduction order and numeric environment may need to be controlled.

---

# 66. Reproducibility

Numerical reproducibility can depend on:

- Floating-point format
- Operation ordering
- Hardware
- Compiler optimizations
- Fused operations
- Parallel reduction order
- Library implementations
- Rounding behavior
- Handling of subnormals

Bit-for-bit reproducibility can therefore require more control than simply using the same source code.

---

# 67. Serialization

Floating-point serialization should distinguish between:

- Human-readable decimal output
- Exact numerical round trips

A short decimal string can lose information.

Python's `repr()` is designed to provide a decimal representation suitable for recovering the same float in ordinary Python use.

`float.hex()` and `float.fromhex()` provide another exact representation for binary floating-point values.

---

# 68. Numerical Error Metrics

Two common error metrics are:

### Absolute error

`|approximation - reference|`

### Relative error

`|approximation - reference| / |reference|`

Absolute error is useful near zero.

Relative error is useful when the scale of the reference value matters.

A production numerical specification should define which error metric is meaningful.

---

# 69. Error Propagation

If:

`y = f(x)`

and the input has a small perturbation `dx`, the resulting change can often be approximated using a derivative:

`dy ≈ f'(x) dx`

For:

`y = x²`

we have:

`dy ≈ 2x dx`

This demonstrates how sensitivity can increase with the magnitude of an input.

For multiple variables, error propagation can involve gradients, Jacobians, covariance matrices, or interval methods depending on the application.

---

# 70. Approximate Zero

Testing whether a numerical result is zero often requires an absolute tolerance.

For example:

`abs(value) <= tolerance`

can be used when values close to zero are considered equivalent.

Relative tolerance alone is not sufficient because the relative error relative to zero is undefined.

---

# 71. Floating-Point Input Validation

Applications should explicitly decide whether NaN and infinity are valid inputs.

For example, a system processing physical measurements might reject:

- NaN
- Positive infinity
- Negative infinity

The script implements `validate_finite_float()` to demonstrate boundary validation.

This is especially important when numerical values cross application boundaries.

---

# 72. Overflow and Security

Unexpected floating-point special values can cause robustness problems.

For example, an application that assumes a value is finite may behave incorrectly if it receives infinity or NaN.

Potentially affected areas include:

- Resource calculations
- Financial computations
- Ranking
- Limits
- Geometry
- Billing
- Validation
- Scientific data processing

Numerical validation should therefore be treated as part of input validation when the application depends on finite values.

---

# 73. NaN and Validation Logic

NaN is particularly important because ordinary comparisons behave differently.

For example:

`NaN < 10`

is false.

`NaN > 10`

is also false.

`NaN == 10`

is false.

`NaN == NaN`

is false.

Therefore validation such as:

`if value > maximum:`

may not reject NaN.

Explicit `math.isnan()` or `math.isfinite()` checks may be required.

---

# 74. Infinity and Validation Logic

Infinity can pass some numerical checks unexpectedly.

For example:

`inf > 100`

is true.

A system that only checks whether a value is greater than a lower bound may accidentally accept infinity.

A robust validation policy should determine whether:

- Positive infinity is valid.
- Negative infinity is valid.
- NaN is valid.

When finite values are required, `math.isfinite()` is often appropriate.

---

# 75. Negative Zero

Negative zero can be relevant when the sign of zero carries mathematical or algorithmic information.

Python demonstrates it with:

`-0.0`

The values:

`+0.0`

and:

`-0.0`

compare equal, but their sign bits differ.

Use `math.copysign()` when the sign of zero needs to be inspected explicitly.

---

# 76. Numerical Testing

Numerical tests should account for the fact that mathematically equivalent results may differ slightly in floating-point arithmetic.

Useful techniques include:

- Absolute tolerance
- Relative tolerance
- ULP-based comparisons
- Boundary-value testing
- Exact reference calculations
- High-precision reference calculations
- Known mathematical invariants
- Property-based testing
- Regression tests for numerical edge cases

Exact equality remains appropriate when the algorithm is expected to produce exact representable results.

---

# 77. Testing Floating-Point Edge Cases

Important test categories include:

### Ordinary values

- Positive numbers
- Negative numbers
- Fractions
- Powers of two

### Boundary values

- Zero
- Smallest positive normal
- Smallest positive subnormal
- Largest finite value

### Special values

- Positive infinity
- Negative infinity
- NaN
- Positive zero
- Negative zero

### Precision-sensitive values

- Values near powers of two
- Values near integer precision limits
- Nearly equal operands
- Extremely different magnitudes

---

# 78. Debugging Floating-Point Problems

A useful debugging workflow is:

1. Print `repr(value)`.
2. Print `value.hex()`.
3. Inspect the raw bit pattern.
4. Check whether the value is finite.
5. Check whether it is NaN or infinity.
6. Check whether it is subnormal.
7. Inspect neighboring values using `math.nextafter()`.
8. Calculate absolute error.
9. Calculate relative error.
10. Compare against an exact or higher-precision reference.

The script implements a diagnostic report containing several of these properties.

---

# 79. Bit-Level Inspection

The Python `struct` module can convert a binary64 float into its raw 64-bit representation.

The script extracts:

- Sign
- Exponent field
- Fraction field
- Category

This is useful for understanding IEEE 754 directly rather than treating floating-point as an opaque language feature.

The same technique is demonstrated for binary32.

---

# 80. Special Binary64 Bit Patterns

Representative binary64 encodings include:

- All-zero bits for positive zero.
- Sign bit set with all remaining bits zero for negative zero.
- Maximum exponent and zero fraction for positive infinity.
- Maximum exponent, sign bit set, and zero fraction for negative infinity.
- Zero exponent with the least significant fraction bit set for the smallest positive subnormal.
- Maximum exponent with a nonzero fraction for NaN.

These patterns are useful when studying serialization, debugging, binary protocols, and low-level numerical software.

---

# 81. Exact Stored Float Values

`Fraction.from_float(value)` can reveal the exact rational value encoded by a binary64 float.

For example, `0.1` is stored as a rational number whose denominator is a power of two.

This demonstrates the difference between:

- The mathematical decimal value intended by the programmer.
- The exact binary64 value actually stored.
- The decimal string used to display the value.

These three concepts should not be conflated.

---

# 82. Floating-Point Hashing

Python's numeric equality and hashing rules are designed so that equal numeric values can behave consistently as dictionary keys and set elements.

For example:

`1 == 1.0`

is true, and their hashes are compatible.

NaN requires special care because NaN is not equal to itself.

Applications that use floating-point values as keys should consider whether approximate numerical equivalence is actually appropriate for the application.

---

# 83. Sorting and NaN

NaN does not participate in ordinary numerical ordering like finite values.

Because comparisons involving NaN are unordered, sorting collections containing NaN can produce behavior that does not correspond to an ordinary mathematical total order.

If a total ordering is required, the application should explicitly specify where NaN values belong.

---

# 84. Financial Calculations

Binary floating point is often unsuitable as the authoritative representation for exact monetary quantities.

For example:

`0.1 + 0.2`

does not produce the exact binary64 representation of `0.3`.

Common alternatives include:

### Decimal arithmetic

Useful when decimal rounding rules matter.

### Integer minor units

For example, store cents rather than dollars.

The correct approach depends on the domain's accounting and regulatory requirements.

---

# 85. Scientific and Engineering Applications

Binary floating point is highly useful for:

- Numerical simulation
- Physics
- Engineering
- Signal processing
- Statistics
- Graphics
- Geometry
- Optimization
- Numerical linear algebra

These applications generally tolerate approximation but require careful management of:

- Precision
- Range
- Conditioning
- Stability
- Error accumulation
- Scaling

---

# 86. Performance Considerations

Floating-point representation involves trade-offs between accuracy, range, memory usage, and performance.

Binary32 can reduce storage compared with binary64.

Binary64 provides greater precision and range.

Decimal and rational arithmetic generally require more computational work than binary floating-point.

Integer minor-unit arithmetic can be highly efficient for fixed-scale quantities.

Performance should be measured in the actual workload because hardware support and implementation details can significantly affect the relative costs.

---

# 87. Memory Considerations

The raw binary64 payload requires:

`8 bytes`

A Python `float` object itself requires additional object-management memory.

This distinction matters when processing large numerical datasets.

Compact numerical arrays can use substantially less memory per element than a collection of independent Python objects.

Memory layout also affects cache behavior and memory bandwidth.

---

# 88. Choosing a Numeric Type

A practical decision framework is:

### Use `float` when:

- Approximate binary arithmetic is acceptable.
- Large dynamic range is useful.
- Scientific or engineering calculations are being performed.
- Performance matters.
- The application is tolerant of small numerical errors.

### Use `Decimal` when:

- Decimal arithmetic semantics matter.
- Exact decimal input representation is required.
- Financial or accounting calculations require controlled decimal rounding.

### Use `Fraction` when:

- Exact rational arithmetic is required.
- Numerators and denominators are manageable.
- Performance and denominator growth are acceptable.

### Use `int` when:

- The domain is naturally integral.
- Exact counts are required.
- Fixed-scale quantities can be represented as minor units.

---

# 89. Common Mistakes

## Mistake 1: Assuming decimal fractions are binary-exact

`0.1` is not exactly representable in binary64.

## Mistake 2: Using `==` for approximate results

Use a justified tolerance when appropriate.

## Mistake 3: Treating machine epsilon as the smallest float

Machine epsilon describes spacing around one.

## Mistake 4: Ignoring NaN

NaN can bypass ordinary comparison logic.

## Mistake 5: Ignoring infinity

Infinity can result from overflow or appear at system boundaries.

## Mistake 6: Ignoring cancellation

Subtracting nearly equal values can destroy significant digits.

## Mistake 7: Ignoring operation order

Floating-point addition is not associative.

## Mistake 8: Assuming formatted output changes the stored value

Formatting only changes presentation.

## Mistake 9: Converting large integers to float unnecessarily

This can silently lose integer precision.

## Mistake 10: Assuming mathematically equivalent formulas have identical numerical behavior

Different formulas can have very different stability characteristics.

---

# 90. Implementation Considerations

When implementing numerical code:

1. Define the expected numerical range.
2. Define acceptable precision.
3. Identify whether absolute or relative error matters.
4. Check for cancellation.
5. Check for overflow.
6. Check for underflow.
7. Define NaN and infinity policies.
8. Select an appropriate numeric type.
9. Choose stable library functions.
10. Test boundary values.
11. Document tolerances.
12. Test operation-order sensitivity when reproducibility matters.

---

# 91. Production Considerations

Production numerical systems should treat floating-point behavior as part of the system's technical specification.

Important questions include:

- What precision is required?
- What values are valid?
- Are NaN and infinity allowed?
- What is the maximum acceptable error?
- Is exact reproducibility required?
- What happens during overflow?
- What happens during underflow?
- Is decimal exactness required?
- Are values serialized between different systems?
- Can a different language or platform interpret the data differently?
- Are large integers being converted to floating point?
- Are tolerance values documented?

A numerical specification should be explicit rather than relying on assumptions about machine precision.

---

# 92. Security Considerations

Floating-point values can interact with security and robustness when numerical assumptions are used in application logic.

Relevant issues include:

- NaN bypassing ordinary comparison-based validation.
- Infinity exceeding expected limits.
- Overflow producing non-finite results.
- Precision loss affecting authorization or resource calculations.
- Large integer conversion losing identity information.
- Numerical comparisons producing unexpected boundary behavior.
- Different operation order producing inconsistent decisions.

Security-sensitive validation should explicitly define accepted numeric domains and should not depend on informal assumptions about floating-point behavior.

---

# 93. Numerical Algorithm Design Checklist

For an algorithm involving floating-point values, consider:

1. Expected input range.
2. Required absolute accuracy.
3. Required relative accuracy.
4. Validity of NaN.
5. Validity of infinity.
6. Overflow-prone intermediate calculations.
7. Underflow-prone intermediate calculations.
8. Cancellation.
9. Operation ordering.
10. Summation strategy.
11. Stable mathematical transformations.
12. Numeric representation.
13. Boundary testing.
14. Tolerance documentation.
15. Reproducibility requirements.

---

# 94. Important Distinctions

Several concepts are frequently confused.

| Concept | Meaning |
|---|---|
| Range | Largest and smallest magnitudes representable |
| Precision | Number of significant digits/bits available |
| Machine epsilon | Spacing from 1.0 to the next larger representable value |
| ULP | Local representational spacing |
| Unit roundoff | Typical half-ULP scale for round-to-nearest analysis |
| Representation error | Difference between intended value and stored value |
| Rounding error | Difference introduced when an exact operation result is rounded |
| Conditioning | Sensitivity of the mathematical problem |
| Stability | Sensitivity of the numerical algorithm to arithmetic errors |
| Overflow | Result exceeds finite range |
| Underflow | Result becomes too small for normal representation |
| Subnormal | Small nonzero value below the normal range |
| NaN | Invalid or undefined numerical value |

---

# 95. Practical Numerical Patterns

Several patterns from the script are broadly useful.

### Use `math.isclose()`

When approximate equality is appropriate.

### Use `math.isfinite()`

When an application requires finite values.

### Use `math.isnan()`

When specifically detecting NaN.

### Use `math.nextafter()`

When examining representable neighbors.

### Use `math.fsum()`

When accurate summation matters.

### Use `math.log1p()`

For stable `log(1+x)` computations near zero.

### Use `math.expm1()`

For stable `exp(x)-1` computations near zero.

### Use `math.hypot()`

For robust Euclidean norms.

### Use `Decimal`

When decimal semantics are required.

### Use `Fraction`

When exact rational arithmetic is required.

---

# 96. Conceptual Model of IEEE 754 Binary64

For normal values, binary64 can be understood as:

`sign × significand × power_of_two`

with:

- 1 sign bit
- 11 exponent bits
- 52 stored fraction bits
- 53 effective significand bits
- exponent bias of 1023

The exponent determines scale.

The significand determines precision.

The sign determines direction.

Special exponent patterns encode zeros, subnormals, infinities, and NaNs.

---

# 97. Why Floating Point Is Useful

Floating point succeeds because it allocates finite bits dynamically across a large range of magnitudes.

A fixed-point system might have excellent precision around one scale but poor range.

Floating point provides approximately consistent relative precision across normal magnitudes.

The trade-off is that absolute spacing changes with magnitude.

This is the fundamental behavior behind both the usefulness and the limitations of floating-point arithmetic.

---

# 98. The Central Numerical Lesson

A floating-point value is not an arbitrary real number stored with a decimal point.

It is an element of a finite, structured set of representable binary values.

Consequently:

- Many decimal fractions are approximations.
- Spacing depends on magnitude.
- Arithmetic introduces rounding.
- Order can affect results.
- Overflow and underflow are real numerical conditions.
- Special values have defined semantics.
- Stable algorithms matter.
- Numeric type selection matters.
- Exactness and approximation are different design requirements.

Understanding these properties is necessary for writing reliable numerical software.

---

# 99. Scope of the Python Script

The script provides executable demonstrations of:

- Binary fractions
- Decimal-to-binary behavior
- IEEE 754 binary32
- IEEE 754 binary64
- Sign/exponent/fraction fields
- Normal values
- Subnormal values
- Zero
- Signed zero
- Infinity
- NaN
- NaN payloads
- Precision
- Machine epsilon
- Unit roundoff
- ULP spacing
- `math.nextafter`
- Representation error
- Rounding
- Cancellation
- Absorption
- Overflow
- Underflow
- Kahan summation
- Pairwise summation
- `math.fsum`
- Stable logarithms
- Stable exponentials
- Stable norms
- Log-sum-exp
- Stable softmax
- Horner's method
- FMA availability
- Exact integer limits
- `Decimal`
- `Fraction`
- Integer minor units
- Numerical validation
- Numerical testing
- Bit-level inspection
- Serialization
- Numerical debugging
- Security and robustness considerations
- Production-oriented design practices

The examples use only Python's standard library and are designed to be executable as a single standalone study script.
