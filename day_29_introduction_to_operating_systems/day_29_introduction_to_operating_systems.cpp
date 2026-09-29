/*
 * Introduction to Operating Systems
 *
 * C++17 educational case study:
 * A small operating-system simulator for a multi-user document-processing
 * server. The simulator models:
 *
 *   - processes
 *   - process states
 *   - CPU scheduling
 *   - memory allocation
 *   - files
 *   - system calls
 *   - user/kernel privilege separation
 *   - interrupts
 *   - access control
 *   - virtual memory
 *   - resource validation
 *
 * Compile:
 *   g++ -std=c++17 -Wall -Wextra -pedantic operating_systems.cpp -o os_demo
 */

#include <algorithm>
#include <cstddef>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <queue>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

enum class PrivilegeMode {
    User,
    Kernel
};

enum class ProcessState {
    New,
    Ready,
    Running,
    Waiting,
    Terminated
};

enum class Operation {
    Read,
    Write
};

std::string toString(PrivilegeMode mode) {
    return mode == PrivilegeMode::User ? "USER" : "KERNEL";
}

std::string toString(ProcessState state) {
    switch (state) {
        case ProcessState::New:
            return "NEW";
        case ProcessState::Ready:
            return "READY";
        case ProcessState::Running:
            return "RUNNING";
        case ProcessState::Waiting:
            return "WAITING";
        case ProcessState::Terminated:
            return "TERMINATED";
    }

    return "UNKNOWN";
}

std::string toString(Operation operation) {
    return operation == Operation::Read ? "READ" : "WRITE";
}

// ---------------------------------------------------------------------------
// Process Control Block
// ---------------------------------------------------------------------------

struct Process {
    int pid;
    std::string name;
    int priority;
    int cpuBurst;
    int remainingCpu;
    std::size_t memoryKB;
    ProcessState state;
    std::map<std::string, long long> registers;
};

// ---------------------------------------------------------------------------
// File representation
// ---------------------------------------------------------------------------

struct File {
    std::string name;
    std::string owner;
    std::string contents;
    std::set<Operation> allowedOperations;
};

// ---------------------------------------------------------------------------
// Virtual-memory page table
// ---------------------------------------------------------------------------

class PageTable {
private:
    std::size_t pageSize;
    std::unordered_map<std::size_t, std::size_t> mappings;

public:
    explicit PageTable(std::size_t pageSizeBytes = 4096)
        : pageSize(pageSizeBytes) {
        if (pageSize == 0) {
            throw std::invalid_argument("Page size cannot be zero.");
        }
    }

    void mapPage(std::size_t virtualPage, std::size_t physicalFrame) {
        mappings[virtualPage] = physicalFrame;
    }

    std::size_t translate(std::size_t virtualAddress) const {
        const std::size_t virtualPage = virtualAddress / pageSize;
        const std::size_t offset = virtualAddress % pageSize;

        const auto iterator = mappings.find(virtualPage);

        if (iterator == mappings.end()) {
            throw std::runtime_error(
                "Page fault: virtual page is not mapped."
            );
        }

        return iterator->second * pageSize + offset;
    }
};

// ---------------------------------------------------------------------------
// Memory manager
// ---------------------------------------------------------------------------

class MemoryManager {
private:
    struct Allocation {
        std::size_t baseAddress;
        std::size_t sizeKB;
    };

    std::size_t totalMemoryKB;
    std::size_t nextAddressKB = 0;
    std::map<int, Allocation> allocations;

public:
    explicit MemoryManager(std::size_t totalMemory)
        : totalMemoryKB(totalMemory) {}

    std::size_t allocate(int pid, std::size_t sizeKB) {
        if (sizeKB == 0) {
            throw std::invalid_argument(
                "Process memory allocation must be positive."
            );
        }

        std::size_t used = 0;

        for (const auto& [processId, allocation] : allocations) {
            (void)processId;
            used += allocation.sizeKB;
        }

        if (used + sizeKB > totalMemoryKB) {
            throw std::runtime_error("Insufficient memory.");
        }

        const std::size_t address = nextAddressKB;

        allocations[pid] = Allocation{address, sizeKB};
        nextAddressKB += sizeKB;

        return address;
    }

    void release(int pid) {
        const auto iterator = allocations.find(pid);

        if (iterator == allocations.end()) {
            throw std::runtime_error("No allocation belongs to PID.");
        }

        allocations.erase(iterator);
    }

    std::size_t usedMemory() const {
        std::size_t used = 0;

        for (const auto& [pid, allocation] : allocations) {
            (void)pid;
            used += allocation.sizeKB;
        }

        return used;
    }

    std::size_t freeMemory() const {
        return totalMemoryKB - usedMemory();
    }
};

// ---------------------------------------------------------------------------
// CPU scheduler
// ---------------------------------------------------------------------------

class RoundRobinScheduler {
private:
    std::queue<int> readyQueue;
    std::unordered_map<int, Process*> processes;

public:
    explicit RoundRobinScheduler(std::vector<Process>& processList) {
        for (Process& process : processList) {
            processes[process.pid] = &process;
            process.state = ProcessState::Ready;
            readyQueue.push(process.pid);
        }
    }

    void run(int quantum) {
        if (quantum <= 0) {
            throw std::invalid_argument("Quantum must be positive.");
        }

        std::cout << "\nCPU scheduling timeline:\n";

        while (!readyQueue.empty()) {
            const int pid = readyQueue.front();
            readyQueue.pop();

            Process* process = processes.at(pid);

            if (process->remainingCpu <= 0) {
                process->state = ProcessState::Terminated;
                continue;
            }

            process->state = ProcessState::Running;

            const int executionTime =
                std::min(quantum, process->remainingCpu);

            std::cout
                << "  PID " << process->pid
                << " (" << process->name << ")"
                << " executes for " << executionTime
                << " time units.\n";

            process->remainingCpu -= executionTime;

            if (process->remainingCpu > 0) {
                process->state = ProcessState::Ready;
                readyQueue.push(process->pid);
            } else {
                process->state = ProcessState::Terminated;
            }
        }
    }
};

// ---------------------------------------------------------------------------
// Access-control model
// ---------------------------------------------------------------------------

class AccessController {
private:
    std::map<std::string, std::set<Operation>> permissions;

public:
    void grant(
        const std::string& user,
        Operation operation
    ) {
        permissions[user].insert(operation);
    }

    bool allowed(
        const std::string& user,
        Operation operation
    ) const {
        const auto iterator = permissions.find(user);

        if (iterator == permissions.end()) {
            return false;
        }

        return iterator->second.contains(operation);
    }
};

// ---------------------------------------------------------------------------
// Operating-system kernel
// ---------------------------------------------------------------------------

class OperatingSystem {
private:
    std::string name;
    std::string version;
    PrivilegeMode mode = PrivilegeMode::User;

    int nextPid = 1;

    MemoryManager memoryManager;
    PageTable pageTable;

    std::map<int, Process> processTable;
    std::map<std::string, File> files;

    AccessController accessController;

    // A real kernel would have hardware-specific mechanisms and substantially
    // more metadata. These structures model the central responsibilities.
public:
    OperatingSystem(
        std::string systemName,
        std::string systemVersion,
        std::size_t memoryKB
    )
        : name(std::move(systemName)),
          version(std::move(systemVersion)),
          memoryManager(memoryKB) {}

    void printSystemInformation() const {
        std::cout
            << "\nSystem: " << name << ' ' << version
            << "\nPrivilege mode: " << toString(mode)
            << "\nUsed memory: " << memoryManager.usedMemory()
            << " KB\nFree memory: " << memoryManager.freeMemory()
            << " KB\n";
    }

    Process& createProcess(
        const std::string& processName,
        const std::string& user,
        int priority,
        int cpuBurst,
        std::size_t memoryKB
    ) {
        if (processName.empty()) {
            throw std::invalid_argument(
                "Process name cannot be empty."
            );
        }

        if (cpuBurst <= 0) {
            throw std::invalid_argument(
                "CPU burst must be positive."
            );
        }

        const int pid = nextPid++;

        memoryManager.allocate(pid, memoryKB);

        Process process{
            pid,
            processName,
            priority,
            cpuBurst,
            cpuBurst,
            memoryKB,
            ProcessState::Ready,
            {}
        };

        process.registers["instruction_pointer"] = 0;
        process.registers["stack_pointer"] = 4096;

        processTable.emplace(pid, std::move(process));

        // The access controller is intentionally initialized as part of
        // process creation in this educational model.
        accessController.grant(user, Operation::Read);

        return processTable.at(pid);
    }

    void terminateProcess(int pid) {
        auto iterator = processTable.find(pid);

        if (iterator == processTable.end()) {
            throw std::runtime_error("Process does not exist.");
        }

        iterator->second.state = ProcessState::Terminated;

        memoryManager.release(pid);
        processTable.erase(iterator);
    }

    void enterKernel(const std::string& reason) {
        if (mode == PrivilegeMode::Kernel) {
            throw std::runtime_error("Already in kernel mode.");
        }

        std::cout
            << "[MODE SWITCH] USER -> KERNEL: "
            << reason << '\n';

        mode = PrivilegeMode::Kernel;
    }

    void leaveKernel() {
        if (mode != PrivilegeMode::Kernel) {
            throw std::runtime_error("Not in kernel mode.");
        }

        mode = PrivilegeMode::User;

        std::cout << "[MODE SWITCH] KERNEL -> USER\n";
    }

    /*
     * The system-call wrapper models the fundamental boundary between
     * application code and privileged operating-system services.
     *
     * In a real CPU, a system-call instruction/trap transfers control to a
     * kernel entry point. The hardware and kernel establish a controlled
     * execution environment before privileged work occurs.
     */
    template <typename Function>
    auto systemCall(
        int pid,
        const std::string& serviceName,
        Function service
    ) -> decltype(service()) {
        if (!processTable.contains(pid)) {
            throw std::runtime_error(
                "System call from an unknown process."
            );
        }

        std::cout
            << "\nSystem call from PID " << pid
            << ": " << serviceName << '\n';

        enterKernel(serviceName);

        try {
            auto result = service();
            leaveKernel();
            return result;
        } catch (...) {
            // A kernel must restore its expected state even when an operation
            // fails. Exception-safe state restoration is important in software
            // even though real kernels use different error mechanisms.
            leaveKernel();
            throw;
        }
    }

    void createFile(
        int pid,
        const std::string& user,
        const std::string& fileName,
        const std::string& contents
    ) {
        systemCall(
            pid,
            "create_file",
            [&]() {
                if (fileName.empty()) {
                    throw std::invalid_argument(
                        "File name cannot be empty."
                    );
                }

                if (files.contains(fileName)) {
                    throw std::runtime_error(
                        "File already exists."
                    );
                }

                File file{
                    fileName,
                    user,
                    contents,
                    {Operation::Read, Operation::Write}
                };

                files.emplace(fileName, std::move(file));

                return 0;
            }
        );
    }

    std::string readFile(
        int pid,
        const std::string& user,
        const std::string& fileName
    ) {
        return systemCall(
            pid,
            "read_file",
            [&]() -> std::string {
                const auto iterator = files.find(fileName);

                if (iterator == files.end()) {
                    throw std::runtime_error(
                        "File does not exist."
                    );
                }

                if (!iterator->second.allowedOperations.contains(
                        Operation::Read)) {
                    throw std::runtime_error(
                        "File read permission denied."
                    );
                }

                (void)user;
                return iterator->second.contents;
            }
        );
    }

    void writeFile(
        int pid,
        const std::string& user,
        const std::string& fileName,
        const std::string& contents
    ) {
        systemCall(
            pid,
            "write_file",
            [&]() {
                const auto iterator = files.find(fileName);

                if (iterator == files.end()) {
                    throw std::runtime_error(
                        "File does not exist."
                    );
                }

                if (!iterator->second.allowedOperations.contains(
                        Operation::Write)) {
                    throw std::runtime_error(
                        "File write permission denied."
                    );
                }

                iterator->second.contents = contents;
                (void)user;

                return 0;
            }
        );
    }

    void interrupt(const std::string& interruptName) {
        std::cout
            << "\n[INTERRUPT] "
            << interruptName << '\n';

        const PrivilegeMode previousMode = mode;

        mode = PrivilegeMode::Kernel;

        std::cout
            << "Interrupt handler executes in "
            << toString(mode)
            << " mode.\n";

        std::cout
            << "Kernel records the event and determines the appropriate action.\n";

        mode = previousMode;

        std::cout
            << "Execution resumes in "
            << toString(mode)
            << " mode.\n";
    }

    void contextSwitch(int currentPid, int nextPid) {
        auto current = processTable.find(currentPid);
        auto next = processTable.find(nextPid);

        if (current == processTable.end() ||
            next == processTable.end()) {
            throw std::runtime_error(
                "Context-switch process does not exist."
            );
        }

        current->second.registers["instruction_pointer"] = 1000;
        current->second.registers["stack_pointer"] = 8000;

        std::cout
            << "\nSaving context of PID "
            << currentPid << ":\n";

        for (const auto& [registerName, value]
             : current->second.registers) {
            std::cout
                << "  " << registerName
                << " = " << value << '\n';
        }

        next->second.registers["instruction_pointer"] = 2500;
        next->second.registers["stack_pointer"] = 9000;

        std::cout
            << "Restoring context of PID "
            << nextPid << ":\n";

        for (const auto& [registerName, value]
             : next->second.registers) {
            std::cout
                << "  " << registerName
                << " = " << value << '\n';
        }
    }

    void demonstrateVirtualMemory() {
        pageTable.mapPage(0, 4);
        pageTable.mapPage(1, 9);

        const std::size_t virtualAddress = 4096 + 128;
        const std::size_t physicalAddress =
            pageTable.translate(virtualAddress);

        std::cout
            << "\nVirtual address "
            << virtualAddress
            << " maps to physical address "
            << physicalAddress << ".\n";

        try {
            pageTable.translate(8192);
        } catch (const std::exception& error) {
            std::cout
                << "Expected virtual-memory error: "
                << error.what() << '\n';
        }
    }

    void printProcesses() const {
        std::cout << "\nProcess table:\n";

        for (const auto& [pid, process] : processTable) {
            std::cout
                << "  PID=" << pid
                << ", name=" << process.name
                << ", state=" << toString(process.state)
                << ", priority=" << process.priority
                << ", memory=" << process.memoryKB
                << " KB"
                << ", remaining CPU="
                << process.remainingCpu
                << '\n';
        }
    }
};

// ---------------------------------------------------------------------------
// Operating-system type explanations
// ---------------------------------------------------------------------------

void explainOperatingSystemTypes() {
    std::cout << "\n=== OPERATING-SYSTEM CLASSIFICATIONS ===\n";

    const std::vector<std::pair<std::string, std::string>> types = {
        {
            "Batch",
            "Runs groups of jobs with limited interactive interaction."
        },
        {
            "Multiprogramming",
            "Keeps multiple programs available to improve processor utilization."
        },
        {
            "Multitasking",
            "Shares CPU time among multiple active tasks for interactive execution."
        },
        {
            "Multiprocessing",
            "Uses multiple processors or cores for parallel execution."
        },
        {
            "Real-time",
            "Targets workloads with important timing or response constraints."
        },
        {
            "Distributed",
            "Coordinates resources and computation across networked machines."
        },
        {
            "Network",
            "Provides communication and shared-resource services."
        },
        {
            "Embedded",
            "Targets dedicated hardware and constrained environments."
        },
        {
            "Mobile",
            "Targets mobile hardware, applications, radios, sensors, and power limits."
        },
        {
            "Desktop",
            "Targets general-purpose interactive personal computing."
        },
        {
            "Server",
            "Targets long-running services, concurrency, storage, and networking."
        }
    };

    for (const auto& [type, description] : types) {
        std::cout
            << std::left
            << std::setw(18)
            << type
            << " : "
            << description
            << '\n';
    }
}

// ---------------------------------------------------------------------------
// Kernel architecture explanations
// ---------------------------------------------------------------------------

void explainKernelArchitectures() {
    std::cout << "\n=== KERNEL ARCHITECTURES ===\n";

    std::cout
        << "Monolithic: many core services operate in privileged kernel space.\n"
        << "Microkernel: a small privileged core delegates more services to separate components.\n"
        << "Hybrid: combines structural ideas from monolithic and microkernel designs.\n"
        << "Modular: supports separable kernel components while retaining kernel-space services.\n"
        << "Layered: organizes responsibilities into layers with defined interfaces.\n";
}

// ---------------------------------------------------------------------------
// Main industry-style case study
// ---------------------------------------------------------------------------

int main() {
    try {
        std::cout
            << "============================================================\n"
            << "INTRODUCTION TO OPERATING SYSTEMS\n"
            << "C++ TECHNICAL CASE STUDY: DOCUMENT PROCESSING SERVER\n"
            << "============================================================\n";

        /*
         * Scenario:
         *
         * A server accepts document-processing jobs from users. Each job is
         * represented by a process. The OS must allocate memory, schedule CPU
         * time, protect files, service system calls, and react to interrupts.
         *
         * This is not a real kernel. It is an educational model that exposes
         * the major responsibilities and boundaries of an OS.
         */
        OperatingSystem os(
            "CaseStudyOS",
            "1.0",
            8192
        );

        os.printSystemInformation();

        Process& documentProcessor = os.createProcess(
            "document-processor",
            "alice",
            10,
            6,
            1024
        );

        Process& reportGenerator = os.createProcess(
            "report-generator",
            "bob",
            5,
            8,
            1536
        );

        Process& backupService = os.createProcess(
            "backup-service",
            "alice",
            8,
            4,
            768
        );

        os.printProcesses();
        os.printSystemInformation();

        // File operations intentionally cross the user/kernel boundary.
        os.createFile(
            documentProcessor.pid,
            "alice",
            "report.txt",
            "Initial report data.\n"
        );

        os.writeFile(
            reportGenerator.pid,
            "bob",
            "report.txt",
            "Processed report data.\n"
        );

        std::cout
            << "\nReport contents:\n"
            << os.readFile(
                documentProcessor.pid,
                "alice",
                "report.txt"
            );

        // Timer interrupts are central to preemptive multitasking because
        // they give the OS opportunities to regain control of the CPU.
        os.interrupt("timer tick");

        // The scheduler receives processes that are ready to execute.
        std::vector<Process> schedulingWorkload = {
            {101, "indexer", 5, 5, 5, 512, ProcessState::Ready, {}},
            {102, "compressor", 5, 7, 7, 768, ProcessState::Ready, {}},
            {103, "logger", 5, 3, 3, 256, ProcessState::Ready, {}}
        };

        RoundRobinScheduler scheduler(schedulingWorkload);
        scheduler.run(2);

        // Context switching saves one process state and restores another.
        os.contextSwitch(
            documentProcessor.pid,
            reportGenerator.pid
        );

        // Virtual-memory translation.
        os.demonstrateVirtualMemory();

        // Important failure conditions are deliberately exercised.
        std::cout << "\n=== FAILURE CONDITIONS ===\n";

        try {
            os.readFile(
                documentProcessor.pid,
                "alice",
                "missing.txt"
            );
        } catch (const std::exception& error) {
            std::cout
                << "Missing-file error handled: "
                << error.what() << '\n';
        }

        try {
            os.createProcess(
                "oversized-job",
                "alice",
                5,
                2,
                100000
            );
        } catch (const std::exception& error) {
            std::cout
                << "Memory-allocation error handled: "
                << error.what() << '\n';
        }

        // Terminating a process releases its allocated memory.
        os.terminateProcess(backupService.pid);

        os.printProcesses();
        os.printSystemInformation();

        explainOperatingSystemTypes();
        explainKernelArchitectures();

        /*
         * Complexity observations:
         *
         * - std::map process/file lookup is O(log n).
         * - The educational memory manager scans allocations when calculating
         *   used memory, giving an O(n) calculation.
         * - Round-robin scheduling performs one queue operation per CPU slice.
         * - Page-table lookup is approximately O(1) average because an
         *   unordered_map is used.
         *
         * Production kernels use specialized data structures, hardware
         * translation support, per-CPU structures, synchronization primitives,
         * cache-aware algorithms, and carefully bounded critical sections.
         */

        std::cout
            << "\nCase study completed successfully.\n";

    } catch (const std::exception& error) {
        std::cerr
            << "Fatal operating-system simulation error: "
            << error.what()
            << '\n';

        return 1;
    }

    return 0;
}
