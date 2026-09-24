/*
 * Virtual Memory Case Study
 *
 * Topic:
 *   Paging, segmentation, page tables, TLB, and page faults
 *
 * Scenario:
 *   A simplified operating-system memory manager supporting multiple
 *   processes, virtual-to-physical translation, a TLB, demand paging,
 *   page replacement, permissions, dirty pages, and segmentation metadata.
 *
 * Standard:
 *   C++17 or later
 *
 * Compile:
 *   g++ -std=c++17 -O2 -Wall -Wextra -pedantic virtual_memory.cpp -o virtual_memory
 *
 * Run:
 *   ./virtual_memory
 */

#include <algorithm>
#include <cassert>
#include <cstddef>
#include <deque>
#include <iomanip>
#include <iostream>
#include <limits>
#include <list>
#include <optional>
#include <random>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using namespace std;

// ============================================================================
// 1. BASIC TYPES
// ============================================================================

using ProcessId = int;
using VirtualAddress = uint64_t;
using PhysicalAddress = uint64_t;
using PageNumber = uint64_t;
using FrameNumber = size_t;

enum class ReplacementPolicy {
    FIFO,
    LRU,
    CLOCK
};

struct PageTableEntry {
    optional<FrameNumber> frame;
    bool present = false;
    bool writable = true;
    bool executable = false;
    bool userAccessible = true;
    bool referenced = false;
    bool dirty = false;
};

struct Frame {
    FrameNumber number;
    optional<PageNumber> page;
    optional<ProcessId> process;
    bool referenced = false;
    bool dirty = false;
};

// ============================================================================
// 2. EXCEPTIONS
// ============================================================================

class PageFault : public runtime_error {
public:
    explicit PageFault(PageNumber page)
        : runtime_error("Page fault on virtual page " + to_string(page)),
          page_(page) {}

    PageNumber page() const noexcept {
        return page_;
    }

private:
    PageNumber page_;
};

class ProtectionFault : public runtime_error {
public:
    explicit ProtectionFault(const string& message)
        : runtime_error(message) {}
};

class AddressFault : public runtime_error {
public:
    explicit AddressFault(const string& message)
        : runtime_error(message) {}
};

// ============================================================================
// 3. TLB
// ============================================================================

struct TLBEntry {
    FrameNumber frame;
    bool writable;
    bool executable;
};

class TLB {
public:
    explicit TLB(size_t capacity)
        : capacity_(capacity) {
        if (capacity == 0) {
            throw invalid_argument("TLB capacity must be positive");
        }
    }

    optional<TLBEntry> lookup(PageNumber page) {
        auto iterator = entries_.find(page);

        if (iterator == entries_.end()) {
            ++misses_;
            return nullopt;
        }

        ++hits_;

        // The list front is the most recently used translation.
        usage_.remove(page);
        usage_.push_front(page);

        return iterator->second;
    }

    void insert(PageNumber page, const TLBEntry& entry) {
        entries_[page] = entry;
        usage_.remove(page);
        usage_.push_front(page);

        while (entries_.size() > capacity_) {
            PageNumber victim = usage_.back();
            usage_.pop_back();
            entries_.erase(victim);
        }
    }

    void invalidate(PageNumber page) {
        entries_.erase(page);
        usage_.remove(page);
    }

    void clear() {
        entries_.clear();
        usage_.clear();
    }

    double hitRate() const {
        const size_t total = hits_ + misses_;

        if (total == 0) {
            return 0.0;
        }

        return static_cast<double>(hits_) /
               static_cast<double>(total);
    }

    size_t hits() const {
        return hits_;
    }

    size_t misses() const {
        return misses_;
    }

private:
    size_t capacity_;
    unordered_map<PageNumber, TLBEntry> entries_;
    list<PageNumber> usage_;
    size_t hits_ = 0;
    size_t misses_ = 0;
};

// ============================================================================
// 4. PROCESS ADDRESS SPACE
// ============================================================================

class ProcessAddressSpace {
public:
    ProcessAddressSpace(
        ProcessId id,
        size_t virtualPages,
        size_t pageSize
    )
        : id_(id),
          pageSize_(pageSize),
          pageTable_(virtualPages) {
        if (virtualPages == 0) {
            throw invalid_argument("Virtual page count must be positive");
        }

        if (pageSize == 0 || (pageSize & (pageSize - 1)) != 0) {
            throw invalid_argument(
                "Page size must be a positive power of two"
            );
        }
    }

    ProcessId id() const {
        return id_;
    }

    size_t pageSize() const {
        return pageSize_;
    }

    size_t virtualPages() const {
        return pageTable_.size();
    }

    PageTableEntry& entry(PageNumber page) {
        validatePage(page);
        return pageTable_[static_cast<size_t>(page)];
    }

    const PageTableEntry& entry(PageNumber page) const {
        validatePage(page);
        return pageTable_[static_cast<size_t>(page)];
    }

    pair<PageNumber, size_t> splitAddress(
        VirtualAddress address
    ) const {
        const PageNumber page =
            address / pageSize_;

        const size_t offset =
            static_cast<size_t>(address % pageSize_);

        if (page >= pageTable_.size()) {
            throw AddressFault(
                "Virtual address exceeds process address space"
            );
        }

        return {page, offset};
    }

private:
    void validatePage(PageNumber page) const {
        if (page >= pageTable_.size()) {
            throw AddressFault("Virtual page outside address space");
        }
    }

    ProcessId id_;
    size_t pageSize_;
    vector<PageTableEntry> pageTable_;
};

// ============================================================================
// 5. MEMORY MANAGER
// ============================================================================

struct AccessResult {
    VirtualAddress virtualAddress;
    optional<PhysicalAddress> physicalAddress;
    ProcessId process;
    PageNumber page;
    size_t offset;
    bool tlbHit = false;
    bool pageFault = false;
    optional<PageNumber> evictedPage;
    string mechanism;
};

class MemoryManager {
public:
    MemoryManager(
        size_t physicalFrames,
        size_t tlbCapacity,
        ReplacementPolicy policy
    )
        : frames_(physicalFrames),
          tlb_(tlbCapacity),
          policy_(policy) {
        if (physicalFrames == 0) {
            throw invalid_argument(
                "Physical frame count must be positive"
            );
        }

        for (size_t index = 0; index < physicalFrames; ++index) {
            frames_[index].number = index;
        }
    }

    void addProcess(ProcessId id, size_t virtualPages, size_t pageSize) {
        if (processes_.contains(id)) {
            throw invalid_argument("Process already exists");
        }

        processes_.emplace(
            id,
            ProcessAddressSpace(id, virtualPages, pageSize)
        );
    }

    AccessResult access(
        ProcessId processId,
        VirtualAddress address,
        bool write = false,
        bool execute = false
    ) {
        ProcessAddressSpace& process =
            getProcess(processId);

        const auto [page, offset] =
            process.splitAddress(address);

        ++accesses_;

        const TLBKey key{processId, page};

        if (auto translation = tlb_.lookup(key); translation.has_value()) {
            checkPermissions(
                translation->writable,
                translation->executable,
                write,
                execute
            );

            Frame& frame = frames_[translation->frame];

            frame.referenced = true;

            if (write) {
                frame.dirty = true;
                process.entry(page).dirty = true;
            }

            touch(processId, page);

            return AccessResult{
                address,
                translation->frame * process.pageSize() + offset,
                processId,
                page,
                offset,
                true,
                false,
                nullopt,
                "TLB translation"
            };
        }

        PageTableEntry& entry = process.entry(page);

        if (!entry.present) {
            ++pageFaults_;

            optional<PageNumber> evicted =
                handlePageFault(processId, page);

            PageTableEntry& updatedEntry =
                process.entry(page);

            checkPermissions(
                updatedEntry.writable,
                updatedEntry.executable,
                write,
                execute
            );

            if (write) {
                updatedEntry.dirty = true;
                frames_[*updatedEntry.frame].dirty = true;
            }

            tlb_.insert(
                TLBKey{processId, page},
                TLBEntry{
                    *updatedEntry.frame,
                    updatedEntry.writable,
                    updatedEntry.executable
                }
            );

            return AccessResult{
                address,
                *updatedEntry.frame * process.pageSize() + offset,
                processId,
                page,
                offset,
                false,
                true,
                evicted,
                "Page fault handled"
            };
        }

        checkPermissions(
            entry.writable,
            entry.executable,
            write,
            execute
        );

        entry.referenced = true;

        if (write) {
            entry.dirty = true;
            frames_[*entry.frame].dirty = true;
        }

        tlb_.insert(
            TLBKey{processId, page},
            TLBEntry{
                *entry.frame,
                entry.writable,
                entry.executable
            }
        );

        touch(processId, page);

        return AccessResult{
            address,
            *entry.frame * process.pageSize() + offset,
            processId,
            page,
            offset,
            false,
            false,
            nullopt,
            "Page-table translation"
        };
    }

    void mapPage(
        ProcessId processId,
        PageNumber page,
        bool writable,
        bool executable
    ) {
        ProcessAddressSpace& process =
            getProcess(processId);

        PageTableEntry& entry =
            process.entry(page);

        if (entry.present) {
            return;
        }

        Frame& frame = acquireFrame();

        frame.page = page;
        frame.process = processId;
        frame.referenced = true;
        frame.dirty = false;

        entry.frame = frame.number;
        entry.present = true;
        entry.writable = writable;
        entry.executable = executable;
        entry.referenced = true;
        entry.dirty = false;

        fifoQueue_.push_back(frame.number);
        touch(processId, page);

        tlb_.insert(
            TLBKey{processId, page},
            TLBEntry{
                frame.number,
                writable,
                executable
            }
        );
    }

    void printState() const {
        cout << "\nPhysical memory:\n";

        for (const Frame& frame : frames_) {
            cout << "  Frame "
                 << setw(2) << frame.number
                 << ": process=";

            if (frame.process.has_value()) {
                cout << *frame.process;
            } else {
                cout << "-";
            }

            cout << ", page=";

            if (frame.page.has_value()) {
                cout << *frame.page;
            } else {
                cout << "-";
            }

            cout << ", dirty=" << frame.dirty
                 << ", referenced=" << frame.referenced
                 << '\n';
        }

        cout << "\nProcess page tables:\n";

        for (const auto& [id, process] : processes_) {
            cout << "  Process " << id << ":\n";

            for (PageNumber page = 0;
                 page < process.virtualPages();
                 ++page) {

                const PageTableEntry& entry =
                    process.entry(page);

                cout << "    VPN "
                     << setw(2) << page
                     << " -> ";

                if (entry.present) {
                    cout << "PFN "
                         << *entry.frame
                         << ", dirty=" << entry.dirty
                         << ", referenced="
                         << entry.referenced;
                } else {
                    cout << "not resident";
                }

                cout << '\n';
            }
        }
    }

    void printStatistics() const {
        cout << "\nStatistics:\n";
        cout << "  Accesses    : " << accesses_ << '\n';
        cout << "  Page faults : " << pageFaults_ << '\n';
        cout << "  Fault rate  : "
             << fixed << setprecision(2)
             << pageFaultRate() * 100.0
             << "%\n";

        cout << "  TLB hits    : "
             << tlb_.hits() << '\n';

        cout << "  TLB misses  : "
             << tlb_.misses() << '\n';

        cout << "  TLB hit rate: "
             << fixed << setprecision(2)
             << tlb_.hitRate() * 100.0
             << "%\n";

        cout << "  Disk reads  : " << diskReads_ << '\n';
        cout << "  Disk writes : " << diskWrites_ << '\n';
    }

    double pageFaultRate() const {
        if (accesses_ == 0) {
            return 0.0;
        }

        return static_cast<double>(pageFaults_) /
               static_cast<double>(accesses_);
    }

private:
    struct TLBKey {
        ProcessId process;
        PageNumber page;

        bool operator==(const TLBKey& other) const {
            return process == other.process &&
                   page == other.page;
        }
    };

    struct TLBKeyHash {
        size_t operator()(const TLBKey& key) const noexcept {
            size_t first =
                hash<ProcessId>{}(key.process);

            size_t second =
                hash<PageNumber>{}(key.page);

            return first ^
                   (second + 0x9e3779b9 +
                    (first << 6) +
                    (first >> 2));
        }
    };

    class ProcessTLB {
    public:
        explicit ProcessTLB(size_t capacity)
            : capacity_(capacity) {}

    private:
        size_t capacity_;
    };

    using TranslationKey = TLBKey;

    class TranslationCache {
    public:
        explicit TranslationCache(size_t capacity)
            : capacity_(capacity) {
            if (capacity == 0) {
                throw invalid_argument(
                    "Translation cache capacity must be positive"
                );
            }
        }

    private:
        size_t capacity_;
    };

    // The public TLB above uses a simple PageNumber key. The industry-style
    // case study needs process isolation, so the following process-aware
    // cache wraps the same LRU principle.
    class MultiProcessTLB {
    public:
        explicit MultiProcessTLB(size_t capacity)
            : capacity_(capacity) {
            if (capacity == 0) {
                throw invalid_argument(
                    "TLB capacity must be positive"
                );
            }
        }

        optional<TLBEntry> lookup(
            ProcessId process,
            PageNumber page
        ) {
            TLBKey key{process, page};

            auto iterator = entries_.find(key);

            if (iterator == entries_.end()) {
                ++misses_;
                return nullopt;
            }

            ++hits_;

            usage_.remove(key);
            usage_.push_front(key);

            return iterator->second;
        }

        void insert(
            ProcessId process,
            PageNumber page,
            const TLBEntry& entry
        ) {
            TLBKey key{process, page};

            entries_[key] = entry;
            usage_.remove(key);
            usage_.push_front(key);

            while (entries_.size() > capacity_) {
                TLBKey victim = usage_.back();
                usage_.pop_back();
                entries_.erase(victim);
            }
        }

        void invalidate(ProcessId process, PageNumber page) {
            TLBKey key{process, page};
            entries_.erase(key);
            usage_.remove(key);
        }

        double hitRate() const {
            const size_t total = hits_ + misses_;

            return total == 0
                ? 0.0
                : static_cast<double>(hits_) /
                  static_cast<double>(total);
        }

        size_t hits() const {
            return hits_;
        }

        size_t misses() const {
            return misses_;
        }

    private:
        size_t capacity_;
        unordered_map<
            TLBKey,
            TLBEntry,
            TLBKeyHash
        > entries_;

        list<TLBKey> usage_;
        size_t hits_ = 0;
        size_t misses_ = 0;
    };

    ProcessAddressSpace& getProcess(ProcessId id) {
        auto iterator = processes_.find(id);

        if (iterator == processes_.end()) {
            throw invalid_argument("Unknown process");
        }

        return iterator->second;
    }

    const ProcessAddressSpace& getProcess(ProcessId id) const {
        auto iterator = processes_.find(id);

        if (iterator == processes_.end()) {
            throw invalid_argument("Unknown process");
        }

        return iterator->second;
    }

    void checkPermissions(
        bool writable,
        bool executable,
        bool write,
        bool execute
    ) const {
        if (write && !writable) {
            throw ProtectionFault(
                "Write access denied by page permissions"
            );
        }

        if (execute && !executable) {
            throw ProtectionFault(
                "Execution denied by page permissions"
            );
        }
    }

    Frame& acquireFrame() {
        for (Frame& frame : frames_) {
            if (!frame.page.has_value()) {
                return frame;
            }
        }

        throw runtime_error(
            "No free frame; replacement is required"
        );
    }

    optional<PageNumber> handlePageFault(
        ProcessId processId,
        PageNumber page
    ) {
        ProcessAddressSpace& process =
            getProcess(processId);

        Frame* target = nullptr;
        optional<PageNumber> evictedPage;

        for (Frame& frame : frames_) {
            if (!frame.page.has_value()) {
                target = &frame;
                break;
            }
        }

        if (target == nullptr) {
            target = &chooseVictim();

            if (target->process.has_value() &&
                target->page.has_value()) {

                ProcessId victimProcess =
                    *target->process;

                PageNumber victimPage =
                    *target->page;

                ProcessAddressSpace& victimAddressSpace =
                    getProcess(victimProcess);

                PageTableEntry& victimEntry =
                    victimAddressSpace.entry(victimPage);

                if (victimEntry.dirty) {
                    ++diskWrites_;
                }

                victimEntry.present = false;
                victimEntry.frame.reset();
                victimEntry.dirty = false;
                victimEntry.referenced = false;

                tlb_.invalidate(
                    victimProcess,
                    victimPage
                );

                lruOrder_.erase(
                    make_pair(victimProcess, victimPage)
                );

                evictedPage = victimPage;
            }
        }

        ++diskReads_;

        target->process = processId;
        target->page = page;
        target->referenced = true;
        target->dirty = false;

        PageTableEntry& entry =
            process.entry(page);

        entry.present = true;
        entry.frame = target->number;
        entry.referenced = true;
        entry.dirty = false;

        fifoQueue_.push_back(target->number);

        touch(processId, page);

        return evictedPage;
    }

    Frame& chooseVictim() {
        if (policy_ == ReplacementPolicy::FIFO) {
            if (fifoQueue_.empty()) {
                throw runtime_error(
                    "FIFO queue is unexpectedly empty"
                );
            }

            FrameNumber frameNumber =
                fifoQueue_.front();

            fifoQueue_.pop_front();

            return frames_[frameNumber];
        }

        if (policy_ == ReplacementPolicy::LRU) {
            if (lruOrder_.empty()) {
                throw runtime_error(
                    "LRU state is unexpectedly empty"
                );
            }

            auto iterator = lruOrder_.begin();

            ProcessId process = iterator->first.first;
            PageNumber page = iterator->first.second;

            ProcessAddressSpace& addressSpace =
                getProcess(process);

            FrameNumber frameNumber =
                *addressSpace.entry(page).frame;

            lruOrder_.erase(iterator);

            return frames_[frameNumber];
        }

        // CLOCK / second chance.
        while (true) {
            Frame& frame =
                frames_[clockHand_];

            if (!frame.referenced) {
                clockHand_ =
                    (clockHand_ + 1) % frames_.size();

                return frame;
            }

            frame.referenced = false;

            if (frame.process.has_value() &&
                frame.page.has_value()) {

                ProcessAddressSpace& process =
                    getProcess(*frame.process);

                process.entry(*frame.page).referenced =
                    false;
            }

            clockHand_ =
                (clockHand_ + 1) % frames_.size();
        }
    }

    void touch(ProcessId process, PageNumber page) {
        if (policy_ != ReplacementPolicy::LRU) {
            return;
        }

        pair<ProcessId, PageNumber> key{
            process,
            page
        };

        lruOrder_.erase(key);
        lruOrder_.insert({key, true});

        ProcessAddressSpace& addressSpace =
            getProcess(process);

        PageTableEntry& entry =
            addressSpace.entry(page);

        if (entry.present) {
            frames_[*entry.frame].referenced = true;
        }
    }

    size_t accesses_ = 0;
    size_t pageFaults_ = 0;
    size_t diskReads_ = 0;
    size_t diskWrites_ = 0;

    vector<Frame> frames_;

    // The process-aware TLB is used by the final implementation.
    MultiProcessTLB tlb_;

    ReplacementPolicy policy_;

    unordered_map<
        ProcessId,
        ProcessAddressSpace
    > processes_;

    deque<FrameNumber> fifoQueue_;

    map<pair<ProcessId, PageNumber>, bool> lruOrder_;

    size_t clockHand_ = 0;
};

// ============================================================================
// 6. SEGMENTATION CASE STUDY
// ============================================================================

struct Segment {
    string name;
    uint64_t base;
    uint64_t limit;
    bool readable;
    bool writable;
    bool executable;
};

class SegmentTable {
public:
    void addSegment(
        size_t selector,
        const Segment& segment
    ) {
        if (segments_.contains(selector)) {
            throw invalid_argument(
                "Segment selector already exists"
            );
        }

        segments_[selector] = segment;
    }

    PhysicalAddress translate(
        size_t selector,
        uint64_t offset,
        bool write = false,
        bool execute = false
    ) const {
        auto iterator = segments_.find(selector);

        if (iterator == segments_.end()) {
            throw AddressFault(
                "Invalid segment selector"
            );
        }

        const Segment& segment =
            iterator->second;

        if (offset >= segment.limit) {
            throw AddressFault(
                "Offset outside segment bounds"
            );
        }

        if (write && !segment.writable) {
            throw ProtectionFault(
                "Segment is not writable"
            );
        }

        if (execute && !segment.executable) {
            throw ProtectionFault(
                "Segment is not executable"
            );
        }

        return segment.base + offset;
    }

private:
    unordered_map<size_t, Segment> segments_;
};

// ============================================================================
// 7. REPLACEMENT ALGORITHM STUDY
// ============================================================================

size_t fifoPageFaults(
    const vector<int>& references,
    size_t frameCount
) {
    if (frameCount == 0) {
        throw invalid_argument(
            "Frame count must be positive"
        );
    }

    vector<int> frames;
    deque<int> queue;
    size_t faults = 0;

    for (int page : references) {
        if (find(
                frames.begin(),
                frames.end(),
                page
            ) != frames.end()) {
            continue;
        }

        ++faults;

        if (frames.size() < frameCount) {
            frames.push_back(page);
            queue.push_back(page);
        } else {
            int victim = queue.front();
            queue.pop_front();

            auto iterator =
                find(
                    frames.begin(),
                    frames.end(),
                    victim
                );

            *iterator = page;
            queue.push_back(page);
        }
    }

    return faults;
}

size_t lruPageFaults(
    const vector<int>& references,
    size_t frameCount
) {
    if (frameCount == 0) {
        throw invalid_argument(
            "Frame count must be positive"
        );
    }

    list<int> order;
    unordered_set<int> resident;
    size_t faults = 0;

    for (int page : references) {
        if (resident.contains(page)) {
            order.remove(page);
            order.push_back(page);
            continue;
        }

        ++faults;

        if (resident.size() == frameCount) {
            int victim = order.front();
            order.pop_front();
            resident.erase(victim);
        }

        resident.insert(page);
        order.push_back(page);
    }

    return faults;
}

size_t optimalPageFaults(
    const vector<int>& references,
    size_t frameCount
) {
    if (frameCount == 0) {
        throw invalid_argument(
            "Frame count must be positive"
        );
    }

    vector<int> frames;
    size_t faults = 0;

    for (size_t index = 0;
         index < references.size();
         ++index) {

        int page = references[index];

        if (find(
                frames.begin(),
                frames.end(),
                page
            ) != frames.end()) {
            continue;
        }

        ++faults;

        if (frames.size() < frameCount) {
            frames.push_back(page);
            continue;
        }

        size_t victimIndex = 0;
        size_t farthest = 0;
        bool foundNeverUsedAgain = false;

        for (size_t candidate = 0;
             candidate < frames.size();
             ++candidate) {

            auto next =
                find(
                    references.begin() + index + 1,
                    references.end(),
                    frames[candidate]
                );

            if (next == references.end()) {
                victimIndex = candidate;
                foundNeverUsedAgain = true;
                break;
            }

            size_t distance =
                static_cast<size_t>(
                    distance(
                        references.begin() + index + 1,
                        next
                    )
                );

            if (distance > farthest) {
                farthest = distance;
                victimIndex = candidate;
            }
        }

        static_cast<void>(foundNeverUsedAgain);
        frames[victimIndex] = page;
    }

    return faults;
}

// ============================================================================
// 8. EFFECTIVE ACCESS TIME
// ============================================================================

double effectiveAccessTime(
    double memoryNanoseconds,
    double tlbNanoseconds,
    double tlbHitRate
) {
    if (memoryNanoseconds < 0 ||
        tlbNanoseconds < 0) {
        throw invalid_argument(
            "Timing values cannot be negative"
        );
    }

    if (tlbHitRate < 0 ||
        tlbHitRate > 1) {
        throw invalid_argument(
            "TLB hit rate must be between zero and one"
        );
    }

    double hitCost =
        tlbNanoseconds + memoryNanoseconds;

    double missCost =
        tlbNanoseconds +
        2.0 * memoryNanoseconds;

    return tlbHitRate * hitCost +
           (1.0 - tlbHitRate) * missCost;
}

// ============================================================================
// 9. CASE STUDY DEMONSTRATIONS
// ============================================================================

void demonstrateSegmentation() {
    cout << "\n"
         << string(78, '=')
         << "\nSEGMENTATION\n"
         << string(78, '=')
         << '\n';

    SegmentTable table;

    table.addSegment(
        1,
        Segment{
            "code",
            10000,
            2000,
            true,
            false,
            true
        }
    );

    table.addSegment(
        2,
        Segment{
            "data",
            20000,
            3000,
            true,
            true,
            false
        }
    );

    cout << "Code offset 120 -> "
         << table.translate(
                1,
                120,
                false,
                true
            )
         << '\n';

    cout << "Data offset 500 -> "
         << table.translate(
                2,
                500,
                true,
                false
            )
         << '\n';

    try {
        table.translate(
            1,
            120,
            true,
            false
        );
    } catch (const ProtectionFault& error) {
        cout << "Expected protection failure: "
             << error.what() << '\n';
    }

    try {
        table.translate(
            2,
            3000
        );
    } catch (const AddressFault& error) {
        cout << "Expected bounds failure: "
             << error.what() << '\n';
    }
}

void demonstrateReplacementAlgorithms() {
    cout << "\n"
         << string(78, '=')
         << "\nPAGE REPLACEMENT\n"
         << string(78, '=')
         << '\n';

    vector<int> references{
        7, 0, 1, 2, 0, 3, 0,
        4, 2, 3, 0, 3, 2
    };

    cout << "Reference string: ";

    for (int page : references) {
        cout << page << ' ';
    }

    cout << '\n';

    for (size_t frames : {2u, 3u, 4u}) {
        cout << "Frames=" << frames
             << " FIFO="
             << fifoPageFaults(references, frames)
             << " LRU="
             << lruPageFaults(references, frames)
             << " Optimal="
             << optimalPageFaults(references, frames)
             << '\n';
    }
}

void demonstrateEffectiveAccessTime() {
    cout << "\n"
         << string(78, '=')
         << "\nEFFECTIVE ACCESS TIME\n"
         << string(78, '=')
         << '\n';

    for (double hitRate :
         {0.50, 0.80, 0.95, 0.99}) {

        double result =
            effectiveAccessTime(
                100.0,
                10.0,
                hitRate
            );

        cout << "TLB hit rate="
             << fixed
             << setprecision(0)
             << hitRate * 100.0
             << "% -> EAT="
             << setprecision(1)
             << result
             << " ns\n";
    }
}

void runMemoryManagerCaseStudy() {
    cout << "\n"
         << string(78, '=')
         << "\nINDUSTRY-STYLE MEMORY MANAGER CASE STUDY\n"
         << string(78, '=')
         << '\n';

    MemoryManager manager(
        4,
        3,
        ReplacementPolicy::LRU
    );

    // Process 101 models an application with separate virtual code/data
    // regions. Process 202 demonstrates process isolation.
    manager.addProcess(
        101,
        8,
        1024
    );

    manager.addProcess(
        202,
        8,
        1024
    );

    // Pre-map code and data pages with different protection attributes.
    manager.mapPage(
        101,
        0,
        false,
        true
    );

    manager.mapPage(
        101,
        1,
        true,
        false
    );

    vector<pair<VirtualAddress, bool>> trace{
        {100, false},
        {1100, false},
        {2148, true},
        {100, false},
        {3172, false},
        {1100, false},
        {2148, true},
        {4196, false},
        {5220, false},
        {100, false}
    };

    for (const auto& [address, write] : trace) {
        try {
            AccessResult result =
                manager.access(
                    101,
                    address,
                    write,
                    false
                );

            cout << "PID=" << result.process
                 << " VA=" << setw(5)
                 << result.virtualAddress
                 << " VPN=" << setw(2)
                 << result.page
                 << " offset=" << setw(4)
                 << result.offset
                 << " PA=";

            if (result.physicalAddress.has_value()) {
                cout << setw(5)
                     << *result.physicalAddress;
            } else {
                cout << "-----";
            }

            cout << " TLB="
                 << (result.tlbHit ? "HIT " : "MISS")
                 << " PF="
                 << (result.pageFault ? "YES " : "NO  ")
                 << " mechanism="
                 << result.mechanism;

            if (result.evictedPage.has_value()) {
                cout << " evicted-page="
                     << *result.evictedPage;
            }

            cout << '\n';
        } catch (const exception& error) {
            cout << "Access failed for VA="
                 << address
                 << ": "
                 << error.what()
                 << '\n';
        }
    }

    // Demonstrate a protection violation.
    try {
        manager.access(
            101,
            100,
            true,
            false
        );
    } catch (const ProtectionFault& error) {
        cout << "Expected code-page write rejection: "
             << error.what() << '\n';
    }

    // Demonstrate that another process has its own virtual address space.
    try {
        AccessResult result =
            manager.access(
                202,
                100,
                false,
                false
            );

        cout << "PID=202 VA=100 -> PA="
             << *result.physicalAddress
             << " (independent process address space)\n";
    } catch (const exception& error) {
        cout << "Process 202 access failed: "
             << error.what() << '\n';
    }

    manager.printState();
    manager.printStatistics();
}

// ============================================================================
// 10. TESTS
// ============================================================================

void runSelfTests() {
    cout << "\n"
         << string(78, '=')
         << "\nSELF-TESTS\n"
         << string(78, '=')
         << '\n';

    {
        ProcessAddressSpace process(
            1,
            4,
            4096
        );

        auto [page, offset] =
            process.splitAddress(5000);

        assert(page == 1);
        assert(offset == 904);
    }

    {
        vector<int> references{
            1, 2, 1, 3
        };

        assert(
            fifoPageFaults(references, 2) == 3
        );

        assert(
            lruPageFaults(references, 2) == 3
        );
    }

    {
        SegmentTable table;

        table.addSegment(
            1,
            Segment{
                "test",
                100,
                50,
                true,
                true,
                false
            }
        );

        assert(
            table.translate(
                1,
                10,
                true,
                false
            ) == 110
        );
    }

    {
        double eat =
            effectiveAccessTime(
                100,
                10,
                1.0
            );

        assert(
            abs(eat - 110.0) < 1e-9
        );
    }

    cout << "All self-tests passed.\n";
}

// ============================================================================
// 11. MAIN
// ============================================================================

int main() {
    try {
        cout << "Virtual Memory Technical Case Study\n";
        cout << "C++17\n";

        runSelfTests();
        demonstrateSegmentation();
        demonstrateReplacementAlgorithms();
        demonstrateEffectiveAccessTime();
        runMemoryManagerCaseStudy();

        cout << "\n"
             << string(78, '=')
             << "\nDESIGN CONSIDERATIONS\n"
             << string(78, '=')
             << '\n';

        vector<string> considerations{
            "Pages provide fixed-size allocation and simplify physical placement.",
            "Page tables translate virtual page numbers into physical frames.",
            "The TLB caches recent translations and reduces translation overhead.",
            "A TLB miss does not necessarily mean a page fault.",
            "A page fault means the required page is not currently resident.",
            "Dirty pages may require write-back before eviction.",
            "LRU approximates temporal locality but exact LRU can be expensive.",
            "CLOCK approximates recency using reference bits.",
            "Multi-level page tables reduce metadata for sparse address spaces.",
            "Permissions must be checked consistently during translation.",
            "Process-aware translation state prevents accidental cross-process mappings.",
            "Large pages can improve TLB coverage but may increase fragmentation.",
            "Thrashing is associated with insufficient frames relative to working sets."
        };

        for (const string& item : considerations) {
            cout << " - " << item << '\n';
        }

        cout << "\nProgram completed successfully.\n";
    } catch (const exception& error) {
        cerr << "Fatal error: "
             << error.what()
             << '\n';

        return 1;
    }

    return 0;
}
