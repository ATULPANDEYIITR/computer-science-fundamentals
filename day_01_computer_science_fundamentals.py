# ============================================================
# DAY 01: COMPUTER SCIENCE FUNDAMENTALS
# ============================================================

print("DAY 01 - COMPUTER SCIENCE FUNDAMENTALS")


# ============================================================
# 1. WHAT IS COMPUTER SCIENCE?
# ============================================================

print("\n1. WHAT IS COMPUTER SCIENCE?")

print("Computer Science is the study of computation,")
print("algorithms, information, software, hardware,")
print("and computational systems.")

print("\nIt is not limited to programming.")
print("Programming is one part of Computer Science.")


# ============================================================
# 2. COMPUTER SYSTEM
# ============================================================

print("\n2. COMPUTER SYSTEM")

computer_system = {
    "Input": "Receives data",
    "Processing": "Processes data",
    "Memory": "Stores data temporarily",
    "Storage": "Stores data permanently",
    "Output": "Produces results"
}

for component, purpose in computer_system.items():
    print(component, "->", purpose)


# ============================================================
# 3. HARDWARE
# ============================================================

print("\n3. HARDWARE")

hardware = [
    "CPU",
    "RAM",
    "Storage",
    "Motherboard",
    "GPU",
    "Keyboard",
    "Mouse",
    "Monitor",
    "Network Interface"
]

for component in hardware:
    print("-", component)


# ============================================================
# 4. SOFTWARE
# ============================================================

print("\n4. SOFTWARE")

software = [
    "Operating Systems",
    "Applications",
    "Programming Languages",
    "Drivers",
    "Utilities"
]

for item in software:
    print("-", item)


# ============================================================
# 5. CPU
# ============================================================

print("\n5. CENTRAL PROCESSING UNIT")

print("The CPU executes instructions and performs")
print("operations required by computer programs.")

cpu_components = [
    "Control Unit",
    "Arithmetic Logic Unit",
    "Registers",
    "Cache"
]

for component in cpu_components:
    print("-", component)


# ============================================================
# 6. MEMORY AND STORAGE
# ============================================================

print("\n6. MEMORY AND STORAGE")

memory_storage = {
    "Registers": "Very fast CPU storage",
    "Cache": "Fast memory close to the CPU",
    "RAM": "Temporary working memory",
    "SSD/HDD": "Persistent storage"
}

for component, purpose in memory_storage.items():
    print(component, "->", purpose)


# ============================================================
# 7. DATA
# ============================================================

print("\n7. DATA")

data_examples = [
    "Numbers",
    "Text",
    "Images",
    "Audio",
    "Video",
    "Documents"
]

for data in data_examples:
    print("-", data)


# ============================================================
# 8. BINARY
# ============================================================

print("\n8. BINARY")

print("Computers represent information using bits.")
print("A bit can have two possible values: 0 or 1.")

bits = [0, 1, 1, 0, 1, 0, 0, 1]

print("Example binary data:", bits)


# ============================================================
# 9. NUMBER REPRESENTATION
# ============================================================

print("\n9. NUMBER REPRESENTATION")

number = 25

print("Decimal:", number)
print("Binary:", bin(number))
print("Hexadecimal:", hex(number))

print("\nComputers commonly use binary internally.")
print("Hexadecimal is often used as a compact representation")
print("of binary data.")


# ============================================================
# 10. ALGORITHMS
# ============================================================

print("\n10. ALGORITHMS")

print("An algorithm is a defined sequence of steps")
print("used to solve a problem or perform a task.")

algorithm = [
    "Start",
    "Receive input",
    "Process input",
    "Produce result",
    "End"
]

for step_number, step in enumerate(algorithm, start=1):
    print(step_number, "->", step)


# ============================================================
# 11. SIMPLE ALGORITHM
# ============================================================

print("\n11. SIMPLE ALGORITHM")


def find_largest(numbers):

    largest = numbers[0]

    for number in numbers:

        if number > largest:
            largest = number

    return largest


numbers = [12, 45, 7, 89, 23]

print("Numbers:", numbers)
print("Largest:", find_largest(numbers))


# ============================================================
# 12. PROGRAMMING
# ============================================================

print("\n12. PROGRAMMING")

print("Programming is the process of writing instructions")
print("that computers can execute.")

programming_languages = [
    "Python",
    "C",
    "C++",
    "Java",
    "JavaScript",
    "Go",
    "Rust"
]

for language in programming_languages:
    print("-", language)


# ============================================================
# 13. VARIABLES AND DATA TYPES
# ============================================================

print("\n13. VARIABLES AND DATA TYPES")

name = "Computer Science"
year = 2026
is_learning = True
score = 95.5

print("Name:", name)
print("Year:", year)
print("Learning:", is_learning)
print("Score:", score)

print("\nBasic data types:")
print("- String")
print("- Integer")
print("- Float")
print("- Boolean")


# ============================================================
# 14. CONTROL FLOW
# ============================================================

print("\n14. CONTROL FLOW")

score = 75

if score >= 50:
    print("Result: Pass")
else:
    print("Result: Fail")


# ============================================================
# 15. LOOPS
# ============================================================

print("\n15. LOOPS")

for number in range(1, 6):
    print("Iteration:", number)

print("\nLoops allow a program to repeat operations.")


# ============================================================
# 16. FUNCTIONS
# ============================================================

print("\n16. FUNCTIONS")


def calculate_average(a, b):
    return (a + b) / 2


result = calculate_average(80, 90)

print("Average:", result)

print("\nFunctions divide programs into reusable pieces of logic.")


# ============================================================
# 17. DATA STRUCTURES
# ============================================================

print("\n17. DATA STRUCTURES")

numbers = [10, 20, 30]

student = {
    "name": "Student",
    "score": 85
}

print("List:", numbers)
print("Dictionary:", student)

print("\nData structures organize and store information")
print("so that programs can work with it efficiently.")


# ============================================================
# 18. OPERATING SYSTEM
# ============================================================

print("\n18. OPERATING SYSTEM")

operating_systems = [
    "Linux",
    "Windows",
    "macOS",
    "Android",
    "iOS"
]

for operating_system in operating_systems:
    print("-", operating_system)

print("\nAn operating system manages hardware, software,")
print("memory, processes, files, and other system resources.")


# ============================================================
# 19. NETWORKING
# ============================================================

print("\n19. COMPUTER NETWORKING")

networking_concepts = [
    "IP Address",
    "DNS",
    "TCP/IP",
    "HTTP/HTTPS",
    "Routers",
    "Switches",
    "Servers"
]

for concept in networking_concepts:
    print("-", concept)


# ============================================================
# 20. DATABASES
# ============================================================

print("\n20. DATABASES")

database_concepts = [
    "Data",
    "Tables",
    "Records",
    "Queries",
    "Relationships",
    "Indexes"
]

for concept in database_concepts:
    print("-", concept)


# ============================================================
# 21. CYBERSECURITY
# ============================================================

print("\n21. CYBERSECURITY")

security_concepts = [
    "Authentication",
    "Authorization",
    "Encryption",
    "Access Control",
    "Network Security",
    "Data Protection"
]

for concept in security_concepts:
    print("-", concept)


# ============================================================
# 22. SOFTWARE ENGINEERING
# ============================================================

print("\n22. SOFTWARE ENGINEERING")

software_engineering = [
    "Requirements",
    "Design",
    "Development",
    "Testing",
    "Version Control",
    "Deployment",
    "Maintenance"
]

for stage in software_engineering:
    print("-", stage)


# ============================================================
# 23. COMPUTATIONAL THINKING
# ============================================================

print("\n23. COMPUTATIONAL THINKING")

thinking_methods = [
    "Decomposition",
    "Pattern Recognition",
    "Abstraction",
    "Algorithmic Thinking"
]

for method in thinking_methods:
    print("-", method)

print("\nComputational thinking helps break complex problems")
print("into smaller and manageable parts.")


# ============================================================
# 24. MAJOR AREAS OF COMPUTER SCIENCE
# ============================================================

print("\n24. MAJOR AREAS OF COMPUTER SCIENCE")

areas = [
    "Algorithms and Data Structures",
    "Computer Architecture",
    "Operating Systems",
    "Computer Networks",
    "Databases",
    "Programming Languages",
    "Software Engineering",
    "Cybersecurity",
    "Artificial Intelligence",
    "Machine Learning",
    "Computer Graphics",
    "Distributed Systems",
    "Theory of Computation",
    "Computer Science Mathematics"
]

for area in areas:
    print("-", area)


# ============================================================
# 25. COMPUTER SCIENCE LEARNING FLOW
# ============================================================

print("\n25. COMPUTER SCIENCE LEARNING FLOW")

print("""
Mathematics
     ↓
Computer Fundamentals
     ↓
Programming
     ↓
Data Structures & Algorithms
     ↓
Computer Architecture
     ↓
Operating Systems
     ↓
Networking
     ↓
Databases
     ↓
Software Engineering
     ↓
Advanced Computer Science
""")


# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("DAY 01 COMPLETED")
print("=" * 60)

print("""
Today you learned:

1. Computer Science
2. Computer Systems
3. Hardware
4. Software
5. CPU
6. Memory and Storage
7. Data
8. Binary
9. Number Representation
10. Algorithms
11. Simple Algorithms
12. Programming
13. Variables and Data Types
14. Control Flow
15. Loops
16. Functions
17. Data Structures
18. Operating Systems
19. Networking
20. Databases
21. Cybersecurity
22. Software Engineering
23. Computational Thinking
24. Major Areas of Computer Science
25. Computer Science Learning Flow
""")
