# ============================================================
# DAY 01: INTRODUCTION TO COMPUTER SCIENCE
# ============================================================
#
# PURPOSE:
# This program is designed to teach the foundations of
# Computer Science from absolute beginner level to advanced
# conceptual understanding.
#
# TOPICS COVERED:
# 1. What is Computer Science?
# 2. Major Domains of Computer Science
# 3. Computer Science vs Computer Programming
# 4. Hardware vs Software
# 5. Firmware
# 6. Data, Information, and Knowledge
# 7. Computational Thinking
# 8. Decomposition
# 9. Pattern Recognition
# 10. Abstraction
# 11. Algorithmic Thinking
# 12. Algorithms
# 13. Inputs, Processing, Outputs
# 14. State and State Changes
# 15. Deterministic vs Non-Deterministic Processes
# 16. Finite and Infinite Processes
# 17. Automation
# 18. Efficiency and Optimization
# 19. Correctness
# 20. Scalability
# 21. Trade-offs
# 22. Levels of Abstraction
# 23. Systems Thinking
# 24. Human Problems vs Computational Problems
# 25. Real-world case studies
# 26. Interactive exercises
# 27. Mini computational-thinking project
#
# TOOLS:
# Python
# VS Code
# Terminal / Command Prompt
#
# ============================================================


# ============================================================
# SECTION 0: BASIC PROGRAM SETUP
# ============================================================

print("=" * 70)
print("DAY 01 - INTRODUCTION TO COMPUTER SCIENCE")
print("=" * 70)

print("""
Welcome to Day 01 of Computer Science Fundamentals.

This program is not designed simply to make you memorize
definitions.

The objective is to develop the way a computer scientist thinks.

You will learn how to:

    1. Understand computational problems.
    2. Break large problems into smaller problems.
    3. Identify patterns.
    4. Remove unnecessary details through abstraction.
    5. Design algorithms.
    6. Think about correctness.
    7. Think about efficiency.
    8. Understand how hardware and software interact.
    9. Understand the major fields of Computer Science.
   10. Translate real-world problems into computational models.

Let's begin.
""")


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def heading(title):
    print("\n" + "=" * 70)
    print(title.upper())
    print("=" * 70)


def subheading(title):
    print("\n" + "-" * 60)
    print(title)
    print("-" * 60)


def explain(term, explanation):
    print(f"\n{term}")
    print(explanation)


def pause():
    input("\nPress ENTER to continue...")


# ============================================================
# SECTION 1: WHAT IS COMPUTER SCIENCE?
# ============================================================

heading("1. What is Computer Science?")

print("""
Computer Science is the systematic study of computation.

Computation is the process of transforming information according
to well-defined rules.

Computer Science therefore deals with questions such as:

    - What problems can be solved computationally?
    - How can we represent information?
    - How can we design algorithms?
    - How efficiently can a problem be solved?
    - How can computers execute those algorithms?
    - How can multiple computers communicate?
    - How can data be stored and retrieved?
    - How can software be designed reliably?
    - What are the mathematical limits of computation?

Computer Science is much broader than programming.

Programming is one tool used within Computer Science.

A computer scientist may work on:

    Algorithms
    Operating Systems
    Databases
    Networks
    Artificial Intelligence
    Cybersecurity
    Computer Architecture
    Programming Languages
    Distributed Systems
    Human-Computer Interaction
    Computer Graphics
    Theory of Computation
    Software Engineering
    Information Retrieval
    Robotics
    Quantum Computing
""")


# ============================================================
# SECTION 2: COMPUTER SCIENCE VS PROGRAMMING
# ============================================================

heading("2. Computer Science vs Programming")

print("""
Programming means writing instructions that a computer can execute.

Computer Science asks deeper questions about computation.

For example:

Problem:
"Sort one million numbers."

A programmer might ask:

    How do I write code that sorts the numbers?

A computer scientist might ask:

    Which sorting algorithm should be used?
    What is its time complexity?
    What is its memory requirement?
    Is the data already partially sorted?
    Is stability required?
    Can the problem be distributed?
    Can sorting happen in memory?
    What happens when the data exceeds RAM?
    Can parallel hardware improve performance?

This distinction is extremely important.

Programming is implementation.

Computer Science includes:

    problem formulation
    mathematical modeling
    algorithm design
    computational analysis
    system design
    implementation
    testing
    optimization
    theoretical limits
""")


# ============================================================
# SECTION 3: MAJOR DOMAINS OF COMPUTER SCIENCE
# ============================================================

heading("3. Major Domains of Computer Science")

domains = {
    "Computer Architecture":
        "Studies CPUs, memory, buses, instruction sets and hardware organization.",

    "Operating Systems":
        "Studies processes, memory management, files, scheduling and system resources.",

    "Algorithms":
        "Studies systematic procedures for solving computational problems.",

    "Data Structures":
        "Studies methods for organizing and storing data efficiently.",

    "Database Systems":
        "Studies structured storage, retrieval, transactions and data management.",

    "Computer Networks":
        "Studies communication between computers and network protocols.",

    "Distributed Systems":
        "Studies systems whose components operate across multiple computers.",

    "Cybersecurity":
        "Studies confidentiality, integrity, availability, authentication and secure systems.",

    "Artificial Intelligence":
        "Studies systems capable of performing tasks associated with intelligent behavior.",

    "Machine Learning":
        "Studies algorithms that learn patterns from data.",

    "Programming Languages":
        "Studies language design, syntax, semantics, compilers and runtimes.",

    "Software Engineering":
        "Studies systematic development, testing, maintenance and management of software.",

    "Computer Graphics":
        "Studies generation and manipulation of visual information.",

    "Human-Computer Interaction":
        "Studies how humans interact with computational systems.",

    "Theory of Computation":
        "Studies mathematical models of computation and their limitations.",

    "Robotics":
        "Combines computation, sensing, control and physical machines.",

    "Quantum Computing":
        "Studies computation using quantum-mechanical phenomena."
}

for domain, description in domains.items():
    print(f"\n{domain}")
    print(f"    {description}")


# ============================================================
# SECTION 4: HARDWARE
# ============================================================

heading("4. Hardware")

print("""
Hardware refers to the physical components of a computing system.

Examples include:

    CPU
    RAM
    SSD
    HDD
    Motherboard
    GPU
    Network Interface Card
    Keyboard
    Mouse
    Monitor
    Printer
    Sensors
    Cameras

Hardware performs physical operations that allow software to run.

A useful conceptual model is:

        INPUT
          |
          v
      PROCESSING
          |
          v
        OUTPUT
          |
          v
       STORAGE

Example:

A user types:

    25 + 75

Keyboard
    ->
Operating System
    ->
Program
    ->
CPU
    ->
Result
    ->
Display

The physical hardware performs the underlying operations.
""")


# ============================================================
# SECTION 5: SOFTWARE
# ============================================================

heading("5. Software")

print("""
Software is a collection of instructions and related data that
directs a computer system to perform tasks.

Software can be broadly classified into:

1. System Software
2. Application Software
3. Programming Software

SYSTEM SOFTWARE
----------------

Examples:

    Operating systems
    Device drivers
    System utilities
    Firmware

APPLICATION SOFTWARE
--------------------

Examples:

    Web browsers
    Word processors
    Media players
    Games
    Banking applications

PROGRAMMING SOFTWARE
--------------------

Examples:

    Compilers
    Interpreters
    Debuggers
    IDEs
    Build systems
    Version-control tools

Software exists at multiple levels of abstraction.
""")


# ============================================================
# SECTION 6: HARDWARE VS SOFTWARE
# ============================================================

heading("6. Hardware vs Software")

comparison = [
    ("Physical", "Hardware is physical", "Software is logical/informational"),
    ("Examples", "CPU, RAM, SSD", "Python program, OS, browser"),
    ("Failure", "Physical failure", "Bug, corruption, configuration issue"),
    ("Modification", "Often requires physical change", "Usually requires changing code/data"),
    ("Execution", "Provides physical computation", "Provides instructions"),
    ("Dependency", "Can exist physically", "Normally requires hardware to execute")
]

for category, hardware, software in comparison:
    print(f"\n{category}")
    print(f"    Hardware : {hardware}")
    print(f"    Software : {software}")


# ============================================================
# SECTION 7: FIRMWARE
# ============================================================

heading("7. Firmware")

print("""
Firmware sits conceptually between hardware and software.

It is software stored in non-volatile memory and is closely
associated with controlling a hardware device.

Examples include:

    BIOS/UEFI firmware
    Router firmware
    SSD firmware
    Embedded-controller firmware
    Device firmware

A useful conceptual hierarchy is:

    Hardware
       ^
       |
    Firmware
       ^
       |
    Operating System
       ^
       |
    Applications

The boundaries can be more complicated in real systems,
but this model is useful for beginners.
""")


# ============================================================
# SECTION 8: DATA, INFORMATION AND KNOWLEDGE
# ============================================================

heading("8. Data, Information and Knowledge")

print("""
DATA
----

Raw symbols or recorded observations.

Example:

    30
    45
    50

INFORMATION
-----------

Data interpreted in context.

Example:

    Student scores are 30, 45 and 50.

KNOWLEDGE
---------

Understanding derived from information and relationships.

Example:

    The third student has the highest score.

Computer systems primarily manipulate data.

Through computation, data can be transformed into useful
information.
""")


# ============================================================
# SECTION 9: COMPUTATIONAL THINKING
# ============================================================

heading("9. Computational Thinking")

print("""
Computational Thinking is a structured approach to solving
problems in a way that can potentially be performed by humans,
computers, or both.

The four classical pillars are:

    1. Decomposition
    2. Pattern Recognition
    3. Abstraction
    4. Algorithm Design

These ideas are not restricted to programming.

They can be applied to:

    Business
    Project Management
    Science
    Engineering
    Finance
    Healthcare
    Logistics
    Cybersecurity
    Education
    Everyday decision making
""")


# ============================================================
# SECTION 10: DECOMPOSITION
# ============================================================

heading("10. Decomposition")

print("""
Decomposition means breaking a complex problem into smaller
manageable problems.

Example:

Problem:
"Build an online shopping platform."

Instead of treating it as one giant problem, decompose it:

    User Management
        |
        +-- Registration
        +-- Login
        +-- Authentication

    Product Management
        |
        +-- Product catalog
        +-- Search
        +-- Categories

    Shopping Cart
        |
        +-- Add item
        +-- Remove item
        +-- Update quantity

    Payment
        |
        +-- Payment processing
        +-- Transaction verification

    Order Management
        |
        +-- Create order
        +-- Track order
        +-- Cancel order

Each component can then be analyzed separately.
""")


# ============================================================
# SECTION 11: PATTERN RECOGNITION
# ============================================================

heading("11. Pattern Recognition")

print("""
Pattern recognition means identifying similarities or repeated
structures in problems.

Example:

    2, 4, 6, 8, 10

The pattern is:

    next = previous + 2

Another example:

Suppose a company receives thousands of customer complaints.

Instead of examining every complaint as completely unique,
we can identify patterns:

    Login problems
    Payment problems
    Delivery problems
    Product problems

Patterns help us generalize solutions.
""")


# ============================================================
# SECTION 12: ABSTRACTION
# ============================================================

heading("12. Abstraction")

print("""
Abstraction means focusing on important characteristics while
hiding unnecessary implementation details.

Consider a car.

A driver uses:

    Steering wheel
    Accelerator
    Brake
    Gear selector

The driver does not need to understand every detail of:

    fuel injection
    combustion
    transmission gears
    engine timing
    electronic control units

The interface hides complexity.

Programming works similarly.

When you call:

    print("Hello")

you do not manually control:

    CPU registers
    memory buses
    display hardware
    operating-system system calls
    device drivers

The programming language and operating system provide
abstractions over those details.
""")


# ============================================================
# SECTION 13: LEVELS OF ABSTRACTION
# ============================================================

heading("13. Levels of Abstraction")

print("""
A modern computing system contains many layers.

A simplified model is:

    Physical Hardware
            |
            v
    Machine Instructions
            |
            v
    Assembly Language
            |
            v
    High-Level Language
            |
            v
    Libraries
            |
            v
    Operating System
            |
            v
    Application
            |
            v
        End User

Each layer hides some complexity from the layer above it.

This is one of the most important ideas in Computer Science.

Without abstraction, software development would become
extremely difficult.
""")


# ============================================================
# SECTION 14: ALGORITHMIC THINKING
# ============================================================

heading("14. Algorithmic Thinking")

print("""
Algorithmic thinking means designing a precise sequence of
steps to transform an input into a desired output.

Example problem:

Find the largest number in a list.

Input:

    [12, 45, 7, 91, 34]

Algorithm:

    1. Assume the first number is largest.
    2. Compare it with the next number.
    3. If the next number is larger, update the largest value.
    4. Continue until the list ends.
    5. Return the largest value.

Output:

    91
""")


# ============================================================
# SECTION 15: FIRST ALGORITHM IMPLEMENTATION
# ============================================================

heading("15. Implementing an Algorithm")

def find_largest(numbers):

    if not numbers:
        raise ValueError("The list cannot be empty.")

    largest = numbers[0]

    for number in numbers[1:]:
        if number > largest:
            largest = number

    return largest


numbers = [12, 45, 7, 91, 34]

print("\nInput:", numbers)
print("Largest value:", find_largest(numbers))


# ============================================================
# SECTION 16: INPUT -> PROCESSING -> OUTPUT
# ============================================================

heading("16. Input, Processing and Output")

print("""
Most computational tasks can be understood using:

    INPUT
      |
      v
   PROCESS
      |
      v
    OUTPUT

Example:

Input:
    Marks = [70, 80, 90]

Processing:
    Calculate average.

Output:
    80
""")


def calculate_average(numbers):

    if len(numbers) == 0:
        raise ValueError("Cannot calculate average of empty data.")

    total = sum(numbers)
    count = len(numbers)

    return total / count


marks = [70, 80, 90]

print("\nMarks:", marks)
print("Average:", calculate_average(marks))


# ============================================================
# SECTION 17: STATE
# ============================================================

heading("17. State and State Changes")

print("""
A state represents the condition of a system at a particular
point in time.

Example:

Bank account:

    Initial balance = 10,000

Transaction:

    Deposit = 5,000

New state:

    Balance = 15,000

The operation transformed:

    OLD STATE -> OPERATION -> NEW STATE

This concept is fundamental in:

    Operating Systems
    Databases
    Distributed Systems
    Games
    User Interfaces
    Networking
    Programming Languages
""")


balance = 10000

print("\nInitial balance:", balance)

balance += 5000

print("After deposit:", balance)

balance -= 2000

print("After withdrawal:", balance)


# ============================================================
# SECTION 18: DETERMINISTIC COMPUTATION
# ============================================================

heading("18. Deterministic vs Non-Deterministic Processes")

print("""
A deterministic process produces the same output when given
the same input and the same conditions.

Example:

    5 + 10 = 15

Every time this computation is performed, the result is 15.

A process can be non-deterministic when factors such as:

    random events
    timing
    concurrency
    external inputs
    network behavior

can influence the result.

Understanding determinism becomes important when studying:

    Algorithms
    Operating Systems
    Distributed Systems
    Concurrent Programming
    Artificial Intelligence
""")


def deterministic_square(number):
    return number * number


print("\nDeterministic examples:")

for value in [2, 5, 10]:
    print(value, "->", deterministic_square(value))


# ============================================================
# SECTION 19: ALGORITHM CORRECTNESS
# ============================================================

heading("19. Algorithm Correctness")

print("""
An algorithm is useful only if it produces the correct result
for all valid inputs within its specified problem domain.

Consider this function:

    find_largest()

We should ask:

    Does it work with positive numbers?
    Does it work with negative numbers?
    Does it work with duplicate numbers?
    Does it work with one number?
    What happens with an empty list?

Testing examples:
""")


test_cases = [
    [1, 2, 3],
    [-10, -5, -20],
    [5, 5, 5],
    [100],
    [-1, -2, -3]
]

for case in test_cases:
    print(f"{case} -> {find_largest(case)}")


# ============================================================
# SECTION 20: EDGE CASES
# ============================================================

heading("20. Edge Cases")

print("""
An edge case is an unusual or boundary input that can reveal
problems in an algorithm.

For find_largest():

    Normal:
        [10, 20, 30]

    Duplicate:
        [10, 10, 10]

    Negative:
        [-5, -10, -1]

    Single value:
        [42]

    Empty:
        []

Good computer science practice requires thinking about
edge cases before implementation.
""")


# ============================================================
# SECTION 21: ALGORITHM EFFICIENCY
# ============================================================

heading("21. Algorithm Efficiency")

print("""
Two algorithms may solve the same problem but require very
different amounts of computational resources.

Important resources include:

    Time
    Memory
    Network bandwidth
    Storage
    Energy

Example:

Searching for a value in a list can be performed using:

    Linear Search
    Binary Search

Linear search may inspect items one by one.

Binary search can repeatedly divide a sorted search space.

The key idea is:

    Correctness is necessary.
    Efficiency matters when systems become large.
""")


# ============================================================
# SECTION 22: SIMPLE SEARCH ALGORITHM
# ============================================================

heading("22. Linear Search")

def linear_search(data, target):

    for index, value in enumerate(data):

        if value == target:
            return index

    return -1


data = [10, 25, 30, 45, 60]

print("\nData:", data)
print("Search target: 45")
print("Index:", linear_search(data, 45))

print("\nSearch target: 99")
print("Index:", linear_search(data, 99))


# ============================================================
# SECTION 23: COMPLEXITY
# ============================================================

heading("23. Introduction to Complexity")

print("""
Complexity describes how resource requirements grow as input
size increases.

Suppose we search through n elements.

In the worst case, linear search may inspect:

    n elements

We describe this growth using asymptotic notation.

Linear search:

    O(n)

This does NOT mean exactly n operations in every situation.

Big-O describes an upper-bound style growth classification
commonly used to discuss scalability.

Later in Computer Science you will study:

    O(1)
    O(log n)
    O(n)
    O(n log n)
    O(n²)
    O(2^n)
    O(n!)

These concepts become fundamental in algorithms and
data structures.
""")


# ============================================================
# SECTION 24: SCALABILITY
# ============================================================

heading("24. Scalability")

print("""
Scalability asks:

    What happens when the size of the problem becomes larger?

Imagine an application that works perfectly for:

    100 users

What happens at:

    10,000 users?
    1 million users?
    100 million users?

A scalable design should continue functioning effectively
as workload increases.

Scalability may involve:

    Better algorithms
    More memory
    Faster processors
    Caching
    Parallel processing
    Distributed systems
    Database indexing
    Load balancing
    Horizontal scaling
""")


# ============================================================
# SECTION 25: TRADE-OFFS
# ============================================================

heading("25. Computational Trade-offs")

print("""
Computer Science is full of trade-offs.

Improving one property may negatively affect another.

Examples:

    Speed vs memory
    Security vs convenience
    Accuracy vs computational cost
    Simplicity vs flexibility
    Latency vs throughput
    Consistency vs availability
    Storage vs retrieval speed

Example:

A cache stores frequently accessed information closer to the
processor.

This can improve speed.

But cache memory is expensive and limited.

Therefore:

    More cache -> potentially better performance
    More cache -> greater hardware cost

Computer science often involves choosing an appropriate
trade-off rather than finding a perfect solution.
""")


# ============================================================
# SECTION 26: AUTOMATION
# ============================================================

heading("26. Automation")

print("""
Automation means allowing a system to perform tasks with
minimal human intervention.

Example:

Manual process:

    Open file
    Read data
    Calculate total
    Write result
    Repeat

Automated process:

    Program reads files
    Program calculates totals
    Program generates report

Python is particularly useful for automation.

Let's automate a simple calculation.
""")


def calculate_total(values):
    return sum(values)


expenses = [500, 1200, 800, 350, 950]

print("\nExpenses:", expenses)
print("Total:", calculate_total(expenses))


# ============================================================
# SECTION 27: SYSTEMS THINKING
# ============================================================

heading("27. Systems Thinking")

print("""
A system is a collection of interacting components that work
together toward some purpose.

Consider an online banking system.

Components might include:

    User Interface
    Authentication Service
    Account Service
    Transaction Service
    Database
    Fraud Detection
    Notification Service
    Network
    Operating System
    Hardware

A failure in one component can affect other components.

Computer scientists therefore study not only individual
components but also their interactions.
""")


# ============================================================
# SECTION 28: REAL-WORLD PROBLEM
# ============================================================

heading("28. Real-World Problem: Food Delivery")

print("""
Suppose we want to build a food-delivery application.

The real-world problem is:

    "Help customers order food from restaurants."

A computer scientist decomposes the problem.

CUSTOMER
    |
    +-- Registration
    +-- Login
    +-- Search restaurants
    +-- Select food
    +-- Add to cart
    +-- Pay
    +-- Track order

RESTAURANT
    |
    +-- Receive order
    +-- Accept order
    +-- Prepare food
    +-- Update status

DELIVERY
    |
    +-- Assign delivery partner
    +-- Navigate to restaurant
    +-- Pick up order
    +-- Deliver order

SYSTEM
    |
    +-- Database
    +-- Authentication
    +-- Payments
    +-- Notifications
    +-- Maps
    +-- Monitoring

This demonstrates decomposition and abstraction.
""")


# ============================================================
# SECTION 29: ALGORITHM FOR FOOD DELIVERY
# ============================================================

heading("29. Food Delivery Algorithm")

print("""
A simplified ordering algorithm could be:

    STEP 1:
        Customer selects restaurant.

    STEP 2:
        Customer selects items.

    STEP 3:
        System calculates total.

    STEP 4:
        Customer confirms order.

    STEP 5:
        Payment is processed.

    STEP 6:
        Restaurant receives order.

    STEP 7:
        Restaurant accepts order.

    STEP 8:
        Delivery partner is assigned.

    STEP 9:
        Food is prepared.

    STEP 10:
        Delivery partner collects food.

    STEP 11:
        Food is delivered.

    STEP 12:
        Order status becomes "Completed".

Real systems are much more complex because each step may
fail and require error handling.
""")


# ============================================================
# SECTION 30: FAILURE THINKING
# ============================================================

heading("30. Failure Thinking")

print("""
Computer scientists must think about what happens when things
go wrong.

Possible failures:

    Network unavailable
    Database unavailable
    Payment rejected
    Restaurant rejects order
    Delivery partner unavailable
    User closes application
    Server crashes
    Duplicate request
    Incorrect input
    Malicious input

A robust system must account for these possibilities.

This leads to important concepts that you will study later:

    Exception handling
    Fault tolerance
    Transactions
    Retries
    Logging
    Monitoring
    Authentication
    Authorization
    Distributed systems
""")


# ============================================================
# SECTION 31: HUMAN PROBLEM VS COMPUTATIONAL PROBLEM
# ============================================================

heading("31. Translating Human Problems into Computational Problems")

print("""
Humans often describe problems ambiguously.

Example:

    "Find the best route."

A computer needs a precise definition.

What does "best" mean?

    Shortest distance?
    Lowest cost?
    Lowest travel time?
    Least traffic?
    Safest route?
    Lowest fuel consumption?

Computer Science requires converting vague objectives into
precise computational models.

For example:

    Objective:
        Minimize travel time.

    Input:
        Locations
        Roads
        Distances
        Traffic information

    Output:
        A route minimizing estimated travel time.

This process of formalization is a critical CS skill.
""")


# ============================================================
# SECTION 32: ALGORITHM AS A CONTRACT
# ============================================================

heading("32. Algorithms as Contracts")

print("""
An algorithm can be viewed as a contract:

    Given valid input,
    perform defined operations,
    produce required output.

For example:

    Function:
        calculate_average(numbers)

    Input:
        A non-empty collection of numbers.

    Output:
        Arithmetic mean.

    Invalid input:
        Empty collection.

Defining the contract makes software easier to reason about,
test and maintain.
""")


# ============================================================
# SECTION 33: REUSABILITY
# ============================================================

heading("33. Reusable Abstractions")

print("""
A good computational solution can often be reused.

Instead of writing:

    total_expenses()
    total_sales()
    total_marks()

separately, we can recognize a common pattern:

    Calculate the sum of values.

Then create:

    calculate_total(values)

This is abstraction and generalization.

The same principle appears throughout software engineering.
""")


# ============================================================
# SECTION 34: GENERALIZATION
# ============================================================

heading("34. Generalization")

def calculate_total(values):
    return sum(values)


examples = {
    "Marks": [80, 75, 90],
    "Expenses": [500, 1200, 300],
    "Sales": [1000, 2500, 3000]
}

for name, values in examples.items():
    print(f"{name}: {values}")
    print(f"Total: {calculate_total(values)}")


# ============================================================
# SECTION 35: COMPUTATIONAL MODEL
# ============================================================

heading("35. Computational Models")

print("""
A computational model is an abstract representation of how
computation works.

Examples include:

    Turing Machines
    Finite Automata
    Pushdown Automata
    Lambda Calculus
    Boolean Circuits
    State Machines
    RAM Models

You do not need to master these today.

The important idea is:

    We can mathematically model computation.

This eventually leads to questions such as:

    What can computers compute?

    What cannot computers compute?

    How much computational resource is required?

    Are some problems fundamentally harder than others?
""")


# ============================================================
# SECTION 36: COMPUTABILITY
# ============================================================

heading("36. Computability")

print("""
Computability asks whether a problem can be solved by an
algorithm at all.

This is deeper than asking whether a computer is fast enough.

Some problems have algorithms.

Some problems may be computationally infeasible at large scale.

Some problems are undecidable under particular formal models.

This area leads into:

    Theory of Computation
    Automata Theory
    Formal Languages
    Computability Theory
    Complexity Theory

These are advanced areas of Computer Science.
""")


# ============================================================
# SECTION 37: FEASIBILITY
# ============================================================

heading("37. Feasibility")

print("""
A problem can be computable but still practically difficult.

Suppose an algorithm requires:

    2^n operations

For small n, that may be manageable.

For large n, the number of operations can become enormous.

Therefore we distinguish between:

    Computable
    Practically feasible
    Efficient
    Infeasible

This distinction becomes extremely important in algorithm
design.
""")


# ============================================================
# SECTION 38: CORRECTNESS + EFFICIENCY + RESOURCE USAGE
# ============================================================

heading("38. Three Major Questions")

print("""
When evaluating a computational solution, ask:

1. CORRECTNESS

    Does it produce the right answer?

2. EFFICIENCY

    How much time does it require?

3. RESOURCE USAGE

    How much memory, storage, bandwidth or energy does it use?

A solution that is correct but extremely inefficient may not
be useful in the real world.

A fast solution that produces incorrect results is also useless.

Good Computer Science balances these dimensions.
""")


# ============================================================
# SECTION 39: PYTHON AS A CS LEARNING TOOL
# ============================================================

heading("39. Why Python is Useful for Learning Computer Science")

print("""
Python is not Computer Science itself.

It is a tool for expressing computational ideas.

Python is useful because it provides:

    Simple syntax
    Functions
    Data structures
    Object-oriented programming
    Functional programming features
    File processing
    Networking libraries
    Automation
    Scientific libraries
    Visualization libraries
    Machine learning libraries

During your Computer Science journey, Python can be used to
experiment with:

    Algorithms
    Data structures
    Operating-system concepts
    Networking
    Databases
    AI
    Simulations
    Automation
""")


# ============================================================
# SECTION 40: MINI EXERCISE
# ============================================================

heading("40. Mini Exercise")

print("""
Problem:

Given a list of numbers, determine:

    1. Total
    2. Average
    3. Minimum
    4. Maximum
    5. Number of elements
""")


def analyze_numbers(numbers):

    if not numbers:
        raise ValueError("Input cannot be empty.")

    result = {
        "total": sum(numbers),
        "average": sum(numbers) / len(numbers),
        "minimum": min(numbers),
        "maximum": max(numbers),
        "count": len(numbers)
    }

    return result


sample_numbers = [10, 20, 30, 40, 50]

analysis = analyze_numbers(sample_numbers)

print("\nInput:", sample_numbers)

for key, value in analysis.items():
    print(f"{key.capitalize()}: {value}")


# ============================================================
# SECTION 41: COMPUTATIONAL THINKING CHALLENGE
# ============================================================

heading("41. Computational Thinking Challenge")

print("""
Challenge:

Imagine you need to manage a library.

The library has:

    10,000 books
    2,000 users
    Thousands of borrowing transactions

You need to build a computerized system.

Think through these questions:

    1. What are the main components?

    2. How would you decompose the problem?

    3. What data needs to be stored?

    4. What operations are required?

    5. How would users search for books?

    6. How would you identify overdue books?

    7. What happens if two users attempt to borrow the same
       book simultaneously?

    8. What happens if the database becomes unavailable?

    9. How would the system scale to one million books?

   10. What security controls are required?

Do not immediately write code.

First think computationally.
""")


# ============================================================
# SECTION 42: POSSIBLE LIBRARY SYSTEM DECOMPOSITION
# ============================================================

heading("42. Library System Decomposition")

library_modules = [
    "User Management",
    "Book Management",
    "Search",
    "Borrowing",
    "Returns",
    "Reservations",
    "Fine Calculation",
    "Notifications",
    "Authentication",
    "Database",
    "Reporting",
    "Security"
]

for number, module in enumerate(library_modules, start=1):
    print(f"{number:02d}. {module}")


# ============================================================
# SECTION 43: DESIGN QUESTIONS
# ============================================================

heading("43. Questions Every Computer Scientist Learns to Ask")

questions = [
    "What exactly is the problem?",
    "What are the inputs?",
    "What is the expected output?",
    "What constraints exist?",
    "What assumptions are being made?",
    "Can the problem be decomposed?",
    "Are there recognizable patterns?",
    "What details can be abstracted away?",
    "What algorithm can solve the problem?",
    "Is the algorithm correct?",
    "How efficient is it?",
    "How much memory does it need?",
    "How does it behave at scale?",
    "What are the edge cases?",
    "What happens when something fails?",
    "What security risks exist?",
    "Can the solution be generalized?",
    "Can the solution be reused?",
    "What trade-offs are involved?"
]

for number, question in enumerate(questions, start=1):
    print(f"{number:02d}. {question}")


# ============================================================
# SECTION 44: KNOWLEDGE CHECK
# ============================================================

heading("44. Knowledge Check")

print("""
Answer these questions yourself before reading the answers.

Q1. Is Computer Science the same as programming?

Q2. What are the four major pillars of computational thinking?

Q3. What is abstraction?

Q4. What is decomposition?

Q5. What is an algorithm?

Q6. What is the difference between hardware and software?

Q7. Why is algorithmic efficiency important?

Q8. What is scalability?

Q9. What is a computational model?

Q10. What is the difference between computability and efficiency?
""")


# ============================================================
# SECTION 45: KNOWLEDGE CHECK ANSWERS
# ============================================================

heading("45. Knowledge Check Answers")

answers = {
    1: "No. Programming is one activity within the broader field of Computer Science.",
    2: "Decomposition, pattern recognition, abstraction and algorithm design.",
    3: "Abstraction hides unnecessary details while exposing the important characteristics.",
    4: "Decomposition means breaking a complex problem into smaller manageable problems.",
    5: "An algorithm is a well-defined procedure for solving a problem or performing a computation.",
    6: "Hardware is physical computing machinery; software consists primarily of instructions and data.",
    7: "Because inefficient algorithms can become impractical as input size grows.",
    8: "Scalability is the ability of a system or solution to handle increasing workload effectively.",
    9: "A computational model is an abstract mathematical or conceptual representation of computation.",
    10: "Computability asks whether a problem can be solved algorithmically; efficiency asks how much resources the solution requires."
}

for number, answer in answers.items():
    print(f"\nQ{number}: {answer}")


# ============================================================
# SECTION 46: FINAL CONCEPT MAP
# ============================================================

heading("46. Final Concept Map")

print("""
                         COMPUTER SCIENCE
                                |
             +------------------+------------------+
             |                  |                  |
        COMPUTATION          SYSTEMS           THEORY
             |                  |                  |
        Algorithms          Hardware          Computability
        Data Structures      Software          Complexity
        Programming          Operating         Automata
        Data                  Systems           Formal Methods
             |
             +----------------+
             |
      COMPUTATIONAL THINKING
             |
      +------+------+------+
      |      |      |      |
 Decompose Pattern Abstract Algorithm
             |
             v
        PROBLEM SOLVING
             |
             v
        IMPLEMENTATION
             |
             v
        CORRECTNESS
             |
             v
        EFFICIENCY
             |
             v
        SCALABILITY
             |
             v
        REAL-WORLD SYSTEM
""")


# ============================================================
# SECTION 47: WHAT YOU SHOULD NOW UNDERSTAND
# ============================================================

heading("47. End-of-Day Understanding")

print("""
After completing this program, you should understand that:

    Computer Science is the study of computation.

    Programming is a tool used to express computational solutions.

    Hardware provides physical computing capabilities.

    Software provides instructions and abstractions.

    Computational thinking provides a structured approach to
    solving problems.

    Decomposition breaks large problems into smaller problems.

    Pattern recognition identifies reusable structures.

    Abstraction hides unnecessary complexity.

    Algorithms provide systematic procedures for computation.

    Correctness determines whether a solution solves the intended
    problem.

    Complexity helps us reason about computational resources.

    Scalability determines how solutions behave as workloads grow.

    Systems thinking helps us understand interactions between
    components.

    Advanced Computer Science eventually asks deeper questions
    about computation, efficiency, communication, security,
    distributed systems and the fundamental limits of machines.
""")


# ============================================================
# SECTION 48: FINAL MINI PROJECT
# ============================================================

heading("48. Final Mini Project")

print("""
FINAL PROJECT:

Create a simple "Student Result Analyzer".

Requirements:

    Input:
        Student name
        Marks in multiple subjects

    Processing:
        Calculate total
        Calculate average
        Find highest mark
        Find lowest mark
        Determine pass/fail
        Determine grade

    Output:
        Student report

Then improve it using computational-thinking principles.

Version 1:
    Simple implementation

Version 2:
    Functions

Version 3:
    Validation

Version 4:
    Multiple students

Version 5:
    File storage

Version 6:
    Searching

Version 7:
    Sorting

Version 8:
    Statistical analysis

Version 9:
    Database storage

Version 10:
    Web-based application

This demonstrates how a simple problem can evolve into a
complete software system.
""")


# ============================================================
# OPTIONAL IMPLEMENTATION OF THE MINI PROJECT
# ============================================================

def calculate_grade(average):

    if average >= 90:
        return "A+"
    elif average >= 80:
        return "A"
    elif average >= 70:
        return "B"
    elif average >= 60:
        return "C"
    elif average >= 50:
        return "D"
    else:
        return "F"


def generate_student_report(name, marks):

    if not marks:
        raise ValueError("Marks cannot be empty.")

    total = sum(marks)
    average = total / len(marks)
    highest = max(marks)
    lowest = min(marks)

    passed = all(mark >= 40 for mark in marks)

    grade = calculate_grade(average) if passed else "F"

    return {
        "name": name,
        "marks": marks,
        "total": total,
        "average": average,
        "highest": highest,
        "lowest": lowest,
        "result": "PASS" if passed else "FAIL",
        "grade": grade
    }


student = generate_student_report(
    "Atul",
    [85, 78, 92, 88, 76]
)

print("\nSTUDENT REPORT")
print("-" * 40)

for key, value in student.items():
    print(f"{key.capitalize():12}: {value}")


# ============================================================
# SECTION 49: FINAL REFLECTION
# ============================================================

heading("49. Final Reflection")

print("""
Before moving to Day 02, you should be able to explain these
concepts without memorizing the definitions:

    What is Computer Science?

    Why is Computer Science broader than programming?

    What are the major areas of Computer Science?

    What is hardware?

    What is software?

    What is firmware?

    What is computational thinking?

    What is decomposition?

    What is pattern recognition?

    What is abstraction?

    What is an algorithm?

    What is correctness?

    What is efficiency?

    What is complexity?

    What is scalability?

    What is a computational model?

    What is computability?

    Why are trade-offs unavoidable?

If you can explain these concepts in your own words and apply
them to a new problem, you have successfully completed the
conceptual foundation of Day 01.
""")


# ============================================================
# PROGRAM COMPLETION
# ============================================================

print("\n" + "=" * 70)
print("DAY 01 COMPLETE")
print("=" * 70)

print("""
You have completed:

    Introduction to Computer Science

The next stage of the journey is to understand how information
is represented inside computers.

Next major topic:

    NUMBER SYSTEMS AND DIGITAL REPRESENTATION

You will eventually move from:

    Human concepts
        ->
    Computational thinking
        ->
    Algorithms
        ->
    Data representation
        ->
    Hardware
        ->
    Operating systems
        ->
    Networks
        ->
    Databases
        ->
    Distributed systems
        ->
    Security
        ->
    Advanced Computer Science
""")

print("=" * 70)
print("END OF DAY 01")
print("=" * 70)
