/*
 * INPUT AND OUTPUT SYSTEMS
 * =========================
 *
 * Technical case study:
 * A simplified operating-system storage I/O subsystem demonstrating
 * devices, controllers, registers, interrupts, DMA, buses, queues,
 * buffering, validation, error handling, and performance.
 *
 * Standard: C++17
 */

#include <algorithm>
#include <cassert>
#include <chrono>
#include <cstdint>
#include <deque>
#include <exception>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <optional>
#include <queue>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>


// ============================================================================
// 1. DEVICE TYPES
// ============================================================================

enum class DeviceType {
    Input,
    Output,
    Storage,
    Network,
    Mixed
};

std::string deviceTypeToString(DeviceType type) {
    switch (type) {
        case DeviceType::Input:
            return "Input";
        case DeviceType::Output:
            return "Output";
        case DeviceType::Storage:
            return "Storage";
        case DeviceType::Network:
            return "Network";
        case DeviceType::Mixed:
            return "Mixed";
    }

    return "Unknown";
}


// ============================================================================
// 2. DEVICE
// ============================================================================

class Device {
private:
    std::string name_;
    DeviceType type_;
    double transferRateMBps_;
    double latencyMs_;
    std::size_t blockSize_;

public:
    Device(
        std::string name,
        DeviceType type,
        double transferRateMBps,
        double latencyMs,
        std::size_t blockSize
    )
        : name_(std::move(name)),
          type_(type),
          transferRateMBps_(transferRateMBps),
          latencyMs_(latencyMs),
          blockSize_(blockSize) {

        if (name_.empty()) {
            throw std::invalid_argument("Device name cannot be empty.");
        }

        if (transferRateMBps_ <= 0.0) {
            throw std::invalid_argument(
                "Device transfer rate must be positive."
            );
        }

        if (latencyMs_ < 0.0) {
            throw std::invalid_argument(
                "Device latency cannot be negative."
            );
        }
    }

    const std::string& name() const {
        return name_;
    }

    double transferRateMBps() const {
        return transferRateMBps_;
    }

    double latencyMs() const {
        return latencyMs_;
    }

    std::size_t blockSize() const {
        return blockSize_;
    }

    void describe() const {
        std::cout
            << "Device: " << name_
            << ", type=" << deviceTypeToString(type_)
            << ", rate=" << transferRateMBps_ << " MB/s"
            << ", latency=" << latencyMs_ << " ms"
            << ", block=" << blockSize_ << " bytes\n";
    }
};


// ============================================================================
// 3. MEMORY
// ============================================================================

class Memory {
private:
    std::vector<std::uint8_t> bytes_;

    void validateRange(
        std::size_t address,
        std::size_t length
    ) const {
        if (address > bytes_.size()) {
            throw std::out_of_range("Memory address is outside memory.");
        }

        if (length > bytes_.size() - address) {
            throw std::out_of_range(
                "Memory operation exceeds available memory."
            );
        }
    }

public:
    explicit Memory(std::size_t size)
        : bytes_(size, 0) {

        if (size == 0) {
            throw std::invalid_argument(
                "Memory size must be greater than zero."
            );
        }
    }

    std::size_t size() const {
        return bytes_.size();
    }

    void write(
        std::size_t address,
        const std::vector<std::uint8_t>& data
    ) {
        validateRange(address, data.size());

        std::copy(
            data.begin(),
            data.end(),
            bytes_.begin() + static_cast<std::ptrdiff_t>(address)
        );
    }

    std::vector<std::uint8_t> read(
        std::size_t address,
        std::size_t length
    ) const {
        validateRange(address, length);

        return std::vector<std::uint8_t>(
            bytes_.begin() + static_cast<std::ptrdiff_t>(address),
            bytes_.begin()
                + static_cast<std::ptrdiff_t>(address + length)
        );
    }
};


// ============================================================================
// 4. DEVICE CONTROLLER AND REGISTERS
// ============================================================================

enum class ControllerStatus {
    Idle,
    CommandReceived,
    DataReady,
    Busy,
    Complete,
    Error
};

std::string statusToString(ControllerStatus status) {
    switch (status) {
        case ControllerStatus::Idle:
            return "IDLE";
        case ControllerStatus::CommandReceived:
            return "COMMAND_RECEIVED";
        case ControllerStatus::DataReady:
            return "DATA_READY";
        case ControllerStatus::Busy:
            return "BUSY";
        case ControllerStatus::Complete:
            return "COMPLETE";
        case ControllerStatus::Error:
            return "ERROR";
    }

    return "UNKNOWN";
}

class DeviceController {
private:
    Device& device_;

    ControllerStatus status_ = ControllerStatus::Idle;

    std::string command_;
    std::vector<std::uint8_t> dataRegister_;

    std::string errorMessage_;

public:
    explicit DeviceController(Device& device)
        : device_(device) {}

    void writeCommand(const std::string& command) {
        if (command != "READ" && command != "WRITE") {
            status_ = ControllerStatus::Error;
            errorMessage_ = "Unsupported command.";
            throw std::invalid_argument(errorMessage_);
        }

        command_ = command;
        status_ = ControllerStatus::CommandReceived;
        errorMessage_.clear();
    }

    void writeData(const std::vector<std::uint8_t>& data) {
        dataRegister_ = data;
        status_ = ControllerStatus::DataReady;
    }

    void execute() {
        if (command_.empty()) {
            status_ = ControllerStatus::Error;
            errorMessage_ = "No command has been configured.";
            return;
        }

        status_ = ControllerStatus::Busy;

        if (command_ == "READ") {
            const std::string message = "DEVICE-DATA";

            dataRegister_ = std::vector<std::uint8_t>(
                message.begin(),
                message.end()
            );

            status_ = ControllerStatus::Complete;
            return;
        }

        if (command_ == "WRITE") {
            if (dataRegister_.empty()) {
                status_ = ControllerStatus::Error;
                errorMessage_ = "No write data was supplied.";
                return;
            }

            status_ = ControllerStatus::Complete;
        }
    }

    ControllerStatus status() const {
        return status_;
    }

    const std::vector<std::uint8_t>& dataRegister() const {
        return dataRegister_;
    }

    const std::string& errorMessage() const {
        return errorMessage_;
    }

    const Device& device() const {
        return device_;
    }
};


// ============================================================================
// 5. INTERRUPTS
// ============================================================================

struct InterruptRequest {
    int priority;
    std::string source;
    std::string description;

    bool operator<(const InterruptRequest& other) const {
        // std::priority_queue places the "largest" item first.
        // Reverse comparison makes a smaller number more urgent.
        return priority > other.priority;
    }
};

class InterruptController {
private:
    std::priority_queue<InterruptRequest> pending_;

public:
    void raise(
        std::string source,
        int priority,
        std::string description
    ) {
        pending_.push({
            priority,
            std::move(source),
            std::move(description)
        });
    }

    bool hasPending() const {
        return !pending_.empty();
    }

    InterruptRequest acknowledge() {
        if (pending_.empty()) {
            throw std::runtime_error(
                "No interrupt is pending."
            );
        }

        InterruptRequest request = pending_.top();
        pending_.pop();

        return request;
    }
};


// ============================================================================
// 6. BUS AND ARBITRATION
// ============================================================================

class Bus {
private:
    std::string name_;
    double bandwidthMBps_;
    std::optional<std::string> owner_;

public:
    Bus(std::string name, double bandwidthMBps)
        : name_(std::move(name)),
          bandwidthMBps_(bandwidthMBps) {

        if (bandwidthMBps_ <= 0.0) {
            throw std::invalid_argument(
                "Bus bandwidth must be positive."
            );
        }
    }

    bool acquire(const std::string& requester) {
        if (owner_.has_value()) {
            return false;
        }

        owner_ = requester;
        return true;
    }

    void release(const std::string& requester) {
        if (!owner_.has_value() || owner_.value() != requester) {
            throw std::logic_error(
                "Requester does not own the bus."
            );
        }

        owner_.reset();
    }

    double transferTimeSeconds(double megabytes) const {
        if (megabytes < 0.0) {
            throw std::invalid_argument(
                "Transfer size cannot be negative."
            );
        }

        return megabytes / bandwidthMBps_;
    }

    const std::string& name() const {
        return name_;
    }
};


// ============================================================================
// 7. DMA CONTROLLER
// ============================================================================

class DMAController {
private:
    Memory& memory_;
    InterruptController& interrupts_;

    bool busy_ = false;
    std::size_t bytesTransferred_ = 0;

public:
    DMAController(
        Memory& memory,
        InterruptController& interrupts
    )
        : memory_(memory),
          interrupts_(interrupts) {}

    void deviceToMemory(
        const std::vector<std::uint8_t>& deviceData,
        std::size_t destinationAddress
    ) {
        if (busy_) {
            throw std::runtime_error(
                "DMA controller is already busy."
            );
        }

        busy_ = true;

        try {
            memory_.write(destinationAddress, deviceData);
            bytesTransferred_ = deviceData.size();
        } catch (...) {
            busy_ = false;
            throw;
        }

        busy_ = false;

        interrupts_.raise(
            "DMA",
            3,
            "Device-to-memory transfer completed"
        );
    }

    std::vector<std::uint8_t> memoryToDevice(
        std::size_t sourceAddress,
        std::size_t length
    ) {
        if (busy_) {
            throw std::runtime_error(
                "DMA controller is already busy."
            );
        }

        busy_ = true;

        std::vector<std::uint8_t> result;

        try {
            result = memory_.read(sourceAddress, length);
            bytesTransferred_ = length;
        } catch (...) {
            busy_ = false;
            throw;
        }

        busy_ = false;

        interrupts_.raise(
            "DMA",
            3,
            "Memory-to-device transfer completed"
        );

        return result;
    }

    std::size_t bytesTransferred() const {
        return bytesTransferred_;
    }

    bool busy() const {
        return busy_;
    }
};


// ============================================================================
// 8. I/O REQUEST
// ============================================================================

enum class IOOperation {
    Read,
    Write
};

std::string operationToString(IOOperation operation) {
    return operation == IOOperation::Read ? "READ" : "WRITE";
}

struct IORequest {
    std::uint64_t id;
    IOOperation operation;
    std::size_t memoryAddress;
    std::size_t size;
};

class IOQueue {
private:
    std::deque<IORequest> requests_;

public:
    void submit(const IORequest& request) {
        if (request.id == 0) {
            throw std::invalid_argument(
                "Request ID cannot be zero."
            );
        }

        if (request.size == 0) {
            throw std::invalid_argument(
                "I/O request size must be greater than zero."
            );
        }

        requests_.push_back(request);
    }

    bool empty() const {
        return requests_.empty();
    }

    IORequest next() {
        if (requests_.empty()) {
            throw std::runtime_error(
                "I/O queue is empty."
            );
        }

        IORequest request = requests_.front();
        requests_.pop_front();

        return request;
    }

    std::size_t size() const {
        return requests_.size();
    }
};


// ============================================================================
// 9. BUFFER
// ============================================================================

class IOBuffer {
private:
    std::size_t capacity_;
    std::deque<std::vector<std::uint8_t>> entries_;

public:
    explicit IOBuffer(std::size_t capacity)
        : capacity_(capacity) {

        if (capacity_ == 0) {
            throw std::invalid_argument(
                "Buffer capacity must be greater than zero."
            );
        }
    }

    bool write(const std::vector<std::uint8_t>& data) {
        if (entries_.size() >= capacity_) {
            return false;
        }

        entries_.push_back(data);
        return true;
    }

    std::optional<std::vector<std::uint8_t>> read() {
        if (entries_.empty()) {
            return std::nullopt;
        }

        auto value = entries_.front();
        entries_.pop_front();

        return value;
    }

    std::size_t size() const {
        return entries_.size();
    }
};


// ============================================================================
// 10. COMPLETION RECORD
// ============================================================================

struct IOCompletion {
    std::uint64_t requestId;
    bool success;
    std::size_t bytesTransferred;
    std::string message;
};


// ============================================================================
// 11. INTEGRATED STORAGE I/O SUBSYSTEM
// ============================================================================

class StorageIOSubsystem {
private:
    Device device_;
    DeviceController controller_;

    Memory memory_;
    InterruptController interrupts_;
    DMAController dma_;
    Bus bus_;

    IOQueue queue_;

    std::vector<IOCompletion> completions_;

public:
    StorageIOSubsystem()
        : device_(
              "Case Study SSD",
              DeviceType::Storage,
              3500.0,
              0.08,
              4096
          ),
          controller_(device_),
          memory_(64 * 1024),
          interrupts_(),
          dma_(memory_, interrupts_),
          bus_("SYSTEM_BUS", 2000.0) {}

    void submit(const IORequest& request) {
        // The operating system places an application request into
        // an I/O queue instead of forcing the application to control
        // hardware registers directly.
        queue_.submit(request);
    }

    void processRead(
        const IORequest& request,
        const std::vector<std::uint8_t>& deviceData
    ) {
        if (request.operation != IOOperation::Read) {
            throw std::invalid_argument(
                "processRead requires a READ request."
            );
        }

        if (request.size != deviceData.size()) {
            throw std::invalid_argument(
                "Request size and device data size differ."
            );
        }

        // A DMA engine must only access a permitted memory region.
        // Memory::write performs the final range validation.
        if (!bus_.acquire("DMA")) {
            throw std::runtime_error(
                "System bus is currently occupied."
            );
        }

        try {
            dma_.deviceToMemory(
                deviceData,
                request.memoryAddress
            );

            bus_.release("DMA");
        } catch (...) {
            bus_.release("DMA");
            throw;
        }

        InterruptRequest completionInterrupt =
            interrupts_.acknowledge();

        if (completionInterrupt.source != "DMA") {
            throw std::runtime_error(
                "Unexpected interrupt source."
            );
        }

        completions_.push_back({
            request.id,
            true,
            deviceData.size(),
            "DMA read completed"
        });
    }

    void processNext(
        const std::vector<std::uint8_t>& simulatedDeviceData
    ) {
        if (queue_.empty()) {
            return;
        }

        IORequest request = queue_.next();

        if (request.operation == IOOperation::Read) {
            processRead(request, simulatedDeviceData);
            return;
        }

        throw std::runtime_error(
            "WRITE processing is not part of this read case study."
        );
    }

    const Memory& memory() const {
        return memory_;
    }

    const std::vector<IOCompletion>& completions() const {
        return completions_;
    }

    const Device& device() const {
        return device_;
    }
};


// ============================================================================
// 12. PERFORMANCE MODEL
// ============================================================================

double estimateTransferTime(
    double sizeMB,
    double deviceRateMBps,
    double busRateMBps,
    double latencyMs
) {
    if (sizeMB < 0.0) {
        throw std::invalid_argument(
            "Size cannot be negative."
        );
    }

    if (deviceRateMBps <= 0.0 || busRateMBps <= 0.0) {
        throw std::invalid_argument(
            "Transfer rates must be positive."
        );
    }

    if (latencyMs < 0.0) {
        throw std::invalid_argument(
            "Latency cannot be negative."
        );
    }

    const double effectiveRate =
        std::min(deviceRateMBps, busRateMBps);

    return latencyMs / 1000.0
        + sizeMB / effectiveRate;
}


// ============================================================================
// 13. SECURITY VALIDATION
// ============================================================================

void validateDMARegion(
    const Memory& memory,
    std::size_t address,
    std::size_t length
) {
    if (address > memory.size()) {
        throw std::out_of_range(
            "DMA address is outside memory."
        );
    }

    if (length > memory.size() - address) {
        throw std::out_of_range(
            "DMA region exceeds permitted memory."
        );
    }
}


// ============================================================================
// 14. UTILITY FUNCTIONS
// ============================================================================

std::vector<std::uint8_t> toBytes(const std::string& text) {
    return std::vector<std::uint8_t>(
        text.begin(),
        text.end()
    );
}

std::string toString(
    const std::vector<std::uint8_t>& bytes
) {
    return std::string(
        bytes.begin(),
        bytes.end()
    );
}


// ============================================================================
// 15. CASE STUDY EXECUTION
// ============================================================================

void runCaseStudy() {
    std::cout << "============================================================\n";
    std::cout << "STORAGE I/O SUBSYSTEM CASE STUDY\n";
    std::cout << "============================================================\n\n";

    StorageIOSubsystem subsystem;

    subsystem.device().describe();

    std::cout << "\nApplication creates an I/O request.\n";

    const std::string payloadText =
        "Hello I/O World";

    const auto devicePayload = toBytes(payloadText);

    IORequest request{
        1001,
        IOOperation::Read,
        8192,
        devicePayload.size()
    };

    subsystem.submit(request);

    std::cout
        << "Request ID: "
        << request.id
        << "\nOperation: "
        << operationToString(request.operation)
        << "\nMemory address: "
        << request.memoryAddress
        << "\nRequested bytes: "
        << request.size
        << "\n";

    std::cout << "\nI/O pipeline:\n";
    std::cout << "Application\n";
    std::cout << "    -> Operating System\n";
    std::cout << "    -> I/O Queue\n";
    std::cout << "    -> Device Controller\n";
    std::cout << "    -> DMA Controller\n";
    std::cout << "    -> System Bus\n";
    std::cout << "    -> Memory\n";

    std::cout << "\nProcessing request...\n";

    subsystem.processNext(devicePayload);

    const auto memoryResult =
        subsystem.memory().read(
            request.memoryAddress,
            request.size
        );

    std::cout
        << "Memory contains: "
        << toString(memoryResult)
        << "\n";

    for (const auto& completion : subsystem.completions()) {
        std::cout
            << "Completion: request="
            << completion.requestId
            << ", success="
            << std::boolalpha
            << completion.success
            << ", bytes="
            << completion.bytesTransferred
            << ", message="
            << completion.message
            << "\n";
    }
}


// ============================================================================
// 16. POLLING VERSUS INTERRUPTS
// ============================================================================

void demonstratePolling() {
    std::cout << "\n============================================================\n";
    std::cout << "POLLING\n";
    std::cout << "============================================================\n";

    int checks = 0;
    constexpr int readyAfter = 4;

    bool ready = false;

    while (!ready) {
        ++checks;

        std::cout
            << "CPU checks device: "
            << checks
            << "\n";

        if (checks >= readyAfter) {
            ready = true;
        }
    }

    std::cout << "Device became ready.\n";
}


void demonstrateInterrupts() {
    std::cout << "\n============================================================\n";
    std::cout << "INTERRUPTS\n";
    std::cout << "============================================================\n";

    InterruptController controller;

    controller.raise(
        "KEYBOARD",
        5,
        "Key available"
    );

    controller.raise(
        "NETWORK",
        2,
        "Incoming packet"
    );

    controller.raise(
        "THERMAL_SENSOR",
        1,
        "Critical temperature"
    );

    while (controller.hasPending()) {
        auto interrupt = controller.acknowledge();

        std::cout
            << "Servicing "
            << interrupt.source
            << ", priority="
            << interrupt.priority
            << ", event="
            << interrupt.description
            << "\n";
    }
}


// ============================================================================
// 17. DMA DEMONSTRATION
// ============================================================================

void demonstrateDMA() {
    std::cout << "\n============================================================\n";
    std::cout << "DMA\n";
    std::cout << "============================================================\n";

    Memory memory(1024);
    InterruptController interrupts;
    DMAController dma(memory, interrupts);

    const auto data = toBytes(
        "Large block moved without CPU copying each byte."
    );

    dma.deviceToMemory(data, 128);

    const auto result =
        memory.read(128, data.size());

    std::cout
        << "Transferred: "
        << toString(result)
        << "\n";

    if (interrupts.hasPending()) {
        auto interrupt = interrupts.acknowledge();

        std::cout
            << "CPU receives completion interrupt from "
            << interrupt.source
            << "\n";
    }
}


// ============================================================================
// 18. BUFFERING
// ============================================================================

void demonstrateBuffering() {
    std::cout << "\n============================================================\n";
    std::cout << "BUFFERING\n";
    std::cout << "============================================================\n";

    IOBuffer buffer(2);

    buffer.write(toBytes("A"));
    buffer.write(toBytes("B"));

    const bool accepted =
        buffer.write(toBytes("C"));

    std::cout
        << "Third item accepted: "
        << std::boolalpha
        << accepted
        << "\n";

    while (buffer.size() > 0) {
        auto value = buffer.read();

        if (value.has_value()) {
            std::cout
                << "Read buffered value: "
                << toString(value.value())
                << "\n";
        }
    }
}


// ============================================================================
// 19. PERFORMANCE ANALYSIS
// ============================================================================

void demonstratePerformance() {
    std::cout << "\n============================================================\n";
    std::cout << "PERFORMANCE MODEL\n";
    std::cout << "============================================================\n";

    const double scenarios[][4] = {
        {100.0, 100.0, 1000.0, 5.0},
        {100.0, 5000.0, 1000.0, 1.0},
        {100.0, 1000.0, 5000.0, 1.0}
    };

    for (const auto& scenario : scenarios) {
        const double size = scenario[0];
        const double deviceRate = scenario[1];
        const double busRate = scenario[2];
        const double latency = scenario[3];

        const double seconds =
            estimateTransferTime(
                size,
                deviceRate,
                busRate,
                latency
            );

        std::cout
            << "Size="
            << size
            << " MB, device="
            << deviceRate
            << " MB/s, bus="
            << busRate
            << " MB/s, time="
            << std::fixed
            << std::setprecision(6)
            << seconds
            << " s\n";
    }

    std::cout
        << "The slower transfer stage becomes the simplified bottleneck.\n";
}


// ============================================================================
// 20. ERROR AND EDGE-CASE TESTS
// ============================================================================

void demonstrateErrors() {
    std::cout << "\n============================================================\n";
    std::cout << "ERROR HANDLING AND EDGE CASES\n";
    std::cout << "============================================================\n";

    Memory memory(16);

    try {
        memory.read(15, 2);
    } catch (const std::exception& error) {
        std::cout
            << "Invalid memory access rejected: "
            << error.what()
            << "\n";
    }

    try {
        validateDMARegion(memory, 10, 10);
    } catch (const std::exception& error) {
        std::cout
            << "Invalid DMA region rejected: "
            << error.what()
            << "\n";
    }

    try {
        estimateTransferTime(
            100,
            -1,
            1000,
            1
        );
    } catch (const std::exception& error) {
        std::cout
            << "Invalid performance parameters rejected: "
            << error.what()
            << "\n";
    }
}


// ============================================================================
// 21. DEVICE DRIVER DEMONSTRATION
// ============================================================================

void demonstrateControllerAndDriver() {
    std::cout << "\n============================================================\n";
    std::cout << "CONTROLLER / DRIVER MODEL\n";
    std::cout << "============================================================\n";

    Device device(
        "Driver Test Device",
        DeviceType::Storage,
        3500.0,
        0.08,
        4096
    );

    DeviceController controller(device);

    controller.writeCommand("WRITE");
    controller.writeData(
        toBytes("Operating system data")
    );

    controller.execute();

    std::cout
        << "WRITE status: "
        << statusToString(controller.status())
        << "\n";

    controller.writeCommand("READ");
    controller.execute();

    std::cout
        << "READ status: "
        << statusToString(controller.status())
        << "\n";

    std::cout
        << "READ result: "
        << toString(controller.dataRegister())
        << "\n";
}


// ============================================================================
// 22. SELF-TESTS
// ============================================================================

void runTests() {
    std::cout << "\n============================================================\n";
    std::cout << "SELF-TESTS\n";
    std::cout << "============================================================\n";

    {
        Memory memory(100);

        memory.write(
            10,
            toBytes("abc")
        );

        assert(
            toString(memory.read(10, 3)) == "abc"
        );
    }

    {
        Bus bus("TEST_BUS", 1000);

        assert(bus.acquire("CPU"));
        assert(!bus.acquire("DMA"));

        bus.release("CPU");

        assert(bus.acquire("DMA"));
        bus.release("DMA");
    }

    {
        InterruptController interrupts;

        interrupts.raise("LOW", 5, "Low priority");
        interrupts.raise("HIGH", 1, "High priority");

        assert(
            interrupts.acknowledge().source == "HIGH"
        );
    }

    {
        IOBuffer buffer(1);

        assert(buffer.write(toBytes("A")));
        assert(!buffer.write(toBytes("B")));

        const auto result = buffer.read();

        assert(result.has_value());
        assert(toString(result.value()) == "A");
        assert(!buffer.read().has_value());
    }

    {
        const double result =
            estimateTransferTime(
                100,
                1000,
                500,
                1
            );

        assert(result > 0.0);
    }

    std::cout << "All tests passed.\n";
}


// ============================================================================
// 23. MAIN
// ============================================================================

int main() {
    try {
        runCaseStudy();
        demonstrateControllerAndDriver();
        demonstratePolling();
        demonstrateInterrupts();
        demonstrateDMA();
        demonstrateBuffering();
        demonstratePerformance();
        demonstrateErrors();
        runTests();

        std::cout
            << "\n============================================================\n"
            << "CASE STUDY COMPLETED\n"
            << "============================================================\n";

        return 0;
    }
    catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << "\n";

        return 1;
    }
}
