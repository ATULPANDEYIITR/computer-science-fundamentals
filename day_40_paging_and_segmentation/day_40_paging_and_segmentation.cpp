#include <algorithm>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <optional>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

enum class AccessType {
    Read,
    Write,
    Execute
};

enum class MergeDecision {
    Eligible,
    PageFault,
    ProtectionFault,
    SegmentFault
};

struct PageTableEntry {
    uint32_t frame;
    bool present;
    bool readable;
    bool writable;
    bool executable;
    bool user;
    bool accessed;
    bool dirty;
};

struct Segment {
    std::string name;
    uint32_t base;
    uint32_t limit;
    bool readable;
    bool writable;
    bool executable;
};

struct Translation {
    uint32_t logicalAddress;
    uint32_t linearAddress;
    uint32_t physicalAddress;
    uint32_t page;
    uint32_t offset;
    uint32_t frame;
    bool tlbHit;
};

class MemoryFault : public std::runtime_error {
public:
    explicit MemoryFault(const std::string& message)
        : std::runtime_error(message) {}
};

class PageFault : public MemoryFault {
public:
    explicit PageFault(const std::string& message)
        : MemoryFault(message) {}
};

class ProtectionFault : public MemoryFault {
public:
    explicit ProtectionFault(const std::string& message)
        : MemoryFault(message) {}
};

class SegmentFault : public MemoryFault {
public:
    explicit SegmentFault(const std::string& message)
        : MemoryFault(message) {}
};

/*
 * The TLB stores page-to-frame translations separately from the page table.
 * A small capacity makes replacement visible in the case study.
 */
class TLB {
private:
    std::size_t capacity_;
    std::unordered_map<uint32_t, uint32_t> entries_;
    std::vector<uint32_t> order_;

public:
    explicit TLB(std::size_t capacity) : capacity_(capacity) {
        if (capacity == 0) {
            throw std::invalid_argument("TLB capacity cannot be zero");
        }
    }

    std::optional<uint32_t> lookup(uint32_t page) {
        auto it = entries_.find(page);
        if (it == entries_.end()) {
            return std::nullopt;
        }
        return it->second;
    }

    void insert(uint32_t page, uint32_t frame) {
        if (entries_.contains(page)) {
            entries_[page] = frame;
            return;
        }

        if (entries_.size() >= capacity_) {
            uint32_t victim = order_.front();
            order_.erase(order_.begin());
            entries_.erase(victim);
        }

        entries_[page] = frame;
        order_.push_back(page);
    }

    void invalidate(uint32_t page) {
        entries_.erase(page);
        order_.erase(
            std::remove(order_.begin(), order_.end(), page),
            order_.end()
        );
    }
};

class AddressSpace {
public:
    static constexpr uint32_t PageBits = 8;
    static constexpr uint32_t PageSize = 1u << PageBits;
    static constexpr uint32_t VirtualBits = 16;
    static constexpr uint32_t AddressSpaceSize = 1u << VirtualBits;

private:
    std::unordered_map<uint32_t, PageTableEntry> pageTable_;
    std::unordered_map<std::string, Segment> segments_;
    std::vector<uint8_t> physicalMemory_;
    TLB tlb_;

    bool permitted(const PageTableEntry& entry, AccessType access) const {
        switch (access) {
            case AccessType::Read: return entry.readable;
            case AccessType::Write: return entry.writable;
            case AccessType::Execute: return entry.executable;
        }
        return false;
    }

    bool permitted(const Segment& segment, AccessType access) const {
        switch (access) {
            case AccessType::Read: return segment.readable;
            case AccessType::Write: return segment.writable;
            case AccessType::Execute: return segment.executable;
        }
        return false;
    }

public:
    explicit AddressSpace(std::size_t physicalSize = 65536)
        : physicalMemory_(physicalSize), tlb_(4) {}

    void mapPage(
        uint32_t page,
        uint32_t frame,
        bool readable,
        bool writable,
        bool executable
    ) {
        if (page >= 256 || frame * PageSize >= physicalMemory_.size()) {
            throw std::invalid_argument("Invalid page or frame");
        }

        pageTable_[page] = PageTableEntry{
            frame, true, readable, writable, executable,
            true, false, false
        };
        tlb_.invalidate(page);
    }

    void addSegment(
        std::string name,
        uint32_t base,
        uint32_t limit,
        bool readable,
        bool writable,
        bool executable
    ) {
        if (base + limit >= AddressSpaceSize) {
            throw std::invalid_argument("Segment exceeds address space");
        }

        segments_[name] = Segment{
            std::move(name), base, limit,
            readable, writable, executable
        };
    }

    Translation translate(
        const std::string& segmentName,
        uint32_t offset,
        AccessType access
    ) {
        auto segmentIt = segments_.find(segmentName);
        if (segmentIt == segments_.end()) {
            throw SegmentFault("Segment does not exist");
        }

        const Segment& segment = segmentIt->second;

        if (offset > segment.limit) {
            throw SegmentFault("Segment limit violation");
        }

        if (!permitted(segment, access)) {
            throw ProtectionFault("Segment permission violation");
        }

        const uint32_t linearAddress = segment.base + offset;
        const uint32_t page = linearAddress >> PageBits;
        const uint32_t pageOffset = linearAddress & (PageSize - 1);

        auto frame = tlb_.lookup(page);
        bool tlbHit = frame.has_value();

        auto pageIt = pageTable_.find(page);

        if (!frame.has_value()) {
            if (pageIt == pageTable_.end() || !pageIt->second.present) {
                throw PageFault("Linear page is not present");
            }

            frame = pageIt->second.frame;
            tlb_.insert(page, *frame);
        }

        if (pageIt == pageTable_.end() ||
            !pageIt->second.present ||
            !permitted(pageIt->second, access)) {
            throw ProtectionFault("Page permission violation");
        }

        PageTableEntry& entry = pageIt->second;
        entry.accessed = true;

        if (access == AccessType::Write) {
            entry.dirty = true;
        }

        uint32_t physicalAddress = *frame * PageSize + pageOffset;

        return Translation{
            offset,
            linearAddress,
            physicalAddress,
            page,
            pageOffset,
            *frame,
            tlbHit
        };
    }

    void printPageTable() const {
        std::cout << "\nPage table state\n";
        for (const auto& [page, entry] : pageTable_) {
            std::cout
                << "page=" << page
                << " frame=" << entry.frame
                << " present=" << entry.present
                << " R=" << entry.readable
                << " W=" << entry.writable
                << " X=" << entry.executable
                << " accessed=" << entry.accessed
                << " dirty=" << entry.dirty
                << '\n';
        }
    }
};

void printTranslation(
    const Translation& translation,
    const std::string& segment
) {
    std::cout
        << segment
        << ": offset=0x"
        << std::hex
        << translation.logicalAddress
        << " -> linear=0x"
        << translation.linearAddress
        << " -> physical=0x"
        << translation.physicalAddress
        << std::dec
        << " page=" << translation.page
        << " frame=" << translation.frame
        << " "
        << (translation.tlbHit ? "TLB hit" : "page-table lookup")
        << '\n';
}

/*
 * Case study: a small operating-system memory subsystem has separate
 * code and data segments. Segmentation validates the logical reference,
 * then paging resolves the resulting linear address. The same request
 * can therefore fail for a segment-limit reason, a segment-permission
 * reason, a missing-page reason, or a page-permission reason.
 */
int main() {
    AddressSpace addressSpace;

    addressSpace.addSegment(
        "code", 0x1000, 0x01ff,
        true, false, true
    );

    addressSpace.addSegment(
        "data", 0x3000, 0x02ff,
        true, true, false
    );

    addressSpace.mapPage(0x10, 4, true, false, true);
    addressSpace.mapPage(0x11, 5, true, false, true);
    addressSpace.mapPage(0x30, 8, true, true, false);
    addressSpace.mapPage(0x31, 9, true, true, false);

    std::cout << "=== Segmentation and paging case study ===\n";

    try {
        auto result = addressSpace.translate(
            "code", 0x20, AccessType::Execute
        );
        printTranslation(result, "code");
    } catch (const MemoryFault& error) {
        std::cout << "Execution failed: " << error.what() << '\n';
    }

    try {
        auto result = addressSpace.translate(
            "data", 0x40, AccessType::Write
        );
        printTranslation(result, "data");
    } catch (const MemoryFault& error) {
        std::cout << "Data access failed: " << error.what() << '\n';
    }

    try {
        addressSpace.translate(
            "code", 0x20, AccessType::Write
        );
    } catch (const MemoryFault& error) {
        std::cout
            << "Expected code-write failure: "
            << error.what()
            << '\n';
    }

    try {
        addressSpace.translate(
            "code", 0x200, AccessType::Execute
        );
    } catch (const MemoryFault& error) {
        std::cout
            << "Expected segment-limit failure: "
            << error.what()
            << '\n';
    }

    try {
        addressSpace.translate(
            "data", 0x500, AccessType::Read
        );
    } catch (const MemoryFault& error) {
        std::cout
            << "Expected segment-limit failure: "
            << error.what()
            << '\n';
    }

    /*
     * Repeating a translation demonstrates why a TLB exists: the page-table
     * mapping remains authoritative, while the cached page-to-frame mapping
     * avoids another page-table traversal for subsequent references.
     */
    std::cout << "\nRepeated data translations\n";
    for (uint32_t offset : {0x10u, 0x11u, 0x12u, 0x13u}) {
        try {
            auto result = addressSpace.translate(
                "data", offset, AccessType::Read
            );
            printTranslation(result, "data");
        } catch (const MemoryFault& error) {
            std::cout << error.what() << '\n';
        }
    }

    addressSpace.printPageTable();

    std::cout << "\nArchitecture relationship\n";
    std::cout
        << "Logical address -> segment validation -> linear address -> "
           "TLB/page-table lookup -> physical frame + offset.\n";

    return 0;
}
