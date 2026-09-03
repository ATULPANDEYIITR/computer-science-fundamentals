"""
====================================================================
COMPUTER SYSTEM OVERVIEW
====================================================================

Topic:
    Input, Processing, Output, Storage, Computer System Components,
    Interaction Between Hardware and Software, and System Information
    Tools.

Purpose:
    This script is a comprehensive educational guide that explains
    computer systems from the most basic concepts to advanced
    system-level concepts and demonstrates how Python can inspect
    various aspects of a computer system.

Learning progression:
    1. What is a computer?
    2. Input -> Processing -> Output -> Storage
    3. Hardware components
    4. Software components
    5. Hardware/software interaction
    6. CPU and processing
    7. Memory
    8. Storage
    9. Operating systems
    10. Drivers
    11. System architecture
    12. System information
    13. Python system information tools
    14. Cross-platform system inspection
    15. Advanced concepts
    16. Practical system monitor
    17. Final knowledge summary

Python version:
    Python 3.x

Most examples use only the Python standard library.
Optional psutil examples are clearly separated.
====================================================================
"""


# ====================================================================
# SECTION 1: WHAT IS A COMPUTER SYSTEM?
# ====================================================================

"""
A computer is an electronic system that:

    1. Accepts INPUT
    2. PROCESSES data
    3. Produces OUTPUT
    4. STORES data and instructions

A simplified model is:

                 +----------------+
                 |     INPUT      |
                 +--------+-------+
                          |
                          v
                 +----------------+
                 |   PROCESSING   |
                 |      CPU       |
                 +--------+-------+
                          |
                          v
                 +----------------+
                 |     OUTPUT     |
                 +--------+-------+
                          |
                          v
                 +----------------+
                 |    STORAGE     |
                 +----------------+

Real computer systems are more complex because:

    - Input devices communicate through controllers and buses.
    - CPUs use registers and cache.
    - RAM temporarily stores active programs/data.
    - Storage provides persistent data.
    - Operating systems manage hardware.
    - Device drivers translate software requests into hardware actions.
    - Applications interact with the operating system through APIs.

Important distinction:

    DATA:
        Raw facts.

    INFORMATION:
        Processed and meaningful data.

Example:

    Input:
        80, 90, 70

    Processing:
        Calculate average.

    Output:
        80

    Storage:
        Save the result to a file/database.
"""


# ====================================================================
# SECTION 2: BASIC INPUT -> PROCESSING -> OUTPUT -> STORAGE
# ====================================================================

def basic_computer_model():
    """Demonstrate the basic IPO + storage model."""

    # ------------------------------
    # INPUT
    # ------------------------------
    name = input("Enter your name: ")

    # ------------------------------
    # PROCESSING
    # ------------------------------
    message = f"Hello, {name}! Your computer processed the input."

    # ------------------------------
    # OUTPUT
    # ------------------------------
    print(message)

    # ------------------------------
    # STORAGE
    # ------------------------------
    with open("computer_output.txt", "w", encoding="utf-8") as file:
        file.write(message)

    print("Result has been stored in computer_output.txt")


# ====================================================================
# SECTION 3: INPUT DEVICES
# ====================================================================

"""
Input devices allow users or other systems to provide data.

Examples:

    Keyboard
    Mouse
    Touchscreen
    Microphone
    Camera
    Scanner
    Barcode reader
    Biometric sensor
    Game controller
    Network interface

Input can also come from:

    - Files
    - Databases
    - APIs
    - Sensors
    - Network packets
    - Other computers

Therefore, "input" is broader than simply pressing a keyboard key.
"""


def demonstrate_input_sources():
    """Show different conceptual sources of input."""

    keyboard_input = "User typed this text."

    file_input = "Data could come from a file."

    api_input = {
        "source": "API",
        "value": 42
    }

    sensor_input = {
        "temperature": 28.5,
        "unit": "C"
    }

    print("Keyboard:", keyboard_input)
    print("File:", file_input)
    print("API:", api_input)
    print("Sensor:", sensor_input)


# ====================================================================
# SECTION 4: PROCESSING
# ====================================================================

"""
Processing is the transformation of input into useful information.

The CPU is the primary general-purpose processing component.

A simplified CPU cycle is:

    FETCH
       |
       v
    DECODE
       |
       v
    EXECUTE
       |
       v
    STORE

This is often called the instruction cycle.

Example:

    x = 10
    y = 20
    z = x + y

Conceptually:

    1. Load instruction.
    2. Decode instruction.
    3. Retrieve operands.
    4. Perform arithmetic.
    5. Store result.
"""


def demonstrate_processing():
    """Simple examples of processing."""

    numbers = [10, 20, 30, 40, 50]

    total = sum(numbers)
    count = len(numbers)
    average = total / count

    print("Input numbers:", numbers)
    print("Total:", total)
    print("Count:", count)
    print("Average:", average)


# ====================================================================
# SECTION 5: OUTPUT
# ====================================================================

"""
Output is information produced by the computer.

Examples:

    Monitor
    Printer
    Speakers
    Headphones
    Projector
    Haptic device
    Network response
    File
    Database record

Output does not necessarily mean something visible to a human.

For example:

    An API returning JSON is output.
    A program writing to a database is output.
    A computer sending a network packet is output.
"""


def demonstrate_output():
    """Demonstrate several types of output."""

    result = {
        "status": "success",
        "message": "Processing completed",
        "value": 100
    }

    # Screen output
    print(result)

    # File output
    with open("output.json", "w", encoding="utf-8") as file:
        import json
        json.dump(result, file, indent=4)

    print("Output written to output.json")


# ====================================================================
# SECTION 6: STORAGE
# ====================================================================

"""
Storage is used to retain data.

There are two major conceptual categories:

    PRIMARY MEMORY
        Usually RAM and CPU cache.
        Fast.
        Mostly temporary/volatile.

    SECONDARY STORAGE
        SSD
        HDD
        USB drives
        Memory cards
        Persistent storage.

Volatile memory:
    Data is generally lost when power is removed.

Non-volatile storage:
    Data remains after power is removed.

Storage hierarchy:

    CPU Registers
        ↓
    CPU Cache
        ↓
    RAM
        ↓
    SSD / HDD
        ↓
    Network / Cloud Storage

Generally:

    Faster memory
        = smaller
        = more expensive per byte

    Slower storage
        = larger
        = cheaper per byte
"""


def demonstrate_storage():
    """Demonstrate writing and reading persistent storage."""

    filename = "storage_demo.txt"

    data = """
Computer systems use storage to preserve information.
This text demonstrates persistent file storage.
"""

    # WRITE
    with open(filename, "w", encoding="utf-8") as file:
        file.write(data)

    # READ
    with open(filename, "r", encoding="utf-8") as file:
        stored_data = file.read()

    print("Stored data:")
    print(stored_data)


# ====================================================================
# SECTION 7: COMPUTER HARDWARE
# ====================================================================

"""
Hardware means the physical components of a computer.

Major components:

    1. CPU
    2. RAM
    3. Motherboard
    4. Storage
    5. GPU
    6. Power supply
    7. Network interface
    8. Input/output controllers
    9. Cooling system
    10. Peripheral devices
"""


# ====================================================================
# SECTION 8: CPU
# ====================================================================

"""
CPU = Central Processing Unit

The CPU executes machine instructions.

Important CPU concepts:

    Core:
        An independent processing unit.

    Thread:
        A sequence of instructions managed by a CPU core/logical processor.

    Clock frequency:
        Measured commonly in GHz.

    Cache:
        Very fast memory close to the CPU.

    Instruction Set Architecture:
        Defines instructions a processor understands.

Examples:

    x86-64
    ARM
    RISC-V

CPU performance depends on many factors, not only GHz.

Important factors include:

    - Architecture
    - Instructions per cycle
    - Number of cores
    - Cache
    - Memory subsystem
    - Branch prediction
    - Compiler optimization
    - Workload characteristics
"""


# ====================================================================
# SECTION 9: RAM
# ====================================================================

"""
RAM = Random Access Memory

RAM stores data and instructions currently being used.

Example:

    You open a Python program.

    Storage:
        Program exists on SSD/HDD.

    RAM:
        Operating system loads program data into memory.

    CPU:
        Executes instructions.

RAM is generally volatile.

Important concepts:

    Memory capacity
    Memory bandwidth
    Memory latency
    Virtual memory
    Paging
    Swap
"""


# ====================================================================
# SECTION 10: GPU
# ====================================================================

"""
GPU = Graphics Processing Unit

Originally designed primarily for graphics workloads.

Modern GPUs are also heavily used for:

    - Machine learning
    - Scientific computing
    - Image processing
    - Video processing
    - Parallel computation

CPU:
    Often optimized for general-purpose, sequential and moderately
    parallel workloads.

GPU:
    Often optimized for highly parallel workloads.

Example:

    Matrix multiplication can contain thousands/millions of
    independent operations, making GPUs useful for certain workloads.
"""


# ====================================================================
# SECTION 11: MOTHERBOARD
# ====================================================================

"""
The motherboard connects major components.

It provides:

    - Electrical connections
    - Communication pathways
    - Expansion slots
    - Memory slots
    - CPU socket
    - Storage interfaces
    - Peripheral interfaces

Communication may occur through buses and interfaces such as:

    PCI Express
    USB
    SATA
    NVMe interfaces
"""


# ====================================================================
# SECTION 12: NETWORK INTERFACE
# ====================================================================

"""
A Network Interface Controller allows a system to communicate over
networks.

Examples:

    Ethernet
    Wi-Fi
    Virtual network adapters

Networking concepts include:

    MAC address
    IP address
    Gateway
    DNS
    TCP/IP
    Network interface
"""


# ====================================================================
# SECTION 13: POWER SUPPLY
# ====================================================================

"""
Desktop systems generally use a PSU.

PSU responsibilities:

    - Convert electrical power
    - Provide appropriate voltages
    - Supply components
    - Provide power protection features

Laptops and mobile systems use batteries and power management
circuits.
"""


# ====================================================================
# SECTION 14: SOFTWARE
# ====================================================================

"""
Software consists of instructions that tell hardware what to do.

Major categories:

    SYSTEM SOFTWARE
        Operating systems
        Device drivers
        Firmware
        System utilities

    APPLICATION SOFTWARE
        Browsers
        Editors
        Games
        Business applications
        Data analysis tools

    DEVELOPMENT SOFTWARE
        Compilers
        Interpreters
        Debuggers
        IDEs
        Build tools
"""


# ====================================================================
# SECTION 15: OPERATING SYSTEM
# ====================================================================

"""
The operating system acts as a major abstraction layer between
applications and hardware.

Examples:

    Windows
    Linux
    macOS
    Android
    iOS

Major operating system responsibilities:

    - Process management
    - Memory management
    - File management
    - Device management
    - Networking
    - Security
    - User management
    - Resource allocation

Conceptually:

    Application
         |
         v
    Libraries / APIs
         |
         v
    Operating System
         |
         v
    Device Drivers
         |
         v
    Hardware
"""


# ====================================================================
# SECTION 16: DEVICE DRIVERS
# ====================================================================

"""
A device driver is software that allows the operating system to
communicate with hardware.

Example:

    Python application
          |
          v
    Operating System
          |
          v
    Printer Driver
          |
          v
    Printer

The application does not normally need to understand every
electrical detail of the printer.

The driver provides the required abstraction.
"""


# ====================================================================
# SECTION 17: FIRMWARE
# ====================================================================

"""
Firmware is software closely associated with hardware.

Examples:

    BIOS
    UEFI
    Device firmware
    Embedded controller firmware

Firmware can initialize hardware and provide low-level functionality.

A simplified startup process:

    Power On
       |
       v
    Firmware
       |
       v
    Hardware Initialization
       |
       v
    Bootloader
       |
       v
    Operating System
       |
       v
    Applications
"""


# ====================================================================
# SECTION 18: HOW HARDWARE AND SOFTWARE INTERACT
# ====================================================================

"""
Consider saving a file.

User:
    Clicks "Save"

Application:
    Requests the operating system to write data.

Operating system:
    Determines where and how data should be written.

File system:
    Manages the logical organization of the file.

Storage driver:
    Converts operating system requests into device-specific
    operations.

Storage controller:
    Communicates with the storage device.

SSD:
    Physically stores the data.

The reverse process occurs when reading.

This demonstrates abstraction.

Applications do not normally directly manipulate electrical signals
on a storage device.
"""


# ====================================================================
# SECTION 19: PROCESS
# ====================================================================

"""
A process is a running instance of a program.

Example:

    Python source code
          |
          v
    Python interpreter
          |
          v
    Running process

A process generally has:

    - Process ID (PID)
    - Memory space
    - Open files
    - Resources
    - Security context
    - Threads

Multiple processes can run simultaneously.
"""


# ====================================================================
# SECTION 20: THREAD
# ====================================================================

"""
A thread is an execution path within a process.

Example:

    Browser process
        |
        +--- Thread 1
        +--- Thread 2
        +--- Thread 3
        +--- Thread 4

Threads within a process typically share process memory.

Concurrency:
    Multiple tasks make progress.

Parallelism:
    Multiple tasks execute simultaneously on different processing
    resources.

These concepts are related but not identical.
"""


# ====================================================================
# SECTION 21: FILE SYSTEM
# ====================================================================

"""
The file system organizes persistent data.

Examples:

    NTFS
    FAT32
    exFAT
    ext4
    APFS

A file system manages concepts such as:

    Files
    Directories
    Permissions
    Metadata
    Allocation
    File names
"""


def inspect_file_system():
    """Inspect current working directory and basic filesystem data."""

    import os

    print("Current directory:")
    print(os.getcwd())

    print("\nDirectory contents:")

    for item in os.listdir("."):
        print(" -", item)


# ====================================================================
# SECTION 22: PYTHON'S PLATFORM MODULE
# ====================================================================

"""
Python provides the platform module for basic system information.

Useful functions:

    platform.system()
    platform.release()
    platform.version()
    platform.machine()
    platform.processor()
    platform.python_version()
    platform.platform()
"""


def platform_information():
    """Display basic operating system and Python information."""

    import platform

    print("\n===== PLATFORM INFORMATION =====")

    print("Operating System:", platform.system())
    print("OS Release:", platform.release())
    print("OS Version:", platform.version())
    print("Architecture:", platform.machine())
    print("Processor:", platform.processor())
    print("Platform:", platform.platform())
    print("Python Version:", platform.python_version())


# ====================================================================
# SECTION 23: CPU INFORMATION
# ====================================================================

def cpu_information():
    """Display basic CPU information."""

    import os
    import platform

    print("\n===== CPU INFORMATION =====")

    print("Processor:", platform.processor())
    print("Logical CPU count:", os.cpu_count())

    try:
        print("Physical CPU information may require platform-specific tools.")
    except Exception as error:
        print("Error:", error)


# ====================================================================
# SECTION 24: MEMORY INFORMATION
# ====================================================================

"""
The standard library provides limited portable RAM information.

For detailed memory statistics, psutil is highly useful.

Installation:

    pip install psutil

This script attempts to use psutil if available.
"""


def memory_information():
    """Display memory information when psutil is available."""

    try:
        import psutil

        memory = psutil.virtual_memory()

        print("\n===== MEMORY INFORMATION =====")

        print("Total RAM:", memory.total, "bytes")
        print("Available RAM:", memory.available, "bytes")
        print("Used RAM:", memory.used, "bytes")
        print("Free RAM:", memory.free, "bytes")
        print("RAM Usage:", memory.percent, "%")

    except ImportError:
        print("\npsutil is not installed.")
        print("Install it using:")
        print("pip install psutil")


# ====================================================================
# SECTION 25: DISK INFORMATION
# ====================================================================

def disk_information():
    """Display disk usage information."""

    import shutil

    print("\n===== DISK INFORMATION =====")

    total, used, free = shutil.disk_usage("/")

    print("Total:", total, "bytes")
    print("Used:", used, "bytes")
    print("Free:", free, "bytes")

    print("\nApproximate values in GB:")

    print("Total:",
          round(total / (1024 ** 3), 2),
          "GB")

    print("Used:",
          round(used / (1024 ** 3), 2),
          "GB")

    print("Free:",
          round(free / (1024 ** 3), 2),
          "GB")


# ====================================================================
# SECTION 26: DETAILED DISK INFORMATION USING PSUTIL
# ====================================================================

def detailed_disk_information():
    """Display disk partitions and usage."""

    try:
        import psutil

        print("\n===== DISK PARTITIONS =====")

        partitions = psutil.disk_partitions()

        for partition in partitions:
            print("\nDevice:", partition.device)
            print("Mount point:", partition.mountpoint)
            print("File system:", partition.fstype)

            try:
                usage = psutil.disk_usage(partition.mountpoint)

                print("Total:",
                      round(usage.total / (1024 ** 3), 2),
                      "GB")

                print("Used:",
                      round(usage.used / (1024 ** 3), 2),
                      "GB")

                print("Free:",
                      round(usage.free / (1024 ** 3), 2),
                      "GB")

                print("Usage:", usage.percent, "%")

            except PermissionError:
                print("Permission denied.")

    except ImportError:
        print("Install psutil:")
        print("pip install psutil")


# ====================================================================
# SECTION 27: NETWORK INFORMATION
# ====================================================================

def network_information():
    """Display network interfaces using psutil."""

    try:
        import psutil

        print("\n===== NETWORK INTERFACES =====")

        interfaces = psutil.net_if_addrs()

        for interface, addresses in interfaces.items():

            print("\nInterface:", interface)

            for address in addresses:

                print("  Family:", address.family)
                print("  Address:", address.address)

                if address.netmask:
                    print("  Netmask:", address.netmask)

                if address.broadcast:
                    print("  Broadcast:", address.broadcast)

    except ImportError:
        print("Install psutil:")
        print("pip install psutil")


# ====================================================================
# SECTION 28: NETWORK STATISTICS
# ====================================================================

def network_statistics():
    """Display network traffic statistics."""

    try:
        import psutil

        stats = psutil.net_io_counters()

        print("\n===== NETWORK STATISTICS =====")

        print("Bytes sent:", stats.bytes_sent)
        print("Bytes received:", stats.bytes_recv)
        print("Packets sent:", stats.packets_sent)
        print("Packets received:", stats.packets_recv)

    except ImportError:
        print("Install psutil:")
        print("pip install psutil")


# ====================================================================
# SECTION 29: BATTERY INFORMATION
# ====================================================================

def battery_information():
    """Display battery information when supported."""

    try:
        import psutil

        battery = psutil.sensors_battery()

        print("\n===== BATTERY INFORMATION =====")

        if battery is None:
            print("Battery information is not available.")
            return

        print("Battery percentage:", battery.percent)

        print("Power plugged in:", battery.power_plugged)

        if battery.secsleft >= 0:
            print("Seconds remaining:", battery.secsleft)

    except ImportError:
        print("Install psutil:")
        print("pip install psutil")


# ====================================================================
# SECTION 30: SYSTEM UPTIME
# ====================================================================

def system_uptime():
    """Calculate approximate system uptime."""

    import time

    try:
        import psutil

        boot_time = psutil.boot_time()
        current_time = time.time()

        uptime_seconds = current_time - boot_time

        days = int(uptime_seconds // 86400)

        hours = int((uptime_seconds % 86400) // 3600)

        minutes = int((uptime_seconds % 3600) // 60)

        seconds = int(uptime_seconds % 60)

        print("\n===== SYSTEM UPTIME =====")

        print(
            f"{days} days, "
            f"{hours} hours, "
            f"{minutes} minutes, "
            f"{seconds} seconds"
        )

    except ImportError:
        print("Install psutil:")
        print("pip install psutil")


# ====================================================================
# SECTION 31: RUNNING PROCESSES
# ====================================================================

def running_processes(limit=10):
    """Display information about running processes."""

    try:
        import psutil

        print("\n===== RUNNING PROCESSES =====")

        processes = []

        for process in psutil.process_iter(
            ["pid", "name", "username", "status"]
        ):

            try:
                processes.append(process.info)

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        processes = processes[:limit]

        for process in processes:

            print(
                f"PID={process['pid']} | "
                f"Name={process['name']} | "
                f"Status={process['status']}"
            )

    except ImportError:
        print("Install psutil:")
        print("pip install psutil")


# ====================================================================
# SECTION 32: CPU USAGE
# ====================================================================

def cpu_usage():
    """Measure CPU usage."""

    try:
        import psutil

        print("\n===== CPU USAGE =====")

        print("CPU usage:", psutil.cpu_percent(interval=1), "%")

        print(
            "Per CPU usage:",
            psutil.cpu_percent(interval=1, percpu=True)
        )

    except ImportError:
        print("Install psutil:")
        print("pip install psutil")


# ====================================================================
# SECTION 33: LOAD AVERAGE
# ====================================================================

def load_average():
    """Display Unix-style load averages when supported."""

    import os

    print("\n===== LOAD AVERAGE =====")

    try:
        one, five, fifteen = os.getloadavg()

        print("1 minute:", one)
        print("5 minutes:", five)
        print("15 minutes:", fifteen)

    except (AttributeError, OSError):
        print("Load average is not available on this platform.")


"""
Load average is not exactly the same as CPU percentage.

On Unix-like systems, load average generally reflects the number of
tasks that are runnable or waiting in relevant system states.

A high load value does not automatically mean that CPU utilization
is 100%.
"""


# ====================================================================
# SECTION 34: ENVIRONMENT VARIABLES
# ====================================================================

def environment_information():
    """Display selected environment information."""

    import os

    print("\n===== ENVIRONMENT INFORMATION =====")

    print("Operating system:", os.name)

    print("Current user:",
          os.environ.get("USERNAME")
          or os.environ.get("USER"))

    print("Home directory:",
          os.environ.get("USERPROFILE")
          or os.environ.get("HOME"))

    print("PATH:")
    print(os.environ.get("PATH", ""))


# ====================================================================
# SECTION 35: PYTHON RUNTIME INFORMATION
# ====================================================================

def python_runtime_information():
    """Display Python runtime information."""

    import sys
    import platform

    print("\n===== PYTHON RUNTIME =====")

    print("Python version:", sys.version)
    print("Python implementation:", platform.python_implementation())
    print("Python executable:", sys.executable)
    print("Byte order:", sys.byteorder)
    print("Python architecture:", platform.architecture())


# ====================================================================
# SECTION 36: HOSTNAME
# ====================================================================

def hostname_information():
    """Display the system hostname."""

    import socket

    print("\n===== HOSTNAME =====")

    print("Hostname:", socket.gethostname())


# ====================================================================
# SECTION 37: CURRENT WORKING DIRECTORY
# ====================================================================

def current_directory_information():
    """Display current working directory."""

    import os

    print("\n===== CURRENT DIRECTORY =====")

    print(os.getcwd())


# ====================================================================
# SECTION 38: SYSTEM INFORMATION SUMMARY
# ====================================================================

def system_summary():
    """Produce a compact system summary."""

    import os
    import platform
    import socket
    import shutil

    print("\n")
    print("=" * 60)
    print("SYSTEM INFORMATION SUMMARY")
    print("=" * 60)

    print("Hostname:", socket.gethostname())

    print("Operating System:", platform.system())

    print("OS Release:", platform.release())

    print("Architecture:", platform.machine())

    print("Processor:", platform.processor())

    print("Logical CPUs:", os.cpu_count())

    print("Python:", platform.python_version())

    total, used, free = shutil.disk_usage("/")

    print("Root disk total:",
          round(total / (1024 ** 3), 2),
          "GB")

    print("Root disk used:",
          round(used / (1024 ** 3), 2),
          "GB")

    print("Root disk free:",
          round(free / (1024 ** 3), 2),
          "GB")


# ====================================================================
# SECTION 39: ADVANCED SYSTEM INFORMATION WITH PSUTIL
# ====================================================================

def advanced_system_information():
    """Collect a broad set of system statistics."""

    try:
        import psutil

        print("\n")
        print("=" * 60)
        print("ADVANCED SYSTEM INFORMATION")
        print("=" * 60)

        # CPU
        print("\nCPU")
        print("-" * 60)

        print(
            "Physical cores:",
            psutil.cpu_count(logical=False)
        )

        print(
            "Logical processors:",
            psutil.cpu_count(logical=True)
        )

        print(
            "CPU frequency:",
            psutil.cpu_freq()
        )

        print(
            "CPU usage:",
            psutil.cpu_percent(interval=1),
            "%"
        )

        # Memory
        print("\nMEMORY")
        print("-" * 60)

        virtual_memory = psutil.virtual_memory()

        print("Total:", virtual_memory.total)
        print("Available:", virtual_memory.available)
        print("Used:", virtual_memory.used)
        print("Percentage:", virtual_memory.percent)

        # Swap
        swap = psutil.swap_memory()

        print("\nSWAP")
        print("-" * 60)

        print("Total:", swap.total)
        print("Used:", swap.used)
        print("Free:", swap.free)
        print("Percentage:", swap.percent)

        # Disk
        print("\nDISK")
        print("-" * 60)

        for partition in psutil.disk_partitions():

            try:
                usage = psutil.disk_usage(partition.mountpoint)

                print(
                    partition.mountpoint,
                    "=>",
                    usage.percent,
                    "%"
                )

            except PermissionError:
                pass

        # Network
        print("\nNETWORK")
        print("-" * 60)

        network = psutil.net_io_counters()

        print("Bytes sent:", network.bytes_sent)
        print("Bytes received:", network.bytes_recv)

    except ImportError:

        print(
            "Advanced information requires psutil.\n"
            "Install using: pip install psutil"
        )


# ====================================================================
# SECTION 40: CPU COUNT AND PARALLELISM
# ====================================================================

def cpu_parallelism_example():
    """
    Demonstrate how Python can discover available logical processors.
    """

    import os

    processors = os.cpu_count()

    print("\n===== CPU PARALLELISM =====")

    print("Available logical processors:", processors)

    if processors:
        print(
            "A program may use multiple workers depending on "
            "the workload and architecture."
        )


# ====================================================================
# SECTION 41: MEASURING EXECUTION TIME
# ====================================================================

def performance_measurement():
    """Demonstrate basic performance measurement."""

    import time

    print("\n===== PERFORMANCE MEASUREMENT =====")

    start = time.perf_counter()

    total = 0

    for number in range(1_000_000):
        total += number

    end = time.perf_counter()

    elapsed = end - start

    print("Result:", total)
    print("Execution time:", elapsed, "seconds")


# ====================================================================
# SECTION 42: MEMORY SIZE FORMATTING
# ====================================================================

def format_bytes(number):
    """
    Convert bytes into human-readable units.

    Example:

        1024 -> 1.00 KiB
        1048576 -> 1.00 MiB
    """

    units = [
        "B",
        "KiB",
        "MiB",
        "GiB",
        "TiB",
        "PiB"
    ]

    size = float(number)

    for unit in units:

        if size < 1024 or unit == units[-1]:

            return f"{size:.2f} {unit}"

        size /= 1024

    return f"{size:.2f} PiB"


def demonstrate_byte_formatting():
    """Demonstrate byte formatting."""

    print("\n===== BYTE FORMATTING =====")

    values = [
        100,
        1024,
        1024 ** 2,
        1024 ** 3,
        1024 ** 4
    ]

    for value in values:

        print(
            value,
            "bytes =",
            format_bytes(value)
        )


# ====================================================================
# SECTION 43: SYSTEM RESOURCE MONITOR
# ====================================================================

def simple_resource_monitor(iterations=5, interval=1):
    """
    A small CPU and memory monitoring utility.

    Requires:
        pip install psutil
    """

    try:
        import psutil
        import time

        print("\n===== RESOURCE MONITOR =====")

        for count in range(iterations):

            cpu = psutil.cpu_percent(interval=interval)

            memory = psutil.virtual_memory()

            print(
                f"Sample {count + 1}: "
                f"CPU={cpu}% | "
                f"RAM={memory.percent}%"
            )

    except ImportError:

        print("Install psutil first:")
        print("pip install psutil")


# ====================================================================
# SECTION 44: PROCESS-SPECIFIC RESOURCE INFORMATION
# ====================================================================

def current_process_information():
    """Display resource information for the current Python process."""

    try:
        import psutil
        import os

        process = psutil.Process(os.getpid())

        print("\n===== CURRENT PROCESS =====")

        print("PID:", process.pid)

        print("Name:", process.name())

        print("Status:", process.status())

        print(
            "CPU percentage:",
            process.cpu_percent(interval=0.1)
        )

        memory = process.memory_info()

        print(
            "Resident memory:",
            format_bytes(memory.rss)
        )

        print(
            "Virtual memory:",
            format_bytes(memory.vms)
        )

        print(
            "Threads:",
            process.num_threads()
        )

    except ImportError:

        print("Install psutil:")
        print("pip install psutil")


# ====================================================================
# SECTION 45: HARDWARE/SOFTWARE ABSTRACTION
# ====================================================================

"""
One of the most important concepts in computer science is abstraction.

Example:

    Python:
        open("data.txt", "r")

Python code does not directly specify:

    - electrical voltage
    - storage cell
    - disk sector
    - flash transistor
    - controller command

Instead:

    Python
       |
       v
    Python runtime
       |
       v
    Operating system
       |
       v
    File system
       |
       v
    Storage driver
       |
       v
    Storage controller
       |
       v
    SSD
       |
       v
    Physical storage

Each layer hides implementation details from the layer above it.

This is abstraction.
"""


# ====================================================================
# SECTION 46: SYSTEM CALL CONCEPT
# ====================================================================

"""
A system call is a controlled mechanism through which a user-space
program requests services from the operating system kernel.

Examples include operations related to:

    - Files
    - Processes
    - Memory
    - Networking
    - Devices

Conceptually:

    User Application
           |
           v
    Library / Runtime
           |
           v
    System Call
           |
           v
    Kernel
           |
           v
    Hardware / Drivers

Python's open(), socket APIs, subprocess APIs, and many other
operations eventually interact with operating-system facilities.
"""


# ====================================================================
# SECTION 47: USER SPACE VS KERNEL SPACE
# ====================================================================

"""
Modern operating systems commonly separate execution privileges.

USER SPACE:
    Where normal applications execute.

KERNEL SPACE:
    Where the operating system kernel executes with higher privileges.

Why?

    Security
    Stability
    Isolation

A faulty application should ideally not be able to directly overwrite
arbitrary kernel memory.

The operating system provides controlled interfaces between the two.
"""


# ====================================================================
# SECTION 48: MEMORY VIRTUALIZATION
# ====================================================================

"""
Applications typically operate within virtual address spaces.

A simplified conceptual model:

    Application virtual address
                |
                v
        Memory Management Unit
                |
                v
        Physical memory page
                |
                v
               RAM

Virtual memory provides:

    - Process isolation
    - Memory abstraction
    - Efficient allocation
    - Support for paging
    - Larger logical address spaces

Modern systems use mechanisms such as:

    Page tables
    Virtual addresses
    Physical addresses
    Translation Lookaside Buffers (TLB)
    Memory Management Units (MMU)
"""


# ====================================================================
# SECTION 49: CACHE HIERARCHY
# ====================================================================

"""
Modern CPUs commonly contain multiple cache levels.

Typical hierarchy:

    Registers
        ↓
    L1 Cache
        ↓
    L2 Cache
        ↓
    L3 Cache
        ↓
    RAM
        ↓
    SSD/HDD

Closer to CPU:
    Faster
    Smaller

Farther from CPU:
    Slower
    Larger

Cache improves performance by exploiting locality.

Temporal locality:
    Recently accessed data may be accessed again.

Spatial locality:
    Nearby memory locations may be accessed soon.
"""


# ====================================================================
# SECTION 50: BUSES AND INTERCONNECTS
# ====================================================================

"""
Computer components communicate through interconnects.

Examples:

    PCI Express
    USB
    SATA
    Memory buses
    Network interfaces

A bus/interconnect provides pathways for:

    Data
    Addressing
    Control/signaling

Modern architectures are more complex than a single shared bus,
but the fundamental communication concept remains important.
"""


# ====================================================================
# SECTION 51: INTERRUPTS
# ====================================================================

"""
An interrupt allows hardware or software to signal that attention is
required.

Example:

    Keyboard event
        |
        v
    Hardware interrupt
        |
        v
    Operating system
        |
        v
    Keyboard driver
        |
        v
    Application receives event

Interrupts allow systems to respond to events without continuously
polling every device.
"""


# ====================================================================
# SECTION 52: DMA
# ====================================================================

"""
DMA = Direct Memory Access

DMA allows certain hardware devices to transfer data to/from memory
with reduced CPU involvement.

Example:

    Network device
          |
          v
        DMA
          |
          v
        RAM

The CPU configures the transfer and handles completion/events rather
than manually copying every byte.
"""


# ====================================================================
# SECTION 53: STORAGE PERFORMANCE
# ====================================================================

"""
Important storage metrics include:

    Capacity
    Sequential read speed
    Sequential write speed
    Random read/write performance
    IOPS
    Latency
    Queue depth
    Endurance

HDD:
    Mechanical storage.
    Rotating platters.
    Mechanical seek.

SSD:
    Solid-state storage.
    No rotating platter.
    Typically much lower access latency.

NVMe:
    A protocol/interface commonly used for high-performance SSDs,
    typically communicating over PCI Express.
"""


# ====================================================================
# SECTION 54: BOOT PROCESS
# ====================================================================

"""
A simplified modern boot process:

    1. Power is applied.
    2. Firmware starts.
    3. Hardware is initialized.
    4. Boot device is identified.
    5. Bootloader starts.
    6. Operating system kernel loads.
    7. Kernel initializes drivers/subsystems.
    8. User-space services start.
    9. Login/session starts.
    10. Applications run.

This sequence can vary by architecture and operating system.
"""


# ====================================================================
# SECTION 55: SYSTEM INFORMATION TOOLS
# ====================================================================

"""
System information tools help administrators, developers and users
understand the machine on which software runs.

Common categories:

    OS information
    CPU information
    Memory information
    Disk information
    Network information
    Process information
    Hardware information
    Temperature information
    Battery information
    Uptime
    Environment variables
    Python runtime information

Python tools:

    platform
    os
    sys
    shutil
    socket
    subprocess
    pathlib
    psutil (third-party)
"""


# ====================================================================
# SECTION 56: SUBPROCESS AND NATIVE SYSTEM COMMANDS
# ====================================================================

"""
Python can execute operating-system commands using subprocess.

This is powerful but platform-dependent.

Examples:

Windows:
    systeminfo
    tasklist
    ipconfig

Linux:
    uname
    lscpu
    free
    df
    ip
    ps

macOS:
    uname
    system_profiler
    df
    ps

Never blindly execute untrusted strings as shell commands.
"""


def run_system_command(command):
    """Run a command safely without shell parsing."""

    import subprocess

    try:

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False
        )

        print("Return code:", result.returncode)

        print("\nSTDOUT:")
        print(result.stdout)

        if result.stderr:

            print("\nSTDERR:")
            print(result.stderr)

    except FileNotFoundError:

        print("Command not found:", command[0])

    except Exception as error:

        print("Error:", error)


# Example:
#
# run_system_command(["python", "--version"])
#
# On Windows:
# run_system_command(["systeminfo"])
#
# On Linux/macOS:
# run_system_command(["uname", "-a"])


# ====================================================================
# SECTION 57: WHY CROSS-PLATFORM SYSTEM INFORMATION IS HARD
# ====================================================================

"""
A major engineering challenge is that operating systems expose
different system interfaces.

For example:

    Windows:
        systeminfo
        wmic (legacy/deprecated on many systems)
        PowerShell
        WMI/CIM

    Linux:
        /proc
        /sys
        lscpu
        free
        df

    macOS:
        system_profiler
        sysctl

Therefore, portable Python applications should prefer:

    platform
    os
    shutil

and use:

    psutil

when detailed cross-platform information is required.
"""


# ====================================================================
# SECTION 58: SECURITY CONSIDERATIONS
# ====================================================================

"""
System information can be useful for legitimate administration,
diagnostics and performance analysis.

It can also reveal sensitive information.

Examples:

    Hostname
    Username
    Network addresses
    Running processes
    Installed software
    Hardware configuration

Good practice:

    - Collect only what is necessary.
    - Protect logs.
    - Avoid exposing sensitive information.
    - Do not publish machine-specific information unnecessarily.
    - Apply least privilege.
"""


# ====================================================================
# SECTION 59: DIAGNOSTIC WORKFLOW
# ====================================================================

"""
When diagnosing a slow computer, use a structured approach.

Step 1:
    Check CPU utilization.

Step 2:
    Check RAM usage.

Step 3:
    Check disk utilization.

Step 4:
    Check disk space.

Step 5:
    Check network activity.

Step 6:
    Check running processes.

Step 7:
    Check temperature if supported.

Step 8:
    Check application-specific metrics.

Step 9:
    Identify bottleneck.

Step 10:
    Change one variable at a time and measure again.

Important:

    High CPU usage does not automatically mean CPU is the root cause.

    High RAM usage does not automatically mean more RAM is required.

    High disk utilization may result from paging, indexing, updates,
    backups, logging, or an application workload.
"""


# ====================================================================
# SECTION 60: BOTTLENECK CONCEPT
# ====================================================================

"""
A bottleneck is the component or resource limiting overall
performance.

Possible bottlenecks:

    CPU
    RAM
    Storage
    Network
    GPU
    Database
    Application logic
    External API
    Synchronization/locking

Example:

    Fast CPU
       +
    Fast SSD
       +
    Slow network
       =
    Network-bound application

The fastest component does not necessarily determine application
performance.

The limiting component often does.
"""


# ====================================================================
# SECTION 61: SYSTEM OBSERVABILITY
# ====================================================================

"""
Observability means understanding internal system behavior through
available outputs/signals.

Important telemetry categories:

    Metrics
    Logs
    Traces

System metrics include:

    CPU utilization
    Memory utilization
    Disk I/O
    Network I/O
    Process counts
    Latency
    Error rates

For production systems, observability is a major engineering
discipline.
"""


# ====================================================================
# SECTION 62: CAPACITY VS UTILIZATION
# ====================================================================

"""
Capacity:
    How much resource exists.

Utilization:
    How much of the resource is currently being used.

Example:

    Computer has:
        16 GB RAM

    Current usage:
        8 GB

    Approximate utilization:
        50%

Capacity and utilization answer different questions.
"""


# ====================================================================
# SECTION 63: THROUGHPUT VS LATENCY
# ====================================================================

"""
Latency:
    Time required for one operation/request.

Throughput:
    Amount of work completed per unit time.

Example:

    API request latency:
        100 ms

    Throughput:
        1,000 requests/second

A system can have high throughput but relatively high latency, or
low latency but limited throughput.

Both metrics matter in system engineering.
"""


# ====================================================================
# SECTION 64: SYNCHRONOUS VS ASYNCHRONOUS OPERATIONS
# ====================================================================

"""
Synchronous:
    A task waits for an operation to complete.

Asynchronous:
    A task can continue while waiting for an operation.

Example:

    Reading a slow network resource can be I/O-bound.

Python provides mechanisms such as:

    threading
    multiprocessing
    asyncio

Choice depends on workload characteristics.
"""


# ====================================================================
# SECTION 65: CPU-BOUND VS I/O-BOUND
# ====================================================================

"""
CPU-bound:
    Performance is primarily limited by computation.

Examples:

    Large mathematical computation
    Image processing
    Certain ML workloads

I/O-bound:
    Performance is primarily limited by waiting for input/output.

Examples:

    Network requests
    File operations
    Database queries

This distinction helps determine the appropriate concurrency strategy.
"""


# ====================================================================
# SECTION 66: COMPLETE SYSTEM DIAGNOSTIC REPORT
# ====================================================================

def generate_system_report():
    """
    Generate a text-based system report.

    This function uses standard-library information and optional
    psutil information.
    """

    import platform
    import socket
    import os
    import shutil
    from datetime import datetime

    report = []

    report.append("=" * 70)
    report.append("COMPUTER SYSTEM DIAGNOSTIC REPORT")
    report.append("=" * 70)

    report.append(
        f"Generated: {datetime.now().isoformat()}"
    )

    report.append(
        f"Hostname: {socket.gethostname()}"
    )

    report.append(
        f"Operating System: {platform.system()}"
    )

    report.append(
        f"OS Release: {platform.release()}"
    )

    report.append(
        f"Architecture: {platform.machine()}"
    )

    report.append(
        f"Processor: {platform.processor()}"
    )

    report.append(
        f"Logical CPUs: {os.cpu_count()}"
    )

    report.append(
        f"Python Version: {platform.python_version()}"
    )

    total, used, free = shutil.disk_usage("/")

    report.append(
        f"Disk Total: {format_bytes(total)}"
    )

    report.append(
        f"Disk Used: {format_bytes(used)}"
    )

    report.append(
        f"Disk Free: {format_bytes(free)}"
    )

    try:

        import psutil

        memory = psutil.virtual_memory()

        report.append(
            f"RAM Total: {format_bytes(memory.total)}"
        )

        report.append(
            f"RAM Available: {format_bytes(memory.available)}"
        )

        report.append(
            f"RAM Usage: {memory.percent}%"
        )

        report.append(
            f"CPU Usage: {psutil.cpu_percent(interval=1)}%"
        )

    except ImportError:

        report.append(
            "psutil: Not installed"
        )

    return "\n".join(report)


# ====================================================================
# SECTION 67: SAVE DIAGNOSTIC REPORT
# ====================================================================

def save_system_report(filename="system_report.txt"):
    """Save the generated system report."""

    report = generate_system_report()

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(report)

    print(
        f"\nSystem report saved to: {filename}"
    )


# ====================================================================
# SECTION 68: SYSTEM INFORMATION JSON
# ====================================================================

def system_information_dictionary():
    """Return system information as a Python dictionary."""

    import platform
    import os
    import socket

    information = {

        "hostname": socket.gethostname(),

        "operating_system": platform.system(),

        "os_release": platform.release(),

        "os_version": platform.version(),

        "architecture": platform.machine(),

        "processor": platform.processor(),

        "logical_cpus": os.cpu_count(),

        "python_version": platform.python_version(),

        "python_implementation":
            platform.python_implementation()

    }

    return information


def save_system_information_json(
    filename="system_information.json"
):
    """Save system information as JSON."""

    import json

    information = system_information_dictionary()

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            information,
            file,
            indent=4
        )

    print(
        f"System information saved to: {filename}"
    )


# ====================================================================
# SECTION 69: PRACTICAL MENU
# ====================================================================

def system_information_menu():
    """
    Interactive menu for exploring the system.

    This menu demonstrates how system information utilities can be
    organized into a small command-line application.
    """

    while True:

        print("\n")
        print("=" * 60)
        print("SYSTEM INFORMATION TOOL")
        print("=" * 60)

        print("1. Platform information")
        print("2. CPU information")
        print("3. Memory information")
        print("4. Disk information")
        print("5. Detailed disk information")
        print("6. Network information")
        print("7. Network statistics")
        print("8. Battery information")
        print("9. System uptime")
        print("10. Running processes")
        print("11. CPU usage")
        print("12. Environment information")
        print("13. Python runtime information")
        print("14. Hostname")
        print("15. System summary")
        print("16. Advanced system information")
        print("17. Current process information")
        print("18. Generate system report")
        print("19. Save system information as JSON")
        print("0. Exit")

        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            platform_information()

        elif choice == "2":
            cpu_information()

        elif choice == "3":
            memory_information()

        elif choice == "4":
            disk_information()

        elif choice == "5":
            detailed_disk_information()

        elif choice == "6":
            network_information()

        elif choice == "7":
            network_statistics()

        elif choice == "8":
            battery_information()

        elif choice == "9":
            system_uptime()

        elif choice == "10":
            running_processes()

        elif choice == "11":
            cpu_usage()

        elif choice == "12":
            environment_information()

        elif choice == "13":
            python_runtime_information()

        elif choice == "14":
            hostname_information()

        elif choice == "15":
            system_summary()

        elif choice == "16":
            advanced_system_information()

        elif choice == "17":
            current_process_information()

        elif choice == "18":

            print(
                "\n",
                generate_system_report()
            )

        elif choice == "19":
            save_system_information_json()

        elif choice == "0":

            print("Exiting system information tool.")

            break

        else:

            print("Invalid choice. Try again.")


# ====================================================================
# SECTION 70: CONCEPTUAL COMPUTER SYSTEM ARCHITECTURE
# ====================================================================

"""
A useful mental model:

+--------------------------------------------------------------+
|                        APPLICATIONS                          |
|  Browser | Editor | Python | Database | Games | AI Software |
+--------------------------------------------------------------+
                            |
                            v
+--------------------------------------------------------------+
|                    APPLICATION LIBRARIES                    |
|       APIs | Runtime Libraries | Frameworks | SDKs           |
+--------------------------------------------------------------+
                            |
                            v
+--------------------------------------------------------------+
|                    OPERATING SYSTEM                         |
| Process | Memory | File System | Network | Security | I/O    |
+--------------------------------------------------------------+
                            |
                            v
+--------------------------------------------------------------+
|                    DEVICE DRIVERS                            |
| CPU | GPU | Storage | Network | USB | Audio | Input Devices |
+--------------------------------------------------------------+
                            |
                            v
+--------------------------------------------------------------+
|                       HARDWARE                              |
| CPU | RAM | SSD | GPU | Motherboard | NIC | Peripherals     |
+--------------------------------------------------------------+

This layered model is extremely important for software engineers.
"""


# ====================================================================
# SECTION 71: EXAMPLE END-TO-END DATA FLOW
# ====================================================================

"""
Suppose you type:

    25

into a Python program.

INPUT:
    Keyboard produces electrical signals/events.

OPERATING SYSTEM:
    Receives the input through hardware and drivers.

APPLICATION:
    Python program receives the input.

PROCESSING:
    Python converts the string "25" into an integer.

CPU:
    Executes instructions.

RAM:
    Holds active program state and data.

OUTPUT:
    Program prints the result.

STORAGE:
    Program may save the result to a file.

This demonstrates the complete relationship:

    Human
      ↓
    Input device
      ↓
    Driver
      ↓
    Operating system
      ↓
    Application
      ↓
    CPU + RAM
      ↓
    Output / Storage
"""


# ====================================================================
# SECTION 72: KEY DISTINCTIONS
# ====================================================================

"""
HARDWARE vs SOFTWARE

Hardware:
    Physical components.

Software:
    Instructions and programs.

RAM vs STORAGE

RAM:
    Fast, temporary working memory.

Storage:
    Persistent data storage.

CPU vs GPU

CPU:
    General-purpose processing.

GPU:
    Highly parallel processing for suitable workloads.

PROCESS vs PROGRAM

Program:
    A set of instructions.

Process:
    A running instance of a program.

INPUT vs OUTPUT

Input:
    Data entering a system.

Output:
    Data/results leaving a system.

CAPACITY vs UTILIZATION

Capacity:
    Total available resource.

Utilization:
    Portion currently being used.

LATENCY vs THROUGHPUT

Latency:
    Time per operation.

Throughput:
    Work completed per unit time.
"""


# ====================================================================
# SECTION 73: MINI PROJECT
# ====================================================================

def computer_system_monitor_project():
    """
    Mini-project:

    Build a simple system monitoring utility.

    Features:

        - OS information
        - CPU information
        - RAM information
        - Disk information
        - Network information
        - Process information

    Requires:
        pip install psutil
    """

    print("\n")
    print("=" * 70)
    print("COMPUTER SYSTEM MONITOR")
    print("=" * 70)

    platform_information()

    cpu_information()

    memory_information()

    disk_information()

    network_statistics()

    current_process_information()

    system_uptime()


# ====================================================================
# SECTION 74: BEST PRACTICES
# ====================================================================

"""
Best practices when building system information tools:

    1. Prefer standard-library APIs when sufficient.

    2. Use psutil for detailed cross-platform resource monitoring.

    3. Handle missing permissions.

    4. Handle unsupported hardware.

    5. Handle operating-system differences.

    6. Avoid assuming a specific drive path.

    7. Avoid assuming a specific shell.

    8. Validate external input.

    9. Avoid unsafe shell execution.

    10. Do not collect unnecessary sensitive system information.

    11. Use structured output such as JSON for automation.

    12. Separate data collection from presentation.

    13. Add logging for production applications.

    14. Handle exceptions gracefully.

    15. Measure performance rather than guessing.
"""


# ====================================================================
# SECTION 75: FINAL KNOWLEDGE MODEL
# ====================================================================

"""
The complete computer-system mental model can be summarized as:

                        COMPUTER SYSTEM
                              |
            +-----------------+-----------------+
            |                                   |
         HARDWARE                           SOFTWARE
            |                                   |
    +-------+--------+              +-----------+-----------+
    |       |        |              |           |           |
   CPU     RAM    STORAGE           OS      APPLICATIONS  DRIVERS
    |       |        |              |
    +-------+--------+--------------+
                    |
                    v
             DATA PROCESSING
                    |
        +-----------+-----------+
        |           |           |
      INPUT     PROCESSING    OUTPUT
        |           |           |
        +-----------+-----------+
                    |
                    v
                 STORAGE

The system works because hardware and software cooperate through
layers of abstraction.

At the lowest level:
    Electrical and physical operations.

At the hardware level:
    CPU, memory, storage, buses and devices.

At the operating-system level:
    Processes, memory, files, networking and drivers.

At the application level:
    User-facing programs and services.

At the developer level:
    APIs, libraries, frameworks and programming languages.

At the system-administration level:
    Monitoring, diagnostics, performance and security.
"""


# ====================================================================
# SECTION 76: MAIN EXECUTION
# ====================================================================

def main():
    """
    Main educational demonstration.

    Uncomment individual functions to explore specific topics.
    """

    print("=" * 70)
    print("COMPUTER SYSTEM OVERVIEW")
    print("=" * 70)

    print("\nThis script explains:")
    print("Input")
    print("Processing")
    print("Output")
    print("Storage")
    print("Hardware")
    print("Software")
    print("Operating Systems")
    print("Hardware/Software Interaction")
    print("System Information Tools")

    print("\nBasic platform information:")

    platform_information()

    print("\nCPU information:")

    cpu_information()

    print("\nDisk information:")

    disk_information()

    print("\nSystem summary:")

    system_summary()

    print("\nFor advanced monitoring, install:")
    print("pip install psutil")

    print("\nAvailable educational functions include:")
    print("basic_computer_model()")
    print("demonstrate_input_sources()")
    print("demonstrate_processing()")
    print("demonstrate_output()")
    print("demonstrate_storage()")
    print("platform_information()")
    print("cpu_information()")
    print("memory_information()")
    print("disk_information()")
    print("detailed_disk_information()")
    print("network_information()")
    print("network_statistics()")
    print("battery_information()")
    print("system_uptime()")
    print("running_processes()")
    print("cpu_usage()")
    print("environment_information()")
    print("python_runtime_information()")
    print("advanced_system_information()")
    print("current_process_information()")
    print("generate_system_report()")
    print("save_system_report()")
    print("save_system_information_json()")
    print("computer_system_monitor_project()")


# ====================================================================
# PROGRAM ENTRY POINT
# ====================================================================

if __name__ == "__main__":
    main()


"""
====================================================================
FINAL TAKEAWAY
====================================================================

A computer system is not simply a CPU.

It is an integrated system consisting of:

    Hardware
    Software
    Operating system
    Firmware
    Drivers
    Memory
    Storage
    Input/output devices
    Networking
    Applications

The fundamental information flow is:

    INPUT
       ↓
    PROCESSING
       ↓
    OUTPUT
       ↓
    STORAGE

But a modern system actually operates through many abstraction
layers:

    User
      ↓
    Application
      ↓
    Libraries / APIs
      ↓
    Operating System
      ↓
    Drivers
      ↓
    Controllers / Buses
      ↓
    Hardware
      ↓
    Physical operations

Understanding this hierarchy is essential for:

    Python developers
    Software engineers
    System administrators
    DevOps engineers
    Cloud engineers
    Cybersecurity professionals
    Data engineers
    AI/ML engineers
    Embedded engineers
    Performance engineers

Python provides several ways to inspect the system.

Standard library:

    platform
    os
    sys
    shutil
    socket
    subprocess
    pathlib

Detailed monitoring:

    psutil

Once these concepts are understood, system information stops being
a collection of commands and becomes a structured way of understanding
how software executes on real computing hardware.
====================================================================
"""
