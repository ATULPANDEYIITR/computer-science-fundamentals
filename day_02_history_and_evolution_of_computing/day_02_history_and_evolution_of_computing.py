"""
HISTORY AND EVOLUTION OF COMPUTING
===================================

This program is an educational timeline and reference guide to the history
and evolution of computing.

It covers:

1. Early human calculation and numerical systems
2. Mechanical calculation devices
3. Charles Babbage and Ada Lovelace
4. Electromechanical computing
5. Early electronic computers
6. Generations of computers
7. Vacuum tubes, transistors, integrated circuits and microprocessors
8. Stored-program computing
9. Major computer architectures
10. Programming language evolution
11. Operating-system evolution
12. Networking and the Internet
13. Personal computers
14. Graphical user interfaces
15. World Wide Web
16. Mobile computing
17. Cloud computing
18. Distributed and parallel computing
19. GPUs and specialized processors
20. Artificial intelligence and machine learning
21. Modern computing paradigms
22. Important historical machines and people
23. Important technical concepts
24. Historical relationships between hardware and software
25. The transition from mechanical to electronic and intelligent systems

The code is intentionally verbose and explanatory. It is designed to be
read as a learning document as well as executed as a Python program.
"""


# ============================================================================
# 1. INTRODUCTION
# ============================================================================

def introduction():
    print("=" * 80)
    print("HISTORY AND EVOLUTION OF COMPUTING")
    print("=" * 80)

    print("""
Computing is the study and practice of processing information using
algorithms, machines, data structures, hardware, software, and communication
systems.

The history of computing is not simply the history of computers.

It is the history of humanity's attempt to:

    - represent information
    - perform calculations
    - automate repetitive work
    - store information
    - communicate information
    - make decisions using rules
    - process increasingly large amounts of data
    - automate reasoning and learning

Modern computers are the result of several centuries of development.

The progression can be broadly understood as:

    Human calculation
        |
        v
    Manual counting devices
        |
        v
    Mechanical calculators
        |
        v
    Programmable mechanical machines
        |
        v
    Electromechanical machines
        |
        v
    Electronic computers
        |
        v
    Transistor-based computers
        |
        v
    Integrated circuits
        |
        v
    Microprocessors
        |
        v
    Personal computers
        |
        v
    Networked computing
        |
        v
    Internet and Web
        |
        v
    Mobile and cloud computing
        |
        v
    Parallel and accelerated computing
        |
        v
    Artificial intelligence and intelligent systems

The important point is that each stage solved limitations of the previous
stage while creating new possibilities.
""")

    print()


# ============================================================================
# 2. WHAT IS COMPUTING?
# ============================================================================

def what_is_computing():
    print("=" * 80)
    print("WHAT IS COMPUTING?")
    print("=" * 80)

    concepts = {
        "Data":
            "Represented information that can be stored or processed.",

        "Algorithm":
            "A finite and well-defined procedure for solving a problem.",

        "Computation":
            "The execution of operations according to specified rules.",

        "Computer":
            "A programmable machine capable of accepting input, processing it, "
            "storing information, and producing output.",

        "Hardware":
            "The physical components of a computing system.",

        "Software":
            "Programs and instructions that control computer hardware.",

        "Information":
            "Data interpreted in a meaningful context.",

        "Programming":
            "The process of expressing algorithms in a form that a computer "
            "can execute."
    }

    for concept, definition in concepts.items():
        print(f"{concept}:")
        print(f"    {definition}")
        print()

    print("""
Computing is broader than computer science.

Computer science investigates computation, algorithms, programming,
data structures, operating systems, networks, architecture, artificial
intelligence, databases, security, and many other areas.

Computing has also influenced mathematics, science, engineering,
business, medicine, communication, entertainment, government and education.
""")

    print()


# ============================================================================
# 3. HUMAN CALCULATION BEFORE MACHINES
# ============================================================================

def early_human_computation():
    print("=" * 80)
    print("EARLY HUMAN COMPUTATION")
    print("=" * 80)

    print("""
Before machines existed, humans performed computation manually.

Early societies needed calculation for:

    - trade
    - taxation
    - agriculture
    - construction
    - astronomy
    - calendars
    - navigation
    - accounting
    - surveying

The earliest form of computation was therefore closely connected to
record keeping and measurement.
""")

    print("Major developments:")
    developments = [
        "Tally marks",
        "Finger counting",
        "Pebbles and tokens",
        "Clay tablets",
        "Numerical notation",
        "Place-value systems",
        "Written arithmetic",
        "Multiplication and division procedures",
        "Astronomical calculation"
    ]

    for number, item in enumerate(developments, start=1):
        print(f"{number:2}. {item}")

    print("""
A crucial historical development was the creation of numerical systems.

Different civilizations developed different representations of numbers.
The Babylonian, Egyptian, Greek, Roman, Indian, Chinese and other traditions
contributed to the development of mathematics.

The modern positional decimal system is strongly associated with the
Indian mathematical tradition and later transmission through the Islamic
world into Europe.

The idea of place value was extremely important because it made arithmetic
more systematic and suitable for algorithms.
""")

    print()


# ============================================================================
# 4. ABACUS
# ============================================================================

def abacus():
    print("=" * 80)
    print("THE ABACUS")
    print("=" * 80)

    print("""
The abacus is one of the most important early calculation devices.

It uses physical objects, usually beads or counters, arranged according
to positional values.

An abacus does not automatically execute arbitrary programs.

Instead, a human operator manipulates its components according to
mathematical procedures.

Its importance lies in the separation between:

    physical representation of numbers
                    +
    systematic calculation procedure
""")

    print("""
Important ideas represented by the abacus:

    1. Representation
       Numbers can be represented physically.

    2. Position
       The position of a bead can represent different numerical values.

    3. Procedure
       Calculation can follow repeatable rules.

    4. External memory
       The physical arrangement preserves intermediate results.

The abacus therefore represents an early stage in the development of
human-machine computation.
""")

    print()


# ============================================================================
# 5. NUMERICAL SYSTEMS
# ============================================================================

def numerical_systems():
    print("=" * 80)
    print("NUMERICAL SYSTEMS AND THE DEVELOPMENT OF COMPUTATION")
    print("=" * 80)

    systems = {
        "Decimal": "Base 10. Uses digits 0 through 9.",
        "Binary": "Base 2. Uses digits 0 and 1.",
        "Octal": "Base 8. Uses digits 0 through 7.",
        "Hexadecimal": "Base 16. Uses digits 0 through 9 and A through F.",
        "Roman numerals":
            "A non-positional numerical representation based on symbols."
    }

    for name, description in systems.items():
        print(f"{name}: {description}")

    print("""
Binary became especially important in electronic computing because many
electronic components can conveniently represent two distinguishable states.

A binary digit is called a bit.

A bit can represent:

    0 or 1
    false or true
    off or on
    low or high

This does not mean that computers inherently understand only the concepts
of zero and one. Rather, physical systems can reliably distinguish two
states, and logical systems can be built from those states.
""")

    print()


# ============================================================================
# 6. NAPIER'S BONES
# ============================================================================

def napiers_bones():
    print("=" * 80)
    print("NAPIER'S BONES")
    print("=" * 80)

    print("""
John Napier developed logarithms and Napier's Bones in the early
seventeenth century.

Napier's Bones consisted of numbered rods that helped simplify
multiplication and division.

The broader historical significance is that mathematical operations
were increasingly being transformed into structured mechanical procedures.

Logarithms later became extremely important for calculation because they
allowed multiplication to be transformed into addition.

    multiplication of numbers
              |
              v
        addition of logarithms
              |
              v
       conversion back

Before electronic calculators, logarithmic methods were widely used by
scientists, engineers and navigators.
""")

    print()


# ============================================================================
# 7. SLIDE RULE
# ============================================================================

def slide_rule():
    print("=" * 80)
    print("THE SLIDE RULE")
    print("=" * 80)

    print("""
The slide rule emerged from logarithmic principles.

It is an analog calculating instrument.

Instead of representing numbers through discrete electronic states,
it represents numerical relationships through physical positions.

Slide rules were widely used for:

    - engineering
    - physics
    - navigation
    - architecture
    - scientific calculation

The slide rule demonstrates an important distinction:

DIGITAL COMPUTING
    represents values discretely.

ANALOG COMPUTING
    represents values through continuous physical quantities.
""")

    print()


# ============================================================================
# 8. PASCALINE
# ============================================================================

def pascaline():
    print("=" * 80)
    print("PASCALINE")
    print("=" * 80)

    print("""
Blaise Pascal developed the Pascaline in the seventeenth century.

It was a mechanical calculator designed primarily for arithmetic
operations such as addition and subtraction.

The machine used gears and mechanical mechanisms.

Its significance is not that it was a modern computer.

Its importance is that it demonstrated that arithmetic could be partially
automated using mechanical machinery.

This introduced a fundamental idea:

    arithmetic procedure
            +
    mechanical mechanism
            =
    automated calculation
""")

    print()


# ============================================================================
# 9. LEIBNIZ STEPPED RECKONER
# ============================================================================

def leibniz_machine():
    print("=" * 80)
    print("LEIBNIZ STEPPED RECKONER")
    print("=" * 80)

    print("""
Gottfried Wilhelm Leibniz developed the Stepped Reckoner in the
seventeenth century.

It improved mechanical calculation by supporting multiplication and
division as well as addition and subtraction.

Leibniz was also an important mathematical thinker.

His work helped reinforce the idea that calculations could be represented
as formal operations.

Leibniz also promoted binary arithmetic.

Binary representation later became fundamental to digital computing.
""")

    print()


# ============================================================================
# 10. JACQUARD LOOM
# ============================================================================

def jacquard_loom():
    print("=" * 80)
    print("JACQUARD LOOM")
    print("=" * 80)

    print("""
Joseph-Marie Jacquard developed a mechanism for controlling textile
patterns using punched cards.

The punched cards encoded instructions about which threads should be
raised or lowered.

The machine is historically important because it demonstrated:

    DATA/INSTRUCTIONS
            |
            v
    PHYSICAL ENCODING
            |
            v
    AUTOMATIC MACHINE BEHAVIOR

The machine was not a general-purpose computer.

Its importance is the principle of programmable control.
""")

    print()


# ============================================================================
# 11. CHARLES BABBAGE
# ============================================================================

def charles_babbage():
    print("=" * 80)
    print("CHARLES BABBAGE")
    print("=" * 80)

    print("""
Charles Babbage is one of the central figures in computing history.

He designed two major machines:

    1. Difference Engine
    2. Analytical Engine

The Difference Engine was designed to automate mathematical calculations,
especially the generation of mathematical tables.

The Analytical Engine was much more ambitious.

It introduced ideas resembling components of modern computers.
""")

    components = {
        "Mill":
            "The computational unit, broadly analogous to a processor.",
        "Store":
            "The storage area for numbers, analogous to memory.",
        "Input":
            "A mechanism for supplying instructions and data.",
        "Output":
            "A mechanism for producing results.",
        "Control":
            "A mechanism intended to determine the sequence of operations."
    }

    for component, meaning in components.items():
        print(f"{component}:")
        print(f"    {meaning}")
        print()

    print("""
The Analytical Engine was never completed as a fully functioning
general-purpose machine during Babbage's lifetime.

Its conceptual significance is enormous.

Babbage moved the idea of computation toward:

    programmable
    general-purpose
    stored numerical processing

This is much closer to the conceptual structure of modern computers.
""")

    print()


# ============================================================================
# 12. ADA LOVELACE
# ============================================================================

def ada_lovelace():
    print("=" * 80)
    print("ADA LOVELACE")
    print("=" * 80)

    print("""
Augusta Ada King, Countess of Lovelace, worked with ideas surrounding
Babbage's Analytical Engine.

She is widely recognized for writing what is often described as the first
published computer algorithm intended for implementation on a machine.

Her work concerned the calculation of Bernoulli numbers using the
Analytical Engine.

More importantly, Lovelace understood something deeper than arithmetic.

She recognized that a general-purpose machine could manipulate symbols
according to rules.

This insight points toward the broader concept of programmable computation.

A machine does not have to be designed only for arithmetic.

If information can be represented symbolically and operations can be
specified algorithmically, a general-purpose machine can process many
different kinds of information.
""")

    print()


# ============================================================================
# 13. GEORGE BOOLE
# ============================================================================

def george_boole():
    print("=" * 80)
    print("GEORGE BOOLE AND BOOLEAN LOGIC")
    print("=" * 80)

    print("""
George Boole developed Boolean algebra.

Boolean logic deals with values such as:

    TRUE
    FALSE

The fundamental logical operations include:

    AND
    OR
    NOT

Boolean algebra became foundational to digital computing.

Electronic circuits can implement Boolean operations.

For example:

    AND gate
    OR gate
    NOT gate

Complex digital systems can be constructed by combining simple logical
operations.

Therefore there is a historical connection:

    Boolean algebra
          |
          v
    logic operations
          |
          v
    digital circuits
          |
          v
    processors and computers
""")

    print()


# ============================================================================
# 14. HERMAN HOLLERITH
# ============================================================================

def herman_hollerith():
    print("=" * 80)
    print("HERMAN HOLLERITH")
    print("=" * 80)

    print("""
Herman Hollerith developed a punched-card tabulating system.

His technology was used to process large quantities of statistical data,
including data associated with the United States census.

The important development was automated data processing.

Punched cards could encode information.

Machines could then read the cards and perform operations on the encoded
data.

This introduced an important distinction between:

    calculation
    and
    data processing

The idea became central to business computing.
""")

    print()


# ============================================================================
# 15. ELECTROMECHANICAL COMPUTING
# ============================================================================

def electromechanical_computing():
    print("=" * 80)
    print("ELECTROMECHANICAL COMPUTING")
    print("=" * 80)

    print("""
The twentieth century saw the development of electromechanical computing.

These systems combined:

    mechanical components
    +
    electrical relays
    +
    control mechanisms

Relays could function as switches.

They could be used to implement logical operations and control sequences.

Electromechanical systems were generally slower than later electronic
computers because mechanical switching components had physical movement.
""")

    print("""
Important systems and developments include:

    - Harvard Mark I
    - Zuse machines
    - relay-based calculators
    - early automatic sequence-controlled machines

This period forms a bridge between mechanical and fully electronic
computing.
""")

    print()


# ============================================================================
# 16. KONRAD ZUSE
# ============================================================================

def konrad_zuse():
    print("=" * 80)
    print("KONRAD ZUSE")
    print("=" * 80)

    print("""
Konrad Zuse was a German computing pioneer.

His Z-series machines were among the earliest programmable calculating
machines.

The Z3, completed in 1941, was an electromechanical programmable computer.

Zuse's work is particularly important because it demonstrated that
programmability could be combined with automatic calculation.

His work also involved early ideas about programming and floating-point
representation.
""")

    print()


# ============================================================================
# 17. HARVARD MARK I
# ============================================================================

def harvard_mark_i():
    print("=" * 80)
    print("HARVARD MARK I")
    print("=" * 80)

    print("""
The Harvard Mark I, associated with Howard Aiken and IBM, was an
electromechanical automatic calculator.

It used switches, relays, rotating shafts and mechanical components.

The machine could execute sequences of arithmetic operations automatically.

It was enormous compared with modern computers.

Its importance lies in its automation and sequence control.

It demonstrates the transitional stage:

    mechanical calculation
            ->
    electromechanical automation
            ->
    electronic computation
""")

    print()


# ============================================================================
# 18. ALAN TURING
# ============================================================================

def alan_turing():
    print("=" * 80)
    print("ALAN TURING AND THE THEORY OF COMPUTATION")
    print("=" * 80)

    print("""
Alan Turing made fundamental contributions to theoretical computer
science.

In 1936, he described an abstract computational model now called the
Turing machine.

A Turing machine consists conceptually of:

    - an infinite tape
    - symbols written on the tape
    - a read/write mechanism
    - a finite set of states
    - transition rules

The Turing machine is not intended to be a practical physical computer.

It is a mathematical model used to investigate computation.

One of the most important ideas associated with Turing's work is that
a general computational machine can execute different algorithms when
provided with different descriptions of those algorithms.
""")

    print("""
This contributes to the conceptual foundation of general-purpose
computing.

Turing also made major contributions during World War II to cryptanalysis
and worked with early computing systems.
""")

    print()


# ============================================================================
# 19. CHURCH-TURING IDEA
# ============================================================================

def church_turing():
    print("=" * 80)
    print("CHURCH-TURING PERSPECTIVE")
    print("=" * 80)

    print("""
Alonzo Church and Alan Turing independently developed formal approaches
to the nature of computation.

The Church-Turing thesis is a foundational idea in theoretical computer
science.

In simplified terms, it proposes that anything that can be effectively
computed by an algorithm can be computed by a Turing-machine-like formal
system.

It is important to distinguish this from a physical computer.

The thesis concerns the nature of effective computation, not the speed,
cost, energy consumption or engineering limitations of real machines.
""")

    print()


# ============================================================================
# 20. COLOSSUS
# ============================================================================

def colossus():
    print("=" * 80)
    print("COLOSSUS")
    print("=" * 80)

    print("""
Colossus was a family of electronic computing machines developed in
Britain during World War II.

They were used for cryptanalysis.

Colossus used electronic valves and could process information at
high speed compared with electromechanical systems.

Its historical importance includes the demonstration that electronic
switching could provide major computational advantages.

Colossus was specialized rather than a general-purpose computer in the
modern sense.
""")

    print()


# ============================================================================
# 21. ENIAC
# ============================================================================

def eniac():
    print("=" * 80)
    print("ENIAC")
    print("=" * 80)

    print("""
ENIAC stands for Electronic Numerical Integrator and Computer.

It was developed at the University of Pennsylvania.

ENIAC was one of the earliest large-scale electronic general-purpose
computing machines.

It used thousands of vacuum tubes.

Compared with mechanical and electromechanical machines, electronic
operation allowed much higher processing speeds.

ENIAC's programming and configuration involved extensive physical
rewiring and setting switches.

This illustrates an important historical problem:

    electronic computation was fast,
    but programming was still cumbersome.
""")

    print()


# ============================================================================
# 22. EDVAC AND STORED PROGRAM
# ============================================================================

def edvac():
    print("=" * 80)
    print("EDVAC AND THE STORED-PROGRAM CONCEPT")
    print("=" * 80)

    print("""
EDVAC is associated with the development of the stored-program concept.

The central idea is:

    instructions
        +
    data
        |
        v
    memory

Instead of physically rebuilding or rewiring a machine whenever a new
program was required, instructions could be represented in memory.

This was a major conceptual breakthrough.

A computer could become more flexible because the program itself became
data stored within the machine.
""")

    print()


# ============================================================================
# 23. JOHN VON NEUMANN ARCHITECTURE
# ============================================================================

def von_neumann_architecture():
    print("=" * 80)
    print("VON NEUMANN ARCHITECTURE")
    print("=" * 80)

    print("""
The stored-program architecture became strongly associated with the
von Neumann model.

A simplified model contains:

    +---------------------+
    |      MEMORY         |
    |  Data + Instructions|
    +----------+----------+
               |
               v
    +----------+----------+
    |        CPU          |
    |                     |
    | Control Unit        |
    | ALU                 |
    | Registers           |
    +----------+----------+
               |
               v
         Input / Output

The CPU repeatedly performs a cycle:

    FETCH
      |
      v
    DECODE
      |
      v
    EXECUTE
      |
      v
    STORE / UPDATE
      |
      +-----> repeat

This is commonly called the fetch-decode-execute cycle.
""")

    print("""
The model is extremely influential.

A limitation is the von Neumann bottleneck.

The CPU and memory are separate components, and instructions and data
must move between them.

If the CPU becomes much faster than memory, the processor may spend
significant time waiting for data or instructions.
""")

    print()


# ============================================================================
# 24. VACUUM TUBES
# ============================================================================

def vacuum_tubes():
    print("=" * 80)
    print("VACUUM TUBE ERA")
    print("=" * 80)

    print("""
Vacuum tubes were electronic devices capable of controlling electrical
signals.

They could function as switches and amplifying components.

Early electronic computers used large numbers of vacuum tubes.

Advantages:

    - much faster switching than mechanical systems
    - fully electronic operation
    - suitable for complex digital circuits

Disadvantages:

    - large physical size
    - substantial heat production
    - high power consumption
    - limited reliability
    - maintenance requirements

The vacuum tube era demonstrated the potential of electronic computing,
but the technology had major engineering limitations.
""")

    print()


# ============================================================================
# 25. TRANSISTOR
# ============================================================================

def transistor():
    print("=" * 80)
    print("TRANSISTOR REVOLUTION")
    print("=" * 80)

    print("""
The transistor was developed at Bell Labs in 1947 by John Bardeen,
Walter Brattain and William Shockley.

The transistor could perform switching and amplification functions.

Compared with vacuum tubes, transistors were:

    - smaller
    - more reliable
    - more energy efficient
    - less heat-producing
    - suitable for large-scale integration

The transistor transformed computing.

The progression became:

    Vacuum tubes
        ->
    Transistors
        ->
    Integrated circuits
        ->
    Microprocessors
        ->
    Highly integrated processors
""")

    print()


# ============================================================================
# 26. INTEGRATED CIRCUITS
# ============================================================================

def integrated_circuits():
    print("=" * 80)
    print("INTEGRATED CIRCUITS")
    print("=" * 80)

    print("""
An integrated circuit places multiple electronic components onto a
single semiconductor chip.

Instead of constructing circuits from individually wired components,
many components can be manufactured together.

This dramatically improved:

    - size
    - reliability
    - cost
    - speed
    - power efficiency
    - manufacturing scalability

Integrated circuits enabled increasingly complex computers.
""")

    print("""
Levels of integration are often described historically as:

    SSI  = Small-Scale Integration
    MSI  = Medium-Scale Integration
    LSI  = Large-Scale Integration
    VLSI = Very-Large-Scale Integration
    ULSI = Ultra-Large-Scale Integration

These terms describe increasing numbers of components integrated into
a chip.
""")

    print()


# ============================================================================
# 27. MOORE'S LAW
# ============================================================================

def moores_law():
    print("=" * 80)
    print("MOORE'S LAW")
    print("=" * 80)

    print("""
Gordon Moore observed that the number of components on integrated
circuits had historically increased rapidly over time.

This observation became known as Moore's Law.

It is not a physical law like Newton's laws.

It is an observation and industry trend concerning semiconductor
integration.

For decades, increasing transistor density supported:

    - higher performance
    - smaller devices
    - lower cost per computation
    - increased memory capacity
    - more complex processors

Modern semiconductor development faces physical and economic challenges,
so transistor scaling is not an unlimited or simple exponential process.
""")

    print()


# ============================================================================
# 28. MICROPROCESSOR
# ============================================================================

def microprocessor():
    print("=" * 80)
    print("MICROPROCESSOR REVOLUTION")
    print("=" * 80)

    print("""
A microprocessor places the central processing functionality of a
computer on an integrated circuit.

Intel's 4004, introduced in 1971, is historically recognized as one of
the first commercially available microprocessors.

The microprocessor enabled the creation of smaller and less expensive
computing systems.

The progression was:

    room-sized computer
          ->
    minicomputer
          ->
    microcomputer
          ->
    personal computer
          ->
    laptop
          ->
    smartphone
          ->
    embedded processor everywhere
""")

    print()


# ============================================================================
# 29. COMPUTER GENERATIONS
# ============================================================================

def computer_generations():
    print("=" * 80)
    print("GENERATIONS OF COMPUTERS")
    print("=" * 80)

    generations = [
        (
            "First Generation",
            "Vacuum tubes",
            "Machine language",
            "Very large, hot, expensive, high power consumption"
        ),
        (
            "Second Generation",
            "Transistors",
            "Assembly and early high-level languages",
            "Smaller, faster, more reliable"
        ),
        (
            "Third Generation",
            "Integrated circuits",
            "FORTRAN, COBOL and other high-level languages",
            "Greater reliability and reduced size"
        ),
        (
            "Fourth Generation",
            "Microprocessors and VLSI",
            "C, C++, BASIC and many modern languages",
            "Personal computing and mass adoption"
        ),
        (
            "Fifth Generation",
            "AI-oriented and highly parallel systems",
            "AI languages and modern programming ecosystems",
            "Knowledge processing, intelligent systems and advanced parallelism"
        )
    ]

    for generation, hardware, software, characteristics in generations:
        print(f"{generation}")
        print(f"    Hardware: {hardware}")
        print(f"    Programming: {software}")
        print(f"    Characteristics: {characteristics}")
        print()

    print("""
The generation classification is useful for learning but should not be
treated as a perfectly precise historical boundary.

Different computers evolved at different rates.

Some systems combined technologies from multiple periods.
""")

    print()


# ============================================================================
# 30. MAINFRAME COMPUTERS
# ============================================================================

def mainframes():
    print("=" * 80)
    print("MAINFRAME COMPUTING")
    print("=" * 80)

    print("""
Mainframes became important for large organizations.

They were designed for:

    - high-volume transaction processing
    - large databases
    - government operations
    - banking
    - airline reservation systems
    - enterprise workloads

Mainframe computing introduced ideas such as centralized computing,
batch processing and large-scale organizational data processing.

The development of enterprise computing influenced the design of
databases, operating systems, programming languages and transaction
processing systems.
""")

    print()


# ============================================================================
# 31. MINICOMPUTERS
# ============================================================================

def minicomputers():
    print("=" * 80)
    print("MINICOMPUTERS")
    print("=" * 80)

    print("""
Minicomputers emerged as smaller and more accessible alternatives to
large mainframes.

They were widely used in:

    - laboratories
    - universities
    - engineering
    - industrial control
    - scientific research

Digital Equipment Corporation became particularly important in this
period.

The minicomputer helped expand computing beyond centralized corporate
data centers.
""")

    print()


# ============================================================================
# 32. PERSONAL COMPUTER REVOLUTION
# ============================================================================

def personal_computers():
    print("=" * 80)
    print("PERSONAL COMPUTER REVOLUTION")
    print("=" * 80)

    print("""
The personal computer transformed computing from an organizational
resource into a personal tool.

Important systems included:

    - Apple II
    - IBM PC
    - Commodore systems
    - early Macintosh computers
    - MS-DOS systems

Personal computers were used for:

    - word processing
    - spreadsheets
    - programming
    - education
    - games
    - business
    - communications
""")

    print("""
The importance of the PC revolution is not only technological.

It changed the social distribution of computing power.

Instead of:

    organization -> central computer -> user

the model increasingly became:

    individual -> personal computer -> software
""")

    print()


# ============================================================================
# 33. GRAPHICAL USER INTERFACE
# ============================================================================

def gui():
    print("=" * 80)
    print("GRAPHICAL USER INTERFACES")
    print("=" * 80)

    print("""
Early computers were often controlled through switches, punched cards,
paper tape, command languages and other interfaces.

Graphical user interfaces introduced:

    - windows
    - icons
    - menus
    - pointers
    - visual interaction

Research at Xerox PARC influenced modern graphical interfaces.

Apple and Microsoft later played major roles in bringing graphical
interfaces to large numbers of users.

The GUI reduced the need for users to memorize complex command syntax
for common operations.
""")

    print()


# ============================================================================
# 34. OPERATING SYSTEM EVOLUTION
# ============================================================================

def operating_systems():
    print("=" * 80)
    print("EVOLUTION OF OPERATING SYSTEMS")
    print("=" * 80)

    print("""
An operating system manages hardware resources and provides services
for application programs.

Early computers often executed one job at a time with limited abstraction.

Operating systems gradually introduced:

    - batch processing
    - job scheduling
    - multiprogramming
    - multitasking
    - memory management
    - file systems
    - process management
    - device management
    - networking
    - security
    - virtualization

The operating system became a layer between hardware and applications.

Conceptually:

    APPLICATIONS
         |
         v
    OPERATING SYSTEM
         |
         v
    HARDWARE
""")

    print()


# ============================================================================
# 35. PROGRAMMING LANGUAGE EVOLUTION
# ============================================================================

def programming_languages():
    print("=" * 80)
    print("PROGRAMMING LANGUAGE EVOLUTION")
    print("=" * 80)

    print("""
Programming languages evolved because direct machine programming was
difficult and error-prone.

The broad progression was:

    Machine language
        ->
    Assembly language
        ->
    High-level procedural languages
        ->
    Structured programming
        ->
    Object-oriented programming
        ->
    Functional and declarative approaches
        ->
    Scripting and dynamic languages
        ->
    Domain-specific and specialized languages
        ->
    Modern multi-paradigm ecosystems
""")

    languages = {
        "Machine language":
            "Binary instructions directly represented for a processor.",

        "Assembly":
            "Human-readable symbolic representation of machine instructions.",

        "FORTRAN":
            "Important early high-level language for scientific and numerical computing.",

        "COBOL":
            "Important language for business and administrative data processing.",

        "LISP":
            "Highly influential language in artificial intelligence research.",

        "C":
            "Efficient systems programming language with major influence on operating systems and software.",

        "C++":
            "General-purpose language extending C with object-oriented and other features.",

        "Java":
            "Object-oriented language emphasizing portability through the JVM.",

        "Python":
            "High-level general-purpose language widely used in automation, data science, web development and AI.",

        "JavaScript":
            "Major language of Web development, later expanded into server and application environments."
    }

    for language, description in languages.items():
        print(f"{language}:")
        print(f"    {description}")
        print()

    print()


# ============================================================================
# 36. COMPILER
# ============================================================================

def compiler_concept():
    print("=" * 80)
    print("COMPILERS")
    print("=" * 80)

    print("""
A compiler translates source code from one programming language into
another representation, often machine code or an intermediate form.

A simplified compiler pipeline can be represented as:

    SOURCE CODE
        |
        v
    LEXICAL ANALYSIS
        |
        v
    SYNTAX ANALYSIS
        |
        v
    SEMANTIC ANALYSIS
        |
        v
    INTERMEDIATE REPRESENTATION
        |
        v
    OPTIMIZATION
        |
        v
    CODE GENERATION
        |
        v
    TARGET CODE

Compiler technology is essential to modern software development.

It allows humans to write programs using abstractions that are much
higher-level than raw machine instructions.
""")

    print()


# ============================================================================
# 37. ASSEMBLY LANGUAGE
# ============================================================================

def assembly_language():
    print("=" * 80)
    print("ASSEMBLY LANGUAGE")
    print("=" * 80)

    print("""
Assembly language uses symbolic instructions corresponding closely to
machine instructions.

For example, a conceptual instruction might be:

    LOAD
    ADD
    STORE
    JUMP

The exact instructions depend on the processor architecture.

Assembly language provides more abstraction than binary machine code
but remains closely connected to hardware.

It is historically important because it represents the intermediate
layer between hardware and high-level programming.
""")

    print()


# ============================================================================
# 38. DATABASE EVOLUTION
# ============================================================================

def databases():
    print("=" * 80)
    print("EVOLUTION OF DATABASE COMPUTING")
    print("=" * 80)

    print("""
As computers became responsible for increasingly large amounts of
organizational data, systematic data management became essential.

Early data processing relied heavily on files and sequential storage.

Database systems later introduced structured approaches to storing and
retrieving information.

Important stages include:

    - file processing
    - hierarchical databases
    - network databases
    - relational databases
    - SQL
    - distributed databases
    - object-oriented databases
    - NoSQL systems
    - NewSQL and distributed SQL
    - cloud databases

The relational model became particularly influential.

A relational database organizes information into tables consisting
of rows and columns.

SQL provides a declarative language for querying and manipulating
relational data.
""")

    print()


# ============================================================================
# 39. NETWORKING
# ============================================================================

def networking():
    print("=" * 80)
    print("EVOLUTION OF COMPUTER NETWORKING")
    print("=" * 80)

    print("""
Early computers were mostly isolated machines.

Networking changed computing by allowing computers to exchange information.

The basic networking model involves:

    sender
       |
       v
    communication medium
       |
       v
    receiver

Networks developed from local and specialized systems into global
interconnected infrastructures.

Important concepts include:

    - packets
    - protocols
    - addressing
    - routing
    - error detection
    - congestion control
    - reliability
    - layered architecture
""")

    print()


# ============================================================================
# 40. ARPANET
# ============================================================================

def arpanet():
    print("=" * 80)
    print("ARPANET")
    print("=" * 80)

    print("""
ARPANET was an early packet-switched network funded by the U.S.
Advanced Research Projects Agency.

It became an important predecessor to the modern Internet.

Packet switching divides information into packets that can be transmitted
through a network.

This differs from traditional circuit-oriented communication, where
communication resources may be reserved for a connection.

ARPANET contributed to the development of networked computing and the
eventual adoption of TCP/IP.
""")

    print()


# ============================================================================
# 41. TCP/IP
# ============================================================================

def tcp_ip():
    print("=" * 80)
    print("TCP/IP")
    print("=" * 80)

    print("""
TCP/IP is the protocol suite underlying the Internet.

IP is responsible for addressing and routing packets between networks.

TCP provides reliable, ordered delivery for applications that require it.

The Internet is not a single physical network.

It is a network of interconnected networks.

This architecture allowed independently operated networks to communicate
using common protocols.
""")

    print()


# ============================================================================
# 42. WORLD WIDE WEB
# ============================================================================

def world_wide_web():
    print("=" * 80)
    print("WORLD WIDE WEB")
    print("=" * 80)

    print("""
Tim Berners-Lee developed the foundational technologies of the World Wide
Web at CERN.

The Web introduced a system based around:

    - HTML
    - HTTP
    - URLs

A web browser can request resources from a web server.

Conceptually:

    USER
      |
      v
    BROWSER
      |
      v
    HTTP REQUEST
      |
      v
    SERVER
      |
      v
    HTTP RESPONSE
      |
      v
    BROWSER
      |
      v
    USER

The Web made Internet resources accessible through interconnected
hypertext documents.
""")

    print()


# ============================================================================
# 43. DOT-COM AND WEB APPLICATIONS
# ============================================================================

def web_evolution():
    print("=" * 80)
    print("WEB EVOLUTION")
    print("=" * 80)

    print("""
The Web evolved from mostly static documents toward interactive
applications.

Broad stages include:

    Early Web
        Static pages and documents

    Dynamic Web
        Server-side generated content

    Web applications
        User accounts, databases and interactive services

    Rich client applications
        JavaScript-heavy interfaces

    Cloud-backed applications
        Globally distributed services

    Modern Web
        APIs, real-time communication, distributed systems,
        progressive applications and sophisticated client-side software
""")

    print()


# ============================================================================
# 44. MOBILE COMPUTING
# ============================================================================

def mobile_computing():
    print("=" * 80)
    print("MOBILE COMPUTING")
    print("=" * 80)

    print("""
Mobile computing combines:

    - portable hardware
    - wireless communication
    - operating systems
    - applications
    - cloud services
    - sensors
    - location technologies

Smartphones transformed computing because a single portable device can
combine:

    telephone
    camera
    GPS
    computer
    media player
    browser
    payment device
    communication platform
    sensor platform
""")

    print()


# ============================================================================
# 45. EMBEDDED SYSTEMS
# ============================================================================

def embedded_systems():
    print("=" * 80)
    print("EMBEDDED COMPUTING")
    print("=" * 80)

    print("""
A computer does not need to look like a desktop or laptop.

Embedded computers are integrated into larger products.

Examples include:

    - automobiles
    - washing machines
    - medical devices
    - industrial equipment
    - cameras
    - routers
    - televisions
    - aircraft systems
    - smart appliances

Embedded systems often have strict constraints involving:

    - power
    - memory
    - processing capacity
    - real-time response
    - reliability
    - safety
""")

    print()


# ============================================================================
# 46. CLOUD COMPUTING
# ============================================================================

def cloud_computing():
    print("=" * 80)
    print("CLOUD COMPUTING")
    print("=" * 80)

    print("""
Cloud computing provides computing resources through network-accessible
infrastructure.

Instead of purchasing and maintaining all computing hardware locally,
organizations can consume resources as services.

Cloud computing commonly provides:

    - compute
    - storage
    - databases
    - networking
    - analytics
    - machine learning
    - application platforms

Important service models include:

    IaaS
        Infrastructure as a Service

    PaaS
        Platform as a Service

    SaaS
        Software as a Service
""")

    print("""
Cloud computing relies heavily on:

    virtualization
    distributed systems
    data centers
    networking
    automation
    resource pooling
    elasticity
    orchestration
""")

    print()


# ============================================================================
# 47. VIRTUALIZATION
# ============================================================================

def virtualization():
    print("=" * 80)
    print("VIRTUALIZATION")
    print("=" * 80)

    print("""
Virtualization allows physical computing resources to support multiple
logical computing environments.

A hypervisor can manage virtual machines.

Conceptually:

    PHYSICAL HARDWARE
            |
            v
        HYPERVISOR
        /        \
       /          \
      v            v
    VM 1          VM 2
    OS            OS
    App           App

Virtualization improved:

    - resource utilization
    - isolation
    - flexibility
    - deployment speed
    - server consolidation
""")

    print()


# ============================================================================
# 48. CONTAINERS
# ============================================================================

def containers():
    print("=" * 80)
    print("CONTAINERIZATION")
    print("=" * 80)

    print("""
Containers provide a lightweight method for packaging applications
and their dependencies.

Unlike traditional virtual machines, containers typically share the
host operating system kernel.

Conceptually:

    HOST OS
       |
       +-------------------+
       | Container 1       |
       | Application       |
       | Dependencies      |
       +-------------------+
       |
       +-------------------+
       | Container 2       |
       | Application       |
       | Dependencies      |
       +-------------------+

Containerization became highly important in modern software deployment
and cloud-native computing.
""")

    print()


# ============================================================================
# 49. DISTRIBUTED COMPUTING
# ============================================================================

def distributed_computing():
    print("=" * 80)
    print("DISTRIBUTED COMPUTING")
    print("=" * 80)

    print("""
Distributed computing divides computation or data processing across
multiple computers.

Instead of:

    one machine
        |
        v
    one computation

we can have:

    machine A ----\
    machine B -----+----> coordinated computation
    machine C ----/
    machine D ----/

Distributed systems introduce challenges such as:

    - network delays
    - partial failures
    - synchronization
    - consistency
    - replication
    - fault tolerance
    - distributed coordination

Modern Internet services depend heavily on distributed computing.
""")

    print()


# ============================================================================
# 50. PARALLEL COMPUTING
# ============================================================================

def parallel_computing():
    print("=" * 80)
    print("PARALLEL COMPUTING")
    print("=" * 80)

    print("""
Parallel computing performs multiple computations at the same time.

A sequential computation can be represented as:

    Task A -> Task B -> Task C -> Task D

Parallel computation may allow:

    Task A ----\
    Task B -----+
    Task C -----+----> combined result
    Task D ----/

Parallelism can exist at multiple levels:

    - instruction level
    - data level
    - thread level
    - process level
    - task level
    - machine level
""")

    print()


# ============================================================================
# 51. GPU COMPUTING
# ============================================================================

def gpu_computing():
    print("=" * 80)
    print("GPU COMPUTING")
    print("=" * 80)

    print("""
Graphics Processing Units were originally designed primarily for
graphics workloads.

Graphics processing requires performing similar operations over large
numbers of pixels and vertices.

This naturally benefits from parallel execution.

GPUs later became useful for:

    - scientific computing
    - numerical simulation
    - data processing
    - machine learning
    - deep learning

The broader lesson is that computer architecture can be specialized
for particular classes of workloads.
""")

    print()


# ============================================================================
# 52. MULTICORE PROCESSORS
# ============================================================================

def multicore_processors():
    print("=" * 80)
    print("MULTICORE PROCESSORS")
    print("=" * 80)

    print("""
Instead of continually increasing the clock frequency of a single
processor, processor designers increasingly adopted multiple cores.

A multicore processor contains several processing cores on one chip.

For example:

    CPU
    +----------------------+
    | Core 1 | Core 2      |
    | Core 3 | Core 4      |
    +----------------------+

Applications can exploit multiple cores through parallelism.

Multicore computing changed software design because programmers increasingly
needed to reason about:

    - threads
    - synchronization
    - race conditions
    - locks
    - parallel algorithms
""")

    print()


# ============================================================================
# 53. RISC AND CISC
# ============================================================================

def risc_cisc():
    print("=" * 80)
    print("RISC AND CISC")
    print("=" * 80)

    print("""
RISC means Reduced Instruction Set Computer.

CISC means Complex Instruction Set Computer.

RISC designs generally emphasize:

    - relatively simple instructions
    - regular instruction formats
    - efficient pipelining
    - large register sets in many designs

CISC designs generally provide a richer and more complex instruction
set.

The distinction is useful historically, but modern processors often
combine ideas from both approaches.

Examples of important instruction set families include:

    x86
    ARM
    RISC-V
    MIPS
    Power
""")

    print()


# ============================================================================
# 54. COMPUTER ARCHITECTURE
# ============================================================================

def computer_architecture():
    print("=" * 80)
    print("COMPUTER ARCHITECTURE EVOLUTION")
    print("=" * 80)

    print("""
Computer architecture describes how a computing system is organized
and how its components work together.

Important architectural concepts include:

    - CPU
    - ALU
    - control unit
    - registers
    - cache
    - memory
    - buses
    - storage
    - input/output
    - instruction set
    - pipeline
    - branch prediction
    - multicore processing
    - accelerators

A simplified hierarchy is:

    Registers
        |
    CPU Cache
        |
    Main Memory
        |
    SSD / Storage
        |
    External / Network Storage

Generally, faster storage is smaller and more expensive per unit of
capacity, while slower storage tends to provide greater capacity.
""")

    print()


# ============================================================================
# 55. MEMORY EVOLUTION
# ============================================================================

def memory_evolution():
    print("=" * 80)
    print("MEMORY TECHNOLOGY EVOLUTION")
    print("=" * 80)

    print("""
Computer memory evolved through several technologies.

Examples include:

    - delay-line memory
    - magnetic-core memory
    - semiconductor memory
    - DRAM
    - SRAM
    - flash memory

Modern memory systems use hierarchy.

    Registers
        fastest, smallest

    Cache
        very fast

    RAM
        main working memory

    SSD/HDD
        persistent storage

    Network/cloud storage
        potentially very large but network-dependent
""")

    print()


# ============================================================================
# 56. STORAGE EVOLUTION
# ============================================================================

def storage_evolution():
    print("=" * 80)
    print("STORAGE TECHNOLOGY EVOLUTION")
    print("=" * 80)

    storage = [
        "Paper and punched cards",
        "Magnetic tape",
        "Magnetic drums",
        "Hard disk drives",
        "Floppy disks",
        "Optical discs",
        "Solid-state drives",
        "Flash storage",
        "Distributed and cloud storage"
    ]

    for index, item in enumerate(storage, start=1):
        print(f"{index:2}. {item}")

    print("""
Storage evolved in terms of:

    - capacity
    - access speed
    - portability
    - reliability
    - cost
    - physical size

The general trend has been toward storing dramatically more information
in increasingly compact physical systems.
""")

    print()


# ============================================================================
# 57. INPUT AND OUTPUT
# ============================================================================

def input_output():
    print("=" * 80)
    print("INPUT AND OUTPUT EVOLUTION")
    print("=" * 80)

    print("""
Computers need mechanisms for receiving information and communicating
results.

Early methods included:

    - switches
    - punched cards
    - paper tape

Later systems introduced:

    - keyboards
    - monitors
    - printers
    - magnetic storage
    - mice
    - touchscreens

Modern systems may use:

    - cameras
    - microphones
    - sensors
    - biometric devices
    - GPS
    - accelerometers
    - wireless interfaces
    - voice input

The computer has therefore evolved from a machine operating on manually
prepared input into an environment continuously interacting with its
physical and digital surroundings.
""")

    print()


# ============================================================================
# 58. ARTIFICIAL INTELLIGENCE
# ============================================================================

def artificial_intelligence():
    print("=" * 80)
    print("EVOLUTION OF ARTIFICIAL INTELLIGENCE")
    print("=" * 80)

    print("""
Artificial intelligence attempts to create systems capable of tasks
associated with intelligent behavior.

Early AI research explored:

    - symbolic reasoning
    - logic
    - theorem proving
    - search
    - planning
    - expert systems

Later approaches increasingly emphasized learning from data.

The broad progression includes:

    symbolic AI
        ->
    statistical machine learning
        ->
    neural networks
        ->
    deep learning
        ->
    large-scale foundation models
        ->
    generative and multimodal systems
""")

    print()


# ============================================================================
# 59. EARLY AI
# ============================================================================

def early_ai():
    print("=" * 80)
    print("EARLY ARTIFICIAL INTELLIGENCE")
    print("=" * 80)

    print("""
The term artificial intelligence became established as a research field
during the 1950s.

Researchers explored whether machines could perform tasks involving:

    - reasoning
    - problem solving
    - games
    - language
    - theorem proving
    - symbolic manipulation

Early AI often represented knowledge explicitly.

For example:

    IF condition A is true
    AND condition B is true
    THEN conclude C

This approach can be effective when the rules are known and manageable.

It becomes difficult when the real world is highly uncertain, ambiguous
and difficult to encode manually.
""")

    print()


# ============================================================================
# 60. EXPERT SYSTEMS
# ============================================================================

def expert_systems():
    print("=" * 80)
    print("EXPERT SYSTEMS")
    print("=" * 80)

    print("""
Expert systems attempted to encode specialist knowledge into software.

A simplified expert system contains:

    Knowledge Base
        |
        v
    Inference Engine
        |
        v
    Conclusion

The knowledge base contains rules or facts.

The inference engine applies those rules.

Expert systems were important because they demonstrated that software
could represent specialized knowledge and use it for decision support.

Their limitations included:

    - knowledge acquisition difficulty
    - brittle rules
    - limited adaptability
    - difficulty handling unexpected situations
""")

    print()


# ============================================================================
# 61. MACHINE LEARNING
# ============================================================================

def machine_learning():
    print("=" * 80)
    print("MACHINE LEARNING")
    print("=" * 80)

    print("""
Machine learning changes the programming model.

Traditional rule-based programming:

    Data + explicitly written rules
                 |
                 v
               Output

Machine learning:

    Data + desired examples
                 |
                 v
           Learning process
                 |
                 v
                Model

The learned model can then process new inputs.

Major categories include:

    - supervised learning
    - unsupervised learning
    - semi-supervised learning
    - self-supervised learning
    - reinforcement learning
""")

    print()


# ============================================================================
# 62. NEURAL NETWORKS
# ============================================================================

def neural_networks():
    print("=" * 80)
    print("NEURAL NETWORKS")
    print("=" * 80)

    print("""
Artificial neural networks are computational models composed of
interconnected processing units.

A simplified network contains:

    Input Layer
         |
         v
    Hidden Layer
         |
         v
    Output Layer

Modern neural networks can contain many layers.

The term deep learning generally refers to machine learning methods
based on deep neural networks.

Neural networks became increasingly powerful as three resources
expanded:

    1. Data
    2. Computational power
    3. Efficient learning algorithms
""")

    print()


# ============================================================================
# 63. DEEP LEARNING
# ============================================================================

def deep_learning():
    print("=" * 80)
    print("DEEP LEARNING")
    print("=" * 80)

    print("""
Deep learning became especially influential in areas such as:

    - computer vision
    - speech recognition
    - natural language processing
    - recommendation systems
    - autonomous systems
    - scientific computing

Modern deep learning relies heavily on accelerated parallel computation.

This illustrates an important historical relationship:

    semiconductor scaling
          |
          v
    powerful processors
          |
          v
    large-scale training
          |
          v
    increasingly capable models
""")

    print()


# ============================================================================
# 64. TRANSFORMERS
# ============================================================================

def transformers():
    print("=" * 80)
    print("TRANSFORMER ARCHITECTURE")
    print("=" * 80)

    print("""
Transformer architectures became highly influential in modern AI.

They use attention mechanisms to model relationships between elements
of sequences and other structured inputs.

Transformers are widely used in:

    - natural language processing
    - computer vision
    - speech
    - multimodal systems
    - generative AI

Large-scale transformer models demonstrated that increasing model size,
data and computational resources could produce powerful general-purpose
capabilities.
""")

    print()


# ============================================================================
# 65. GENERATIVE COMPUTING
# ============================================================================

def generative_ai():
    print("=" * 80)
    print("GENERATIVE COMPUTING")
    print("=" * 80)

    print("""
Generative systems produce new content based on learned representations.

Examples include generation of:

    - text
    - images
    - audio
    - video
    - software code
    - structured information

This represents another shift in computing.

Traditional software usually follows explicitly defined instructions.

Machine learning systems can learn patterns from data.

Generative models can then produce new outputs based on those learned
patterns.
""")

    print()


# ============================================================================
# 66. DATA CENTER EVOLUTION
# ============================================================================

def data_centers():
    print("=" * 80)
    print("DATA CENTER EVOLUTION")
    print("=" * 80)

    print("""
Computing gradually moved from individual machines toward large-scale
data centers.

A modern data center may contain:

    - thousands of servers
    - high-speed networking
    - storage systems
    - accelerators
    - cooling systems
    - backup power
    - security systems
    - automated orchestration

Large computing workloads can therefore be treated as infrastructure
rather than individual machines.

This is one of the foundations of cloud computing and large-scale AI.
""")

    print()


# ============================================================================
# 67. EDGE COMPUTING
# ============================================================================

def edge_computing():
    print("=" * 80)
    print("EDGE COMPUTING")
    print("=" * 80)

    print("""
Cloud computing centralizes significant processing in data centers.

Edge computing moves some processing closer to where data is produced
or consumed.

For example:

    SENSOR
      |
      v
    EDGE DEVICE
      |
      v
    LOCAL DECISION
      |
      v
    CLOUD

Benefits can include:

    - lower latency
    - reduced bandwidth requirements
    - local processing
    - improved responsiveness

Edge computing is useful for systems that need rapid decisions or operate
with intermittent connectivity.
""")

    print()


# ============================================================================
# 68. INTERNET OF THINGS
# ============================================================================

def internet_of_things():
    print("=" * 80)
    print("INTERNET OF THINGS")
    print("=" * 80)

    print("""
The Internet of Things refers broadly to physical devices equipped with
sensors, processing capabilities and network connectivity.

Examples:

    - smart appliances
    - industrial sensors
    - vehicles
    - medical devices
    - environmental monitoring systems

The traditional computer was a visible machine.

IoT represents a world in which computing becomes embedded into many
physical objects.
""")

    print()


# ============================================================================
# 69. QUANTUM COMPUTING
# ============================================================================

def quantum_computing():
    print("=" * 80)
    print("QUANTUM COMPUTING")
    print("=" * 80)

    print("""
Quantum computing uses quantum-mechanical phenomena for computation.

The fundamental unit is commonly called a qubit.

A classical bit is represented as:

    0
    or
    1

A qubit can exist in a quantum state that involves superposition.

Important quantum concepts include:

    - superposition
    - entanglement
    - interference
    - quantum measurement

Quantum computers are not simply faster versions of classical computers.

They use different computational principles and are expected to be useful
for particular classes of problems.

Quantum computing remains a specialized and developing field.
""")

    print()


# ============================================================================
# 70. NEUROMORPHIC COMPUTING
# ============================================================================

def neuromorphic_computing():
    print("=" * 80)
    print("NEUROMORPHIC COMPUTING")
    print("=" * 80)

    print("""
Neuromorphic computing attempts to design computing systems inspired
by aspects of biological neural systems.

The goal can include efficient processing of:

    - sensory information
    - sparse signals
    - event-driven workloads

Neuromorphic architectures represent one direction in the search for
computational systems beyond conventional CPU-centric designs.
""")

    print()


# ============================================================================
# 71. SUPERCOMPUTERS
# ============================================================================

def supercomputers():
    print("=" * 80)
    print("SUPERCOMPUTING")
    print("=" * 80)

    print("""
Supercomputers are designed for extremely demanding computational tasks.

Applications include:

    - weather modeling
    - climate simulation
    - physics
    - computational chemistry
    - nuclear research
    - astrophysics
    - engineering simulation
    - genomics
    - artificial intelligence

Modern supercomputers typically rely on massive parallelism.

A supercomputer is therefore not necessarily one extraordinarily fast
CPU.

It is generally a large system composed of many computational resources
working together.
""")

    print()


# ============================================================================
# 72. SOFTWARE ENGINEERING EVOLUTION
# ============================================================================

def software_engineering():
    print("=" * 80)
    print("EVOLUTION OF SOFTWARE ENGINEERING")
    print("=" * 80)

    print("""
As software systems became larger, informal programming became
insufficient.

Software engineering developed practices for:

    - requirements
    - design
    - implementation
    - testing
    - maintenance
    - version control
    - project management
    - configuration management
    - security
    - deployment

Development methodologies evolved through approaches such as:

    - waterfall
    - iterative development
    - incremental development
    - agile methods
    - continuous integration
    - continuous delivery
    - DevOps
    - DevSecOps
""")

    print()


# ============================================================================
# 73. OPEN SOURCE SOFTWARE
# ============================================================================

def open_source():
    print("=" * 80)
    print("OPEN SOURCE COMPUTING")
    print("=" * 80)

    print("""
Open-source software allows source code to be inspected and, depending
on its license, modified and redistributed.

Important open-source projects and ecosystems include:

    - GNU
    - Linux
    - Apache
    - Python
    - PostgreSQL
    - Git
    - Kubernetes

Open-source development changed software creation by enabling global
communities to collaborate around shared codebases.
""")

    print()


# ============================================================================
# 74. GIT AND DISTRIBUTED DEVELOPMENT
# ============================================================================

def git():
    print("=" * 80)
    print("VERSION CONTROL AND GIT")
    print("=" * 80)

    print("""
As software became collaborative, developers needed reliable mechanisms
for tracking changes.

Version control systems allow developers to:

    - record changes
    - compare versions
    - create branches
    - merge work
    - recover previous versions
    - collaborate across locations

Git became one of the most influential distributed version control systems.

Its importance reflects a broader evolution:

    computing is not only about hardware performance.

It is also about managing increasingly complex human and software
collaboration.
""")

    print()


# ============================================================================
# 75. CYBERSECURITY
# ============================================================================

def cybersecurity():
    print("=" * 80)
    print("EVOLUTION OF COMPUTER SECURITY")
    print("=" * 80)

    print("""
Early computing security often focused on physical access and controlled
use of centralized machines.

As computers became networked, security expanded.

Modern cybersecurity addresses:

    - authentication
    - authorization
    - confidentiality
    - integrity
    - availability
    - cryptography
    - secure software
    - network security
    - identity management
    - malware
    - incident response
    - privacy
    - supply-chain security

The evolution of computing therefore created both new capabilities and
new security challenges.
""")

    print()


# ============================================================================
# 76. CRYPTOGRAPHY
# ============================================================================

def cryptography():
    print("=" * 80)
    print("CRYPTOGRAPHY AND COMPUTING")
    print("=" * 80)

    print("""
Cryptography provides mathematical techniques for protecting information.

Major concepts include:

    - encryption
    - decryption
    - keys
    - hashing
    - digital signatures
    - authentication

Computing dramatically expanded the ability to perform cryptographic
operations.

At the same time, more powerful computers created new capabilities
for attacking weak cryptographic systems.

This created an ongoing relationship between computational power and
information security.
""")

    print()


# ============================================================================
# 77. HISTORICAL TIMELINE
# ============================================================================

def historical_timeline():
    print("=" * 80)
    print("MAJOR HISTORICAL TIMELINE")
    print("=" * 80)

    timeline = [
        ("Ancient period", "Tallying, counting systems and early arithmetic"),
        ("Ancient to medieval", "Abacus and systematic calculation"),
        ("1610s", "Napier's logarithmic work and Napier's Bones"),
        ("1620s", "Development of early slide-rule concepts"),
        ("1640s", "Pascal develops the Pascaline"),
        ("1670s", "Leibniz develops the Stepped Reckoner"),
        ("1800s", "Jacquard punched-card control"),
        ("1820s", "Babbage develops plans for Difference Engine"),
        ("1830s", "Babbage develops Analytical Engine concepts"),
        ("1840s", "Ada Lovelace publishes work on the Analytical Engine"),
        ("1850s", "Boolean develops formal algebra of logic"),
        ("1890s", "Hollerith develops punched-card tabulation"),
        ("1930s", "Formal theories of computation develop"),
        ("1940s", "Electromechanical and electronic computers emerge"),
        ("1940s", "Colossus used for cryptanalysis"),
        ("1940s", "ENIAC becomes a major electronic computing system"),
        ("1947", "Transistor developed at Bell Labs"),
        ("1950s", "Stored-program systems and commercial computers expand"),
        ("1950s", "Artificial intelligence becomes an established research field"),
        ("1960s", "Integrated circuits transform computer hardware"),
        ("1960s", "Mainframe and minicomputer computing expand"),
        ("1970s", "Microprocessors enable increasingly small computers"),
        ("1970s", "Early networking technologies expand"),
        ("1980s", "Personal computers become widely adopted"),
        ("1980s", "Graphical interfaces become increasingly important"),
        ("1990s", "World Wide Web expands globally"),
        ("1990s", "Commercial Internet grows rapidly"),
        ("2000s", "Mobile and broadband computing expand"),
        ("2000s", "Cloud computing becomes increasingly important"),
        ("2010s", "Smartphones, GPUs and deep learning transform computing"),
        ("2020s", "Generative AI and large-scale AI systems become prominent")
    ]

    for period, event in timeline:
        print(f"{period:20} | {event}")

    print()


# ============================================================================
# 78. MAJOR FIGURES
# ============================================================================

def major_figures():
    print("=" * 80)
    print("MAJOR FIGURES IN COMPUTING HISTORY")
    print("=" * 80)

    figures = {
        "Blaise Pascal":
            "Developed the Pascaline mechanical calculator.",

        "Gottfried Wilhelm Leibniz":
            "Developed the Stepped Reckoner and contributed to binary arithmetic.",

        "Joseph-Marie Jacquard":
            "Developed punched-card control for textile pattern automation.",

        "Charles Babbage":
            "Designed the Difference Engine and Analytical Engine.",

        "Ada Lovelace":
            "Developed influential early algorithmic work for the Analytical Engine.",

        "George Boole":
            "Developed Boolean algebra.",

        "Herman Hollerith":
            "Developed punched-card tabulation systems.",

        "Alan Turing":
            "Contributed fundamentally to computation theory and early computing.",

        "John von Neumann":
            "Contributed to stored-program computer architecture and many areas of mathematics and computing.",

        "Konrad Zuse":
            "Developed early programmable electromechanical computers.",

        "John Bardeen":
            "Co-inventor of the transistor.",

        "Walter Brattain":
            "Co-inventor of the transistor.",

        "William Shockley":
            "Co-inventor of the transistor.",

        "Gordon Moore":
            "Observed the historical trend associated with Moore's Law.",

        "Tim Berners-Lee":
            "Invented the foundational technologies of the World Wide Web."
    }

    for person, contribution in figures.items():
        print(f"{person}:")
        print(f"    {contribution}")
        print()

    print()


# ============================================================================
# 79. HARDWARE EVOLUTION
# ============================================================================

def hardware_evolution():
    print("=" * 80)
    print("HARDWARE EVOLUTION")
    print("=" * 80)

    print("""
The broad hardware evolution can be represented as:

    Mechanical
        |
        v
    Electromechanical
        |
        v
    Vacuum tube
        |
        v
    Transistor
        |
        v
    Integrated circuit
        |
        v
    Microprocessor
        |
        v
    Multicore processor
        |
        v
    GPU / accelerator
        |
        v
    Heterogeneous computing
        |
        v
    Specialized AI hardware

Each transition increased the ability to place computational capability
into smaller, more efficient and more scalable systems.
""")

    print()


# ============================================================================
# 80. SOFTWARE EVOLUTION
# ============================================================================

def software_evolution():
    print("=" * 80)
    print("SOFTWARE EVOLUTION")
    print("=" * 80)

    print("""
Software evolved alongside hardware.

The progression can be viewed as:

    Machine instructions
        |
        v
    Assembly
        |
        v
    High-level languages
        |
        v
    Operating systems
        |
        v
    Application software
        |
        v
    Networked applications
        |
        v
    Web applications
        |
        v
    Mobile applications
        |
        v
    Cloud-native systems
        |
        v
    Distributed applications
        |
        v
    AI-enabled applications
""")

    print()


# ============================================================================
# 81. REPRESENTATION OF INFORMATION
# ============================================================================

def information_representation():
    print("=" * 80)
    print("REPRESENTATION OF INFORMATION")
    print("=" * 80)

    print("""
One of the deepest ideas in computing history is representation.

A computer does not need a separate physical machine for every type of
information.

Different information can be encoded into patterns of bits.

For example:

    Numbers
       |
       v
    Binary representation

    Text
       |
       v
    Character encoding

    Images
       |
       v
    Pixels and numerical values

    Audio
       |
       v
    Digital samples

    Video
       |
       v
    Sequences of digital images and audio

Once represented digitally, different forms of information can be
processed using common computational infrastructure.
""")

    print()


# ============================================================================
# 82. DIGITALIZATION
# ============================================================================

def digitalization():
    print("=" * 80)
    print("DIGITALIZATION")
    print("=" * 80)

    print("""
Digitalization refers broadly to transforming information or processes
into digital form.

Examples:

    paper records
        ->
    digital databases

    physical maps
        ->
    digital mapping systems

    printed photographs
        ->
    digital images

    physical documents
        ->
    electronic documents

The significance is that digital information can be copied, transmitted,
searched, indexed, transformed and processed by computers.
""")

    print()


# ============================================================================
# 83. AUTOMATION
# ============================================================================

def automation():
    print("=" * 80)
    print("AUTOMATION")
    print("=" * 80)

    print("""
Automation is a recurring theme throughout computing history.

The pattern is:

    repetitive human task
            |
            v
    formal procedure
            |
            v
    machine representation
            |
            v
    automated execution

Examples include:

    - mechanical calculation
    - punched-card tabulation
    - payroll processing
    - manufacturing control
    - software automation
    - cloud deployment
    - machine learning inference

Computing continually expands the range of tasks that can be automated.
""")

    print()


# ============================================================================
# 84. COMPUTING PARADIGMS
# ============================================================================

def computing_paradigms():
    print("=" * 80)
    print("MAJOR COMPUTING PARADIGMS")
    print("=" * 80)

    paradigms = [
        "Mechanical computation",
        "Analog computation",
        "Digital computation",
        "Centralized computing",
        "Personal computing",
        "Network computing",
        "Distributed computing",
        "Parallel computing",
        "Mobile computing",
        "Cloud computing",
        "Edge computing",
        "Quantum computing",
        "Neuromorphic computing"
    ]

    for index, paradigm in enumerate(paradigms, start=1):
        print(f"{index:2}. {paradigm}")

    print()


# ============================================================================
# 85. ANALOG VS DIGITAL
# ============================================================================

def analog_vs_digital():
    print("=" * 80)
    print("ANALOG VS DIGITAL COMPUTING")
    print("=" * 80)

    print("""
ANALOG COMPUTING

Analog systems represent quantities using continuous physical variables.

Examples historically included:

    - mechanical position
    - voltage
    - rotation
    - fluid pressure

DIGITAL COMPUTING

Digital systems represent information using discrete states.

Modern digital computers commonly use binary representations.

The digital approach became dominant because it provides strong advantages
for:

    - reliable storage
    - reproducibility
    - programmability
    - error detection
    - large-scale integration
    - communication

Analog computing has not disappeared.

Analog techniques remain relevant in specialized engineering and
scientific systems.
""")

    print()


# ============================================================================
# 86. CENTRALIZED VS DISTRIBUTED
# ============================================================================

def centralized_vs_distributed():
    print("=" * 80)
    print("CENTRALIZED VS DISTRIBUTED COMPUTING")
    print("=" * 80)

    print("""
CENTRALIZED MODEL:

    Many users
        |
        v
    Central computer

DISTRIBUTED MODEL:

    Computer A ----\
    Computer B -----+
    Computer C -----+---- Network
    Computer D -----+

Centralized computing simplified management in many historical contexts.

Distributed computing provides scalability and resilience but introduces
new complexity.

Modern systems often combine both approaches.
""")

    print()


# ============================================================================
# 87. COMPUTING SCALE
# ============================================================================

def computing_scale():
    print("=" * 80)
    print("THE SCALE OF COMPUTING")
    print("=" * 80)

    print("""
Computing has expanded across multiple scales.

DEVICE SCALE
    Microcontrollers and embedded processors

PERSONAL SCALE
    Smartphones, laptops and desktops

SERVER SCALE
    Enterprise servers

CLUSTER SCALE
    Multiple connected machines

DATA CENTER SCALE
    Large collections of computing infrastructure

SUPERCOMPUTER SCALE
    Massive parallel systems

GLOBAL SCALE
    Internet-scale distributed infrastructure

The evolution is therefore not simply from large computers to small
computers.

It is from isolated computation toward computing everywhere.
""")

    print()


# ============================================================================
# 88. HUMAN-COMPUTER INTERACTION
# ============================================================================

def human_computer_interaction():
    print("=" * 80)
    print("HUMAN-COMPUTER INTERACTION")
    print("=" * 80)

    print("""
Human-computer interaction evolved through several interfaces.

    Physical switches
        ->
    punched cards
        ->
    command lines
        ->
    keyboards
        ->
    graphical interfaces
        ->
    mouse interaction
        ->
    touch interfaces
        ->
    voice interfaces
        ->
    natural-language interfaces
        ->
    multimodal interaction

The historical direction is toward reducing the distance between human
intent and machine operation.

Modern systems increasingly allow users to interact using natural
language, images, speech and other forms of input.
""")

    print()


# ============================================================================
# 89. COMPUTING AND SCIENCE
# ============================================================================

def computing_and_science():
    print("=" * 80)
    print("COMPUTING AND SCIENTIFIC RESEARCH")
    print("=" * 80)

    print("""
Computing changed science in three major ways.

1. Numerical computation

Scientists can simulate mathematical models.

2. Data processing

Large experimental datasets can be analyzed.

3. Scientific discovery

Computational methods can help identify patterns, test hypotheses
and simulate systems that are difficult to reproduce physically.

Examples include:

    - weather simulation
    - astrophysics
    - genomics
    - molecular modeling
    - particle physics
    - climate science
    - computational biology
""")

    print()


# ============================================================================
# 90. COMPUTING AND BUSINESS
# ============================================================================

def computing_and_business():
    print("=" * 80)
    print("COMPUTING AND BUSINESS")
    print("=" * 80)

    print("""
Business computing developed around the need to process large amounts
of structured information.

Important applications include:

    - accounting
    - payroll
    - inventory
    - banking
    - customer management
    - enterprise resource planning
    - supply chains
    - analytics
    - electronic commerce

The transition from manual records to computerized information systems
dramatically changed organizational processes.
""")

    print()


# ============================================================================
# 91. COMPUTING AND COMMUNICATION
# ============================================================================

def computing_and_communication():
    print("=" * 80)
    print("COMPUTING AND COMMUNICATION")
    print("=" * 80)

    print("""
Computers initially operated primarily as standalone calculation
machines.

Networking changed this model.

Modern computing combines:

    computation
        +
    communication
        +
    storage

This combination makes services such as:

    email
    messaging
    social networks
    video conferencing
    streaming
    cloud applications
    online collaboration

possible at global scale.
""")

    print()


# ============================================================================
# 92. COMPUTING AND EDUCATION
# ============================================================================

def computing_and_education():
    print("=" * 80)
    print("COMPUTING AND EDUCATION")
    print("=" * 80)

    print("""
Computers changed education through:

    - digital libraries
    - online courses
    - educational software
    - simulations
    - virtual laboratories
    - collaborative tools
    - computer-based assessment
    - adaptive learning systems

The cost of distributing digital information is dramatically lower than
the cost of distributing many traditional physical resources.
""")

    print()


# ============================================================================
# 93. COMPUTING AND SOCIETY
# ============================================================================

def computing_and_society():
    print("=" * 80)
    print("COMPUTING AND SOCIETY")
    print("=" * 80)

    print("""
The evolution of computing has affected:

    - employment
    - communication
    - education
    - commerce
    - entertainment
    - government
    - privacy
    - security
    - scientific research
    - social interaction

Computing technology is therefore not merely an engineering development.

It is also a social and economic transformation.
""")

    print()


# ============================================================================
# 94. IMPORTANT HISTORICAL TRANSITIONS
# ============================================================================

def historical_transitions():
    print("=" * 80)
    print("IMPORTANT HISTORICAL TRANSITIONS")
    print("=" * 80)

    transitions = [
        (
            "Manual -> Mechanical",
            "Machines began automating arithmetic."
        ),
        (
            "Mechanical -> Electromechanical",
            "Electrical control increased automation and speed."
        ),
        (
            "Electromechanical -> Electronic",
            "Electronic switching dramatically increased speed."
        ),
        (
            "Vacuum Tube -> Transistor",
            "Computers became smaller, more reliable and more efficient."
        ),
        (
            "Transistor -> Integrated Circuit",
            "Many components could be placed onto a single chip."
        ),
        (
            "Integrated Circuit -> Microprocessor",
            "Central processing functionality became highly compact."
        ),
        (
            "Centralized -> Personal",
            "Computing became accessible to individuals."
        ),
        (
            "Standalone -> Networked",
            "Computers began communicating with one another."
        ),
        (
            "Internet -> Web",
            "Network resources became accessible through hypertext systems."
        ),
        (
            "Desktop -> Mobile",
            "Computing became continuously portable."
        ),
        (
            "Local -> Cloud",
            "Computing resources increasingly became remotely provisioned."
        ),
        (
            "Sequential -> Parallel",
            "Performance increasingly relied on concurrent computation."
        ),
        (
            "Rule-based -> Learning-based",
            "Systems increasingly learned patterns from data."
        )
    ]

    for transition, explanation in transitions:
        print(f"{transition}")
        print(f"    {explanation}")
        print()

    print()


# ============================================================================
# 95. COMPUTER AS A GENERAL-PURPOSE MACHINE
# ============================================================================

def general_purpose_computer():
    print("=" * 80)
    print("THE GENERAL-PURPOSE COMPUTER")
    print("=" * 80)

    print("""
The most important conceptual transition in computing history is the
movement from specialized machines toward general-purpose computers.

A specialized machine is designed for a narrow task.

A general-purpose computer can execute different programs.

This distinction is fundamental.

Hardware provides general computational capabilities.

Software determines how those capabilities are used.

Therefore:

    GENERAL HARDWARE
           +
    DIFFERENT SOFTWARE
           =
    DIFFERENT COMPUTATIONAL TASKS

The same physical computer can be:

    calculator
    word processor
    database server
    web browser
    game machine
    scientific system
    programming environment
    media system
    AI application

depending on the software executing on it.
""")

    print()


# ============================================================================
# 96. HARDWARE-SOFTWARE ABSTRACTION
# ============================================================================

def hardware_software_abstraction():
    print("=" * 80)
    print("ABSTRACTION IN COMPUTING")
    print("=" * 80)

    print("""
Computing became more powerful partly because abstraction allowed
people to work without understanding every lower-level detail.

A modern software stack can be represented as:

    User
      |
      v
    Application
      |
      v
    Framework / Runtime
      |
      v
    Programming Language
      |
      v
    Compiler / Interpreter
      |
      v
    Operating System
      |
      v
    Instruction Set Architecture
      |
      v
    Processor
      |
      v
    Digital Logic
      |
      v
    Transistors
      |
      v
    Semiconductor physics

Each layer hides many implementation details of the layer below it.

This abstraction is one of the reasons modern computing systems can
be extraordinarily complex while remaining usable.
""")

    print()


# ============================================================================
# 97. COMPUTATIONAL COMPLEXITY
# ============================================================================

def computational_complexity():
    print("=" * 80)
    print("COMPUTATIONAL COMPLEXITY")
    print("=" * 80)

    print("""
As computers became more powerful, the focus shifted from merely asking:

    "Can this computer perform the calculation?"

to asking:

    "How efficiently can the calculation be performed?"

Computational complexity studies resources required by algorithms.

Important resources include:

    - time
    - memory
    - communication
    - computational operations

Common complexity classes include:

    O(1)
    O(log n)
    O(n)
    O(n log n)
    O(n^2)
    O(2^n)

The evolution of computing hardware does not eliminate the importance
of efficient algorithms.

Better hardware and better algorithms complement each other.
""")

    print()


# ============================================================================
# 98. RELATIONSHIP BETWEEN ALGORITHMS AND HARDWARE
# ============================================================================

def algorithms_and_hardware():
    print("=" * 80)
    print("ALGORITHMS AND HARDWARE")
    print("=" * 80)

    print("""
Computing performance depends on both algorithms and hardware.

Consider:

    Algorithm
       |
       v
    Operations
       |
       v
    Processor
       |
       v
    Memory
       |
       v
    Storage / Network

An inefficient algorithm may remain slow even on powerful hardware.

A good algorithm can make better use of available computational resources.

This is why computer science and computer engineering developed as
closely connected disciplines.
""")

    print()


# ============================================================================
# 99. THE DATA REVOLUTION
# ============================================================================

def data_revolution():
    print("=" * 80)
    print("THE DATA REVOLUTION")
    print("=" * 80)

    print("""
Early computers were largely valued for calculation.

Modern computing is equally important for managing enormous quantities
of data.

Data is generated by:

    - websites
    - smartphones
    - sensors
    - transactions
    - scientific instruments
    - cameras
    - satellites
    - industrial systems
    - social platforms

The rise of data-intensive computing created fields such as:

    - data engineering
    - data science
    - analytics
    - machine learning
    - big data systems
""")

    print()


# ============================================================================
# 100. BIG DATA
# ============================================================================

def big_data():
    print("=" * 80)
    print("BIG DATA COMPUTING")
    print("=" * 80)

    print("""
Big data refers to datasets whose scale, speed or complexity creates
special computational challenges.

Common characteristics are described using concepts such as:

    Volume
    Velocity
    Variety
    Veracity
    Value

Large datasets require scalable:

    - storage
    - processing
    - networking
    - databases
    - analytics

Distributed systems became important because a single machine may not
provide sufficient resources.
""")

    print()


# ============================================================================
# 101. COMPUTING TRENDS AS A SYSTEM
# ============================================================================

def computing_as_system():
    print("=" * 80)
    print("COMPUTING EVOLUTION AS A SYSTEM")
    print("=" * 80)

    print("""
Computing evolution can be understood through interacting dimensions.

HARDWARE
    More transistors
    More processing capability
    More memory
    More specialized accelerators

SOFTWARE
    Higher abstraction
    Better development tools
    Larger applications
    Distributed architectures

NETWORKING
    Faster communication
    Global connectivity
    Wireless access
    Low-latency networks

DATA
    Greater volume
    Greater variety
    Continuous generation

ALGORITHMS
    Better efficiency
    Parallelism
    Machine learning
    Optimization

INTERACTION
    Keyboard
    Mouse
    Touch
    Voice
    Natural language
    Multimodal interaction

These dimensions reinforce one another.
""")

    print()


# ============================================================================
# 102. WHY COMPUTING EVOLVED
# ============================================================================

def why_computing_evolved():
    print("=" * 80)
    print("WHY COMPUTING EVOLVED")
    print("=" * 80)

    print("""
The evolution of computing was driven by recurring requirements.

1. SPEED

Humans wanted calculations to be completed faster.

2. ACCURACY

Automated systems can reduce certain classes of arithmetic errors.

3. SCALE

Organizations needed to process more information.

4. AUTOMATION

Repetitive work could be performed automatically.

5. STORAGE

Increasing quantities of information required systematic storage.

6. COMMUNICATION

Computers needed to exchange information.

7. FLEXIBILITY

General-purpose systems allowed different programs to run on the same
hardware.

8. PORTABILITY

Computing moved from rooms to desks, pockets and embedded devices.

9. SCALABILITY

Large workloads required distributed and parallel systems.

10. INTELLIGENCE

Modern systems increasingly use machine learning to infer patterns
and generate useful outputs.
""")

    print()


# ============================================================================
# 103. IMPORTANT PECULIARITIES
# ============================================================================

def peculiarities():
    print("=" * 80)
    print("IMPORTANT PECULIARITIES AND HISTORICAL NUANCES")
    print("=" * 80)

    print("""
1. THE FIRST COMPUTER IS NOT A SIMPLE QUESTION

Different definitions produce different answers.

A machine may be considered first based on:

    - electronic operation
    - programmability
    - general-purpose capability
    - stored-program architecture
    - digital operation
    - practical use

Therefore, historical claims about "the first computer" need precise
definitions.

2. BABBAGE'S MACHINES WERE NOT MODERN ELECTRONIC COMPUTERS

Their importance is primarily conceptual and mechanical.

3. ADA LOVELACE DID NOT BUILD A MODERN COMPUTER PROGRAM

Her contribution involved algorithmic work for Babbage's proposed
Analytical Engine.

4. ENIAC WAS ELECTRONIC BUT NOT A MODERN STORED-PROGRAM COMPUTER IN
ITS ORIGINAL CONFIGURATION

Programming involved significant physical configuration.

5. VON NEUMANN ARCHITECTURE IS A MODEL

Real systems can contain architectural features beyond the simplified
von Neumann model.

6. MOORE'S LAW IS NOT A PHYSICAL LAW

It describes a historical trend in semiconductor development.

7. COMPUTER GENERATIONS ARE A TEACHING FRAMEWORK

They simplify a complex historical progression.

8. AI DID NOT BEGIN WITH DEEP LEARNING

AI research has a long history involving symbolic reasoning, search,
logic, knowledge representation and other methods.

9. CLOUD COMPUTING DID NOT APPEAR FROM NOTHING

It emerged from earlier developments in:

    - time-sharing
    - virtualization
    - distributed systems
    - data centers
    - networking
    - service-oriented architectures

10. MODERN COMPUTING IS HETEROGENEOUS

Modern systems can combine:

    CPU
    GPU
    accelerator
    memory hierarchy
    distributed servers
    specialized hardware
""")

    print()


# ============================================================================
# 104. CONCEPTUAL TIMELINE
# ============================================================================

def conceptual_timeline():
    print("=" * 80)
    print("CONCEPTUAL EVOLUTION")
    print("=" * 80)

    stages = [
        ("Counting", "Represent quantities"),
        ("Calculation", "Perform arithmetic"),
        ("Mechanization", "Automate arithmetic"),
        ("Programmability", "Specify sequences of operations"),
        ("Electronic computation", "Execute operations electronically"),
        ("Stored programs", "Store instructions in memory"),
        ("General-purpose computing", "Run many different programs"),
        ("Operating systems", "Abstract hardware management"),
        ("Networking", "Connect computers"),
        ("Internet", "Connect networks globally"),
        ("Web", "Publish and access linked information"),
        ("Personal computing", "Put computers into individual hands"),
        ("Mobile computing", "Make computing portable"),
        ("Cloud computing", "Deliver computing as network services"),
        ("Distributed computing", "Coordinate many machines"),
        ("AI computing", "Learn patterns and generate outputs")
    ]

    for stage, meaning in stages:
        print(f"{stage:28} -> {meaning}")

    print()


# ============================================================================
# 105. KEY TERMS
# ============================================================================

def key_terms():
    print("=" * 80)
    print("KEY TERMS")
    print("=" * 80)

    terms = {
        "Algorithm":
            "A finite procedure for solving a problem.",

        "Analog":
            "Representation using continuous physical quantities.",

        "Binary":
            "A base-2 numerical system.",

        "Bit":
            "A binary digit.",

        "Byte":
            "A common unit consisting of eight bits.",

        "CPU":
            "Central Processing Unit.",

        "ALU":
            "Arithmetic Logic Unit.",

        "RAM":
            "Random Access Memory used for active working data.",

        "ROM":
            "Read-Only Memory, traditionally associated with persistent programmed data.",

        "Cache":
            "Fast memory used to reduce effective access latency.",

        "Transistor":
            "A semiconductor device used for switching and amplification.",

        "Integrated Circuit":
            "A semiconductor chip containing multiple electronic components.",

        "Microprocessor":
            "A processor implemented largely on a single integrated circuit.",

        "Operating System":
            "Software that manages hardware and provides services to applications.",

        "Compiler":
            "Software that translates source programs into another representation.",

        "Protocol":
            "A set of rules governing communication between systems.",

        "Internet":
            "A global system of interconnected networks using common protocols.",

        "Web":
            "A hypertext-based information system operating over the Internet.",

        "Cloud Computing":
            "Network-accessible computing resources delivered as services.",

        "Distributed Computing":
            "Computing performed across multiple networked machines.",

        "Parallel Computing":
            "Concurrent execution of multiple computational tasks.",

        "Machine Learning":
            "Methods that allow systems to learn patterns from data.",

        "Deep Learning":
            "Machine learning based heavily on deep neural networks.",

        "Quantum Computing":
            "Computing based on quantum-mechanical principles."
    }

    for term, definition in terms.items():
        print(f"{term}:")
        print(f"    {definition}")
        print()

    print()


# ============================================================================
# 106. COMPLETE EVOLUTION MODEL
# ============================================================================

def complete_evolution_model():
    print("=" * 80)
    print("COMPLETE EVOLUTION MODEL")
    print("=" * 80)

    print("""
                    HISTORY OF COMPUTING
                           |
         +-----------------+-----------------+
         |                                   |
     REPRESENTATION                      AUTOMATION
         |                                   |
     Numbers                            Mechanical
     Symbols                            Electromechanical
     Data                               Electronic
         |                                   |
         +-----------------+-----------------+
                           |
                     PROGRAMMABILITY
                           |
                    Stored Programs
                           |
                    General Purpose
                           |
         +-----------------+-----------------+
         |                                   |
       HARDWARE                          SOFTWARE
         |                                   |
     Transistors                         Languages
     ICs                                 OS
     CPUs                                Applications
     GPUs                                Databases
     Accelerators                        AI
         |                                   |
         +-----------------+-----------------+
                           |
                       NETWORKING
                           |
                    Local Networks
                           |
                        Internet
                           |
                          Web
                           |
                    Cloud Services
                           |
                 Distributed Systems
                           |
                     EDGE + CLOUD
                           |
                    INTELLIGENT SYSTEMS
                           |
                  AI + MULTIMODAL SYSTEMS
""")

    print()


# ============================================================================
# 107. RUNNING THE COMPLETE LESSON
# ============================================================================

def run_complete_lesson():
    introduction()
    what_is_computing()
    early_human_computation()
    abacus()
    numerical_systems()
    napiers_bones()
    slide_rule()
    pascaline()
    leibniz_machine()
    jacquard_loom()
    charles_babbage()
    ada_lovelace()
    george_boole()
    herman_hollerith()
    electromechanical_computing()
    konrad_zuse()
    harvard_mark_i()
    alan_turing()
    church_turing()
    colossus()
    eniac()
    edvac()
    von_neumann_architecture()
    vacuum_tubes()
    transistor()
    integrated_circuits()
    moores_law()
    microprocessor()
    computer_generations()
    mainframes()
    minicomputers()
    personal_computers()
    gui()
    operating_systems()
    programming_languages()
    compiler_concept()
    assembly_language()
    databases()
    networking()
    arpanet()
    tcp_ip()
    world_wide_web()
    web_evolution()
    mobile_computing()
    embedded_systems()
    cloud_computing()
    virtualization()
    containers()
    distributed_computing()
    parallel_computing()
    gpu_computing()
    multicore_processors()
    risc_cisc()
    computer_architecture()
    memory_evolution()
    storage_evolution()
    input_output()
    artificial_intelligence()
    early_ai()
    expert_systems()
    machine_learning()
    neural_networks()
    deep_learning()
    transformers()
    generative_ai()
    data_centers()
    edge_computing()
    internet_of_things()
    quantum_computing()
    neuromorphic_computing()
    supercomputers()
    software_engineering()
    open_source()
    git()
    cybersecurity()
    cryptography()
    historical_timeline()
    major_figures()
    hardware_evolution()
    software_evolution()
    information_representation()
    digitalization()
    automation()
    computing_paradigms()
    analog_vs_digital()
    centralized_vs_distributed()
    computing_scale()
    human_computer_interaction()
    computing_and_science()
    computing_and_business()
    computing_and_communication()
    computing_and_education()
    computing_and_society()
    historical_transitions()
    general_purpose_computer()
    hardware_software_abstraction()
    computational_complexity()
    algorithms_and_hardware()
    data_revolution()
    big_data()
    computing_as_system()
    why_computing_evolved()
    peculiarities()
    conceptual_timeline()
    key_terms()
    complete_evolution_model()


# ============================================================================
# 108. PROGRAM ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    run_complete_lesson()
