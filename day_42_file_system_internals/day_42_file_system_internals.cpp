#include <algorithm>
#include <cstdint>
#include <exception>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using BlockNumber = std::size_t;
using InodeNumber = std::size_t;

enum class FileType {
    Regular,
    Directory
};

enum class JournalState {
    Prepared,
    Committed
};

struct Superblock {
    std::string magic = "CPP-FS-INTERNALS";
    std::size_t blockSize{};
    std::size_t totalBlocks{};
    std::size_t inodeLimit{};
    InodeNumber rootInode{};
    std::size_t journalStart{};
    std::size_t journalBlocks{};
    std::uint64_t generation{1};
    bool clean{true};
};

struct Inode {
    InodeNumber number{};
    FileType type{};
    std::uint32_t mode{};
    InodeNumber parent{};
    std::size_t size{};
    std::size_t linkCount{};
    std::vector<BlockNumber> directBlocks;
    std::optional<BlockNumber> indirectBlock;
    std::vector<BlockNumber> indirectEntries;

    std::vector<BlockNumber> dataBlocks() const {
        std::vector<BlockNumber> result = directBlocks;
        result.insert(
            result.end(),
            indirectEntries.begin(),
            indirectEntries.end()
        );
        return result;
    }
};

struct DirectoryEntry {
    std::string name;
    InodeNumber inode;
};

struct JournalRecord {
    std::uint64_t id{};
    std::string description;
    JournalState state{JournalState::Prepared};

    /*
     * The case study journals logical metadata snapshots. A production
     * filesystem may use physical redo logging, metadata-only journaling,
     * ordered data, copy-on-write structures, or another persistence model.
     */
    std::unordered_map<InodeNumber, Inode> inodeSnapshots;
    std::unordered_map<InodeNumber, std::vector<DirectoryEntry>>
        directorySnapshots;
    Superblock superblockSnapshot;
};

class FileSystemError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};

class AllocationError : public FileSystemError {
public:
    using FileSystemError::FileSystemError;
};

class RepositoryStorageEngine {
private:
    static constexpr std::size_t DirectBlockLimit = 4;

    Superblock superblock_;
    std::vector<std::vector<std::uint8_t>> disk_;
    std::set<BlockNumber> metadataBlocks_;
    std::set<BlockNumber> allocatedBlocks_;

    std::unordered_map<InodeNumber, Inode> inodes_;
    std::unordered_map<InodeNumber, std::vector<DirectoryEntry>>
        directories_;

    std::vector<JournalRecord> journal_;
    InodeNumber nextInode_{1};
    std::uint64_t nextTransaction_{1};
    bool mounted_{false};

public:
    RepositoryStorageEngine(
        std::size_t blockSize,
        std::size_t totalBlocks,
        std::size_t inodeLimit,
        std::size_t journalBlocks
    ) {
        if (blockSize == 0 || totalBlocks < 48 || inodeLimit < 4) {
            throw std::invalid_argument("Invalid filesystem geometry");
        }

        if (8 + journalBlocks >= totalBlocks) {
            throw std::invalid_argument("Journal consumes too much disk space");
        }

        superblock_.blockSize = blockSize;
        superblock_.totalBlocks = totalBlocks;
        superblock_.inodeLimit = inodeLimit;
        superblock_.rootInode = 1;
        superblock_.journalStart = 8;
        superblock_.journalBlocks = journalBlocks;

        disk_.resize(
            totalBlocks,
            std::vector<std::uint8_t>(blockSize, 0)
        );

        for (BlockNumber block = 0; block < 8 + journalBlocks; ++block) {
            metadataBlocks_.insert(block);
            allocatedBlocks_.insert(block);
        }

        Inode root;
        root.number = allocateInodeNumber();
        root.type = FileType::Directory;
        root.mode = 0755;
        root.parent = root.number;
        root.linkCount = 2;

        inodes_.emplace(root.number, root);
        directories_[root.number] = {
            {".", root.number},
            {"..", root.number}
        };
    }

    void mount() {
        if (mounted_) {
            return;
        }

        if (superblock_.magic != "CPP-FS-INTERNALS") {
            throw FileSystemError("Invalid filesystem magic");
        }

        if (!superblock_.clean) {
            recoverJournal();
        }

        consistencyCheck();
        mounted_ = true;

        std::cout
            << "[mount] filesystem mounted at generation "
            << superblock_.generation
            << "\n";
    }

    void unmount() {
        requireMounted();
        consistencyCheck();

        superblock_.clean = true;
        mounted_ = false;

        std::cout << "[mount] filesystem cleanly unmounted\n";
    }

    void simulateCrash() {
        requireMounted();

        /*
         * No orderly unmount occurs during a crash. The clean flag therefore
         * records that recovery may be required on the next mount.
         */
        superblock_.clean = false;
        mounted_ = false;

        std::cout << "[crash] simulated power loss\n";
    }

    InodeNumber createFile(
        const std::string& path,
        std::uint32_t mode = 0644
    ) {
        requireMounted();

        auto [parent, name] = parentAndName(path);
        validateName(name);

        if (findDirectoryEntry(parent, name).has_value()) {
            throw FileSystemError("Directory entry already exists");
        }

        JournalRecord transaction = beginTransaction(
            "create regular file " + path,
            {parent},
            {parent}
        );

        Inode inode;
        inode.number = allocateInodeNumber();
        inode.type = FileType::Regular;
        inode.mode = mode;
        inode.parent = parent;
        inode.linkCount = 1;

        inodes_[inode.number] = inode;
        directories_[parent].push_back({name, inode.number});

        commit(transaction);
        return inode.number;
    }

    InodeNumber createDirectory(
        const std::string& path,
        std::uint32_t mode = 0755
    ) {
        requireMounted();

        auto [parent, name] = parentAndName(path);
        validateName(name);

        if (findDirectoryEntry(parent, name).has_value()) {
            throw FileSystemError("Directory entry already exists");
        }

        JournalRecord transaction = beginTransaction(
            "create directory " + path,
            {parent},
            {parent}
        );

        Inode inode;
        inode.number = allocateInodeNumber();
        inode.type = FileType::Directory;
        inode.mode = mode;
        inode.parent = parent;
        inode.linkCount = 2;

        inodes_[inode.number] = inode;
        directories_[inode.number] = {
            {".", inode.number},
            {"..", parent}
        };

        directories_[parent].push_back({name, inode.number});
        inodes_.at(parent).linkCount++;

        commit(transaction);
        return inode.number;
    }

    std::size_t writeFile(
        const std::string& path,
        const std::string& text,
        std::size_t offset = 0
    ) {
        requireMounted();

        InodeNumber inodeNumber = resolve(path);
        Inode& inode = inodes_.at(inodeNumber);

        if (inode.type != FileType::Regular) {
            throw FileSystemError("Cannot write a directory");
        }

        if (text.empty()) {
            return 0;
        }

        const std::size_t finalSize = offset + text.size();
        const std::size_t neededBlocks =
            (finalSize + superblock_.blockSize - 1)
            / superblock_.blockSize;

        JournalRecord transaction = beginTransaction(
            "write " + path,
            {inodeNumber},
            {}
        );

        while (inode.dataBlocks().size() < neededBlocks) {
            BlockNumber dataBlock = allocateBlock();

            if (inode.directBlocks.size() < DirectBlockLimit) {
                inode.directBlocks.push_back(dataBlock);
            } else {
                if (!inode.indirectBlock.has_value()) {
                    inode.indirectBlock = allocateBlock();
                }

                inode.indirectEntries.push_back(dataBlock);
            }
        }

        for (std::size_t logical = 0; logical < neededBlocks; ++logical) {
            BlockNumber physical = inode.dataBlocks().at(logical);

            const std::size_t blockStart =
                logical * superblock_.blockSize;

            const std::size_t writeStart =
                std::max(offset, blockStart);

            const std::size_t writeEnd =
                std::min(
                    finalSize,
                    blockStart + superblock_.blockSize
                );

            if (writeStart >= writeEnd) {
                continue;
            }

            const std::size_t sourceOffset = writeStart - offset;
            const std::size_t targetOffset = writeStart - blockStart;
            const std::size_t count = writeEnd - writeStart;

            std::copy_n(
                text.begin() + static_cast<std::ptrdiff_t>(sourceOffset),
                static_cast<std::ptrdiff_t>(count),
                disk_[physical].begin()
                    + static_cast<std::ptrdiff_t>(targetOffset)
            );
        }

        inode.size = std::max(inode.size, finalSize);
        superblock_.clean = false;

        commit(transaction);
        return text.size();
    }

    std::string readFile(
        const std::string& path,
        std::size_t offset = 0,
        std::optional<std::size_t> length = std::nullopt
    ) const {
        const InodeNumber inodeNumber = resolveWithoutMountCheck(path);
        const Inode& inode = inodes_.at(inodeNumber);

        if (inode.type != FileType::Regular) {
            throw FileSystemError("Cannot read a directory as a file");
        }

        if (offset >= inode.size) {
            return {};
        }

        const std::size_t requested =
            length.has_value()
                ? std::min(length.value(), inode.size - offset)
                : inode.size - offset;

        std::string result;
        result.reserve(requested);

        for (std::size_t position = 0; position < requested; ++position) {
            const std::size_t absolute = offset + position;
            const std::size_t logical =
                absolute / superblock_.blockSize;
            const std::size_t local =
                absolute % superblock_.blockSize;

            const BlockNumber physical =
                inode.dataBlocks().at(logical);

            result.push_back(
                static_cast<char>(disk_[physical][local])
            );
        }

        return result;
    }

    void truncateFile(
        const std::string& path,
        std::size_t newSize
    ) {
        requireMounted();

        InodeNumber inodeNumber = resolve(path);
        Inode& inode = inodes_.at(inodeNumber);

        if (inode.type != FileType::Regular) {
            throw FileSystemError("Cannot truncate a directory");
        }

        const std::size_t neededBlocks =
            (newSize + superblock_.blockSize - 1)
            / superblock_.blockSize;

        JournalRecord transaction = beginTransaction(
            "truncate " + path,
            {inodeNumber},
            {}
        );

        while (inode.dataBlocks().size() > neededBlocks) {
            if (!inode.indirectEntries.empty()) {
                BlockNumber block = inode.indirectEntries.back();
                inode.indirectEntries.pop_back();
                freeBlock(block);
            } else {
                BlockNumber block = inode.directBlocks.back();
                inode.directBlocks.pop_back();
                freeBlock(block);
            }
        }

        if (
            inode.indirectEntries.empty() &&
            inode.indirectBlock.has_value()
        ) {
            freeBlock(inode.indirectBlock.value());
            inode.indirectBlock.reset();
        }

        inode.size = newSize;
        superblock_.clean = false;

        commit(transaction);
    }

    std::vector<DirectoryEntry> listDirectory(
        const std::string& path
    ) const {
        InodeNumber inodeNumber = resolveWithoutMountCheck(path);

        const Inode& inode = inodes_.at(inodeNumber);
        if (inode.type != FileType::Directory) {
            throw FileSystemError("Path is not a directory");
        }

        return directories_.at(inodeNumber);
    }

    void consistencyCheck() const {
        if (!inodes_.contains(superblock_.rootInode)) {
            throw FileSystemError("Root inode is missing");
        }

        std::set<BlockNumber> referenced = metadataBlocks_;

        for (const auto& [inodeNumber, inode] : inodes_) {
            if (inode.type == FileType::Directory) {
                const auto& entries = directories_.at(inodeNumber);

                bool hasDot = false;
                bool hasDotDot = false;
                std::set<std::string> names;

                for (const auto& entry : entries) {
                    if (!names.insert(entry.name).second) {
                        throw FileSystemError(
                            "Duplicate directory name"
                        );
                    }

                    if (entry.name == ".") {
                        hasDot = true;
                    }

                    if (entry.name == "..") {
                        hasDotDot = true;
                    }

                    if (!inodes_.contains(entry.inode)) {
                        throw FileSystemError(
                            "Directory references missing inode"
                        );
                    }
                }

                if (!hasDot || !hasDotDot) {
                    throw FileSystemError(
                        "Directory lacks . or .. entries"
                    );
                }
            }

            const std::size_t expected =
                inode.type == FileType::Regular
                    ? (inode.size + superblock_.blockSize - 1)
                        / superblock_.blockSize
                    : 0;

            if (
                inode.type == FileType::Regular &&
                inode.dataBlocks().size() < expected
            ) {
                throw FileSystemError(
                    "Inode does not reference enough blocks"
                );
            }

            for (BlockNumber block : inode.dataBlocks()) {
                if (!referenced.insert(block).second) {
                    throw FileSystemError(
                        "Multiple inodes reference the same block"
                    );
                }
            }

            if (inode.indirectBlock.has_value()) {
                if (
                    !referenced.insert(
                        inode.indirectBlock.value()
                    ).second
                ) {
                    throw FileSystemError(
                        "Indirect block is multiply allocated"
                    );
                }
            }
        }

        if (referenced != allocatedBlocks_) {
            throw FileSystemError(
                "Allocation map disagrees with inode references"
            );
        }
    }

    void printInode(const std::string& path) const {
        const Inode& inode = inodes_.at(resolveWithoutMountCheck(path));

        std::cout
            << "inode=" << inode.number
            << " type="
            << (inode.type == FileType::Regular
                    ? "regular"
                    : "directory")
            << " size=" << inode.size
            << " direct=[";

        for (std::size_t i = 0; i < inode.directBlocks.size(); ++i) {
            if (i != 0) {
                std::cout << ",";
            }
            std::cout << inode.directBlocks[i];
        }

        std::cout << "] indirect=";

        if (inode.indirectBlock.has_value()) {
            std::cout << inode.indirectBlock.value() << " entries=[";
            for (std::size_t i = 0; i < inode.indirectEntries.size(); ++i) {
                if (i != 0) {
                    std::cout << ",";
                }
                std::cout << inode.indirectEntries[i];
            }
            std::cout << "]";
        } else {
            std::cout << "none";
        }

        std::cout << "\n";
    }

private:
    InodeNumber allocateInodeNumber() {
        if (inodes_.size() >= superblock_.inodeLimit) {
            throw AllocationError("Inode table exhausted");
        }

        return nextInode_++;
    }

    BlockNumber allocateBlock() {
        for (BlockNumber block = 0;
             block < superblock_.totalBlocks;
             ++block) {
            if (!allocatedBlocks_.contains(block)) {
                allocatedBlocks_.insert(block);
                return block;
            }
        }

        throw AllocationError("Data area exhausted");
    }

    void freeBlock(BlockNumber block) {
        if (metadataBlocks_.contains(block)) {
            throw FileSystemError("Cannot free metadata block");
        }

        allocatedBlocks_.erase(block);
    }

    JournalRecord beginTransaction(
        const std::string& description,
        const std::vector<InodeNumber>& inodeNumbers,
        const std::vector<InodeNumber>& directoryNumbers
    ) {
        if (journal_.size() >= superblock_.journalBlocks) {
            throw FileSystemError("Journal is full");
        }

        JournalRecord record;
        record.id = nextTransaction_++;
        record.description = description;
        record.superblockSnapshot = superblock_;

        for (InodeNumber number : inodeNumbers) {
            record.inodeSnapshots[number] = inodes_.at(number);
        }

        for (InodeNumber number : directoryNumbers) {
            record.directorySnapshots[number] = directories_.at(number);
        }

        journal_.push_back(record);

        std::cout
            << "[journal] prepare #"
            << record.id
            << " "
            << description
            << "\n";

        return record;
    }

    void commit(JournalRecord& record) {
        auto iterator = std::find_if(
            journal_.begin(),
            journal_.end(),
            [&](const JournalRecord& candidate) {
                return candidate.id == record.id;
            }
        );

        if (iterator == journal_.end()) {
            throw FileSystemError("Journal transaction disappeared");
        }

        iterator->state = JournalState::Committed;
        superblock_.clean = true;
        superblock_.generation++;

        std::cout
            << "[journal] commit #"
            << record.id
            << "\n";

        /*
         * The committed record would normally remain on persistent journal
         * storage until checkpointing confirms that the corresponding
         * filesystem metadata has reached its home location.
         */
        journal_.erase(iterator);
    }

    void recoverJournal() {
        /*
         * This simplified engine retains transaction snapshots. If the
         * simulation is extended to keep committed records across a crash,
         * recovery replays committed snapshots here before normal mounting.
         */
        for (const auto& record : journal_) {
            if (record.state != JournalState::Committed) {
                continue;
            }

            for (const auto& [number, inode] : record.inodeSnapshots) {
                inodes_[number] = inode;
            }

            for (const auto& [number, entries] : record.directorySnapshots) {
                directories_[number] = entries;
            }

            superblock_ = record.superblockSnapshot;
        }

        journal_.clear();
        superblock_.clean = true;
        superblock_.generation++;
    }

    std::optional<InodeNumber> findDirectoryEntry(
        InodeNumber directory,
        const std::string& name
    ) const {
        auto iterator = directories_.find(directory);
        if (iterator == directories_.end()) {
            throw FileSystemError("Not a directory");
        }

        for (const auto& entry : iterator->second) {
            if (entry.name == name) {
                return entry.inode;
            }
        }

        return std::nullopt;
    }

    InodeNumber resolve(const std::string& path) const {
        requireMounted();
        return resolveWithoutMountCheck(path);
    }

    InodeNumber resolveWithoutMountCheck(
        const std::string& path
    ) const {
        if (path.empty() || path.front() != '/') {
            throw FileSystemError("Only absolute paths are supported");
        }

        InodeNumber current = superblock_.rootInode;
        std::stringstream stream(path);
        std::string component;

        while (std::getline(stream, component, '/')) {
            if (component.empty() || component == ".") {
                continue;
            }

            if (component == "..") {
                current = inodes_.at(current).parent;
                continue;
            }

            auto next = findDirectoryEntry(current, component);
            if (!next.has_value()) {
                throw FileSystemError(
                    "Path component does not exist: " + component
                );
            }

            current = next.value();
        }

        return current;
    }

    std::pair<InodeNumber, std::string> parentAndName(
        const std::string& path
    ) const {
        if (path.empty() || path == "/") {
            throw FileSystemError("Root has no parent entry");
        }

        const std::size_t slash = path.find_last_of('/');
        const std::string name = path.substr(slash + 1);
        const std::string parentPath =
            slash == 0 ? "/" : path.substr(0, slash);

        return {resolve(parentPath), name};
    }

    static void validateName(const std::string& name) {
        if (
            name.empty() ||
            name == "." ||
            name == ".." ||
            name.find('/') != std::string::npos ||
            name.size() > 255
        ) {
            throw FileSystemError("Invalid directory entry name");
        }
    }

    void requireMounted() const {
        if (!mounted_) {
            throw FileSystemError("Filesystem is not mounted");
        }
    }
};

int main() {
    try {
        RepositoryStorageEngine fs(
            32,   // block size
            100,  // total blocks
            24,   // inode capacity
            10    // journal capacity
        );

        fs.mount();

        std::cout << "\n=== Repository storage case study ===\n";

        /*
         * The simulated repository stores operational metadata under a
         * directory tree. This makes inode allocation, directory entries, and
         * file growth observable without pretending that repository objects
         * are themselves filesystem primitives.
         */
        fs.createDirectory("/repositories");
        fs.createDirectory("/repositories/kernel");
        fs.createDirectory("/repositories/kernel/objects");

        fs.createFile("/repositories/kernel/objects/pack.index");
        fs.createFile("/repositories/kernel/objects/pack.data");

        fs.writeFile(
            "/repositories/kernel/objects/pack.index",
            "object-001 -> 9a7f\n"
            "object-002 -> 3bd2\n"
            "object-003 -> 88e1\n"
        );

        /*
         * This write crosses the direct-reference threshold. The inode must
         * therefore allocate an indirect metadata block and then data blocks.
         */
        fs.writeFile(
            "/repositories/kernel/objects/pack.data",
            std::string(220, 'K')
        );

        fs.printInode(
            "/repositories/kernel/objects/pack.data"
        );

        std::cout
            << "Read prefix: "
            << fs.readFile(
                "/repositories/kernel/objects/pack.data",
                0,
                40
            )
            << "\n";

        std::cout << "\nDirectory entries:\n";
        for (
            const auto& entry :
            fs.listDirectory("/repositories/kernel/objects")
        ) {
            std::cout
                << "  "
                << entry.name
                << " -> inode "
                << entry.inode
                << "\n";
        }

        std::cout << "\n=== Truncation ===\n";
        fs.truncateFile(
            "/repositories/kernel/objects/pack.data",
            48
        );
        fs.printInode(
            "/repositories/kernel/objects/pack.data"
        );

        std::cout << "\n=== Consistency validation ===\n";
        fs.consistencyCheck();
        std::cout
            << "inode/block references are internally consistent\n";

        std::cout << "\n=== Mount lifecycle ===\n";
        fs.unmount();
        fs.mount();

        std::cout
            << "Post-remount read: "
            << fs.readFile(
                "/repositories/kernel/objects/pack.index"
            );

        /*
         * A production implementation would place stronger emphasis on
         * durable ordering, checksums, crash-consistent superblock updates,
         * persistent allocation bitmaps, journal sequence numbers, and
         * carefully defined recovery semantics.
         */
        std::cout
            << "\nFilesystem case study completed successfully.\n";
    }
    catch (const std::exception& error) {
        std::cerr
            << "Fatal filesystem error: "
            << error.what()
            << "\n";
        return 1;
    }

    return 0;
}
