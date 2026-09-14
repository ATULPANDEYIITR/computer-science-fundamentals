# Sequential logic circuits

## Introduction

Sequential logic circuits are digital circuits whose behavior depends on both present inputs and stored state. This distinguishes them from combinational circuits, where outputs depend only on current inputs.

The Python script develops sequential logic from simple storage elements to larger structures such as registers, counters, shift registers, frequency dividers, finite-state machines, and synchronous data paths.

The central relationship can be expressed conceptually as:

**Next state = function of current state and current inputs**

A sequential circuit therefore requires some mechanism for storing information. Common storage elements include latches and flip-flops. Multiple storage elements can be combined to create registers and counters, while larger collections of registers and combinational logic form processors, controllers, communication interfaces, and other digital systems.

## Combinational and sequential logic

A combinational circuit has no intentional memory.

Examples include:

- AND gates
- OR gates
- XOR gates
- multiplexers
- decoders
- adders

The script begins with NOT, AND, OR, and XOR operations and then demonstrates half-adders and full-adders.

A sequential circuit contains state.

Examples include:

- latches
- flip-flops
- registers
- counters
- finite-state machines

A useful distinction is:

| Property | Combinational logic | Sequential logic |
|---|---|---|
| State | No stored state | Stores state |
| Output depends on | Current inputs | Current inputs and state |
| Feedback | Usually absent or carefully controlled | Common |
| Clock | Usually unnecessary | Often used |
| Examples | Adder, multiplexer | Register, counter |

## State and feedback

State represents information retained from an earlier point in time.

For example, a one-bit storage element may currently contain:

`Q = 1`

Even when its input later changes, the stored output can remain 1 until a permitted control or clock event changes it.

Feedback is fundamental to storage. The circuit's previous output participates in determining its future behavior. This allows a circuit to remember information.

The script models this behavior directly through Python classes whose objects maintain an internal `q`, `bits`, or `count` value.

## Clock signals

A clock is a periodic digital timing signal used to coordinate state changes.

An idealized clock alternates between:

- logic LOW, represented by 0
- logic HIGH, represented by 1

Important clock terminology includes:

### Period

The period is the time for one complete clock cycle.

It is commonly represented as:

**T = 1 / f**

where `T` is period and `f` is frequency.

### Frequency

Frequency represents the number of complete cycles per unit of time.

For example, a 100 MHz clock has a frequency of 100 million cycles per second.

### Rising edge

A rising edge is the transition:

**0 → 1**

### Falling edge

A falling edge is the transition:

**1 → 0**

Many flip-flops are edge-triggered. A positive-edge-triggered device responds to the rising edge, while a negative-edge-triggered device responds to the falling edge.

The `Clock` class in the script provides an idealized clock model and records rising and falling transitions.

Real clocks are not perfectly ideal. Physical systems can experience jitter, skew, duty-cycle distortion, noise, and propagation delay.

## Latches

A latch is a level-sensitive storage element.

Level-sensitive means that the storage element can respond during an active level of a control signal rather than only at one instantaneous transition.

For example, a D latch can be described as:

- Enable = 1: Q follows D
- Enable = 0: Q holds its previous value

This distinction is important because a latch can be transparent for part of a clock or enable interval.

## SR latch

An SR latch has two primary inputs:

- S: Set
- R: Reset

For a conventional active-high NOR SR latch:

| S | R | Behavior |
|---|---|---|
| 0 | 0 | Hold |
| 0 | 1 | Reset |
| 1 | 0 | Set |
| 1 | 1 | Invalid or forbidden |

The hold operation demonstrates memory. When both inputs are inactive, the latch retains its previous value.

The `SRLatch` class explicitly rejects the forbidden `S=1, R=1` combination.

The exact invalid condition depends on the latch implementation. NAND-based active-low SR structures use different input conventions, so the active level must always be identified before interpreting a truth table.

## Gated SR latch

A gated SR latch adds an enable signal.

When enable is inactive, the latch holds its state.

When enable is active, the S and R inputs control the state.

This provides a basic mechanism for controlling when a storage element is allowed to respond to its inputs.

## D latch

The D latch simplifies the SR interface by using a single data input.

Its fundamental behavior is:

| Enable | D | Q behavior |
|---|---|---|
| 0 | 0 or 1 | Hold |
| 1 | 0 | Q becomes 0 |
| 1 | 1 | Q becomes 1 |

The D latch is useful when the desired operation is simply to store one data bit.

Its single data input also avoids the direct presentation of the forbidden S/R combination found in a conventional SR latch.

## Flip-flops

A flip-flop is commonly described as an edge-triggered storage element.

Unlike a level-sensitive latch, an edge-triggered flip-flop normally samples its input at a particular clock transition.

A positive-edge-triggered D flip-flop therefore behaves conceptually as:

**At the rising edge: Q ← D**

Between active clock edges, changes in D do not immediately change Q.

This behavior makes flip-flops especially useful for synchronous digital systems.

## D flip-flop

The D flip-flop has one primary data input:

**D**

Its characteristic equation is:

**Q(next) = D**

at the active clock edge.

The script implements a positive-edge-triggered D flip-flop by detecting a transition from clock level 0 to clock level 1.

This implementation demonstrates an important point: simply observing that the clock is HIGH is not equivalent to detecting a rising edge.

A level-sensitive latch can remain responsive while a control signal is active. An edge-triggered flip-flop responds to a transition.

## JK flip-flop

The JK flip-flop extends the SR concept.

Its behavior is:

| J | K | Operation |
|---|---|---|
| 0 | 0 | Hold |
| 0 | 1 | Reset |
| 1 | 0 | Set |
| 1 | 1 | Toggle |

The toggle operation is particularly useful for counters.

For J = K = 1:

**Q(next) = NOT Q**

The JK structure avoids the forbidden state associated with the basic SR latch interface.

In practical modern digital design, D flip-flops are extremely common, while JK behavior remains important for understanding sequential logic and counter design.

## T flip-flop

A T flip-flop has a single primary control input.

Its behavior is:

| T | Operation |
|---|---|
| 0 | Hold |
| 1 | Toggle |

When T is permanently connected to logic 1, the output changes state at every active clock edge.

This produces frequency division.

If an input clock has frequency `f`, an ideal toggle flip-flop produces an output with frequency:

**f / 2**

Cascading toggle stages can produce further division.

## Characteristic equations

Common simplified characteristic equations include:

### D flip-flop

**Q(next) = D**

### T flip-flop

**Q(next) = T XOR Q**

### JK flip-flop

A commonly used characteristic expression is:

**Q(next) = JQ' + K'Q**

These equations describe the next state at the active sampling event.

Characteristic tables are useful when analyzing existing circuits. Excitation tables are useful when designing a circuit that must transition from a known current state to a desired next state.

## Setup time

Setup time is the minimum interval during which the input data must remain stable before the active clock edge.

If the data changes too close to the clock edge, the storage element may not reliably capture the intended value.

The script includes a simplified timing check that compares a data transition time with a clock edge.

## Hold time

Hold time is the minimum interval for which data must remain stable after the active clock edge.

A complete timing analysis therefore considers both:

- setup time before the edge
- hold time after the edge

Violating either requirement can produce incorrect or unpredictable behavior.

## Propagation delay

Propagation delay is the time between an input or clock transition and the corresponding output response.

For a real flip-flop, the output does not change instantaneously after the clock edge.

Propagation delay is important when calculating the maximum operating frequency of a synchronous system.

## Metastability

Metastability can occur when a physical storage element samples a signal that changes too close to its sampling edge.

Instead of immediately resolving to a valid digital 0 or 1, the internal analog state can temporarily become uncertain.

Metastability is a physical phenomenon. A normal Boolean simulation cannot accurately predict its analog resolution behavior.

A common engineering technique for transferring a single asynchronous control signal into a clock domain is a multi-stage synchronizer, often implemented with two flip-flops. The additional stages reduce the probability that metastability propagates into downstream logic, although they do not mathematically eliminate it.

## Latches versus flip-flops

The distinction is fundamental.

| Characteristic | Latch | Edge-triggered flip-flop |
|---|---|---|
| Sensitivity | Level-sensitive | Edge-sensitive |
| Control | Enable or clock level | Clock transition |
| Transparency | Can be transparent during active level | Samples at edge |
| Typical use | Timing structures and controlled storage | Synchronous registers and pipelines |
| Timing analysis | Includes latch transparency | Primarily edge-to-edge timing |

Latches are not inherently inferior to flip-flops. They can be useful in carefully designed timing architectures. They do require careful analysis because data may propagate through the latch during its transparent interval.

## Registers

A register is a collection of storage elements used to store multiple bits.

An 8-bit register contains eight one-bit storage elements conceptually.

The script's `Register` class provides:

- loading a value
- reading the value
- binary representation
- clearing
- setting all bits

For example, the decimal value 42 is represented in eight bits as:

`00101010`

A register can therefore preserve an entire binary word rather than only one bit.

Registers are fundamental components of:

- processors
- microcontrollers
- digital signal processors
- communication systems
- hardware state machines
- pipeline stages
- memory interfaces

## Parallel registers

A parallel register loads multiple bits at the same clock event.

For an N-bit register, N storage elements normally operate together.

Parallel loading is appropriate when the complete data word is already available simultaneously.

## Shift registers

A shift register moves stored bits in a defined direction on each shift event.

For example, an 8-bit shift register can transform:

`10110010`

by shifting left and inserting a new serial bit.

Shift registers can be used for:

- serial data transfer
- serial-to-parallel conversion
- parallel-to-serial conversion
- programmable delays
- display control
- data manipulation

The exact meaning of left and right shift depends on the chosen bit-order convention. The script explicitly documents its convention to avoid ambiguity.

## Serial-to-parallel conversion

Serial data arrives one bit at a time.

A shift register can collect the incoming bits until a complete word has been received.

For example:

`11010110`

can be transmitted one bit at a time and reconstructed into the same eight-bit value.

This principle appears in serial communication interfaces and many hardware data paths.

## Parallel-to-serial conversion

A parallel word can be loaded into a register and shifted out one bit at a time.

The script's `parallel_to_serial` function converts an integer into an MSB-first bit sequence.

Real hardware commonly uses a parallel-load shift register to implement this operation.

## Universal shift registers

A universal shift register can support multiple operations, such as:

- hold
- shift left
- shift right
- parallel load

A hardware implementation commonly uses multiplexing logic before the flip-flop inputs so that the desired source can be selected.

The script models these operations through the `UniversalShiftRegister` class.

## Counters

A counter is sequential logic that advances through a predefined state sequence in response to clock events.

A binary counter commonly follows:

`000 → 001 → 010 → 011 → 100 → ...`

A three-bit binary counter has eight possible states:

**2³ = 8**

After the highest state, a modulo-8 counter returns to zero.

## Synchronous counters

In a synchronous counter, the storage elements receive a common clock.

This allows the state transition to be designed so that the counter bits update in a coordinated manner.

Synchronous counters generally provide better timing behavior than ripple counters when high-speed or predictable timing is important.

The script includes synchronous up and down counters.

## Asynchronous or ripple counters

In an asynchronous counter, the output of one storage element can act as the timing input for a subsequent stage.

The transition therefore propagates through the chain rather than occurring simultaneously.

This is why it is called a ripple counter.

The principal limitation is accumulated propagation delay. During a transition, intermediate combinations can briefly occur.

For example, a multi-bit transition such as:

`0111 → 1000`

requires several bits to change. In an ideal synchronous representation, the transition is treated as one clocked state change. In a ripple implementation, individual stages can change at different times.

The script's `RippleCounter` records conceptual intermediate states to illustrate this behavior.

## Up counters and down counters

An up counter increments:

`0, 1, 2, 3, ...`

A down counter decrements:

`7, 6, 5, 4, ...`

Binary counters naturally wrap around their available state space.

For an N-bit counter:

**modulus = 2^N**

## Modulo-N counters

A modulo-N counter contains N logical states in its cycle, where N does not necessarily have to be a power of two.

A modulo-10 counter cycles through:

`0 → 1 → 2 → ... → 9 → 0`

Four bits are required because:

**2³ = 8**, which is insufficient.

**2⁴ = 16**, which is sufficient.

The remaining six four-bit combinations are unused by the intended modulo-10 sequence.

Unused states require deliberate design consideration. A robust hardware implementation should define how invalid states are handled, especially when recovery to a valid state is required.

## Counter width calculation

The minimum width for a modulo-N counter is:

**ceil(log₂(N))**

For example:

| Modulus | Minimum bits | Available binary states |
|---:|---:|---:|
| 2 | 1 | 2 |
| 3 | 2 | 4 |
| 4 | 2 | 4 |
| 5 | 3 | 8 |
| 8 | 3 | 8 |
| 10 | 4 | 16 |
| 16 | 4 | 16 |
| 17 | 5 | 32 |
| 100 | 7 | 128 |
| 256 | 8 | 256 |

## Ring counters

A ring counter circulates a single active bit.

A four-bit ring counter can follow:

`1000 → 0100 → 0010 → 0001 → 1000`

The state is one-hot because exactly one bit is active in every valid state.

A ring counter with N bits normally provides N useful states.

A major consideration is initialization. If the counter begins in an invalid all-zero state, a simple circulating-one design may remain stuck there.

## Johnson counters

A Johnson counter is a twisted-ring counter.

Instead of feeding the final output directly back into the first stage, its complement is fed back.

For four bits, a typical sequence is:

`0000 → 1000 → 1100 → 1110 → 1111 → 0111 → 0011 → 0001 → 0000`

An N-bit Johnson counter provides up to 2N distinct states in its intended sequence.

Johnson counters are useful for:

- sequence generation
- timing generation
- simple state decoding
- control circuits

## Frequency division

A T flip-flop with T permanently asserted toggles on every active clock edge.

This produces a divide-by-two output.

A chain of toggle stages can produce:

- divide by 2
- divide by 4
- divide by 8
- divide by 16

and so on.

This is closely related to binary counters because each successive binary stage represents a lower-frequency signal.

Frequency-divider circuits are used in timing systems, clock generation, counters, and communication hardware.

## Reset

Reset establishes a known initial state.

A reset can be:

- synchronous
- asynchronous

A synchronous reset is acted upon according to the clocking mechanism.

An asynchronous reset can affect the storage element independently of the normal clock event.

The correct choice depends on the system architecture and technology.

Reset implementation also requires careful consideration of reset assertion and deassertion timing. In practical systems, asynchronous reset release can create timing problems if not synchronized appropriately.

The script includes an illustrative resettable D flip-flop.

## Enable signals

An enable allows a sequential element to update only when a particular condition is true.

For an enabled counter:

- reset active → reset state
- enable active → increment
- enable inactive → hold

Clock enables are commonly used to control state updates without unnecessarily changing the logical state on every clock cycle.

## Finite-state machines

A finite-state machine, or FSM, is a sequential system with a finite set of states.

A state machine normally contains:

- current state
- inputs
- next-state logic
- state storage
- outputs

Two major FSM classifications are:

### Moore machine

Outputs depend primarily on the current state.

### Mealy machine

Outputs depend on the current state and current inputs.

The script demonstrates a small traffic-light FSM using enumerated states.

FSMs are widely used in:

- communication protocols
- processor control units
- traffic controllers
- user interfaces
- bus controllers
- memory controllers
- hardware sequencing

## Synchronous design

A synchronous digital system uses clock events to coordinate state transitions.

A common conceptual architecture is:

**register → combinational logic → register**

The first register stores an input state. Combinational logic calculates a result. The second register captures that result at a later clock edge.

The script demonstrates this concept using a two-stage pipeline.

## Pipeline registers

Pipeline registers divide a long computation into multiple timing stages.

If one combinational path is too slow for a target clock frequency, the work can be divided into smaller sections with registers between them.

This can increase throughput because multiple inputs can occupy different stages simultaneously.

Pipeline design introduces latency and requires careful management of:

- setup time
- hold time
- clock skew
- propagation delay
- data dependencies
- control hazards
- reset behavior

## Sequential accumulator

The script implements an accumulator:

**A(next) = A(current) + input**

The stored accumulator value persists between clock events.

For example, inputs of:

`10, 20, 50`

produce accumulated states:

`10, 30, 80`

This is a simple example of stateful arithmetic.

Accumulators are common in:

- digital signal processing
- counters
- timers
- numerical hardware
- control systems

## Timing analysis

For a basic register-to-register synchronous path, a simplified maximum-frequency relationship can be expressed conceptually as:

**Tclock ≥ Tcq + Tcomb + Tsetup + Tskew/jitter margin**

where:

- `Tcq` is clock-to-Q delay
- `Tcomb` is combinational propagation delay
- `Tsetup` is destination setup time
- clock uncertainty includes effects such as skew and jitter

The exact timing equations used by physical design tools are more detailed.

Hold timing is analyzed separately and concerns the minimum delay path after a clock edge.

The script's timing model is intentionally simplified for conceptual learning. It should not be interpreted as a replacement for static timing analysis of real hardware.

## Edge cases

The script deliberately tests invalid situations.

Examples include:

- non-binary input values
- negative register widths
- values that do not fit a register
- zero or negative counter modulus
- invalid SR latch input combinations
- invalid shift inputs

Input validation is important because digital hardware has defined legal state spaces and interfaces.

For a Python simulation, rejecting invalid values makes incorrect assumptions visible immediately.

For real hardware, equivalent protection may be achieved through circuit constraints, state recovery logic, protocol validation, fault detection, or architectural design.

## Unused states

A binary storage structure with N bits provides:

**2^N**

possible combinations.

A state machine may intentionally use only some of them.

For example, a modulo-10 counter uses ten states but a four-bit implementation provides sixteen possible states.

The six unused states must be considered.

Possible strategies include:

- reset to a known state
- transition unused states to a valid state
- detect invalid states
- use don't-care conditions when justified by the design methodology

Ignoring unused states can make a circuit harder to recover from faults or unexpected initialization conditions.

## Common mistakes

### Confusing a latch with a flip-flop

A latch is level-sensitive. An edge-triggered flip-flop samples at a clock transition.

### Ignoring setup and hold requirements

A circuit can be logically correct yet fail at its target operating frequency if timing requirements are violated.

### Assuming all bits change simultaneously

Ripple counters demonstrate why propagation delay matters.

### Ignoring invalid states

Modulo counters and FSMs may have states that are not part of their intended sequence.

### Treating reset as ordinary data

Reset has architectural timing implications and should be analyzed as part of the sequential design.

### Assuming simulation proves hardware correctness

Functional simulation verifies modeled logic behavior. It does not automatically verify physical timing, metastability behavior, signal integrity, power integrity, or manufacturing variation.

### Creating uncontrolled feedback

Feedback is necessary for storage but uncontrolled combinational feedback can create oscillation, instability, or synthesis problems.

## Design trade-offs

### Latch versus flip-flop

Latches can support time borrowing in some architectures and can be efficient in particular designs. Their transparency makes timing analysis more complex.

Flip-flops provide a straightforward edge-based abstraction and are widely used in synchronous designs, at the cost of their own area, clock power, and timing characteristics.

### Synchronous versus ripple counters

Synchronous counters provide coordinated state transitions and are generally preferable when predictable high-speed timing is important.

Ripple counters can use relatively simple structures but suffer from cumulative propagation delay and transient intermediate states.

### Ring versus binary counters

A binary counter represents many states with relatively few bits.

A ring counter uses more storage elements for its state sequence but can make certain one-hot control operations simple.

### Johnson versus ring counters

A ring counter with N stages normally provides N one-hot states.

A Johnson counter with N stages can provide up to 2N states, although the state encoding and decoding requirements differ.

## Performance considerations

The performance of sequential circuits is strongly related to timing.

Important factors include:

- maximum clock frequency
- clock-to-Q delay
- combinational delay
- setup time
- hold time
- clock skew
- clock jitter
- routing delay
- fan-out
- physical implementation

Increasing clock frequency reduces the available time per cycle.

For example, a 1 GHz clock has a period of:

**1 ns**

A 500 MHz clock has a period of:

**2 ns**

Every synchronous path must satisfy the relevant timing constraints within the available cycle.

## Power considerations

Sequential circuits consume power through both switching and leakage.

Clock networks are particularly important because clock signals can toggle across large portions of a chip.

Reducing unnecessary switching can reduce dynamic power.

Common architectural techniques include:

- clock enables
- appropriate power domains
- reduced switching activity
- efficient state encoding
- carefully controlled clock distribution

Actual clock-gating implementation requires technology-specific methodology and timing verification.

## Security considerations

Sequential logic can influence security because state can contain sensitive information.

Relevant concerns include:

- clearing registers containing sensitive data
- preventing unintended information leakage through state transitions
- ensuring reset behavior is well defined
- validating protocol state transitions
- handling fault conditions
- preventing unauthorized state changes

In hardware security, attackers may deliberately manipulate timing, voltage, clock signals, or fault conditions. Robust state-machine design and defensive fault handling can therefore be important parts of secure hardware architecture.

## Testing and verification

The script contains automated assertions for:

- logic gates
- SR latches
- D latches
- D flip-flops
- JK flip-flops
- T flip-flops
- registers
- shift registers
- counters
- ring counters
- Johnson counters

Testing sequential circuits requires checking sequences, not only individual input/output combinations.

A combinational circuit can often be tested with a truth table.

A sequential circuit requires tests that consider:

- initial state
- current input
- clock event
- previous state
- next state
- reset behavior
- enable behavior
- invalid states

This is why state-transition testing is central to sequential-logic verification.

## Implementation considerations

The Python classes in the script are behavioral models. They represent logical behavior rather than transistor-level electrical implementation.

A real digital circuit may be constructed from:

- CMOS transistors
- logic gates
- latches
- flip-flop cells
- multiplexers
- buffers
- clock networks

Hardware description languages such as Verilog or VHDL can describe synthesizable sequential logic. Synthesis tools then map the logical description to technology-specific cells.

A Python behavioral model is useful for learning algorithms and state transitions, but it does not directly model all physical implementation details.

## Registers, counters, and system architecture

The final mini-system in the script combines:

- an 8-bit input register
- an 8-bit accumulator
- a modulo-16 counter
- enable control
- reset behavior

This demonstrates how simple sequential components can form a larger synchronous system.

The conceptual flow is:

**input → register → accumulator**

while the counter independently tracks clocked events.

Each clock event provides an opportunity for state to change according to the system's rules.

## Real-world relevance

Sequential logic is foundational to digital computing.

Processors use registers and flip-flops to maintain architectural and microarchitectural state.

Memory interfaces rely on carefully timed storage elements.

Communication systems use shift registers, counters, state machines, and synchronizers.

Timers and digital clocks depend heavily on counters and frequency division.

Control systems use finite-state machines to sequence operations.

Modern integrated circuits contain enormous numbers of sequential elements organized into synchronous timing structures.

Understanding latches, flip-flops, registers, counters, and clock signals therefore provides the conceptual foundation for analyzing larger digital systems.
