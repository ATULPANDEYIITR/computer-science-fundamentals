"""
Input and Output Systems
========================

Topic:
    I/O devices, controllers, interrupts, DMA, and buses

This standalone study program progresses from basic I/O concepts to a
simulation of a modern I/O subsystem involving devices, controllers,
interrupts, DMA, buses, buffering, queues, errors, and performance.

No external packages are required.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from collections import deque
from typing import Deque, Dict, List, Optional, Callable, Any
import random
import time


# ============================================================================
# 1. FUNDAMENTAL TERMINOLOGY
# ============================================================================

def section(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def explain_fundamentals() -> None:
    section("1. FUNDAMENTAL I/O CONCEPTS")

    concepts = {
        "I/O": "Input/Output: communication between a computer system and devices.",
        "Input device": "A device that supplies data to a computer, such as a keyboard.",
        "Output device": "A device that receives data from a computer, such as a display.",
        "I/O controller": "Hardware that manages communication between a CPU/system bus and a device.",
        "Device driver": "Software that translates operating-system requests into device-specific operations.",
        "Interrupt": "A hardware or software signal requesting CPU attention.",
        "DMA": "Direct Memory Access: a mechanism allowing a controller to transfer data to/from memory with limited CPU involvement.",
        "Bus": "A communication pathway carrying data, addresses, and/or control signals.",
        "Port": "A logical or hardware interface through which a device communicates.",
        "Buffer": "Temporary storage used to absorb differences in transfer timing or speed.",
        "Polling": "A method where the CPU repeatedly checks device status.",
        "Memory-mapped I/O": "Device registers are mapped into the processor's memory address space.",
        "Programmed I/O": "The CPU explicitly performs or controls data transfers.",
    }

    for name, definition in concepts.items():
        print(f"{name:24} : {definition}")


# ============================================================================
# 2. SIMPLE INPUT AND OUTPUT
# ============================================================================

def demonstrate_basic_io() -> None:
    section("2. BASIC INPUT AND OUTPUT")

    user_name = input("Enter a name for the demonstration: ").strip()

    if not user_name:
        user_name = "Anonymous"

    message = f"Hello, {user_name}. This is an input/output demonstration."
    print("Program generated output:")
    print(message)

    # Input validation is an important part of robust I/O.
    numeric_text = input("Enter an integer: ").strip()

    try:
        number = int(numeric_text)
    except ValueError:
        print("Invalid integer input.")
    else:
        print(f"Received integer: {number}")
        print(f"Squared value: {number * number}")


# ============================================================================
# 3. DEVICE CLASSIFICATION
# ============================================================================

class DeviceType(Enum):
    INPUT = auto()
    OUTPUT = auto()
    STORAGE = auto()
    NETWORK = auto()
    MIXED = auto()


@dataclass
class Device:
    name: str
    device_type: DeviceType
    transfer_rate_mb_s: float
    latency_ms: float
    block_size: int = 4096

    def describe(self) -> None:
        print(
            f"{self.name}: type={self.device_type.name}, "
            f"rate={self.transfer_rate_mb_s} MB/s, "
            f"latency={self.latency_ms} ms, "
            f"block={self.block_size} bytes"
        )


def demonstrate_device_types() -> None:
    section("3. DEVICE CLASSIFICATION")

    devices = [
        Device("Keyboard", DeviceType.INPUT, 0.01, 5),
        Device("Display", DeviceType.OUTPUT, 500.0, 2),
        Device("SSD", DeviceType.STORAGE, 3500.0, 0.08),
        Device("Network Adapter", DeviceType.NETWORK, 1250.0, 0.5),
        Device("Touchscreen", DeviceType.MIXED, 100.0, 1.0),
    ]

    for device in devices:
        device.describe()


# ============================================================================
# 4. CONTROLLERS AND REGISTERS
# ============================================================================

class Controller:
    """
    A simplified device controller.

    Real controllers expose registers such as:
        - command register
        - status register
        - data register
        - address/count registers
        - interrupt configuration
        - DMA configuration
    """

    def __init__(self, device: Device):
        self.device = device
        self.status = "IDLE"
        self.command = None
        self.data_register: Optional[bytes] = None
        self.error: Optional[str] = None

    def write_command(self, command: str) -> None:
        self.command = command
        self.status = "COMMAND_RECEIVED"

    def read_status(self) -> str:
        return self.status

    def write_data(self, data: bytes) -> None:
        self.data_register = data
        self.status = "DATA_READY"

    def execute(self) -> None:
        if self.command is None:
            self.error = "No command"
            self.status = "ERROR"
            return

        self.status = "BUSY"

        if self.command == "READ":
            self.data_register = b"DEVICE-DATA"
            self.status = "COMPLETE"
        elif self.command == "WRITE":
            if self.data_register is None:
                self.error = "No data supplied"
                self.status = "ERROR"
            else:
                self.status = "COMPLETE"
        else:
            self.error = f"Unsupported command: {self.command}"
            self.status = "ERROR"


def demonstrate_controller() -> None:
    section("4. DEVICE CONTROLLER")

    disk = Device("Demo SSD", DeviceType.STORAGE, 3500, 0.08)
    controller = Controller(disk)

    print("Initial status:", controller.read_status())

    controller.write_command("WRITE")
    controller.write_data(b"Important data")
    controller.execute()

    print("After WRITE:", controller.read_status())

    controller.write_command("READ")
    controller.execute()

    print("After READ:", controller.read_status())
    print("Data register:", controller.data_register)


# ============================================================================
# 5. POLLING VS INTERRUPTS
# ============================================================================

class InterruptController:
    """A simplified interrupt controller."""

    def __init__(self):
        self.pending: Deque[str] = deque()

    def raise_interrupt(self, source: str) -> None:
        self.pending.append(source)

    def has_interrupt(self) -> bool:
        return bool(self.pending)

    def acknowledge(self) -> Optional[str]:
        if not self.pending:
            return None
        return self.pending.popleft()


def polling_example(device_ready_after: int = 4) -> None:
    print("\nPolling demonstration")

    checks = 0
    ready = False

    while not ready:
        checks += 1
        print(f"CPU checks device: attempt {checks}")

        if checks >= device_ready_after:
            ready = True

    print("Device is ready.")


def interrupt_example() -> None:
    print("\nInterrupt demonstration")

    interrupt_controller = InterruptController()

    print("CPU performs other work.")
    print("Device completes an operation.")
    interrupt_controller.raise_interrupt("SSD_CONTROLLER")

    if interrupt_controller.has_interrupt():
        source = interrupt_controller.acknowledge()
        print(f"CPU services interrupt from {source}.")


def compare_polling_and_interrupts() -> None:
    section("5. POLLING AND INTERRUPTS")

    polling_example()
    interrupt_example()

    print(
        "\nPolling repeatedly consumes CPU attention. "
        "Interrupts allow the CPU to perform other work until an event occurs."
    )


# ============================================================================
# 6. INTERRUPT PRIORITY
# ============================================================================

@dataclass(order=True)
class InterruptRequest:
    priority: int
    source: str = field(compare=False)
    description: str = field(compare=False)


def interrupt_priority_demo() -> None:
    section("6. INTERRUPT PRIORITY")

    requests = [
        InterruptRequest(3, "Keyboard", "User input"),
        InterruptRequest(1, "Network", "Incoming packet"),
        InterruptRequest(5, "Thermal Sensor", "Critical temperature"),
        InterruptRequest(2, "Storage", "I/O completion"),
    ]

    for request in sorted(requests):
        print(
            f"priority={request.priority}, "
            f"source={request.source}, "
            f"event={request.description}"
        )

    print(
        "\nLower numerical priority is treated as more urgent in this simulation."
    )


# ============================================================================
# 7. DMA
# ============================================================================

@dataclass
class Memory:
    size: int

    def __post_init__(self):
        self.data = bytearray(self.size)

    def write(self, address: int, data: bytes) -> None:
        if address < 0 or address + len(data) > self.size:
            raise ValueError("Memory write is outside the valid address range.")
        self.data[address:address + len(data)] = data

    def read(self, address: int, length: int) -> bytes:
        if address < 0 or address + length > self.size:
            raise ValueError("Memory read is outside the valid address range.")
        return bytes(self.data[address:address + length])


class DMAController:
    """
    Simplified DMA engine.

    CPU responsibilities:
        1. Configure source/destination/count.
        2. Start transfer.
        3. Respond to completion interrupt.

    DMA responsibilities:
        1. Transfer data.
        2. Update transfer state.
        3. Notify CPU when complete.
    """

    def __init__(self, memory: Memory, interrupt_controller: InterruptController):
        self.memory = memory
        self.interrupt_controller = interrupt_controller
        self.busy = False
        self.bytes_transferred = 0

    def transfer_device_to_memory(
        self,
        device_data: bytes,
        destination_address: int
    ) -> None:
        if self.busy:
            raise RuntimeError("DMA engine is already busy.")

        self.busy = True
        self.bytes_transferred = 0

        try:
            self.memory.write(destination_address, device_data)
            self.bytes_transferred = len(device_data)
        finally:
            self.busy = False

        self.interrupt_controller.raise_interrupt("DMA")

    def transfer_memory_to_device(
        self,
        source_address: int,
        length: int
    ) -> bytes:
        if self.busy:
            raise RuntimeError("DMA engine is already busy.")

        self.busy = True

        try:
            data = self.memory.read(source_address, length)
            self.bytes_transferred = length
            return data
        finally:
            self.busy = False
            self.interrupt_controller.raise_interrupt("DMA")


def demonstrate_dma() -> None:
    section("7. DIRECT MEMORY ACCESS")

    memory = Memory(1024)
    interrupt_controller = InterruptController()
    dma = DMAController(memory, interrupt_controller)

    device_payload = b"Large block transferred by DMA"

    print("Device provides:", device_payload)

    dma.transfer_device_to_memory(device_payload, 128)

    print("DMA bytes transferred:", dma.bytes_transferred)
    print("Memory contains:", memory.read(128, len(device_payload)))

    if interrupt_controller.has_interrupt():
        print("CPU receives:", interrupt_controller.acknowledge())


# ============================================================================
# 8. BUSES
# ============================================================================

class Bus:
    """
    Simplified shared bus.

    A real bus involves electrical/physical signaling, arbitration,
    addressing, protocol rules, timing, bandwidth, and error mechanisms.
    """

    def __init__(self, bandwidth_mb_s: float):
        self.bandwidth_mb_s = bandwidth_mb_s
        self.owner: Optional[str] = None

    def acquire(self, requester: str) -> bool:
        if self.owner is not None:
            return False
        self.owner = requester
        return True

    def release(self, requester: str) -> None:
        if self.owner != requester:
            raise RuntimeError("Requester does not own the bus.")
        self.owner = None

    def transfer_time_seconds(self, megabytes: float) -> float:
        if self.bandwidth_mb_s <= 0:
            raise ValueError("Bus bandwidth must be positive.")
        return megabytes / self.bandwidth_mb_s


def demonstrate_bus() -> None:
    section("8. BUSES")

    bus = Bus(1000)

    if bus.acquire("DMA_CONTROLLER"):
        print("DMA controller acquired the bus.")
        print(
            "Transfer time for 250 MB:",
            bus.transfer_time_seconds(250),
            "seconds"
        )
        bus.release("DMA_CONTROLLER")

    if bus.acquire("CPU"):
        print("CPU acquired the bus.")
        bus.release("CPU")


# ============================================================================
# 9. BUFFERING
# ============================================================================

class Buffer:
    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("Buffer capacity must be positive.")

        self.capacity = capacity
        self.queue: Deque[bytes] = deque()

    def write(self, data: bytes) -> bool:
        if len(self.queue) >= self.capacity:
            return False
        self.queue.append(data)
        return True

    def read(self) -> Optional[bytes]:
        if not self.queue:
            return None
        return self.queue.popleft()

    def __len__(self) -> int:
        return len(self.queue)


def demonstrate_buffering() -> None:
    section("9. BUFFERING")

    buffer = Buffer(3)

    for payload in [b"A", b"B", b"C", b"D"]:
        accepted = buffer.write(payload)
        print(
            f"Write {payload!r}: "
            f"{'accepted' if accepted else 'buffer full'}"
        )

    while len(buffer):
        print("Read:", buffer.read())


# ============================================================================
# 10. I/O QUEUES
# ============================================================================

@dataclass
class IORequest:
    request_id: int
    operation: str
    size_bytes: int
    address: int


class IOQueue:
    def __init__(self):
        self.requests: Deque[IORequest] = deque()

    def submit(self, request: IORequest) -> None:
        self.requests.append(request)

    def next_request(self) -> Optional[IORequest]:
        if not self.requests:
            return None
        return self.requests.popleft()

    def __len__(self) -> int:
        return len(self.requests)


def demonstrate_io_queue() -> None:
    section("10. I/O QUEUES")

    queue = IOQueue()

    for request in [
        IORequest(1, "READ", 4096, 100),
        IORequest(2, "WRITE", 8192, 200),
        IORequest(3, "READ", 16384, 500),
    ]:
        queue.submit(request)

    while len(queue):
        request = queue.next_request()
        print(
            f"Processing request {request.request_id}: "
            f"{request.operation} {request.size_bytes} bytes "
            f"at address {request.address}"
        )


# ============================================================================
# 11. ASYNCHRONOUS I/O SIMULATION
# ============================================================================

@dataclass
class AsyncOperation:
    operation_id: int
    duration: float
    callback: Callable[[int], None]
    elapsed: float = 0.0
    complete: bool = False

    def update(self, delta: float) -> None:
        if self.complete:
            return

        self.elapsed += delta

        if self.elapsed >= self.duration:
            self.complete = True
            self.callback(self.operation_id)


def demonstrate_async_io() -> None:
    section("11. ASYNCHRONOUS I/O")

    completed: List[int] = []

    def completion_callback(operation_id: int) -> None:
        completed.append(operation_id)
        print(f"Completion interrupt/event for operation {operation_id}")

    operations = [
        AsyncOperation(1, 0.2, completion_callback),
        AsyncOperation(2, 0.5, completion_callback),
    ]

    simulated_time = 0.0

    while not all(operation.complete for operation in operations):
        step = 0.1
        simulated_time += step

        for operation in operations:
            operation.update(step)

    print("Completed operations:", completed)


# ============================================================================
# 12. ERROR HANDLING
# ============================================================================

class IOErrorType(Enum):
    TIMEOUT = auto()
    DEVICE_FAILURE = auto()
    INVALID_ADDRESS = auto()
    BUFFER_OVERFLOW = auto()
    PERMISSION_DENIED = auto()


def safe_memory_access() -> None:
    section("12. I/O ERRORS AND FAILURE CONDITIONS")

    memory = Memory(32)

    try:
        memory.read(28, 8)
    except ValueError as error:
        print("Caught invalid address:", error)

    print(
        "Important I/O failures include timeouts, device errors, "
        "invalid addresses, overflows, permissions, and protocol failures."
    )


# ============================================================================
# 13. PERFORMANCE MODEL
# ============================================================================

def estimate_io_time(
    data_mb: float,
    device_rate_mb_s: float,
    bus_rate_mb_s: float,
    latency_ms: float,
) -> float:
    """
    Approximate end-to-end transfer time.

    A simplified serial bottleneck model is used:
        effective rate = min(device rate, bus rate)

    Real systems can overlap latency, bus transactions, DMA, caching,
    queueing, and computation, so this is an educational approximation.
    """
    if data_mb < 0:
        raise ValueError("Data size cannot be negative.")

    if device_rate_mb_s <= 0 or bus_rate_mb_s <= 0:
        raise ValueError("Transfer rates must be positive.")

    effective_rate = min(device_rate_mb_s, bus_rate_mb_s)

    return latency_ms / 1000 + data_mb / effective_rate


def demonstrate_performance() -> None:
    section("13. I/O PERFORMANCE")

    scenarios = [
        ("Slow device", 100, 1000, 5),
        ("Fast device / slower bus", 5000, 1000, 1),
        ("Fast bus / slower device", 1000, 5000, 1),
    ]

    for name, device_rate, bus_rate, latency in scenarios:
        seconds = estimate_io_time(100, device_rate, bus_rate, latency)

        print(
            f"{name}: {seconds:.6f} seconds for 100 MB"
        )

    print(
        "\nImportant performance factors include bandwidth, latency, "
        "queue depth, transaction size, CPU overhead, interrupts, DMA, "
        "buffering, contention, and device characteristics."
    )


# ============================================================================
# 14. CACHE AND BUFFERING EFFECT
# ============================================================================

class ReadCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache: Dict[int, bytes] = {}
        self.order: Deque[int] = deque()

    def get(self, address: int) -> Optional[bytes]:
        if address not in self.cache:
            return None

        self.order.remove(address)
        self.order.append(address)
        return self.cache[address]

    def put(self, address: int, data: bytes) -> None:
        if address in self.cache:
            self.order.remove(address)

        self.cache[address] = data
        self.order.append(address)

        while len(self.order) > self.capacity:
            oldest = self.order.popleft()
            del self.cache[oldest]


def demonstrate_cache() -> None:
    section("14. CACHING")

    cache = ReadCache(2)

    cache.put(100, b"Block A")
    cache.put(200, b"Block B")

    print("Cache hit:", cache.get(100))
    print("Cache miss:", cache.get(300))

    cache.put(300, b"Block C")

    print("After eviction, address 200:", cache.get(200))
    print("Address 100:", cache.get(100))
    print("Address 300:", cache.get(300))


# ============================================================================
# 15. DEVICE DRIVER MODEL
# ============================================================================

class DeviceDriver:
    """
    Simplified driver abstraction.

    A real driver often manages:
        - device initialization
        - register programming
        - queues
        - DMA descriptors
        - interrupts
        - synchronization
        - error recovery
        - power management
        - security boundaries
    """

    def __init__(self, controller: Controller):
        self.controller = controller

    def read(self) -> bytes:
        self.controller.write_command("READ")
        self.controller.execute()

        if self.controller.status != "COMPLETE":
            raise IOError(self.controller.error or "Read failed")

        return self.controller.data_register or b""

    def write(self, data: bytes) -> None:
        self.controller.write_command("WRITE")
        self.controller.write_data(data)
        self.controller.execute()

        if self.controller.status != "COMPLETE":
            raise IOError(self.controller.error or "Write failed")


def demonstrate_driver() -> None:
    section("15. DEVICE DRIVERS")

    device = Device("Driver Demo SSD", DeviceType.STORAGE, 3500, 0.08)
    controller = Controller(device)
    driver = DeviceDriver(controller)

    driver.write(b"Operating system request")
    print("Driver write completed.")

    result = driver.read()
    print("Driver read returned:", result)


# ============================================================================
# 16. COMPLETE I/O PIPELINE
# ============================================================================

@dataclass
class IOCompletion:
    request_id: int
    status: str
    bytes_transferred: int


class IOSubsystem:
    """
    Integrated simulation:

        Application
             |
        Operating System
             |
        Device Driver
             |
        I/O Queue
             |
        Controller
             |
        DMA Engine
             |
        Bus
             |
        Device
    """

    def __init__(self):
        self.memory = Memory(8192)
        self.interrupts = InterruptController()
        self.dma = DMAController(self.memory, self.interrupts)
        self.bus = Bus(2000)

        self.completed: List[IOCompletion] = []

    def process_read(self, request: IORequest, device_data: bytes) -> None:
        if request.size_bytes != len(device_data):
            raise ValueError("Request size does not match device payload.")

        if not self.bus.acquire("DMA"):
            raise RuntimeError("Bus is busy.")

        try:
            self.dma.transfer_device_to_memory(
                device_data,
                request.address
            )
        finally:
            self.bus.release("DMA")

        interrupt = self.interrupts.acknowledge()

        if interrupt != "DMA":
            raise RuntimeError("Expected DMA completion interrupt.")

        self.completed.append(
            IOCompletion(
                request.request_id,
                "SUCCESS",
                len(device_data)
            )
        )

    def show_status(self) -> None:
        for completion in self.completed:
            print(
                f"Request {completion.request_id}: "
                f"{completion.status}, "
                f"{completion.bytes_transferred} bytes"
            )


def demonstrate_complete_pipeline() -> None:
    section("16. COMPLETE I/O SUBSYSTEM PIPELINE")

    subsystem = IOSubsystem()

    request = IORequest(
        request_id=101,
        operation="READ",
        size_bytes=15,
        address=1024,
    )

    device_data = b"Hello I/O World"

    print("Application submits request.")
    print("OS places request into I/O subsystem.")
    print("Driver/controller prepares DMA.")
    print("DMA transfers device data into memory.")
    print("DMA raises completion interrupt.")

    subsystem.process_read(request, device_data)

    print("Memory result:", subsystem.memory.read(1024, 15))
    subsystem.show_status()


# ============================================================================
# 17. SECURITY CONSIDERATIONS
# ============================================================================

def security_considerations() -> None:
    section("17. I/O SECURITY CONSIDERATIONS")

    controls = [
        "Validate device and user-provided addresses.",
        "Restrict DMA to authorized memory regions.",
        "Use IOMMU-style isolation where supported.",
        "Validate buffer lengths before transfers.",
        "Avoid exposing privileged device registers to untrusted applications.",
        "Protect firmware and controller configuration.",
        "Handle malformed device responses.",
        "Apply least privilege to device access.",
        "Prevent interrupt storms and resource exhaustion.",
        "Sanitize data received from external devices.",
    ]

    for number, control in enumerate(controls, start=1):
        print(f"{number:02}. {control}")


# ============================================================================
# 18. EDGE CASES
# ============================================================================

def demonstrate_edge_cases() -> None:
    section("18. EDGE CASES")

    memory = Memory(16)

    tests = [
        ("Negative address", lambda: memory.read(-1, 1)),
        ("Read beyond end", lambda: memory.read(15, 2)),
        ("Zero-length read", lambda: memory.read(4, 0)),
    ]

    for name, operation in tests:
        try:
            result = operation()
            print(f"{name}: accepted, result={result!r}")
        except ValueError as error:
            print(f"{name}: rejected -> {error}")


# ============================================================================
# 19. COMPARISON TABLE
# ============================================================================

def comparison_table() -> None:
    section("19. I/O TECHNIQUE COMPARISON")

    rows = [
        ("Polling", "CPU repeatedly checks status", "Simple", "CPU overhead"),
        ("Interrupt I/O", "Device notifies CPU", "Efficient for events", "Interrupt overhead"),
        ("DMA", "Controller transfers blocks", "Low CPU overhead", "More hardware complexity"),
        ("Buffering", "Temporary storage absorbs timing differences", "Smooths producer/consumer rates", "Consumes memory"),
        ("Caching", "Frequently reused data kept nearby", "Reduces device accesses", "Stale-data/coherence concerns"),
    ]

    print(f"{'Technique':<18} {'Mechanism':<48} {'Benefit':<30} Limitation")
    print("-" * 135)

    for row in rows:
        print(f"{row[0]:<18} {row[1]:<48} {row[2]:<30} {row[3]}")


# ============================================================================
# 20. TESTS
# ============================================================================

def run_tests() -> None:
    section("20. SELF-TESTS")

    memory = Memory(100)
    memory.write(10, b"abc")
    assert memory.read(10, 3) == b"abc"

    bus = Bus(100)
    assert bus.acquire("CPU")
    assert not bus.acquire("DMA")
    bus.release("CPU")
    assert bus.acquire("DMA")
    bus.release("DMA")

    controller = InterruptController()
    controller.raise_interrupt("DEVICE")
    assert controller.acknowledge() == "DEVICE"
    assert not controller.has_interrupt()

    buffer = Buffer(1)
    assert buffer.write(b"A")
    assert not buffer.write(b"B")
    assert buffer.read() == b"A"
    assert buffer.read() is None

    print("All self-tests passed.")


# ============================================================================
# 21. STUDY CHECKLIST
# ============================================================================

def study_checklist() -> None:
    section("21. STUDY CHECKLIST")

    checklist = [
        "Understand input versus output devices.",
        "Understand device controllers and registers.",
        "Understand device drivers.",
        "Understand programmed I/O.",
        "Understand polling.",
        "Understand interrupt-driven I/O.",
        "Understand interrupt priority.",
        "Understand DMA.",
        "Understand buses and arbitration.",
        "Understand buffering and caching.",
        "Understand asynchronous I/O.",
        "Understand I/O queues.",
        "Understand latency and bandwidth.",
        "Understand error handling.",
        "Understand DMA security and memory isolation.",
        "Understand the complete application-to-device data path.",
    ]

    for item in checklist:
        print("[ ]", item)


# ============================================================================
# 22. MAIN PROGRAM
# ============================================================================

def main() -> None:
    """
    Execute the educational demonstrations.

    The first demonstration accepts interactive input. The remaining
    demonstrations are deterministic and can be executed repeatedly.
    """

    print("INPUT AND OUTPUT SYSTEMS")
    print("Devices | Controllers | Interrupts | DMA | Buses")
    print("Educational executable study program")

    explain_fundamentals()

    # Interactive input is kept separate so the remaining study examples
    # can also be reused in automated environments.
    demonstrate_basic_io()

    demonstrate_device_types()
    demonstrate_controller()
    compare_polling_and_interrupts()
    interrupt_priority_demo()
    demonstrate_dma()
    demonstrate_bus()
    demonstrate_buffering()
    demonstrate_io_queue()
    demonstrate_async_io()
    safe_memory_access()
    demonstrate_performance()
    demonstrate_cache()
    demonstrate_driver()
    demonstrate_complete_pipeline()
    security_considerations()
    demonstrate_edge_cases()
    comparison_table()
    run_tests()
    study_checklist()

    section("END OF I/O STUDY PROGRAM")
    print("The demonstrations covered the I/O path from application request")
    print("through software, controllers, buses, DMA, memory, and interrupts.")


if __name__ == "__main__":
    main()
