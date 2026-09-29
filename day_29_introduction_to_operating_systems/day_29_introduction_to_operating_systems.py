"""
Introduction to Operating Systems
=================================

A standalone study program covering:
- Purpose of an operating system
- Kernel and operating-system structure
- User mode and kernel/system mode
- System calls
- Processes and scheduling
- Memory and virtual memory concepts
- Files and I/O
- Protection and security boundaries
- Operating-system classifications and trade-offs
- Interrupts and context switching
- A small educational OS simulation

The program uses only the Python standard library.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from collections import deque
from typing import Callable, Optional
import time


# ---------------------------------------------------------------------------
# 1. Fundamental terminology
# ---------------------------------------------------------------------------

class CPUPrivilegeMode(Enum):
    """Simplified CPU execution modes used by the educational simulator."""
    USER = "user mode"
    KERNEL = "kernel/system mode"


class OperatingSystemType(Enum):
    """Common classifications of operating systems."""
    BATCH = "Batch"
    MULTIPROGRAMMING = "Multiprogramming"
    MULTITASKING = "Multitasking"
    MULTIPROCESSING = "Multiprocessing"
    REAL_TIME = "Real-time"
    DISTRIBUTED = "Distributed"
    NETWORK = "Network"
    EMBEDDED = "Embedded"
    MOBILE = "Mobile"
    DESKTOP = "Desktop"
    SERVER = "Server"


@dataclass
class Process:
    """A simplified process-control representation."""
    pid: int
    name: str
    priority: int = 5
    state: str = "NEW"
    memory_kb: int = 1024
    cpu_burst: int = 1
    io_bound: bool = False
    registers: dict[str, int] = field(default_factory=dict)


@dataclass
class File:
    """A simplified in-memory representation of a file."""
    name: str
    contents: str = ""
    owner: str = "user"
    permissions: str = "rw-r--r--"


# ---------------------------------------------------------------------------
# 2. What an operating system does
# ---------------------------------------------------------------------------

class OperatingSystem:
    """
    Educational operating-system model.

    A real operating system is much more complex, but the same broad
    responsibilities appear in real systems:
      1. Process/CPU management
      2. Memory management
      3. Storage/file management
      4. Device/I/O management
      5. Protection and security
      6. Networking
      7. Resource allocation
      8. User-facing services
    """

    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
        self.mode = CPUPrivilegeMode.USER
        self.processes: dict[int, Process] = {}
        self.files: dict[str, File] = {}
        self.next_pid = 1
        self.total_memory_kb = 8192
        self.used_memory_kb = 0
        self.cpu_ticks = 0

    def show_identity(self) -> None:
        print(f"{self.name} {self.version}")
        print(f"Current privilege level: {self.mode.value}")

    def create_process(self, name: str, memory_kb: int = 512) -> Process:
        """Create a process after checking memory availability."""
        if memory_kb <= 0:
            raise ValueError("Process memory must be positive.")

        if self.used_memory_kb + memory_kb > self.total_memory_kb:
            raise MemoryError("Insufficient simulated memory.")

        process = Process(
            pid=self.next_pid,
            name=name,
            memory_kb=memory_kb,
            state="READY",
        )
        self.processes[process.pid] = process
        self.next_pid += 1
        self.used_memory_kb += memory_kb
        return process

    def terminate_process(self, pid: int) -> None:
        """Release resources belonging to a process."""
        process = self.processes.get(pid)

        if process is None:
            raise KeyError(f"Process {pid} does not exist.")

        process.state = "TERMINATED"
        self.used_memory_kb -= process.memory_kb
        del self.processes[pid]

    def create_file(self, name: str, contents: str = "") -> File:
        """Create a file through a simulated OS storage service."""
        if not name or "/" in name:
            raise ValueError("Invalid file name.")

        if name in self.files:
            raise FileExistsError(f"{name} already exists.")

        new_file = File(name=name, contents=contents)
        self.files[name] = new_file
        return new_file

    def read_file(self, name: str) -> str:
        """Read a file through the simulated file-system interface."""
        if name not in self.files:
            raise FileNotFoundError(name)
        return self.files[name].contents

    def write_file(self, name: str, contents: str) -> None:
        """Write data through the simulated file-system interface."""
        if name not in self.files:
            raise FileNotFoundError(name)
        self.files[name].contents = contents

    def enter_kernel(self, reason: str) -> None:
        """
        Simulate a transition from user mode into privileged kernel mode.

        Real CPUs perform hardware-controlled privilege transitions through
        mechanisms such as system-call instructions, traps, or interrupts.
        """
        if self.mode == CPUPrivilegeMode.KERNEL:
            raise RuntimeError("Already in kernel mode.")

        print(f"[MODE SWITCH] USER -> KERNEL: {reason}")
        self.mode = CPUPrivilegeMode.KERNEL

    def leave_kernel(self) -> None:
        """Return from privileged execution to user mode."""
        if self.mode != CPUPrivilegeMode.KERNEL:
            raise RuntimeError("Not currently in kernel mode.")

        print("[MODE SWITCH] KERNEL -> USER")
        self.mode = CPUPrivilegeMode.USER

    def system_call(self, process: Process, service: str, action: Callable[[], object]):
        """
        Simulate a system call.

        User programs do not normally manipulate protected hardware directly.
        They request an OS service through a controlled system-call interface.
        """
        if process.pid not in self.processes:
            raise PermissionError("Process is not managed by this OS.")

        print(f"\nSystem call requested by PID {process.pid}: {service}")

        self.enter_kernel(f"system call '{service}'")
        try:
            result = action()
            return result
        finally:
            self.leave_kernel()


# ---------------------------------------------------------------------------
# 3. System-call demonstrations
# ---------------------------------------------------------------------------

def demonstrate_system_calls() -> None:
    print("\n=== SYSTEM CALL DEMONSTRATION ===")

    os = OperatingSystem("EduOS", "1.0")
    process = os.create_process("text-editor", memory_kb=768)

    # open/read/write are examples of services commonly exposed through
    # system calls in real operating systems.
    os.system_call(
        process,
        "create_file",
        lambda: os.create_file("notes.txt", "Operating systems manage resources."),
    )

    content = os.system_call(
        process,
        "read_file",
        lambda: os.read_file("notes.txt"),
    )

    print(f"Read through OS service: {content}")

    os.system_call(
        process,
        "write_file",
        lambda: os.write_file(
            "notes.txt",
            "A system call is a controlled request for an OS service.",
        ),
    )

    print(f"Updated file: {os.read_file('notes.txt')}")


# ---------------------------------------------------------------------------
# 4. User mode vs kernel mode
# ---------------------------------------------------------------------------

def demonstrate_protection_boundary() -> None:
    print("\n=== USER MODE VS KERNEL MODE ===")

    os = OperatingSystem("EduOS", "1.0")
    process = os.create_process("application")

    print(f"Application PID: {process.pid}")
    print(f"Starting mode: {os.mode.value}")

    # Application code is conceptually restricted to user mode.
    print("Application can perform ordinary computation in user mode.")

    # Directly changing protected OS state is not allowed in this model.
    try:
        if os.mode != CPUPrivilegeMode.KERNEL:
            raise PermissionError(
                "User-mode code cannot directly execute a privileged operation."
            )
    except PermissionError as error:
        print(f"Protection boundary: {error}")

    # A legitimate request crosses the boundary through a system call.
    os.system_call(
        process,
        "create_file",
        lambda: os.create_file("protected.txt", "Created through a system call."),
    )


# ---------------------------------------------------------------------------
# 5. CPU scheduling
# ---------------------------------------------------------------------------

def first_come_first_served(processes: list[Process]) -> list[tuple[str, int]]:
    """
    FCFS scheduling.

    The first process in the ready queue receives the CPU first.
    Simple, predictable, but a long CPU-bound process can delay others.
    """
    timeline = []
    for process in processes:
        process.state = "RUNNING"
        timeline.append((process.name, process.cpu_burst))
        process.state = "READY"
    return timeline


def round_robin(
    processes: list[Process], quantum: int = 2
) -> list[tuple[str, int]]:
    """
    Round-robin scheduling.

    Each ready process receives at most one time quantum before returning
    to the queue. This is useful for interactive multitasking systems.
    """
    if quantum <= 0:
        raise ValueError("Quantum must be positive.")

    remaining = {process.pid: process.cpu_burst for process in processes}
    queue = deque(processes)
    timeline: list[tuple[str, int]] = []

    while queue:
        process = queue.popleft()
        run_time = min(quantum, remaining[process.pid])

        process.state = "RUNNING"
        timeline.append((process.name, run_time))
        remaining[process.pid] -= run_time

        if remaining[process.pid] > 0:
            process.state = "READY"
            queue.append(process)
        else:
            process.state = "TERMINATED"

    return timeline


def demonstrate_scheduling() -> None:
    print("\n=== CPU SCHEDULING ===")

    processes = [
        Process(1, "browser", cpu_burst=5),
        Process(2, "editor", cpu_burst=2),
        Process(3, "compiler", cpu_burst=7),
    ]

    print("FCFS:")
    print(first_come_first_served(processes))

    processes = [
        Process(1, "browser", cpu_burst=5),
        Process(2, "editor", cpu_burst=2),
        Process(3, "compiler", cpu_burst=7),
    ]

    print("Round Robin, quantum=2:")
    print(round_robin(processes, quantum=2))


# ---------------------------------------------------------------------------
# 6. Memory management
# ---------------------------------------------------------------------------

class MemoryManager:
    """
    Simplified contiguous memory allocator.

    Real systems can use paging, segmentation, virtual memory, page tables,
    translation lookaside buffers, and sophisticated allocators.
    """

    def __init__(self, total_kb: int):
        if total_kb <= 0:
            raise ValueError("Memory size must be positive.")

        self.total_kb = total_kb
        self.allocations: dict[str, tuple[int, int]] = {}
        self.next_address = 0

    def allocate(self, process_name: str, size_kb: int) -> int:
        if size_kb <= 0:
            raise ValueError("Allocation size must be positive.")

        used = sum(size for _, size in self.allocations.values())

        if used + size_kb > self.total_kb:
            raise MemoryError("Not enough memory.")

        address = self.next_address
        self.allocations[process_name] = (address, size_kb)
        self.next_address += size_kb
        return address

    def free(self, process_name: str) -> None:
        if process_name not in self.allocations:
            raise KeyError(process_name)

        del self.allocations[process_name]

    def status(self) -> None:
        used = sum(size for _, size in self.allocations.values())
        print(f"Used: {used} KB / {self.total_kb} KB")
        print(f"Free: {self.total_kb - used} KB")
        print(f"Allocations: {self.allocations}")


def demonstrate_memory_management() -> None:
    print("\n=== MEMORY MANAGEMENT ===")

    memory = MemoryManager(4096)

    browser_address = memory.allocate("browser", 1024)
    compiler_address = memory.allocate("compiler", 2048)

    print(f"Browser base address: {browser_address}")
    print(f"Compiler base address: {compiler_address}")
    memory.status()

    memory.free("browser")
    print("Browser memory released.")
    memory.status()

    try:
        memory.allocate("large-job", 5000)
    except MemoryError as error:
        print(f"Expected allocation failure: {error}")


# ---------------------------------------------------------------------------
# 7. Virtual memory and paging concepts
# ---------------------------------------------------------------------------

@dataclass
class Page:
    virtual_page: int
    physical_frame: Optional[int] = None


class SimplePageTable:
    """
    Educational virtual-to-physical page mapping.

    Virtual memory allows a process to use virtual addresses while the
    operating system and memory-management hardware translate those
    addresses into physical locations.
    """

    def __init__(self, page_size: int = 4096):
        if page_size <= 0:
            raise ValueError("Page size must be positive.")
        self.page_size = page_size
        self.mapping: dict[int, int] = {}

    def map_page(self, virtual_page: int, physical_frame: int) -> None:
        if virtual_page < 0 or physical_frame < 0:
            raise ValueError("Page and frame numbers cannot be negative.")
        self.mapping[virtual_page] = physical_frame

    def translate(self, virtual_address: int) -> int:
        if virtual_address < 0:
            raise ValueError("Address cannot be negative.")

        virtual_page, offset = divmod(virtual_address, self.page_size)

        if virtual_page not in self.mapping:
            raise MemoryError(
                f"Page fault: virtual page {virtual_page} is not mapped."
            )

        physical_frame = self.mapping[virtual_page]
        return physical_frame * self.page_size + offset


def demonstrate_virtual_memory() -> None:
    print("\n=== VIRTUAL MEMORY ===")

    page_table = SimplePageTable(page_size=4096)

    page_table.map_page(0, 5)
    page_table.map_page(1, 8)

    virtual_address = 4096 + 123
    physical_address = page_table.translate(virtual_address)

    print(f"Virtual address:  {virtual_address}")
    print(f"Physical address: {physical_address}")

    try:
        page_table.translate(8192)
    except MemoryError as error:
        print(error)


# ---------------------------------------------------------------------------
# 8. Interrupts and context switching
# ---------------------------------------------------------------------------

def simulate_interrupt(os: OperatingSystem, interrupt_name: str) -> None:
    """
    An interrupt causes the processor to transfer control to privileged
    operating-system code.

    Hardware interrupts can indicate events such as timer expiration,
    keyboard input, network arrival, or completion of device I/O.
    """
    print(f"\nInterrupt received: {interrupt_name}")

    previous_mode = os.mode
    os.mode = CPUPrivilegeMode.KERNEL

    print(f"Interrupt handler running in {os.mode.value}.")
    print("Kernel handles the event and updates protected OS state.")

    os.mode = previous_mode
    print(f"Execution restored to {os.mode.value}.")


def simulate_context_switch(
    current: Process, next_process: Process
) -> None:
    """
    A context switch saves the current process state and restores another.

    Real systems save substantially more architectural state than this
    simplified example.
    """
    current.registers = {
        "instruction_pointer": 1000,
        "stack_pointer": 8000,
        "general_register": 42,
    }

    saved_state = current.registers.copy()
    print(f"\nSaved {current.name} state: {saved_state}")

    next_process.registers = {
        "instruction_pointer": 2500,
        "stack_pointer": 9000,
        "general_register": 7,
    }

    print(f"Restored {next_process.name} state: {next_process.registers}")


# ---------------------------------------------------------------------------
# 9. Operating-system classifications
# ---------------------------------------------------------------------------

OS_TYPE_DESCRIPTIONS = {
    OperatingSystemType.BATCH: (
        "Executes groups of jobs with little or no interactive user input."
    ),
    OperatingSystemType.MULTIPROGRAMMING: (
        "Keeps multiple programs available so CPU time can be used efficiently."
    ),
    OperatingSystemType.MULTITASKING: (
        "Rapidly switches among tasks to provide concurrent interactive execution."
    ),
    OperatingSystemType.MULTIPROCESSING: (
        "Uses multiple CPU cores or processors to execute work in parallel."
    ),
    OperatingSystemType.REAL_TIME: (
        "Provides timing guarantees or bounded response requirements for specific tasks."
    ),
    OperatingSystemType.DISTRIBUTED: (
        "Coordinates resources or computation across multiple networked machines."
    ),
    OperatingSystemType.NETWORK: (
        "Provides services for communication and resource sharing across systems."
    ),
    OperatingSystemType.EMBEDDED: (
        "Targets dedicated devices with constrained resources and specific functions."
    ),
    OperatingSystemType.MOBILE: (
        "Targets smartphones and tablets with power, touch, radio, and application constraints."
    ),
    OperatingSystemType.DESKTOP: (
        "Optimizes general-purpose interactive use on personal computers."
    ),
    OperatingSystemType.SERVER: (
        "Provides long-running services, concurrency, networking, and centralized resources."
    ),
}


def explain_os_types() -> None:
    print("\n=== OPERATING-SYSTEM TYPES ===")

    for os_type, description in OS_TYPE_DESCRIPTIONS.items():
        print(f"{os_type.value}: {description}")


# ---------------------------------------------------------------------------
# 10. Architectural styles
# ---------------------------------------------------------------------------

def explain_architectures() -> None:
    print("\n=== OS ARCHITECTURAL STYLES ===")

    architectures = {
        "Monolithic kernel": (
            "Many core OS services execute in kernel space. "
            "This can provide efficient communication but increases the amount "
            "of privileged code."
        ),
        "Microkernel": (
            "Keeps the kernel core relatively small and moves many services "
            "outside the kernel. This can improve isolation but may introduce "
            "communication overhead."
        ),
        "Hybrid kernel": (
            "Combines design ideas from monolithic and microkernel approaches."
        ),
        "Layered design": (
            "Organizes system functionality into conceptual layers with defined responsibilities."
        ),
        "Modular kernel": (
            "Allows kernel functionality to be dynamically or statically composed "
            "from modules while retaining substantial kernel-space functionality."
        ),
    }

    for name, explanation in architectures.items():
        print(f"\n{name}:\n  {explanation}")


# ---------------------------------------------------------------------------
# 11. Security and protection
# ---------------------------------------------------------------------------

def demonstrate_access_control() -> None:
    print("\n=== PROTECTION AND SECURITY ===")

    users = {
        "alice": {"read", "write"},
        "bob": {"read"},
        "guest": set(),
    }

    requested_operation = "write"

    for username, permissions in users.items():
        allowed = requested_operation in permissions
        print(
            f"{username:>6} -> {requested_operation}: "
            f"{'allowed' if allowed else 'denied'}"
        )

    print(
        "\nPrivilege separation reduces the damage that a compromised or "
        "buggy user application can cause to the operating system."
    )


# ---------------------------------------------------------------------------
# 12. I/O model
# ---------------------------------------------------------------------------

def demonstrate_io() -> None:
    print("\n=== I/O MANAGEMENT ===")

    print("Application requests disk read.")
    print("1. User process issues a system call.")
    print("2. Kernel validates the request.")
    print("3. Kernel communicates with the storage subsystem.")
    print("4. Device performs I/O.")
    print("5. Completion may trigger an interrupt.")
    print("6. Kernel makes data available to the requesting process.")


# ---------------------------------------------------------------------------
# 13. Error handling and edge cases
# ---------------------------------------------------------------------------

def demonstrate_edge_cases() -> None:
    print("\n=== EDGE CASES AND ERROR HANDLING ===")

    os = OperatingSystem("EduOS", "1.0")

    try:
        os.create_process("invalid", memory_kb=-1)
    except ValueError as error:
        print(f"Invalid memory request handled: {error}")

    process = os.create_process("application")

    try:
        os.read_file("does-not-exist.txt")
    except FileNotFoundError as error:
        print(f"Missing file handled: {error}")

    try:
        os.terminate_process(9999)
    except KeyError as error:
        print(f"Unknown process handled: {error}")

    os.terminate_process(process.pid)
    print("Normal process termination completed.")


# ---------------------------------------------------------------------------
# 14. Performance considerations
# ---------------------------------------------------------------------------

def compare_scheduling_costs() -> None:
    print("\n=== PERFORMANCE CONSIDERATIONS ===")

    workloads = [
        Process(1, "short-job", cpu_burst=1),
        Process(2, "medium-job", cpu_burst=4),
        Process(3, "long-job", cpu_burst=8),
    ]

    fcfs_timeline = first_come_first_served(workloads)

    workloads = [
        Process(1, "short-job", cpu_burst=1),
        Process(2, "medium-job", cpu_burst=4),
        Process(3, "long-job", cpu_burst=8),
    ]

    rr_timeline = round_robin(workloads, quantum=2)

    print(f"FCFS execution slices: {len(fcfs_timeline)}")
    print(f"Round-robin execution slices: {len(rr_timeline)}")
    print(
        "A smaller time quantum can improve responsiveness but may increase "
        "context-switch overhead."
    )


# ---------------------------------------------------------------------------
# 15. A small end-to-end OS simulation
# ---------------------------------------------------------------------------

def run_operating_system_simulation() -> None:
    print("\n=== END-TO-END OS SIMULATION ===")

    edu_os = OperatingSystem("EduOS", "1.0")
    edu_os.show_identity()

    browser = edu_os.create_process("browser", memory_kb=1024)
    terminal = edu_os.create_process("terminal", memory_kb=512)
    compiler = edu_os.create_process("compiler", memory_kb=2048)

    print("\nCreated processes:")
    for process in edu_os.processes.values():
        print(
            f"PID={process.pid}, name={process.name}, "
            f"state={process.state}, memory={process.memory_kb} KB"
        )

    edu_os.system_call(
        terminal,
        "create_file",
        lambda: edu_os.create_file(
            "build.log",
            "Compilation started.\n",
        ),
    )

    simulate_interrupt(edu_os, "timer")

    simulate_context_switch(browser, compiler)

    edu_os.system_call(
        compiler,
        "write_file",
        lambda: edu_os.write_file(
            "build.log",
            "Compilation started.\nCompilation completed successfully.\n",
        ),
    )

    print("\nBuild log:")
    print(edu_os.read_file("build.log"))

    edu_os.terminate_process(browser.pid)
    edu_os.terminate_process(terminal.pid)
    edu_os.terminate_process(compiler.pid)

    print(f"Remaining managed processes: {len(edu_os.processes)}")
    print(f"Remaining allocated memory: {edu_os.used_memory_kb} KB")


# ---------------------------------------------------------------------------
# 16. Important conceptual distinctions
# ---------------------------------------------------------------------------

def explain_key_distinctions() -> None:
    print("\n=== KEY DISTINCTIONS ===")

    distinctions = [
        (
            "Kernel vs operating system",
            "The kernel is the privileged core. The operating system includes "
            "the kernel plus system services, utilities, libraries, and often user interfaces."
        ),
        (
            "Program vs process",
            "A program is a passive set of instructions; a process is an executing instance "
            "with state and allocated resources."
        ),
        (
            "User mode vs kernel mode",
            "User mode restricts privileged operations. Kernel mode permits the OS to perform "
            "protected operations on behalf of processes."
        ),
        (
            "Concurrency vs parallelism",
            "Concurrency means multiple tasks make progress over time; parallelism means "
            "multiple tasks actually execute simultaneously on multiple execution units."
        ),
        (
            "Multiprogramming vs multitasking",
            "Multiprogramming emphasizes keeping the processor productive among several jobs; "
            "multitasking emphasizes responsive sharing among active tasks."
        ),
        (
            "Interrupt vs system call",
            "A system call is an intentional request by software for an OS service; "
            "an interrupt is an event that transfers execution to an interrupt handler."
        ),
    ]

    for concept, explanation in distinctions:
        print(f"\n{concept}:\n  {explanation}")


# ---------------------------------------------------------------------------
# 17. Study checks
# ---------------------------------------------------------------------------

def run_knowledge_checks() -> None:
    print("\n=== KNOWLEDGE CHECKS ===")

    questions = [
        (
            "Which component normally performs privileged CPU and memory management?",
            "kernel",
        ),
        (
            "Which mode restricts direct access to privileged hardware operations?",
            "user mode",
        ),
        (
            "What mechanism lets an application request an OS service?",
            "system call",
        ),
        (
            "What scheduling algorithm rotates processes through a time quantum?",
            "round robin",
        ),
    ]

    correct = 0

    for question, expected in questions:
        answer = input(f"\n{question}\nAnswer: ").strip().lower()

        if answer == expected:
            print("Correct.")
            correct += 1
        else:
            print(f"Expected concept: {expected}")

    print(f"\nKnowledge-check result: {correct}/{len(questions)}")


# ---------------------------------------------------------------------------
# 18. Main program
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 72)
    print("INTRODUCTION TO OPERATING SYSTEMS")
    print("=" * 72)

    print(
        "\nAn operating system is system software that manages computer "
        "hardware and provides controlled services to application programs."
    )

    demonstrate_system_calls()
    demonstrate_protection_boundary()
    demonstrate_scheduling()
    demonstrate_memory_management()
    demonstrate_virtual_memory()

    os = OperatingSystem("EduOS", "1.0")
    simulate_interrupt(os, "network packet received")

    process_a = Process(10, "process-A")
    process_b = Process(11, "process-B")
    simulate_context_switch(process_a, process_b)

    explain_os_types()
    explain_architectures()
    demonstrate_access_control()
    demonstrate_io()
    demonstrate_edge_cases()
    compare_scheduling_costs()
    explain_key_distinctions()
    run_operating_system_simulation()

    # The interactive knowledge check is opt-in so that the script can also
    # run automatically in terminals, CI systems, or classroom demonstrations.
    print("\nRun with '--quiz' to enable the interactive knowledge check.")

    import sys

    if "--quiz" in sys.argv:
        run_knowledge_checks()

    print("\nEducational OS simulation completed.")


if __name__ == "__main__":
    main()
