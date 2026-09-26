/*
    STORAGE SYSTEMS
    HDD, SSD, flash storage, file storage, and block storage.

    C++17 case study:
    A simplified storage service for an enterprise document repository.

    The program demonstrates:
    - storage media concepts,
    - block devices,
    - block allocation,
    - file metadata,
    - checksums,
    - caching,
    - RAID striping,
    - workload estimation,
    - validation,
    - failure handling,
    - performance reasoning,
    - and an application-level storage service.

    Compile:
        g++ -std=c++17 -O2 storage_systems.cpp -o storage_systems

    Run:
        ./storage_systems
*/

#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <list>
#include <map>
#include <optional>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace fs = std::filesystem;
using Byte = std::uint8_t;
using Bytes = std::vector<Byte>;


// ============================================================================
// 1. GENERAL UTILITIES
// ============================================================================

void printSection(const std::string& title) {
    std::cout << "\n" << std::string(78, '=') << "\n";
    std::cout << title << "\n";
    std::cout << std::string(78, '=') << "\n";
}

std::string humanBytes(std::uint64_t bytes) {
    if (bytes < 1024) {
        return std::to_string(bytes) + " B";
    }

    const std::array<std::string, 5> units = {
        "KiB", "MiB", "GiB", "TiB", "PiB"
    };

    double value = static_cast<double>(bytes);

    for (const auto& unit : units) {
        value /= 1024.0;

        if (value < 1024.0) {
            std::ostringstream output;
            output << std::fixed << std::setprecision(2)
                   << value << " " << unit;
            return output.str();
        }
    }

    std::ostringstream output;
    output << std::fixed << std::setprecision(2)
           << value << " EiB";
    return output.str();
}

Bytes stringToBytes(const std::string& value) {
    return Bytes(value.begin(), value.end());
}

std::string bytesToString(const Bytes& value) {
    return std::string(value.begin(), value.end());
}


// ============================================================================
// 2. STORAGE MEDIA
// ============================================================================

enum class StorageTechnology {
    HDD,
    SSD,
    FLASH
};

struct StorageProfile {
    StorageTechnology technology;
    bool movingParts;
    double latencyMicroseconds;
    std::uint64_t iops;
    double sequentialReadMBps;
    double sequentialWriteMBps;
};

std::string technologyName(StorageTechnology technology) {
    switch (technology) {
        case StorageTechnology::HDD:
            return "HDD";
        case StorageTechnology::SSD:
            return "SSD";
        case StorageTechnology::FLASH:
            return "Flash";
    }

    return "Unknown";
}

void demonstrateMedia() {
    printSection("1. STORAGE MEDIA");

    const std::vector<StorageProfile> profiles = {
        {
            StorageTechnology::HDD,
            true,
            5000,
            150,
            180,
            160
        },
        {
            StorageTechnology::SSD,
            false,
            100,
            100000,
            550,
            500
        },
        {
            StorageTechnology::FLASH,
            false,
            80,
            80000,
            400,
            350
        }
    };

    for (const auto& profile : profiles) {
        std::cout << "\n" << technologyName(profile.technology) << "\n";
        std::cout << "Moving parts: "
                  << std::boolalpha << profile.movingParts << "\n";
        std::cout << "Illustrative latency: "
                  << profile.latencyMicroseconds << " us\n";
        std::cout << "Illustrative IOPS: "
                  << profile.iops << "\n";
        std::cout << "Sequential read: "
                  << profile.sequentialReadMBps << " MB/s\n";
        std::cout << "Sequential write: "
                  << profile.sequentialWriteMBps << " MB/s\n";
    }

    std::cout << R"(
HDD stores data magnetically on rotating platters and uses mechanical heads.

SSD is a solid-state storage product. It normally contains NAND flash,
a controller, firmware, an FTL, error correction, and other management logic.

Flash is the underlying non-volatile semiconductor technology used by many
storage products.

The numerical values are illustrative rather than universal specifications.
)" << "\n";
}


// ============================================================================
// 3. HDD ACCESS MODEL
// ============================================================================

class HDDModel {
private:
    std::size_t tracks_;
    std::size_t sectorsPerTrack_;
    std::size_t bytesPerSector_;
    double rpm_;

public:
    HDDModel(
        std::size_t tracks,
        std::size_t sectorsPerTrack,
        std::size_t bytesPerSector,
        double rpm
    )
        : tracks_(tracks),
          sectorsPerTrack_(sectorsPerTrack),
          bytesPerSector_(bytesPerSector),
          rpm_(rpm) {
        if (
            tracks_ == 0 ||
            sectorsPerTrack_ == 0 ||
            bytesPerSector_ == 0 ||
            rpm_ <= 0
        ) {
            throw std::invalid_argument("Invalid HDD geometry");
        }
    }

    std::uint64_t capacityBytes() const {
        return static_cast<std::uint64_t>(tracks_) *
               sectorsPerTrack_ *
               bytesPerSector_;
    }

    double rotationPeriodMs() const {
        return 60000.0 / rpm_;
    }

    struct AccessEstimate {
        double seekMs;
        double rotationalLatencyMs;
        double transferMs;
        double totalMs;
    };

    AccessEstimate estimateAccess(
        std::size_t currentTrack,
        std::size_t requestedTrack
    ) const {
        if (
            currentTrack >= tracks_ ||
            requestedTrack >= tracks_
        ) {
            throw std::out_of_range("Track outside HDD geometry");
        }

        const double distance = std::abs(
            static_cast<double>(requestedTrack) -
            static_cast<double>(currentTrack)
        );

        const double seekMs = 2.0 + distance * 0.02;
        const double rotationalLatencyMs = rotationPeriodMs() / 2.0;
        const double transferMs =
            rotationPeriodMs() /
            static_cast<double>(sectorsPerTrack_);

        return {
            seekMs,
            rotationalLatencyMs,
            transferMs,
            seekMs + rotationalLatencyMs + transferMs
        };
    }
};

void demonstrateHDD() {
    printSection("2. HDD MECHANICAL ACCESS");

    HDDModel disk(10000, 512, 512, 7200);
    const auto estimate = disk.estimateAccess(100, 4100);

    std::cout << "Capacity: "
              << humanBytes(disk.capacityBytes()) << "\n";

    std::cout << std::fixed << std::setprecision(3);
    std::cout << "Rotation period: "
              << disk.rotationPeriodMs() << " ms\n";

    std::cout << "Seek: "
              << estimate.seekMs << " ms\n";

    std::cout << "Rotational latency: "
              << estimate.rotationalLatencyMs << " ms\n";

    std::cout << "Transfer: "
              << estimate.transferMs << " ms\n";

    std::cout << "Total: "
              << estimate.totalMs << " ms\n";

    std::cout << R"(
HDD latency is affected by mechanical positioning.

A simplified access can be viewed as:
seek + rotational latency + transfer.

This is why sequential access can be substantially more efficient than many
small random operations.
)" << "\n";
}


// ============================================================================
// 4. FLASH CONCEPTS
// ============================================================================

void demonstrateFlash() {
    printSection("3. NAND FLASH");

    struct CellType {
        std::string name;
        int bitsPerCell;
    };

    const std::vector<CellType> types = {
        {"SLC", 1},
        {"MLC", 2},
        {"TLC", 3},
        {"QLC", 4}
    };

    for (const auto& type : types) {
        std::cout << type.name << ": "
                  << type.bitsPerCell
                  << " bit(s) per cell\n";
    }

    std::cout << R"(
Important concepts:

FTL:
    Maps logical block addresses to physical flash locations.

Wear leveling:
    Distributes writes to avoid repeatedly wearing the same cells.

Garbage collection:
    Moves valid pages and reclaims blocks whose old pages are obsolete.

TRIM/deallocate:
    Allows the host to tell a device that logical ranges are no longer needed.

ECC:
    Error-correcting mechanisms compensate for bit errors.

Over-provisioning:
    Reserves physical flash for management, replacement, and performance.

NAND generally programs pages but erases larger blocks. SSD firmware therefore
performs address translation and data movement that applications do not see.
)" << "\n";
}


// ============================================================================
// 5. BLOCK DEVICE
// ============================================================================

class BlockDevice {
private:
    std::size_t blockSize_;
    std::size_t blockCount_;
    Bytes storage_;

    void validateBlock(std::size_t block) const {
        if (block >= blockCount_) {
            throw std::out_of_range("Block outside device range");
        }
    }

public:
    BlockDevice(std::size_t blockSize, std::size_t blockCount)
        : blockSize_(blockSize),
          blockCount_(blockCount),
          storage_(blockSize * blockCount, 0) {
        if (blockSize_ == 0 || blockCount_ == 0) {
            throw std::invalid_argument(
                "Block size and block count must be positive"
            );
        }
    }

    std::size_t blockSize() const {
        return blockSize_;
    }

    std::size_t blockCount() const {
        return blockCount_;
    }

    std::size_t capacity() const {
        return storage_.size();
    }

    Bytes readBlock(std::size_t block) const {
        validateBlock(block);

        const auto start = storage_.begin() +
                           static_cast<std::ptrdiff_t>(
                               block * blockSize_
                           );

        return Bytes(
            start,
            start + static_cast<std::ptrdiff_t>(blockSize_)
        );
    }

    void writeBlock(std::size_t block, const Bytes& data) {
        validateBlock(block);

        if (data.size() != blockSize_) {
            throw std::invalid_argument(
                "Write must contain exactly one block"
            );
        }

        std::copy(
            data.begin(),
            data.end(),
            storage_.begin() +
                static_cast<std::ptrdiff_t>(block * blockSize_)
        );
    }
};

void demonstrateBlockDevice() {
    printSection("4. BLOCK STORAGE");

    BlockDevice device(512, 100);

    std::cout << "Capacity: "
              << humanBytes(device.capacity()) << "\n";

    Bytes record = stringToBytes("BLOCK-DEVICE-RECORD");
    record.resize(device.blockSize(), 0);

    device.writeBlock(7, record);

    const Bytes result = device.readBlock(7);

    std::cout << "Block 7 begins with: "
              << bytesToString(
                     Bytes(
                         result.begin(),
                         result.begin() +
                             static_cast<std::ptrdiff_t>(19)
                     )
                 )
              << "\n";

    try {
        device.readBlock(100);
    } catch (const std::exception& error) {
        std::cout << "Invalid block rejected: "
                  << error.what() << "\n";
    }
}


// ============================================================================
// 6. SIMPLE FILESYSTEM
// ============================================================================

struct FileMetadata {
    std::string name;
    std::size_t size;
    std::vector<std::size_t> blocks;
    std::string checksum;
};

class SimpleFileSystem {
private:
    BlockDevice& device_;
    std::vector<bool> allocated_;
    std::map<std::string, FileMetadata> files_;

public:
    explicit SimpleFileSystem(BlockDevice& device)
        : device_(device),
          allocated_(device.blockCount(), false) {}

    static std::string checksum(const Bytes& data) {
        // Educational non-cryptographic checksum.
        // A production integrity mechanism should use a standardized
        // cryptographic hash or storage-integrity facility.
        std::uint64_t value = 1469598103934665603ULL;

        for (Byte byte : data) {
            value ^= byte;
            value *= 1099511628211ULL;
        }

        std::ostringstream output;
        output << std::hex << value;
        return output.str();
    }

    void createFile(const std::string& name, const Bytes& data) {
        if (name.empty() || name.find('/') != std::string::npos) {
            throw std::invalid_argument("Invalid file name");
        }

        if (files_.contains(name)) {
            throw std::runtime_error("File already exists");
        }

        const std::size_t requiredBlocks =
            std::max<std::size_t>(
                1,
                (data.size() + device_.blockSize() - 1) /
                    device_.blockSize()
            );

        std::vector<std::size_t> selected;

        for (std::size_t block = 0;
             block < allocated_.size() &&
             selected.size() < requiredBlocks;
             ++block) {
            if (!allocated_[block]) {
                selected.push_back(block);
            }
        }

        if (selected.size() != requiredBlocks) {
            throw std::runtime_error("Insufficient free blocks");
        }

        // Allocate all blocks only after verifying capacity.
        for (std::size_t block : selected) {
            allocated_[block] = true;
        }

        Bytes padded(
            requiredBlocks * device_.blockSize(),
            0
        );

        std::copy(data.begin(), data.end(), padded.begin());

        for (std::size_t index = 0; index < selected.size(); ++index) {
            Bytes blockData(
                padded.begin() +
                    static_cast<std::ptrdiff_t>(
                        index * device_.blockSize()
                    ),
                padded.begin() +
                    static_cast<std::ptrdiff_t>(
                        (index + 1) * device_.blockSize()
                    )
            );

            device_.writeBlock(selected[index], blockData);
        }

        files_.emplace(
            name,
            FileMetadata{
                name,
                data.size(),
                selected,
                checksum(data)
            }
        );
    }

    Bytes readFile(const std::string& name) const {
        const auto iterator = files_.find(name);

        if (iterator == files_.end()) {
            throw std::runtime_error("File not found");
        }

        const auto& metadata = iterator->second;

        Bytes result;
        result.reserve(metadata.size);

        for (std::size_t block : metadata.blocks) {
            const Bytes data = device_.readBlock(block);

            const std::size_t remaining =
                metadata.size - result.size();

            const std::size_t amount =
                std::min(remaining, data.size());

            result.insert(
                result.end(),
                data.begin(),
                data.begin() +
                    static_cast<std::ptrdiff_t>(amount)
            );

            if (result.size() == metadata.size) {
                break;
            }
        }

        if (checksum(result) != metadata.checksum) {
            throw std::runtime_error("Filesystem integrity check failed");
        }

        return result;
    }

    void deleteFile(const std::string& name) {
        const auto iterator = files_.find(name);

        if (iterator == files_.end()) {
            throw std::runtime_error("File not found");
        }

        for (std::size_t block : iterator->second.blocks) {
            allocated_[block] = false;
        }

        files_.erase(iterator);
    }

    std::size_t freeBlocks() const {
        return static_cast<std::size_t>(
            std::count(
                allocated_.begin(),
                allocated_.end(),
                false
            )
        );
    }

    std::size_t fileCount() const {
        return files_.size();
    }
};

void demonstrateFilesystem() {
    printSection("5. FILE STORAGE ON BLOCK STORAGE");

    BlockDevice device(128, 64);
    SimpleFileSystem filesystem(device);

    const Bytes content = stringToBytes(
        "A filesystem maps human-readable file names to blocks."
    );

    filesystem.createFile("document.txt", content);

    std::cout << "Free blocks: "
              << filesystem.freeBlocks() << "\n";

    std::cout << "Files: "
              << filesystem.fileCount() << "\n";

    std::cout << "Content: "
              << bytesToString(
                     filesystem.readFile("document.txt")
                 )
              << "\n";

    filesystem.deleteFile("document.txt");

    std::cout << "Free blocks after deletion: "
              << filesystem.freeBlocks() << "\n";
}


// ============================================================================
// 7. LRU CACHE
// ============================================================================

class LRUCache {
private:
    using ListIterator =
        std::list<std::pair<int, Bytes>>::iterator;

    std::size_t capacity_;
    std::list<std::pair<int, Bytes>> entries_;
    std::unordered_map<int, ListIterator> index_;

    std::size_t hits_ = 0;
    std::size_t misses_ = 0;

public:
    explicit LRUCache(std::size_t capacity)
        : capacity_(capacity) {
        if (capacity_ == 0) {
            throw std::invalid_argument(
                "Cache capacity must be positive"
            );
        }
    }

    std::optional<Bytes> get(int key) {
        const auto iterator = index_.find(key);

        if (iterator == index_.end()) {
            ++misses_;
            return std::nullopt;
        }

        entries_.splice(
            entries_.end(),
            entries_,
            iterator->second
        );

        ++hits_;
        return iterator->second->second;
    }

    void put(int key, const Bytes& value) {
        const auto iterator = index_.find(key);

        if (iterator != index_.end()) {
            iterator->second->second = value;

            entries_.splice(
                entries_.end(),
                entries_,
                iterator->second
            );

            return;
        }

        entries_.emplace_back(key, value);
        auto listIterator = std::prev(entries_.end());
        index_[key] = listIterator;

        if (entries_.size() > capacity_) {
            const int oldestKey = entries_.front().first;
            index_.erase(oldestKey);
            entries_.pop_front();
        }
    }

    double hitRate() const {
        const std::size_t total = hits_ + misses_;

        if (total == 0) {
            return 0.0;
        }

        return static_cast<double>(hits_) /
               static_cast<double>(total);
    }

    std::size_t hits() const {
        return hits_;
    }

    std::size_t misses() const {
        return misses_;
    }
};

void demonstrateCache() {
    printSection("6. STORAGE CACHE");

    LRUCache cache(3);
    const std::vector<int> accessPattern =
        {1, 2, 3, 1, 2, 4, 1, 5, 1};

    for (int block : accessPattern) {
        const auto result = cache.get(block);

        if (!result.has_value()) {
            cache.put(
                block,
                stringToBytes("block-" + std::to_string(block))
            );

            std::cout << "MISS " << block << "\n";
        } else {
            std::cout << "HIT  " << block << "\n";
        }
    }

    std::cout << "Hits: "
              << cache.hits() << "\n";

    std::cout << "Misses: "
              << cache.misses() << "\n";

    std::cout << "Hit rate: "
              << std::fixed << std::setprecision(2)
              << cache.hitRate() * 100.0
              << "%\n";
}


// ============================================================================
// 8. RAID 0 STRIPING
// ============================================================================

std::vector<std::vector<std::string>> raid0Stripe(
    const std::vector<std::string>& blocks,
    std::size_t diskCount
) {
    if (diskCount == 0) {
        throw std::invalid_argument("Disk count must be positive");
    }

    std::vector<std::vector<std::string>> disks(diskCount);

    for (std::size_t index = 0; index < blocks.size(); ++index) {
        disks[index % diskCount].push_back(blocks[index]);
    }

    return disks;
}

void demonstrateRAID() {
    printSection("7. RAID 0 STRIPING");

    const std::vector<std::string> blocks = {
        "A", "B", "C", "D", "E", "F", "G", "H"
    };

    const auto disks = raid0Stripe(blocks, 4);

    for (std::size_t index = 0; index < disks.size(); ++index) {
        std::cout << "Disk " << index << ": ";

        for (const auto& block : disks[index]) {
            std::cout << block << " ";
        }

        std::cout << "\n";
    }

    std::cout << R"(
RAID 0 demonstrates striping without redundancy.

RAID 1 mirrors data.
RAID 5 uses distributed parity.
RAID 6 uses dual distributed parity.
RAID 10 combines mirroring and striping.

RAID is a storage availability/performance technique, not a complete backup
strategy.
)" << "\n";
}


// ============================================================================
// 9. WORKLOAD MODEL
// ============================================================================

struct Workload {
    std::string name;
    std::uint64_t operationSizeBytes;
    std::uint64_t operations;
    bool sequential;
};

double estimateWorkload(
    const Workload& workload,
    double throughputMBps,
    std::uint64_t iops
) {
    if (workload.operations == 0) {
        throw std::invalid_argument(
            "Workload must contain operations"
        );
    }

    if (workload.sequential) {
        const double totalBytes =
            static_cast<double>(
                workload.operationSizeBytes
            ) *
            static_cast<double>(workload.operations);

        return totalBytes /
               (throughputMBps * 1024.0 * 1024.0);
    }

    return static_cast<double>(workload.operations) /
           static_cast<double>(iops);
}

void demonstrateWorkloads() {
    printSection("8. STORAGE WORKLOAD MODEL");

    const Workload sequential{
        "Large sequential backup",
        1024 * 1024,
        1000,
        true
    };

    const Workload random{
        "Small random database operations",
        4096,
        100000,
        false
    };

    constexpr double ssdThroughput = 550.0;
    constexpr std::uint64_t ssdIops = 100000;

    std::cout << sequential.name << ": "
              << estimateWorkload(
                     sequential,
                     ssdThroughput,
                     ssdIops
                 )
              << " seconds\n";

    std::cout << random.name << ": "
              << estimateWorkload(
                     random,
                     ssdThroughput,
                     ssdIops
                 )
              << " seconds\n";

    std::cout << R"(
IOPS is especially important for small random requests.
Throughput is especially important for large sequential transfers.
Latency describes responsiveness.
Queue depth controls how many operations may be outstanding.

Real benchmarks must measure the actual workload because device specifications
alone cannot predict every application.
)" << "\n";
}


// ============================================================================
// 10. FILE STORAGE SERVICE
// ============================================================================

class FileStorageService {
private:
    fs::path root_;
    std::map<std::string, std::string> checksums_;

    fs::path safePath(const std::string& relativePath) const {
        if (relativePath.empty()) {
            throw std::invalid_argument("Path cannot be empty");
        }

        const fs::path candidate =
            fs::weakly_canonical(root_ / relativePath);

        const fs::path rootCanonical =
            fs::weakly_canonical(root_);

        const auto relative =
            candidate.lexically_relative(rootCanonical);

        if (
            relative.empty() ||
            relative == ".." ||
            std::string(relative.string()).starts_with("../")
        ) {
            throw std::runtime_error(
                "Path escapes storage root"
            );
        }

        return candidate;
    }

    static std::string checksum(const Bytes& data) {
        // Educational checksum. A production service should use a standard
        // cryptographic hash such as SHA-256 through a vetted implementation.
        std::uint64_t value = 1469598103934665603ULL;

        for (Byte byte : data) {
            value ^= byte;
            value *= 1099511628211ULL;
        }

        std::ostringstream output;
        output << std::hex << value;
        return output.str();
    }

public:
    explicit FileStorageService(fs::path root)
        : root_(std::move(root)) {
        fs::create_directories(root_);
    }

    void store(
        const std::string& name,
        const Bytes& data
    ) {
        const fs::path destination = safePath(name);

        fs::create_directories(destination.parent_path());

        // Write to a temporary file and rename it into place. This reduces
        // the chance that readers observe a partially written replacement.
        const fs::path temporary =
            destination.string() + ".tmp";

        {
            std::ofstream output(
                temporary,
                std::ios::binary |
                std::ios::trunc
            );

            if (!output) {
                throw std::runtime_error(
                    "Unable to open temporary file"
                );
            }

            output.write(
                reinterpret_cast<const char*>(data.data()),
                static_cast<std::streamsize>(data.size())
            );

            if (!output) {
                throw std::runtime_error(
                    "Storage write failed"
                );
            }
        }

        fs::rename(temporary, destination);

        checksums_[name] = checksum(data);
    }

    Bytes retrieve(const std::string& name) const {
        const fs::path source = safePath(name);

        std::ifstream input(
            source,
            std::ios::binary
        );

        if (!input) {
            throw std::runtime_error(
                "Unable to open stored file"
            );
        }

        Bytes data(
            std::istreambuf_iterator<char>(input),
            std::istreambuf_iterator<char>()
        );

        const auto checksumIterator = checksums_.find(name);

        if (
            checksumIterator != checksums_.end() &&
            checksum(data) != checksumIterator->second
        ) {
            throw std::runtime_error(
                "Storage integrity verification failed"
            );
        }

        return data;
    }

    void remove(const std::string& name) {
        const fs::path target = safePath(name);

        if (!fs::exists(target)) {
            throw std::runtime_error(
                "Stored file does not exist"
            );
        }

        fs::remove(target);
        checksums_.erase(name);
    }
};


// ============================================================================
// 11. ENTERPRISE DOCUMENT REPOSITORY CASE STUDY
// ============================================================================

struct Document {
    std::string id;
    std::string filename;
    std::string owner;
    std::size_t size;
    std::string checksum;
};

class DocumentRepository {
private:
    FileStorageService storage_;
    std::map<std::string, Document> catalog_;

    static bool validIdentifier(const std::string& id) {
        if (id.empty()) {
            return false;
        }

        for (char character : id) {
            if (
                !(std::isalnum(
                      static_cast<unsigned char>(character)
                  ) ||
                  character == '-' ||
                  character == '_')
            ) {
                return false;
            }
        }

        return true;
    }

    static std::string catalogKey(
        const std::string& documentId
    ) {
        return "documents/" + documentId + ".bin";
    }

public:
    explicit DocumentRepository(const fs::path& root)
        : storage_(root) {}

    void upload(
        const std::string& documentId,
        const std::string& filename,
        const std::string& owner,
        const Bytes& content
    ) {
        if (!validIdentifier(documentId)) {
            throw std::invalid_argument(
                "Invalid document identifier"
            );
        }

        if (filename.empty()) {
            throw std::invalid_argument(
                "Filename cannot be empty"
            );
        }

        if (owner.empty()) {
            throw std::invalid_argument(
                "Owner cannot be empty"
            );
        }

        if (catalog_.contains(documentId)) {
            throw std::runtime_error(
                "Document already exists"
            );
        }

        if (content.empty()) {
            throw std::invalid_argument(
                "Empty documents are not permitted in this example"
            );
        }

        const std::string key =
            catalogKey(documentId);

        storage_.store(key, content);

        // Same educational checksum used by the underlying service.
        std::uint64_t hash = 1469598103934665603ULL;

        for (Byte byte : content) {
            hash ^= byte;
            hash *= 1099511628211ULL;
        }

        std::ostringstream checksum;
        checksum << std::hex << hash;

        catalog_.emplace(
            documentId,
            Document{
                documentId,
                filename,
                owner,
                content.size(),
                checksum.str()
            }
        );
    }

    Bytes download(
        const std::string& documentId
    ) const {
        const auto iterator =
            catalog_.find(documentId);

        if (iterator == catalog_.end()) {
            throw std::runtime_error(
                "Document not found"
            );
        }

        return storage_.retrieve(
            catalogKey(documentId)
        );
    }

    void remove(
        const std::string& documentId
    ) {
        const auto iterator =
            catalog_.find(documentId);

        if (iterator == catalog_.end()) {
            throw std::runtime_error(
                "Document not found"
            );
        }

        storage_.remove(
            catalogKey(documentId)
        );

        catalog_.erase(iterator);
    }

    void printCatalog() const {
        std::cout << "\nDocument catalog:\n";

        for (const auto& [id, document] : catalog_) {
            std::cout
                << "  ID: " << id
                << " | filename: " << document.filename
                << " | owner: " << document.owner
                << " | size: " << document.size
                << " bytes"
                << " | checksum: " << document.checksum
                << "\n";
        }
    }
};


// ============================================================================
// 12. CASE STUDY EXECUTION
// ============================================================================

void demonstrateDocumentRepository() {
    printSection("9. INDUSTRY-STYLE DOCUMENT REPOSITORY");

    const fs::path root =
        fs::temp_directory_path() /
        "storage_systems_cpp_case_study";

    std::error_code cleanupError;
    fs::remove_all(root, cleanupError);

    try {
        DocumentRepository repository(root);

        const Bytes document =
            stringToBytes(
                "Enterprise document content stored through a "
                "filesystem abstraction."
            );

        repository.upload(
            "DOC-1001",
            "architecture.txt",
            "operations-team",
            document
        );

        repository.upload(
            "DOC-1002",
            "capacity-plan.txt",
            "infrastructure-team",
            stringToBytes(
                "Capacity planning must account for growth, "
                "redundancy, backups, and workload patterns."
            )
        );

        repository.printCatalog();

        const Bytes downloaded =
            repository.download("DOC-1001");

        std::cout << "\nDownloaded content:\n"
                  << bytesToString(downloaded)
                  << "\n";

        try {
            repository.upload(
                "../INVALID",
                "bad.txt",
                "attacker",
                stringToBytes("unsafe")
            );
        } catch (const std::exception& error) {
            std::cout
                << "\nRejected invalid document ID: "
                << error.what()
                << "\n";
        }

        try {
            repository.download("UNKNOWN");
        } catch (const std::exception& error) {
            std::cout
                << "Missing document handled: "
                << error.what()
                << "\n";
        }

        repository.remove("DOC-1002");

        try {
            repository.download("DOC-1002");
        } catch (const std::exception& error) {
            std::cout
                << "Deleted document handled: "
                << error.what()
                << "\n";
        }
    }
    catch (const std::exception& error) {
        std::cerr
            << "Repository case study failed: "
            << error.what()
            << "\n";
    }

    fs::remove_all(root, cleanupError);
}


// ============================================================================
// 13. EDGE CASES
// ============================================================================

void demonstrateEdgeCases() {
    printSection("10. EDGE CASES AND FAILURE CONDITIONS");

    try {
        BlockDevice invalidDevice(0, 10);
    } catch (const std::exception& error) {
        std::cout
            << "Invalid block size rejected: "
            << error.what()
            << "\n";
    }

    try {
        BlockDevice device(512, 2);
        device.writeBlock(0, stringToBytes("too small"));
    } catch (const std::exception& error) {
        std::cout
            << "Invalid block write rejected: "
            << error.what()
            << "\n";
    }

    try {
        BlockDevice device(128, 1);
        SimpleFileSystem filesystem(device);

        filesystem.createFile(
            "large.bin",
            Bytes(129, 42)
        );
    } catch (const std::exception& error) {
        std::cout
            << "Insufficient capacity handled: "
            << error.what()
            << "\n";
    }

    std::cout << R"(
Important storage failure cases include:
- Device full.
- Invalid address.
- Partial write.
- Permission failure.
- Corrupt metadata.
- Device failure.
- Interrupted operation.
- Unexpected power loss.
- Path traversal.
- Missing object.
- Integrity mismatch.
- Simultaneous access.
- Backup restoration failure.

Good storage software makes failure visible and testable.
)" << "\n";
}


// ============================================================================
// 14. DESIGN AND PERFORMANCE DISCUSSION
// ============================================================================

void discussDesign() {
    printSection("11. DESIGN, PERFORMANCE, AND SECURITY");

    std::cout << R"(
Design decisions:

1. Block size
   Larger blocks can improve sequential efficiency but may increase internal
   waste for small records.

2. Allocation
   Simple contiguous or sequential allocation is easy to understand, while
   production filesystems use sophisticated allocation strategies.

3. Caching
   Reduces repeated device access but introduces consistency and durability
   concerns.

4. Checksums
   Detect corruption but do not provide recovery without another valid copy.

5. RAID
   Can provide redundancy or parallelism but is not a substitute for backup.

6. SSD endurance
   Flash has finite program/erase behavior. Controllers use wear leveling,
   garbage collection and over-provisioning.

7. Security
   Access control, encryption, key management, auditing and secure deletion
   policies must cover primary storage and backups.

8. Capacity planning
   A device that reaches very high utilization can experience operational
   and performance problems. Growth should be measured continuously.

9. Benchmarking
   Real workloads should be measured using realistic block sizes, access
   patterns, queue depths and read/write ratios.

10. Failure domains
    Redundancy is stronger when copies are independent across meaningful
    failure boundaries.

The C++ case study separates:
    application -> document repository -> file storage -> filesystem-like
    abstraction -> blocks -> physical storage concept.

That separation mirrors the layered nature of real storage systems.
)" << "\n";
}


// ============================================================================
// 15. MAIN
// ============================================================================

int main() {
    try {
        demonstrateMedia();
        demonstrateHDD();
        demonstrateFlash();
        demonstrateBlockDevice();
        demonstrateFilesystem();
        demonstrateCache();
        demonstrateRAID();
        demonstrateWorkloads();
        demonstrateDocumentRepository();
        demonstrateEdgeCases();
        discussDesign();

        printSection("12. CASE STUDY COMPLETE");

        std::cout << R"(
The program demonstrated the relationship between physical storage media,
logical block storage, filesystems, application-level file storage, caching,
integrity, redundancy, workload characteristics, and security.

The central architectural principle is that storage is layered. An application
usually interacts with an abstraction rather than directly controlling the
physical sectors or flash cells underneath it.
)" << "\n";

        return 0;
    }
    catch (const std::exception& error) {
        std::cerr
            << "Fatal storage-system error: "
            << error.what()
            << "\n";

        return 1;
    }
}
