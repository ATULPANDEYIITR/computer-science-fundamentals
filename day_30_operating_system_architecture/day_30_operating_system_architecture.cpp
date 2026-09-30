#include <algorithm>
#include <chrono>
#include <cstddef>
#include <exception>
#include <functional>
#include <iomanip>
#include <iostream>
#include <map>
#include <memory>
#include <optional>
#include <queue>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

/*
 * Operating System Architecture Case Study
 *
 * Scenario:
 * A company is designing the governance architecture for a secure operating
 * system used by a storage appliance. The system must manage processes,
 * storage requests, device access, service isolation, and architectural
 * dependencies.
 *
 * This program models four architectural approaches:
 *
 *   Monolithic kernel
 *   Microkernel
 *   Hybrid kernel
 *   Layered architecture
 *
 * The same scenario is intentionally represented differently in each model.
 * This allows the architectural boundary, communication path, failure model,
 * and dependency structure to be examined through executable C++17 code.
 */

class ArchitectureError : public std::runtime_error {
public:
    explicit ArchitectureError(const std::string& message)
        : std::runtime_error(message) {}
};


class ValidationError : public std::runtime_error {
public:
    explicit ValidationError(const std::string& message)
        : std::runtime_error(message) {}
};


struct Process {
    int pid;
    std::string name;
    std::size_t memoryBytes;
    std::string state;
};


class MemoryManager {
private:
    std::size_t capacityBytes_;
    std::map<std::string, std::size_t> allocations_;

public:
    explicit MemoryManager(std::size_t capacityBytes)
        : capacityBytes_(capacityBytes) {
        if (capacityBytes == 0) {
            throw ValidationError("Memory capacity must be positive");
        }
    }

    std::size_t usedBytes() const {
        std::size_t total = 0;

        for (const auto& [owner, bytes] : allocations_) {
            static_cast<void>(owner);
            total += bytes;
        }

        return total;
    }

    std::size_t freeBytes() const {
        return capacityBytes_ - usedBytes();
    }

    void allocate(
        const std::string& owner,
        std::size_t bytes
    ) {
        if (owner.empty() || bytes == 0) {
            throw ValidationError("Invalid memory allocation request");
        }

        if (allocations_.contains(owner)) {
            throw ArchitectureError(
                "Memory is already assigned to " + owner
            );
        }

        if (bytes > freeBytes()) {
            throw std::runtime_error(
                "Insufficient memory for " + owner
            );
        }

        allocations_[owner] = bytes;
    }

    void release(const std::string& owner) {
        auto iterator = allocations_.find(owner);

        if (iterator == allocations_.end()) {
            throw ArchitectureError(
                "No memory allocation exists for " + owner
            );
        }

        allocations_.erase(iterator);
    }
};


class ProcessManager {
private:
    MemoryManager& memory_;
    int nextPid_ = 100;

    std::map<int, Process> processes_;

public:
    explicit ProcessManager(MemoryManager& memory)
        : memory_(memory) {}

    Process create(
        const std::string& name,
        std::size_t memoryBytes
    ) {
        if (name.empty()) {
            throw ValidationError("Process name cannot be empty");
        }

        const int pid = nextPid_++;
        const std::string owner = "process:" + std::to_string(pid);

        memory_.allocate(owner, memoryBytes);

        Process process{
            pid,
            name,
            memoryBytes,
            "ready"
        };

        processes_[pid] = process;
        return process;
    }

    void terminate(int pid) {
        auto iterator = processes_.find(pid);

        if (iterator == processes_.end()) {
            throw std::out_of_range(
                "Unknown process PID " + std::to_string(pid)
            );
        }

        memory_.release(
            "process:" + std::to_string(pid)
        );

        processes_.erase(iterator);
    }

    const std::map<int, Process>& processes() const {
        return processes_;
    }
};


class StorageService {
private:
    std::map<std::string, std::string> files_;

public:
    void createFile(
        const std::string& path,
        const std::string& content
    ) {
        if (path.empty() || path.front() != '/') {
            throw ValidationError(
                "Storage paths must be absolute"
            );
        }

        if (files_.contains(path)) {
            throw std::runtime_error(
                "File already exists: " + path
            );
        }

        files_[path] = content;
    }

    std::string readFile(const std::string& path) const {
        auto iterator = files_.find(path);

        if (iterator == files_.end()) {
            throw std::runtime_error(
                "File does not exist: " + path
            );
        }

        return iterator->second;
    }

    void writeFile(
        const std::string& path,
        const std::string& content
    ) {
        auto iterator = files_.find(path);

        if (iterator == files_.end()) {
            throw std::runtime_error(
                "File does not exist: " + path
            );
        }

        iterator->second = content;
    }
};


class DeviceService {
private:
    struct Device {
        std::string type;
        bool online;
    };

    std::map<std::string, Device> devices_{
        {"console0", {"terminal", true}},
        {"disk0", {"storage", true}},
        {"net0", {"network", true}}
    };

public:
    std::string write(
        const std::string& deviceName,
        const std::string& data
    ) const {
        auto iterator = devices_.find(deviceName);

        if (iterator == devices_.end()) {
            throw std::runtime_error(
                "Unknown device: " + deviceName
            );
        }

        if (!iterator->second.online) {
            throw std::runtime_error(
                "Device is offline: " + deviceName
            );
        }

        if (data.empty()) {
            throw ValidationError(
                "Device write data cannot be empty"
            );
        }

        return deviceName + " accepted " +
               std::to_string(data.size()) + " bytes";
    }
};


/*
 * MONOLITHIC KERNEL CASE
 *
 * The storage, device, memory, and process components are all directly
 * reachable through the kernel object. In a real monolithic kernel they
 * execute in privileged kernel space, which is not reproduced by ordinary
 * C++ process execution here.
 */
class MonolithicKernel {
private:
    MemoryManager memory_{128 * 1024 * 1024};
    ProcessManager processes_{memory_};
    StorageService storage_;
    DeviceService devices_;

public:
    Process createProcess(
        const std::string& name,
        std::size_t memoryBytes
    ) {
        return processes_.create(name, memoryBytes);
    }

    void createFile(
        const std::string& path,
        const std::string& content
    ) {
        storage_.createFile(path, content);
    }

    std::string readFile(const std::string& path) const {
        return storage_.readFile(path);
    }

    std::string writeDevice(
        const std::string& device,
        const std::string& data
    ) const {
        return devices_.write(device, data);
    }

    std::size_t freeMemory() const {
        return memory_.freeBytes();
    }
};


/*
 * MICROKERNEL CASE
 *
 * A request is represented explicitly. The service registry models user-space
 * servers and the IPC broker models the communication mechanism used to reach
 * them. The broker does not expose the internal StorageService object to the
 * client.
 */
struct IPCMessage {
    std::uint64_t id;
    std::string sender;
    std::string receiver;
    std::string operation;
    std::map<std::string, std::string> payload;
};


class IPCBroker {
private:
    using Handler =
        std::function<std::string(const IPCMessage&)>;

    std::map<std::string, Handler> services_;
    std::uint64_t nextMessageId_ = 1;

public:
    void registerService(
        const std::string& name,
        Handler handler
    ) {
        if (services_.contains(name)) {
            throw ArchitectureError(
                "IPC service already registered: " + name
            );
        }

        services_[name] = std::move(handler);
    }

    std::string request(
        const std::string& sender,
        const std::string& receiver,
        const std::string& operation,
        std::map<std::string, std::string> payload
    ) {
        auto service = services_.find(receiver);

        if (service == services_.end()) {
            throw std::runtime_error(
                "IPC receiver does not exist: " + receiver
            );
        }

        IPCMessage message{
            nextMessageId_++,
            sender,
            receiver,
            operation,
            std::move(payload)
        };

        return service->second(message);
    }
};


class Microkernel {
private:
    IPCBroker ipc_;
    std::shared_ptr<StorageService> storageServer_;
    std::shared_ptr<DeviceService> deviceServer_;

public:
    Microkernel()
        : storageServer_(std::make_shared<StorageService>()),
          deviceServer_(std::make_shared<DeviceService>()) {

        ipc_.registerService(
            "storage",
            [this](const IPCMessage& message) {
                if (message.operation == "create") {
                    storageServer_->createFile(
                        message.payload.at("path"),
                        message.payload.at("content")
                    );
                    return std::string("storage: file created");
                }

                if (message.operation == "read") {
                    return storageServer_->readFile(
                        message.payload.at("path")
                    );
                }

                if (message.operation == "write") {
                    storageServer_->writeFile(
                        message.payload.at("path"),
                        message.payload.at("content")
                    );
                    return std::string("storage: file written");
                }

                throw ValidationError(
                    "Unsupported storage operation"
                );
            }
        );

        ipc_.registerService(
            "device",
            [this](const IPCMessage& message) {
                if (message.operation != "write") {
                    throw ValidationError(
                        "Unsupported device operation"
                    );
                }

                return deviceServer_->write(
                    message.payload.at("device"),
                    message.payload.at("data")
                );
            }
        );
    }

    std::string request(
        const std::string& sender,
        const std::string& service,
        const std::string& operation,
        std::map<std::string, std::string> payload
    ) {
        return ipc_.request(
            sender,
            service,
            operation,
            std::move(payload)
        );
    }
};


/*
 * HYBRID KERNEL CASE
 *
 * Process management remains a direct kernel facility, while storage is
 * accessed through an explicit service boundary. The point is to demonstrate
 * mixed placement rather than to claim that all hybrid kernels use exactly
 * this organization.
 */
class HybridKernel {
private:
    MemoryManager memory_{256 * 1024 * 1024};
    ProcessManager processes_{memory_};

    IPCBroker ipc_;
    std::shared_ptr<StorageService> storage_;

public:
    HybridKernel()
        : storage_(std::make_shared<StorageService>()) {

        ipc_.registerService(
            "storage-service",
            [this](const IPCMessage& message) {
                if (message.operation == "create") {
                    storage_->createFile(
                        message.payload.at("path"),
                        message.payload.at("content")
                    );
                    return std::string("hybrid storage: created");
                }

                if (message.operation == "read") {
                    return storage_->readFile(
                        message.payload.at("path")
                    );
                }

                throw ValidationError(
                    "Unsupported hybrid storage operation"
                );
            }
        );
    }

    Process createProcess(
        const std::string& name,
        std::size_t memoryBytes
    ) {
        return processes_.create(name, memoryBytes);
    }

    std::string storageRequest(
        const std::string& operation,
        std::map<std::string, std::string> payload
    ) {
        return ipc_.request(
            "hybrid-kernel",
            "storage-service",
            operation,
            std::move(payload)
        );
    }
};


/*
 * LAYERED ARCHITECTURE CASE
 *
 * The layer graph models:
 *
 * applications
 *       |
 *    runtime
 *       |
 * system-services
 *       |
 *     kernel
 *       |
 *    hardware
 *
 * Dependencies may point downward only. This constraint is independent of
 * whether the lower layers are implemented as monolithic or microkernel
 * components.
 */
class LayeredArchitecture {
private:
    std::map<std::string, int> levels_{
        {"hardware", 0},
        {"kernel", 1},
        {"system-services", 2},
        {"runtime", 3},
        {"applications", 4}
    };

    std::map<std::string, std::set<std::string>> dependencies_{
        {"hardware", {}},
        {"kernel", {"hardware"}},
        {"system-services", {"kernel"}},
        {"runtime", {"system-services"}},
        {"applications", {"runtime"}}
    };

public:
    void addDependency(
        const std::string& source,
        const std::string& target
    ) {
        if (!levels_.contains(source) ||
            !levels_.contains(target)) {
            throw ValidationError(
                "Unknown layer in dependency"
            );
        }

        if (levels_.at(target) >= levels_.at(source)) {
            throw ArchitectureError(
                "Layer dependency must point downward: " +
                source + " -> " + target
            );
        }

        dependencies_[source].insert(target);
    }

    std::vector<std::string> validate() const {
        std::vector<std::string> errors;

        for (const auto& [source, targets] : dependencies_) {
            for (const auto& target : targets) {
                if (levels_.at(target) >= levels_.at(source)) {
                    errors.push_back(
                        source + " -> " + target
                    );
                }
            }
        }

        return errors;
    }

    void printArchitecture() const {
        std::cout
            << "applications -> runtime -> system-services "
            << "-> kernel -> hardware\n";
    }
};


void demonstrateMonolithic() {
    std::cout << "\n=== MONOLITHIC KERNEL ===\n";

    MonolithicKernel kernel;

    Process process =
        kernel.createProcess(
            "storage-indexer",
            8 * 1024 * 1024
        );

    kernel.createFile(
        "/var/index/catalog.db",
        "monolithic storage path"
    );

    std::cout
        << "Created PID " << process.pid
        << " for " << process.name << '\n';

    std::cout
        << "Storage content: "
        << kernel.readFile("/var/index/catalog.db")
        << '\n';

    std::cout
        << "Device result: "
        << kernel.writeDevice(
            "console0",
            "indexer started"
        )
        << '\n';

    std::cout
        << "Remaining memory: "
        << kernel.freeMemory()
        << " bytes\n";
}


void demonstrateMicrokernel() {
    std::cout << "\n=== MICROKERNEL ===\n";

    Microkernel kernel;

    kernel.request(
        "shell",
        "storage",
        "create",
        {
            {"path", "/home/operator/config.txt"},
            {"content", "microkernel service"}
        }
    );

    std::string content =
        kernel.request(
            "shell",
            "storage",
            "read",
            {
                {"path", "/home/operator/config.txt"}
            }
        );

    std::string deviceResult =
        kernel.request(
            "shell",
            "device",
            "write",
            {
                {"device", "console0"},
                {"data", "IPC delivered device request"}
            }
        );

    std::cout
        << "Storage server response: "
        << content << '\n';

    std::cout
        << "Device server response: "
        << deviceResult << '\n';
}


void demonstrateHybrid() {
    std::cout << "\n=== HYBRID KERNEL ===\n";

    HybridKernel kernel;

    Process process =
        kernel.createProcess(
            "database-worker",
            16 * 1024 * 1024
        );

    kernel.storageRequest(
        "create",
        {
            {"path", "/database/segment.dat"},
            {"content", "hybrid architecture"}
        }
    );

    std::string result =
        kernel.storageRequest(
            "read",
            {
                {"path", "/database/segment.dat"}
            }
        );

    std::cout
        << "Direct kernel process PID: "
        << process.pid << '\n';

    std::cout
        << "Storage service response: "
        << result << '\n';
}


void demonstrateLayering() {
    std::cout << "\n=== LAYERED ARCHITECTURE ===\n";

    LayeredArchitecture architecture;

    architecture.printArchitecture();

    const auto initialErrors =
        architecture.validate();

    std::cout
        << "Initial validation errors: "
        << initialErrors.size() << '\n';

    try {
        /*
         * This dependency is architecturally problematic because it bypasses
         * the intermediate runtime and service layers.
         */
        architecture.addDependency(
            "applications",
            "kernel"
        );

        std::cout
            << "Direct application-to-kernel dependency accepted\n";
    } catch (const ArchitectureError& error) {
        std::cout
            << "Layer rule rejected dependency: "
            << error.what() << '\n';
    }
}


void demonstrateFailureIsolation() {
    std::cout << "\n=== FAILURE ISOLATION ===\n";

    Microkernel kernel;

    try {
        kernel.request(
            "untrusted-client",
            "storage",
            "read",
            {
                {"path", "/does/not/exist"}
            }
        );
    } catch (const std::exception& error) {
        std::cout
            << "Storage service failure: "
            << error.what() << '\n';
    }

    /*
     * The failed storage operation does not corrupt the simulated IPC broker.
     * A separate service can still process a request.
     */
    std::cout
        << "Independent service response: "
        << kernel.request(
            "untrusted-client",
            "device",
            "write",
            {
                {"device", "console0"},
                {"data", "device service remains reachable"}
            }
        )
        << '\n';
}


void demonstrateBoundaryValidation() {
    std::cout << "\n=== BOUNDARY VALIDATION ===\n";

    Microkernel kernel;

    try {
        kernel.request(
            "untrusted-client",
            "device",
            "format-disk",
            {
                {"device", "disk0"}
            }
        );
    } catch (const std::exception& error) {
        std::cout
            << "Unsupported IPC operation rejected: "
            << error.what() << '\n';
    }

    try {
        kernel.request(
            "untrusted-client",
            "device",
            "write",
            {
                {"device", "unknown0"},
                {"data", "invalid device access"}
            }
        );
    } catch (const std::exception& error) {
        std::cout
            << "Invalid device rejected: "
            << error.what() << '\n';
    }
}


void demonstrateTimingPaths() {
    std::cout << "\n=== SOFTWARE PATH TIMING ===\n";

    constexpr int iterations = 100000;

    MonolithicKernel monolithic;

    monolithic.createFile(
        "/tmp/benchmark.txt",
        "x"
    );

    auto directStart =
        std::chrono::steady_clock::now();

    for (int i = 0; i < iterations; ++i) {
        static_cast<void>(
            monolithic.readFile(
                "/tmp/benchmark.txt"
            )
        );
    }

    auto directEnd =
        std::chrono::steady_clock::now();

    Microkernel microkernel;

    microkernel.request(
        "setup",
        "storage",
        "create",
        {
            {"path", "/tmp/benchmark.txt"},
            {"content", "x"}
        }
    );

    auto ipcStart =
        std::chrono::steady_clock::now();

    for (int i = 0; i < iterations; ++i) {
        static_cast<void>(
            microkernel.request(
                "benchmark",
                "storage",
                "read",
                {
                    {"path", "/tmp/benchmark.txt"}
                }
            )
        );
    }

    auto ipcEnd =
        std::chrono::steady_clock::now();

    const auto directMicroseconds =
        std::chrono::duration_cast<
            std::chrono::microseconds
        >(directEnd - directStart).count();

    const auto ipcMicroseconds =
        std::chrono::duration_cast<
            std::chrono::microseconds
        >(ipcEnd - ipcStart).count();

    std::cout
        << "Direct path: "
        << directMicroseconds
        << " microseconds\n";

    std::cout
        << "IPC model path: "
        << ipcMicroseconds
        << " microseconds\n";

    std::cout
        << "These values measure this C++ model, not actual kernel IPC.\n";
}


void printArchitecturalComparison() {
    std::cout << "\n=== ARCHITECTURAL RELATIONSHIPS ===\n";

    std::cout
        << "Monolithic architecture places many core services inside "
        << "one privileged kernel boundary.\n";

    std::cout
        << "Microkernel architecture minimizes the privileged core and "
        << "uses IPC to reach isolated services.\n";

    std::cout
        << "Hybrid architecture combines selected direct kernel services "
        << "with additional service boundaries.\n";

    std::cout
        << "Layered architecture constrains dependencies according to "
        << "ordered abstraction levels.\n";

    std::cout
        << "Layering can coexist with monolithic, microkernel, or hybrid "
        << "implementation choices.\n";
}


int main() {
    try {
        std::cout
            << "OPERATING SYSTEM ARCHITECTURE CASE STUDY\n"
            << "=========================================\n";

        demonstrateMonolithic();
        demonstrateMicrokernel();
        demonstrateHybrid();
        demonstrateLayering();
        demonstrateFailureIsolation();
        demonstrateBoundaryValidation();
        demonstrateTimingPaths();
        printArchitecturalComparison();

        std::cout
            << "\nCase study completed successfully.\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr
            << "Fatal case-study error: "
            << error.what()
            << '\n';

        return 1;
    }
}
