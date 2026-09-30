"""
Operating System Architecture
=============================

A self-contained technical study of:

- Monolithic kernels
- Microkernels
- Hybrid kernels
- Layered operating-system architecture

The program models the architectural boundaries between kernel subsystems,
demonstrates message-based microkernel communication, simulates a monolithic
kernel with direct subsystem calls, models a hybrid architecture, and builds
a layered system with dependency validation.

Run:
    python os_architecture.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Set, Tuple
import time


class ArchitectureError(Exception):
    """Raised when an architectural rule is violated."""


class KernelMode(Enum):
    KERNEL = "kernel mode"
    USER = "user mode"


class ComponentState(Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    FAILED = "failed"


@dataclass
class Process:
    pid: int
    name: str
    state: str = "ready"
    memory_bytes: int = 0


@dataclass
class File:
    name: str
    content: str


@dataclass
class Device:
    name: str
    device_type: str
    online: bool = True


@dataclass
class Message:
    sender: str
    receiver: str
    operation: str
    payload: Dict[str, object] = field(default_factory=dict)


class MemoryManager:
    """
    Core memory-management mechanism shared by several architecture models.

    The manager tracks allocations explicitly so that the architectural
    examples can demonstrate ownership and failure handling rather than merely
    printing abstract descriptions.
    """

    def __init__(self, total_bytes: int):
        if total_bytes <= 0:
            raise ValueError("total_bytes must be positive")
        self.total_bytes = total_bytes
        self.allocated: Dict[str, int] = {}

    @property
    def used_bytes(self) -> int:
        return sum(self.allocated.values())

    @property
    def free_bytes(self) -> int:
        return self.total_bytes - self.used_bytes

    def allocate(self, owner: str, amount: int) -> bool:
        if amount <= 0:
            raise ValueError("Allocation amount must be positive")
        if owner in self.allocated:
            raise ArchitectureError(f"{owner} already owns an allocation")
        if amount > self.free_bytes:
            return False
        self.allocated[owner] = amount
        return True

    def release(self, owner: str) -> int:
        if owner not in self.allocated:
            raise ArchitectureError(f"No allocation belongs to {owner}")
        return self.allocated.pop(owner)

    def snapshot(self) -> Dict[str, int]:
        return dict(self.allocated)


class ProcessManager:
    """Creates and tracks processes."""

    def __init__(self, memory: MemoryManager):
        self.memory = memory
        self.processes: Dict[int, Process] = {}
        self.next_pid = 100

    def create(self, name: str, memory_bytes: int) -> Process:
        if not name.strip():
            raise ValueError("Process name cannot be empty")

        pid = self.next_pid
        owner = f"process:{pid}"

        if not self.memory.allocate(owner, memory_bytes):
            raise MemoryError(
                f"Insufficient memory for process {name}: "
                f"requested={memory_bytes}, free={self.memory.free_bytes}"
            )

        process = Process(
            pid=pid,
            name=name,
            state="ready",
            memory_bytes=memory_bytes,
        )
        self.processes[pid] = process
        self.next_pid += 1
        return process

    def terminate(self, pid: int) -> None:
        process = self.processes.get(pid)
        if process is None:
            raise KeyError(f"Unknown PID {pid}")

        process.state = "terminated"
        self.memory.release(f"process:{pid}")
        del self.processes[pid]


class FileSystem:
    """A deliberately small in-memory file system."""

    def __init__(self):
        self.files: Dict[str, File] = {}

    def create_file(self, name: str, content: str = "") -> None:
        if not name or "/" not in name:
            raise ValueError("File path must contain a directory separator")
        if name in self.files:
            raise FileExistsError(name)
        self.files[name] = File(name=name, content=content)

    def read(self, name: str) -> str:
        try:
            return self.files[name].content
        except KeyError:
            raise FileNotFoundError(name)

    def write(self, name: str, content: str) -> None:
        if name not in self.files:
            raise FileNotFoundError(name)
        self.files[name].content = content


class DeviceManager:
    """Models device ownership and I/O operations."""

    def __init__(self):
        self.devices: Dict[str, Device] = {
            "console0": Device("console0", "terminal"),
            "disk0": Device("disk0", "storage"),
            "net0": Device("net0", "network"),
        }

    def write(self, device_name: str, data: str) -> str:
        device = self.devices.get(device_name)
        if device is None:
            raise KeyError(f"Unknown device: {device_name}")
        if not device.online:
            raise IOError(f"Device {device_name} is offline")
        if not data:
            raise ValueError("Cannot write empty device data")
        return f"{device_name} accepted {len(data)} bytes"


class Scheduler:
    """Simple round-robin scheduler."""

    def __init__(self):
        self.ready_queue: List[int] = []

    def add(self, process: Process) -> None:
        if process.state not in {"ready", "running"}:
            raise ArchitectureError(
                f"Process {process.pid} is not schedulable"
            )
        self.ready_queue.append(process.pid)

    def next_process(self) -> Optional[int]:
        if not self.ready_queue:
            return None
        pid = self.ready_queue.pop(0)
        self.ready_queue.append(pid)
        return pid


class MonolithicKernel:
    """
    Monolithic architecture model.

    Process management, memory management, file systems, device handling,
    and scheduling operate as kernel-resident subsystems with direct calls
    between trusted components.
    """

    def __init__(self):
        self.mode = KernelMode.KERNEL
        self.memory = MemoryManager(64 * 1024 * 1024)
        self.process_manager = ProcessManager(self.memory)
        self.filesystem = FileSystem()
        self.devices = DeviceManager()
        self.scheduler = Scheduler()

    def syscall_create_process(self, name: str, memory_bytes: int) -> Process:
        self.mode = KernelMode.KERNEL
        process = self.process_manager.create(name, memory_bytes)
        self.scheduler.add(process)
        return process

    def syscall_create_file(self, path: str, content: str) -> None:
        self.filesystem.create_file(path, content)

    def syscall_write_device(self, device: str, data: str) -> str:
        return self.devices.write(device, data)

    def run_demo(self) -> None:
        print("\n=== MONOLITHIC KERNEL ===")
        process = self.syscall_create_process("editor", 4 * 1024 * 1024)
        self.syscall_create_file("/documents/report.txt", "architecture")
        result = self.syscall_write_device("console0", "editor started")

        print(f"Created process: PID={process.pid}, name={process.name}")
        print(f"Direct filesystem access: {self.filesystem.read('/documents/report.txt')}")
        print(f"Direct device operation: {result}")
        print(f"Scheduler selected PID: {self.scheduler.next_process()}")
        print(f"Kernel memory used: {self.memory.used_bytes} bytes")


class IPCChannel:
    """
    Explicit message-passing channel.

    Unlike the direct subsystem calls in the monolithic model, a client must
    construct a message and send it to a server. This makes communication
    boundaries explicit.
    """

    def __init__(self):
        self.queue: List[Message] = []

    def send(self, message: Message) -> None:
        if not message.sender or not message.receiver:
            raise ValueError("IPC endpoints are required")
        self.queue.append(message)

    def receive_for(self, receiver: str) -> Optional[Message]:
        for index, message in enumerate(self.queue):
            if message.receiver == receiver:
                return self.queue.pop(index)
        return None


class MicrokernelIPC:
    """
    Minimal microkernel IPC mechanism.

    The kernel handles IPC and scheduling, while filesystem and device
    services execute outside the kernel in user-space server processes.
    """

    def __init__(self):
        self.ipc = IPCChannel()
        self.services: Dict[str, Callable[[Message], str]] = {}

    def register_service(
        self,
        service_name: str,
        handler: Callable[[Message], str],
    ) -> None:
        if service_name in self.services:
            raise ArchitectureError(f"Service already exists: {service_name}")
        self.services[service_name] = handler

    def send_request(
        self,
        sender: str,
        service: str,
        operation: str,
        payload: Dict[str, object],
    ) -> str:
        if service not in self.services:
            raise ConnectionError(f"No server registered for {service}")

        message = Message(
            sender=sender,
            receiver=service,
            operation=operation,
            payload=payload,
        )
        self.ipc.send(message)

        received = self.ipc.receive_for(service)
        if received is None:
            raise TimeoutError(f"No IPC message delivered to {service}")

        return self.services[service](received)


class FileServer:
    """User-space filesystem server for the microkernel model."""

    def __init__(self):
        self.filesystem = FileSystem()

    def handle(self, message: Message) -> str:
        if message.operation == "create":
            self.filesystem.create_file(
                str(message.payload["path"]),
                str(message.payload.get("content", "")),
            )
            return "file created"

        if message.operation == "read":
            return self.filesystem.read(str(message.payload["path"]))

        raise NotImplementedError(
            f"Filesystem operation {message.operation!r} is unsupported"
        )


class DeviceServer:
    """User-space device server for the microkernel model."""

    def __init__(self):
        self.devices = DeviceManager()

    def handle(self, message: Message) -> str:
        if message.operation != "write":
            raise NotImplementedError(
                f"Device operation {message.operation!r} is unsupported"
            )

        return self.devices.write(
            str(message.payload["device"]),
            str(message.payload["data"]),
        )


class Microkernel:
    """
    Microkernel architecture.

    Only the small kernel-facing mechanism is represented here. Filesystem
    and device behavior lives in isolated service objects and is accessed
    through IPC.
    """

    def __init__(self):
        self.ipc = MicrokernelIPC()
        self.file_server = FileServer()
        self.device_server = DeviceServer()

        self.ipc.register_service("filesystem", self.file_server.handle)
        self.ipc.register_service("device", self.device_server.handle)

    def run_demo(self) -> None:
        print("\n=== MICROKERNEL ===")

        created = self.ipc.send_request(
            "shell",
            "filesystem",
            "create",
            {
                "path": "/home/user/notes.txt",
                "content": "microkernel IPC",
            },
        )

        content = self.ipc.send_request(
            "shell",
            "filesystem",
            "read",
            {"path": "/home/user/notes.txt"},
        )

        device_result = self.ipc.send_request(
            "shell",
            "device",
            "write",
            {"device": "console0", "data": "hello from user-space"},
        )

        print(f"Filesystem server response: {created}")
        print(f"Filesystem server read result: {content}")
        print(f"Device server response: {device_result}")
        print("The client did not directly manipulate the filesystem or device.")


class HybridKernel:
    """
    Hybrid architecture model.

    The design intentionally keeps performance-sensitive facilities inside
    the kernel while retaining explicit service boundaries for selected
    components. Real operating systems use different hybrid boundaries, so
    this is a conceptual model rather than a claim about one specific OS.
    """

    def __init__(self):
        self.memory = MemoryManager(128 * 1024 * 1024)
        self.scheduler = Scheduler()

        # Performance-sensitive core services remain directly accessible.
        self.process_manager = ProcessManager(self.memory)

        # A selected service is represented through an IPC-style boundary.
        self.ipc = MicrokernelIPC()
        self.storage_server = FileServer()
        self.ipc.register_service(
            "storage-service",
            self.storage_server.handle,
        )

    def create_process(self, name: str, memory_bytes: int) -> Process:
        process = self.process_manager.create(name, memory_bytes)
        self.scheduler.add(process)
        return process

    def storage_request(
        self,
        operation: str,
        payload: Dict[str, object],
    ) -> str:
        return self.ipc.send_request(
            "kernel-client",
            "storage-service",
            operation,
            payload,
        )

    def run_demo(self) -> None:
        print("\n=== HYBRID KERNEL ===")

        process = self.create_process("compiler", 8 * 1024 * 1024)

        self.storage_request(
            "create",
            {
                "path": "/build/output.txt",
                "content": "hybrid architecture",
            },
        )

        result = self.storage_request(
            "read",
            {"path": "/build/output.txt"},
        )

        print(f"Kernel-resident process service created PID={process.pid}")
        print(f"Selected service boundary returned: {result}")
        print(
            "The model combines direct kernel services with explicit "
            "service boundaries."
        )


@dataclass(frozen=True)
class Layer:
    name: str
    level: int
    allowed_dependencies: Set[str]


class LayeredSystem:
    """
    Layered architecture model.

    A layer can depend only on layers explicitly declared as lower-level
    dependencies. The validator therefore detects architectural dependency
    violations before runtime deployment.
    """

    def __init__(self):
        self.layers: Dict[str, Layer] = {
            "hardware": Layer("hardware", 0, set()),
            "kernel": Layer("kernel", 1, {"hardware"}),
            "system-services": Layer("system-services", 2, {"kernel"}),
            "runtime": Layer("runtime", 3, {"system-services"}),
            "applications": Layer("applications", 4, {"runtime"}),
        }

        self.dependencies: Dict[str, Set[str]] = {
            name: set(layer.allowed_dependencies)
            for name, layer in self.layers.items()
        }

    def add_dependency(self, source: str, target: str) -> None:
        if source not in self.layers:
            raise KeyError(f"Unknown source layer: {source}")
        if target not in self.layers:
            raise KeyError(f"Unknown target layer: {target}")

        if self.layers[target].level >= self.layers[source].level:
            raise ArchitectureError(
                f"Layer {source!r} cannot depend on same or higher "
                f"layer {target!r}"
            )

        self.dependencies[source].add(target)

    def validate(self) -> List[str]:
        errors: List[str] = []

        for source, targets in self.dependencies.items():
            source_level = self.layers[source].level

            for target in targets:
                target_level = self.layers[target].level

                if target_level >= source_level:
                    errors.append(
                        f"{source} -> {target}: dependency violates "
                        "layer ordering"
                    )

        return errors

    def run_demo(self) -> None:
        print("\n=== LAYERED ARCHITECTURE ===")

        valid_errors = self.validate()
        print(
            "Initial architecture:",
            "valid" if not valid_errors else valid_errors,
        )

        print("Adding invalid application -> kernel dependency...")
        self.add_dependency("applications", "kernel")

        errors = self.validate()
        print("Validation result after dependency change:")

        for error in errors:
            print(f"  {error}")


@dataclass
class BenchmarkResult:
    architecture: str
    operations: int
    elapsed_ms: float


def benchmark_direct_calls(iterations: int = 50_000) -> BenchmarkResult:
    """
    Measures local Python method-call overhead for a monolithic-style path.

    This is not an operating-system benchmark. Python timing is used only to
    illustrate that direct calls and message construction have different
    software paths.
    """

    kernel = MonolithicKernel()
    kernel.syscall_create_file("/tmp/benchmark.txt", "x")

    start = time.perf_counter()

    for _ in range(iterations):
        kernel.filesystem.read("/tmp/benchmark.txt")

    elapsed = (time.perf_counter() - start) * 1000

    return BenchmarkResult(
        architecture="monolithic-style direct call",
        operations=iterations,
        elapsed_ms=elapsed,
    )


def benchmark_ipc_calls(iterations: int = 50_000) -> BenchmarkResult:
    """
    Measures the conceptual IPC path.

    The result should not be interpreted as a real microkernel performance
    figure. Real IPC crosses privilege boundaries and may involve scheduler,
    address-space, cache, and hardware effects not modeled by Python.
    """

    kernel = Microkernel()
    kernel.ipc.send_request(
        "setup",
        "filesystem",
        "create",
        {"path": "/tmp/benchmark.txt", "content": "x"},
    )

    start = time.perf_counter()

    for _ in range(iterations):
        kernel.ipc.send_request(
            "benchmark",
            "filesystem",
            "read",
            {"path": "/tmp/benchmark.txt"},
        )

    elapsed = (time.perf_counter() - start) * 1000

    return BenchmarkResult(
        architecture="microkernel-style IPC",
        operations=iterations,
        elapsed_ms=elapsed,
    )


def print_benchmark(result: BenchmarkResult) -> None:
    print(
        f"{result.architecture}: "
        f"{result.operations:,} operations in "
        f"{result.elapsed_ms:.3f} ms"
    )


def demonstrate_failure_isolation() -> None:
    """
    Shows why isolation changes failure behavior.

    The filesystem server can fail because of an invalid request without
    requiring the simulated IPC kernel itself to expose its internal state.
    """

    print("\n=== FAILURE ISOLATION ===")
    kernel = Microkernel()

    try:
        kernel.ipc.send_request(
            "shell",
            "filesystem",
            "read",
            {"path": "/missing/file.txt"},
        )
    except FileNotFoundError as exc:
        print(f"User-space filesystem failure was contained: {exc}")

    print("IPC infrastructure remains available after the failed request.")

    result = kernel.ipc.send_request(
        "shell",
        "device",
        "write",
        {
            "device": "console0",
            "data": "device server still responds",
        },
    )
    print(result)


def demonstrate_security_boundary() -> None:
    """
    Demonstrates the architectural security principle that an exposed
    service should validate operation and payload rather than trusting clients.
    """

    print("\n=== SERVICE VALIDATION ===")
    kernel = Microkernel()

    unsafe_requests = [
        Message(
            sender="untrusted-client",
            receiver="filesystem",
            operation="delete-all",
            payload={},
        ),
        Message(
            sender="untrusted-client",
            receiver="device",
            operation="write",
            payload={"device": "unknown0", "data": "attack"},
        ),
    ]

    for message in unsafe_requests:
        try:
            if message.receiver == "filesystem":
                kernel.file_server.handle(message)
            else:
                kernel.device_server.handle(message)
        except (NotImplementedError, KeyError, ValueError) as exc:
            print(
                f"Rejected {message.operation!r} request from "
                f"{message.sender}: {exc}"
            )


def explain_architectural_tradeoffs() -> None:
    """
    Prints compact engineering observations based on the implementations.
    These statements describe architectural properties rather than claiming
    that one architecture is universally superior.
    """

    print("\n=== ARCHITECTURAL TRADE-OFFS ===")

    observations = {
        "Monolithic kernel": [
            "Subsystems execute inside a large privileged kernel boundary.",
            "Direct calls can avoid explicit service-message overhead.",
            "A defect in one privileged subsystem can have broad consequences.",
            "Subsystem coupling can increase the complexity of kernel maintenance.",
        ],
        "Microkernel": [
            "The kernel exposes a small privileged core and communication mechanism.",
            "Services can be isolated as separate components.",
            "IPC introduces communication and coordination costs.",
            "Service failures can be isolated when the architecture supports restartable servers.",
        ],
        "Hybrid kernel": [
            "Selected services remain in the kernel for integration or performance reasons.",
            "Other components can retain service-like boundaries.",
            "The resulting design does not fit a single pure architectural category.",
            "The exact boundary depends on the operating system implementation.",
        ],
        "Layered architecture": [
            "Each layer exposes abstractions to layers above it.",
            "Dependency rules can make architectural violations easier to detect.",
            "Strict layering can constrain optimization paths that would cross layers.",
            "Layering is an organizational and dependency model and can coexist with other kernel designs.",
        ],
    }

    for architecture, points in observations.items():
        print(f"\n{architecture}")
        for point in points:
            print(f"  - {point}")


def run_edge_cases() -> None:
    print("\n=== EDGE CASES AND FAILURE CONDITIONS ===")

    memory = MemoryManager(1024)

    try:
        memory.allocate("bad-request", -1)
    except ValueError as exc:
        print(f"Invalid allocation rejected: {exc}")

    try:
        memory.allocate("large-process", 2048)
    except Exception as exc:
        print(f"Capacity constraint handled: {exc}")

    filesystem = FileSystem()

    try:
        filesystem.create_file("/tmp/a.txt", "one")
        filesystem.create_file("/tmp/a.txt", "duplicate")
    except FileExistsError as exc:
        print(f"Duplicate file rejected: {exc}")

    microkernel = Microkernel()

    try:
        microkernel.ipc.send_request(
            "shell",
            "unknown-service",
            "read",
            {},
        )
    except ConnectionError as exc:
        print(f"Unknown IPC endpoint rejected: {exc}")

    layered = LayeredSystem()

    try:
        layered.add_dependency("hardware", "applications")
    except ArchitectureError as exc:
        print(f"Invalid upward dependency rejected: {exc}")


def main() -> None:
    print("OPERATING SYSTEM ARCHITECTURE LAB")
    print("=" * 36)
    print(
        "Models four architectural approaches and demonstrates "
        "their different communication and dependency boundaries."
    )

    monolithic = MonolithicKernel()
    monolithic.run_demo()

    microkernel = Microkernel()
    microkernel.run_demo()

    hybrid = HybridKernel()
    hybrid.run_demo()

    layered = LayeredSystem()
    layered.run_demo()

    demonstrate_failure_isolation()
    demonstrate_security_boundary()
    run_edge_cases()
    explain_architectural_tradeoffs()

    print("\n=== SOFTWARE-PATH TIMING DEMONSTRATION ===")
    direct_result = benchmark_direct_calls()
    ipc_result = benchmark_ipc_calls()

    print_benchmark(direct_result)
    print_benchmark(ipc_result)

    print(
        "\nTiming note: these measurements compare Python software paths, "
        "not real kernel performance."
    )

    print("\n=== ARCHITECTURAL BOUNDARY MAP ===")
    print("Monolithic: application -> system call -> kernel subsystems")
    print("Microkernel: application -> IPC -> user-space services")
    print("Hybrid: application -> kernel services + selected service boundaries")
    print("Layered: application -> runtime -> services -> kernel -> hardware")

    print("\nLab completed successfully.")


if __name__ == "__main__":
    main()
