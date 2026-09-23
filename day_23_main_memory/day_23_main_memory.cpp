/*
 * Main Memory: RAM, DRAM, SRAM, Memory Addressing, and Memory Allocation
 * ======================================================================
 *
 * Industry-style educational case study:
 *     A simplified operating-system memory manager for multiple processes.
 *
 * Demonstrates:
 *     - Byte-addressable memory
 *     - RAM abstraction
 *     - DRAM/SRAM conceptual differences
 *     - Virtual-to-physical address translation
 *     - Page tables
 *     - Contiguous allocation
 *     - First-fit, best-fit, and worst-fit strategies
 *     - Alignment
 *     - Fragmentation
 *     - Memory protection
 *     - Process lifecycle
 *     - Error handling
 *     - Complexity considerations
 *
 * Compile:
 *     g++ -std=c++17 -O2 main_memory.cpp -o main_memory
 *
 * Run:
 *     ./main_memory
 */

#include <algorithm>
#include <array>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <optional>
#include <random>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using Byte = std::uint8_t;
using Address = std::size_t;


// ============================================================================
// 1. MEMORY UNITS
// ============================================================================

constexpr std::size_t BYTES_PER_KIB = 1024;
constexpr std::size_t BYTES_PER_MIB = 1024 * 1024;
constexpr std::size_t BYTES_PER_GIB = 1024ULL * 1024ULL * 1024ULL;

std::string formatBytes(std::size_t bytes) {
    if (bytes < BYTES_PER_KIB) {
        return std::to_string(bytes) + " B";
    }

    const char* units[] = {"KiB", "MiB", "GiB", "TiB"};
    double value = static_cast<double>(bytes) / BYTES_PER_KIB;

    for (const char* unit : units) {
        if (value < 1024.0 || std::string(unit) == "TiB") {
            std::ostringstream output;
            output << std::fixed << std::setprecision(2)
                   << value << " " << unit;
            return output.str();
        }

        value /= 1024.0;
    }

    return std::to_string(bytes) + " B";
}


// ============================================================================
// 2. SIMULATED BYTE-ADDRESSABLE RAM
// ============================================================================

class MemoryAccessException : public std::runtime_error {
public:
    explicit MemoryAccessException(const std::string& message)
        : std::runtime_error(message) {}
};

class SimulatedRAM {
private:
    std::vector<Byte> memory;

    void validate(Address address, std::size_t width = 1) const {
        if (width == 0) {
            throw std::invalid_argument("Access width must be positive.");
        }

        if (address >= memory.size() ||
            width > memory.size() - address) {
            throw MemoryAccessException(
                "Memory access exceeds simulated RAM boundaries."
            );
        }
    }

public:
    explicit SimulatedRAM(std::size_t sizeBytes)
        : memory(sizeBytes, 0) {
        if (sizeBytes == 0) {
            throw std::invalid_argument("RAM size must be positive.");
        }
    }

    std::size_t size() const {
        return memory.size();
    }

    Byte readByte(Address address) const {
        validate(address);
        return memory[address];
    }

    void writeByte(Address address, Byte value) {
        validate(address);
        memory[address] = value;
    }

    std::vector<Byte> read(Address address, std::size_t width) const {
        validate(address, width);

        return std::vector<Byte>(
            memory.begin() + static_cast<std::ptrdiff_t>(address),
            memory.begin() + static_cast<std::ptrdiff_t>(address + width)
        );
    }

    void write(Address address, const std::vector<Byte>& data) {
        validate(address, data.size());

        std::copy(
            data.begin(),
            data.end(),
            memory.begin() + static_cast<std::ptrdiff_t>(address)
        );
    }

    void dump(Address start, std::size_t length) const {
        validate(start, length);

        for (std::size_t offset = 0; offset < length; offset += 8) {
            std::cout
                << std::hex
                << std::setw(4)
                << std::setfill('0')
                << start + offset
                << ": ";

            const std::size_t count =
                std::min<std::size_t>(8, length - offset);

            for (std::size_t index = 0; index < count; ++index) {
                std::cout
                    << std::setw(2)
                    << static_cast<int>(
                        memory[start + offset + index]
                    )
                    << " ";
            }

            std::cout << std::dec << std::setfill(' ') << "\n";
        }
    }
};


// ============================================================================
// 3. DRAM AND SRAM
// ============================================================================

enum class MemoryTechnology {
    DRAM,
    SRAM
};

class MemoryCell {
private:
    MemoryTechnology technology;
    bool bit;
    std::size_t refreshCount = 0;

public:
    MemoryCell(MemoryTechnology technologyValue, bool initialBit)
        : technology(technologyValue), bit(initialBit) {}

    void refresh() {
        if (technology == MemoryTechnology::DRAM) {
            ++refreshCount;
        }
    }

    bool read() const {
        return bit;
    }

    void write(bool value) {
        bit = value;
    }

    std::size_t refreshes() const {
        return refreshCount;
    }
};


// ============================================================================
// 4. MEMORY HIERARCHY
// ============================================================================

struct MemoryLevel {
    std::string name;
    std::string technology;
    std::string relativeSpeed;
    std::string purpose;
};


// ============================================================================
// 5. ALLOCATION DATA STRUCTURES
// ============================================================================

struct FreeBlock {
    Address start;
    std::size_t size;

    Address end() const {
        return start + size;
    }
};

struct Allocation {
    int id;
    Address address;
    std::size_t size;
    std::string owner;
    std::vector<Byte> data;

    Address end() const {
        return address + size;
    }
};

enum class AllocationStrategy {
    FirstFit,
    BestFit,
    WorstFit
};


// ============================================================================
// 6. INDUSTRY-STYLE MEMORY ALLOCATOR
// ============================================================================

class MemoryAllocator {
private:
    std::size_t capacity;
    std::vector<FreeBlock> freeBlocks;
    std::unordered_map<int, Allocation> allocations;
    int nextAllocationId = 1;

    void coalesce() {
        std::sort(
            freeBlocks.begin(),
            freeBlocks.end(),
            [](const FreeBlock& left, const FreeBlock& right) {
                return left.start < right.start;
            }
        );

        std::vector<FreeBlock> merged;

        for (const FreeBlock& block : freeBlocks) {
            if (merged.empty()) {
                merged.push_back(block);
                continue;
            }

            FreeBlock& previous = merged.back();

            if (block.start <= previous.end()) {
                const Address newEnd =
                    std::max(previous.end(), block.end());

                previous.size = newEnd - previous.start;
            } else {
                merged.push_back(block);
            }
        }

        freeBlocks = std::move(merged);
    }

    std::optional<std::size_t> chooseBlock(
        std::size_t requestedSize,
        AllocationStrategy strategy
    ) const {
        std::optional<std::size_t> selected;

        for (std::size_t index = 0; index < freeBlocks.size(); ++index) {
            if (freeBlocks[index].size < requestedSize) {
                continue;
            }

            if (strategy == AllocationStrategy::FirstFit) {
                return index;
            }

            if (!selected.has_value()) {
                selected = index;
                continue;
            }

            if (strategy == AllocationStrategy::BestFit) {
                if (freeBlocks[index].size <
                    freeBlocks[*selected].size) {
                    selected = index;
                }
            } else if (strategy == AllocationStrategy::WorstFit) {
                if (freeBlocks[index].size >
                    freeBlocks[*selected].size) {
                    selected = index;
                }
            }
        }

        return selected;
    }

public:
    explicit MemoryAllocator(std::size_t capacityBytes)
        : capacity(capacityBytes),
          freeBlocks{{0, capacityBytes}} {
        if (capacityBytes == 0) {
            throw std::invalid_argument(
                "Allocator capacity must be positive."
            );
        }
    }

    int allocate(
        std::size_t requestedSize,
        const std::string& owner,
        AllocationStrategy strategy = AllocationStrategy::FirstFit
    ) {
        if (requestedSize == 0) {
            throw std::invalid_argument(
                "Cannot allocate zero bytes."
            );
        }

        const auto blockIndex =
            chooseBlock(requestedSize, strategy);

        if (!blockIndex.has_value()) {
            throw std::runtime_error(
                "Allocation failed: no sufficiently large free block."
            );
        }

        FreeBlock& block = freeBlocks[*blockIndex];

        const int allocationId = nextAllocationId++;

        Allocation allocation{
            allocationId,
            block.start,
            requestedSize,
            owner,
            std::vector<Byte>(requestedSize, 0)
        };

        allocations.emplace(allocationId, std::move(allocation));

        if (block.size == requestedSize) {
            freeBlocks.erase(
                freeBlocks.begin() +
                static_cast<std::ptrdiff_t>(*blockIndex)
            );
        } else {
            block.start += requestedSize;
            block.size -= requestedSize;
        }

        return allocationId;
    }

    void freeAllocation(int allocationId) {
        auto iterator = allocations.find(allocationId);

        if (iterator == allocations.end()) {
            throw std::runtime_error(
                "Invalid free: allocation does not exist."
            );
        }

        const Allocation& allocation = iterator->second;

        freeBlocks.push_back({
            allocation.address,
            allocation.size
        });

        allocations.erase(iterator);

        coalesce();
    }

    std::size_t totalFree() const {
        std::size_t total = 0;

        for (const auto& block : freeBlocks) {
            total += block.size;
        }

        return total;
    }

    std::size_t totalAllocated() const {
        std::size_t total = 0;

        for (const auto& [id, allocation] : allocations) {
            total += allocation.size;
        }

        return total;
    }

    std::size_t largestFreeBlock() const {
        std::size_t largest = 0;

        for (const auto& block : freeBlocks) {
            largest = std::max(largest, block.size);
        }

        return largest;
    }

    double externalFragmentationRatio() const {
        const std::size_t free = totalFree();

        if (free == 0) {
            return 0.0;
        }

        return 1.0 -
            static_cast<double>(largestFreeBlock()) /
            static_cast<double>(free);
    }

    void printState() const {
        std::cout << "\nMemory allocator state\n";
        std::cout << "Capacity:  " << capacity << " bytes\n";
        std::cout << "Allocated: " << totalAllocated() << " bytes\n";
        std::cout << "Free:      " << totalFree() << " bytes\n";

        std::cout << "\nAllocated blocks:\n";

        std::vector<Allocation> orderedAllocations;

        for (const auto& [id, allocation] : allocations) {
            orderedAllocations.push_back(allocation);
        }

        std::sort(
            orderedAllocations.begin(),
            orderedAllocations.end(),
            [](const Allocation& left, const Allocation& right) {
                return left.address < right.address;
            }
        );

        for (const auto& allocation : orderedAllocations) {
            std::cout
                << "  ID=" << allocation.id
                << " address=" << allocation.address
                << " size=" << allocation.size
                << " owner=" << allocation.owner
                << "\n";
        }

        std::cout << "\nFree blocks:\n";

        for (const auto& block : freeBlocks) {
            std::cout
                << "  address=" << block.start
                << " size=" << block.size
                << "\n";
        }

        std::cout
            << "External fragmentation: "
            << std::fixed
            << std::setprecision(2)
            << externalFragmentationRatio() * 100.0
            << "%\n"
            << std::defaultfloat;
    }
};


// ============================================================================
// 7. VIRTUAL MEMORY
// ============================================================================

struct PageTableEntry {
    std::size_t virtualPage;
    std::size_t physicalFrame;
    bool present;
    bool writable;
    bool executable;
};

class VirtualMemoryManager {
private:
    std::size_t pageSize;
    std::size_t physicalFrameCount;
    std::map<std::size_t, PageTableEntry> pageTable;

public:
    VirtualMemoryManager(
        std::size_t pageSizeBytes,
        std::size_t physicalFrames
    )
        : pageSize(pageSizeBytes),
          physicalFrameCount(physicalFrames) {
        if (pageSize == 0 ||
            (pageSize & (pageSize - 1)) != 0) {
            throw std::invalid_argument(
                "Page size must be a positive power of two."
            );
        }

        if (physicalFrameCount == 0) {
            throw std::invalid_argument(
                "Physical frame count must be positive."
            );
        }
    }

    void mapPage(
        std::size_t virtualPage,
        std::size_t physicalFrame,
        bool writable = true,
        bool executable = false
    ) {
        if (physicalFrame >= physicalFrameCount) {
            throw std::out_of_range(
                "Physical frame does not exist."
            );
        }

        pageTable[virtualPage] = {
            virtualPage,
            physicalFrame,
            true,
            writable,
            executable
        };
    }

    std::size_t translate(
        std::size_t virtualAddress
    ) const {
        const std::size_t virtualPage =
            virtualAddress / pageSize;

        const std::size_t offset =
            virtualAddress % pageSize;

        auto iterator = pageTable.find(virtualPage);

        if (iterator == pageTable.end() ||
            !iterator->second.present) {
            throw MemoryAccessException(
                "Page fault: virtual page is not present."
            );
        }

        return iterator->second.physicalFrame *
            pageSize + offset;
    }

    std::size_t getPageSize() const {
        return pageSize;
    }
};


// ============================================================================
// 8. MEMORY PROTECTION
// ============================================================================

enum class Permission {
    Read,
    Write,
    Execute
};

struct ProtectedRegion {
    Address start;
    Address end;
    bool readable;
    bool writable;
    bool executable;
    std::string owner;
};

class ProtectionManager {
private:
    std::size_t capacity;
    std::vector<ProtectedRegion> regions;

public:
    explicit ProtectionManager(std::size_t capacityBytes)
        : capacity(capacityBytes) {}

    void addRegion(
        Address start,
        Address end,
        bool readable,
        bool writable,
        bool executable,
        const std::string& owner
    ) {
        if (start >= end || end > capacity) {
            throw std::invalid_argument(
                "Invalid protected-memory region."
            );
        }

        regions.push_back({
            start,
            end,
            readable,
            writable,
            executable,
            owner
        });
    }

    bool allowed(Address address, Permission permission) const {
        for (const auto& region : regions) {
            if (address >= region.start &&
                address < region.end) {

                switch (permission) {
                    case Permission::Read:
                        return region.readable;
                    case Permission::Write:
                        return region.writable;
                    case Permission::Execute:
                        return region.executable;
                }
            }
        }

        return false;
    }
};


// ============================================================================
// 9. PROCESS MODEL
// ============================================================================

enum class ProcessState {
    Created,
    Running,
    Terminated
};

std::string stateToString(ProcessState state) {
    switch (state) {
        case ProcessState::Created:
            return "created";
        case ProcessState::Running:
            return "running";
        case ProcessState::Terminated:
            return "terminated";
    }

    return "unknown";
}

struct Process {
    int processId;
    std::string name;
    std::size_t memoryRequired;
    std::optional<int> allocationId;
    ProcessState state;
};


// ============================================================================
// 10. INTEGRATED SYSTEM MONITOR
// ============================================================================

struct MemorySample {
    std::size_t allocated;
    std::size_t free;
    std::size_t largestFreeBlock;
    std::size_t processCount;
    double fragmentation;
};

class SystemMemoryMonitor {
private:
    std::vector<MemorySample> samples;

public:
    void record(
        std::size_t allocated,
        std::size_t free,
        std::size_t largestFreeBlock,
        std::size_t processCount,
        double fragmentation
    ) {
        samples.push_back({
            allocated,
            free,
            largestFreeBlock,
            processCount,
            fragmentation
        });
    }

    void print() const {
        std::cout << "\nSystem memory monitor\n";

        for (std::size_t index = 0; index < samples.size(); ++index) {
            const auto& sample = samples[index];

            std::cout
                << "Sample " << index + 1
                << ": allocated=" << formatBytes(sample.allocated)
                << ", free=" << formatBytes(sample.free)
                << ", largest-free="
                << formatBytes(sample.largestFreeBlock)
                << ", processes=" << sample.processCount
                << ", fragmentation="
                << std::fixed
                << std::setprecision(2)
                << sample.fragmentation * 100.0
                << "%\n"
                << std::defaultfloat;
        }
    }
};


// ============================================================================
// 11. PROCESS MEMORY MANAGER
// ============================================================================

class ProcessMemoryManager {
private:
    MemoryAllocator allocator;
    std::map<int, Process> processes;
    int nextProcessId = 1;
    SystemMemoryMonitor monitor;

    void recordSample() {
        monitor.record(
            allocator.totalAllocated(),
            allocator.totalFree(),
            allocator.largestFreeBlock(),
            processes.size(),
            allocator.externalFragmentationRatio()
        );
    }

public:
    explicit ProcessMemoryManager(std::size_t capacity)
        : allocator(capacity) {}

    int createProcess(
        const std::string& name,
        std::size_t memoryRequired
    ) {
        const int processId = nextProcessId++;

        const int allocationId = allocator.allocate(
            memoryRequired,
            "PID " + std::to_string(processId) +
            " " + name,
            AllocationStrategy::FirstFit
        );

        processes[processId] = {
            processId,
            name,
            memoryRequired,
            allocationId,
            ProcessState::Running
        };

        recordSample();

        return processId;
    }

    void terminateProcess(int processId) {
        auto iterator = processes.find(processId);

        if (iterator == processes.end()) {
            throw std::runtime_error(
                "Process does not exist."
            );
        }

        Process& process = iterator->second;

        if (process.state == ProcessState::Terminated) {
            throw std::runtime_error(
                "Process is already terminated."
            );
        }

        if (process.allocationId.has_value()) {
            allocator.freeAllocation(
                *process.allocationId
            );

            process.allocationId.reset();
        }

        process.state = ProcessState::Terminated;

        recordSample();
    }

    void printProcesses() const {
        std::cout << "\nProcess table:\n";

        for (const auto& [id, process] : processes) {
            std::cout
                << "  PID=" << process.processId
                << " name=" << process.name
                << " memory=" << process.memoryRequired
                << " state=" << stateToString(process.state)
                << " allocation=";

            if (process.allocationId.has_value()) {
                std::cout << *process.allocationId;
            } else {
                std::cout << "none";
            }

            std::cout << "\n";
        }
    }

    void printMemory() const {
        allocator.printState();
    }

    void printMonitor() const {
        monitor.print();
    }
};


// ============================================================================
// 12. ALLOCATION STRATEGY CASE STUDY
// ============================================================================

void runAllocationStrategyComparison() {
    std::cout << "\n"
              << std::string(78, '=')
              << "\n";
    std::cout << "ALLOCATION STRATEGY COMPARISON\n";
    std::cout << std::string(78, '=')
              << "\n";

    const std::vector<FreeBlock> initialBlocks{
        {0, 100},
        {100, 500},
        {600, 200},
        {800, 300},
        {1100, 600}
    };

    const std::vector<std::size_t> requests{
        212,
        417,
        112,
        426
    };

    for (const auto strategy : {
        AllocationStrategy::FirstFit,
        AllocationStrategy::BestFit,
        AllocationStrategy::WorstFit
    }) {
        MemoryAllocator allocator(1700);

        // Construct an artificial fragmented state.
        std::vector<int> temporaryIds;

        for (const auto& block : initialBlocks) {
            const int id = allocator.allocate(
                block.size,
                "initial block"
            );

            temporaryIds.push_back(id);
        }

        // Free selected blocks to create the desired free-space pattern.
        allocator.freeAllocation(temporaryIds[0]);
        allocator.freeAllocation(temporaryIds[2]);
        allocator.freeAllocation(temporaryIds[3]);

        std::string strategyName;

        switch (strategy) {
            case AllocationStrategy::FirstFit:
                strategyName = "First-fit";
                break;
            case AllocationStrategy::BestFit:
                strategyName = "Best-fit";
                break;
            case AllocationStrategy::WorstFit:
                strategyName = "Worst-fit";
                break;
        }

        std::cout << "\n" << strategyName << ":\n";

        for (const auto request : requests) {
            try {
                const int id = allocator.allocate(
                    request,
                    "request",
                    strategy
                );

                std::cout
                    << "  request=" << request
                    << " -> allocation ID=" << id
                    << "\n";
            } catch (const std::exception& error) {
                std::cout
                    << "  request=" << request
                    << " -> failed: "
                    << error.what()
                    << "\n";
            }
        }

        allocator.printState();
    }
}


// ============================================================================
// 13. ALIGNMENT
// ============================================================================

std::size_t alignUp(
    std::size_t address,
    std::size_t alignment
) {
    if (
        alignment == 0 ||
        (alignment & (alignment - 1)) != 0
    ) {
        throw std::invalid_argument(
            "Alignment must be a positive power of two."
        );
    }

    const std::size_t remainder =
        address % alignment;

    if (remainder == 0) {
        return address;
    }

    return address + alignment - remainder;
}

void demonstrateAlignment() {
    std::cout << "\n"
              << std::string(78, '=')
              << "\n";
    std::cout << "MEMORY ALIGNMENT\n";
    std::cout << std::string(78, '=')
              << "\n";

    for (const std::size_t address : {
        0ULL, 1ULL, 7ULL, 8ULL, 9ULL, 15ULL, 16ULL, 17ULL
    }) {
        std::cout
            << "address=" << std::setw(2) << address
            << " -> aligned="
            << alignUp(address, 8)
            << "\n";
    }

    std::cout
        << "\nAlignment can simplify hardware access requirements and can "
        << "improve performance, but padding consumes memory.\n";
}


// ============================================================================
// 14. VIRTUAL MEMORY DEMONSTRATION
// ============================================================================

void demonstrateVirtualMemory() {
    std::cout << "\n"
              << std::string(78, '=')
              << "\n";
    std::cout << "VIRTUAL MEMORY TRANSLATION\n";
    std::cout << std::string(78, '=')
              << "\n";

    VirtualMemoryManager manager(256, 8);

    manager.mapPage(0, 3, true, true);
    manager.mapPage(1, 7, true, false);
    manager.mapPage(2, 1, false, false);

    for (const std::size_t virtualAddress :
         {0ULL, 10ULL, 255ULL, 256ULL, 300ULL, 512ULL, 700ULL}) {

        try {
            const std::size_t physicalAddress =
                manager.translate(virtualAddress);

            std::cout
                << "virtual=" << std::setw(3)
                << virtualAddress
                << " -> physical="
                << std::setw(4)
                << physicalAddress
                << "\n";
        } catch (const std::exception& error) {
            std::cout
                << "virtual=" << std::setw(3)
                << virtualAddress
                << " -> "
                << error.what()
                << "\n";
        }
    }

    std::cout
        << "\nA real system also uses translation-lookaside buffers, "
        << "multi-level page tables, access permissions, page-fault handling, "
        << "and operating-system policies.\n";
}


// ============================================================================
// 15. MEMORY PROTECTION DEMONSTRATION
// ============================================================================

void demonstrateProtection() {
    std::cout << "\n"
              << std::string(78, '=')
              << "\n";
    std::cout << "MEMORY PROTECTION\n";
    std::cout << std::string(78, '=')
              << "\n";

    ProtectionManager protection(1024);

    protection.addRegion(
        0,
        256,
        true,
        false,
        true,
        "Code"
    );

    protection.addRegion(
        256,
        768,
        true,
        true,
        false,
        "Data"
    );

    protection.addRegion(
        768,
        1024,
        true,
        false,
        false,
        "Read-only data"
    );

    const std::array<std::pair<Address, Permission>, 6> tests{{
        {100, Permission::Read},
        {100, Permission::Write},
        {100, Permission::Execute},
        {500, Permission::Write},
        {500, Permission::Execute},
        {900, Permission::Write}
    }};

    for (const auto& [address, permission] : tests) {
        std::string operation;

        switch (permission) {
            case Permission::Read:
                operation = "read";
                break;
            case Permission::Write:
                operation = "write";
                break;
            case Permission::Execute:
                operation = "execute";
                break;
        }

        std::cout
            << "address=" << address
            << " operation=" << operation
            << " allowed="
            << std::boolalpha
            << protection.allowed(address, permission)
            << std::noboolalpha
            << "\n";
    }
}


// ============================================================================
// 16. MEMORY WORKLOAD AND PERFORMANCE
// ============================================================================

void performanceDemonstration() {
    std::cout << "\n"
              << std::string(78, '=')
              << "\n";
    std::cout << "PERFORMANCE AND LOCALITY DEMONSTRATION\n";
    std::cout << std::string(78, '=')
              << "\n";

    constexpr std::size_t elementCount = 2'000'000;

    std::vector<std::int32_t> data(elementCount);

    for (std::size_t index = 0; index < data.size(); ++index) {
        data[index] = static_cast<std::int32_t>(index);
    }

    auto start = std::chrono::high_resolution_clock::now();

    std::int64_t sequentialSum = 0;

    for (const auto value : data) {
        sequentialSum += value;
    }

    auto end = std::chrono::high_resolution_clock::now();

    const double sequentialMilliseconds =
        std::chrono::duration<double, std::milli>(
            end - start
        ).count();

    start = std::chrono::high_resolution_clock::now();

    std::int64_t stridedSum = 0;

    constexpr std::size_t stride = 64;

    for (std::size_t offset = 0;
         offset < stride;
         ++offset) {

        for (std::size_t index = offset;
             index < data.size();
             index += stride) {

            stridedSum += data[index];
        }
    }

    end = std::chrono::high_resolution_clock::now();

    const double stridedMilliseconds =
        std::chrono::duration<double, std::milli>(
            end - start
        ).count();

    std::cout
        << "Sequential sum: "
        << sequentialSum
        << "\n";

    std::cout
        << "Strided sum:    "
        << stridedSum
        << "\n";

    std::cout
        << "Sequential time: "
        << sequentialMilliseconds
        << " ms\n";

    std::cout
        << "Strided time:    "
        << stridedMilliseconds
        << " ms\n";

    std::cout
        << "\nExact timings depend on processor architecture, cache state, "
        << "compiler optimization, operating-system activity, and system load.\n";

    std::cout
        << "The relevant concept is spatial locality: nearby elements can "
        << "benefit from cache-line transfers.\n";
}


// ============================================================================
// 17. EDGE CASE TESTS
// ============================================================================

void demonstrateEdgeCases() {
    std::cout << "\n"
              << std::string(78, '=')
              << "\n";
    std::cout << "EDGE CASES AND FAILURE CONDITIONS\n";
    std::cout << std::string(78, '=')
              << "\n";

    SimulatedRAM ram(8);

    try {
        ram.readByte(8);
    } catch (const std::exception& error) {
        std::cout
            << "Out-of-range read handled: "
            << error.what()
            << "\n";
    }

    MemoryAllocator allocator(32);

    try {
        allocator.allocate(64, "Too large");
    } catch (const std::exception& error) {
        std::cout
            << "Oversized allocation handled: "
            << error.what()
            << "\n";
    }

    const int id = allocator.allocate(16, "Temporary");
    allocator.freeAllocation(id);

    try {
        allocator.freeAllocation(id);
    } catch (const std::exception& error) {
        std::cout
            << "Double free handled: "
            << error.what()
            << "\n";
    }

    try {
        alignUp(10, 3);
    } catch (const std::exception& error) {
        std::cout
            << "Invalid alignment handled: "
            << error.what()
            << "\n";
    }
}


// ============================================================================
// 18. MAIN INDUSTRY-STYLE CASE STUDY
// ============================================================================

void runSystemCaseStudy() {
    std::cout << "\n"
              << std::string(78, '=')
              << "\n";
    std::cout << "INDUSTRY-STYLE PROCESS MEMORY CASE STUDY\n";
    std::cout << std::string(78, '=')
              << "\n";

    /*
     * We model a 16 KiB memory pool.
     *
     * The simulated operating system creates processes. Each process receives
     * a contiguous allocation. When a process terminates, its allocation is
     * returned to the free list. Adjacent free regions are coalesced.
     */
    ProcessMemoryManager manager(16 * 1024);

    const int browser =
        manager.createProcess("Browser", 4 * 1024);

    const int editor =
        manager.createProcess("Editor", 2 * 1024);

    const int database =
        manager.createProcess("Database", 5 * 1024);

    std::cout
        << "Created PIDs: "
        << browser << ", "
        << editor << ", "
        << database
        << "\n";

    manager.printProcesses();
    manager.printMemory();

    std::cout
        << "\nTerminating Editor to create a hole in the address space...\n";

    manager.terminateProcess(editor);

    manager.printProcesses();
    manager.printMemory();

    std::cout
        << "\nCreating Compiler requiring 3 KiB...\n";

    const int compiler =
        manager.createProcess("Compiler", 3 * 1024);

    std::cout
        << "Compiler PID: "
        << compiler
        << "\n";

    manager.printProcesses();
    manager.printMemory();

    std::cout
        << "\nTerminating Browser and Database...\n";

    manager.terminateProcess(browser);
    manager.terminateProcess(database);

    manager.printProcesses();
    manager.printMemory();

    std::cout
        << "\nMonitor history:\n";

    manager.printMonitor();

    std::cout
        << "\nThis demonstrates a complete lifecycle: allocation, process "
        << "execution, deallocation, fragmentation, reuse, and monitoring.\n";
}


// ============================================================================
// 19. MAIN
// ============================================================================

int main() {
    try {
        std::cout
            << std::string(78, '=')
            << "\n";
        std::cout
            << "MAIN MEMORY TECHNICAL CASE STUDY\n";
        std::cout
            << "RAM | DRAM | SRAM | ADDRESSING | ALLOCATION | VIRTUAL MEMORY\n";
        std::cout
            << std::string(78, '=')
            << "\n";

        std::cout
            << "\nMemory units:\n"
            << "1 KiB = " << BYTES_PER_KIB << " bytes\n"
            << "1 MiB = " << BYTES_PER_MIB << " bytes\n"
            << "1 GiB = " << BYTES_PER_GIB << " bytes\n";

        std::cout
            << "\nMemory hierarchy:\n";

        const std::vector<MemoryLevel> hierarchy{
            {
                "Registers",
                "CPU register structures",
                "Extremely fast",
                "Immediate CPU state"
            },
            {
                "L1 cache",
                "SRAM",
                "Very fast",
                "Frequently accessed data"
            },
            {
                "L2 cache",
                "SRAM",
                "Very fast",
                "Larger nearby cache"
            },
            {
                "L3 cache",
                "SRAM",
                "Fast",
                "Large shared cache"
            },
            {
                "Main memory",
                "DRAM",
                "Slower than cache",
                "Active processes and data"
            },
            {
                "SSD",
                "Flash",
                "Much slower than RAM",
                "Persistent storage"
            }
        };

        for (const auto& level : hierarchy) {
            std::cout
                << "  "
                << std::left
                << std::setw(14)
                << level.name
                << " | "
                << std::setw(26)
                << level.technology
                << " | "
                << level.relativeSpeed
                << "\n";
        }

        std::cout << std::right;

        std::cout
            << "\nDRAM/SRAM cell demonstration:\n";

        MemoryCell dram(MemoryTechnology::DRAM, true);
        MemoryCell sram(MemoryTechnology::SRAM, true);

        for (int i = 0; i < 5; ++i) {
            dram.refresh();
            sram.refresh();
        }

        std::cout
            << "DRAM refreshes: "
            << dram.refreshes()
            << "\n";

        std::cout
            << "SRAM refreshes: "
            << sram.refreshes()
            << "\n";

        std::cout
            << "\nByte-addressable RAM demonstration:\n";

        SimulatedRAM ram(64);

        ram.writeByte(10, 255);
        ram.write(
            20,
            {'H', 'E', 'L', 'L', 'O'}
        );

        std::cout
            << "RAM[10] = "
            << static_cast<int>(ram.readByte(10))
            << "\n";

        std::cout
            << "RAM[20..24] = ";

        for (const Byte value : ram.read(20, 5)) {
            std::cout
                << static_cast<char>(value);
        }

        std::cout << "\n\nMemory dump:\n";
        ram.dump(0, 32);

        runAllocationStrategyComparison();
        demonstrateAlignment();
        demonstrateVirtualMemory();
        demonstrateProtection();
        performanceDemonstration();
        demonstrateEdgeCases();
        runSystemCaseStudy();

        std::cout
            << "\n"
            << std::string(78, '=')
            << "\n";
        std::cout
            << "END OF MAIN MEMORY CASE STUDY\n";
        std::cout
            << std::string(78, '=')
            << "\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << "\n";

        return 1;
    }
}
