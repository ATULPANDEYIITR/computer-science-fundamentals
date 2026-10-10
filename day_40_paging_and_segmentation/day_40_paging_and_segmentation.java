import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Queue;

public class MemoryManagementEnterpriseDemo {

    enum AccessType {
        READ, WRITE, EXECUTE
    }

    enum Permission {
        READ, WRITE, EXECUTE
    }

    static class MemoryFault extends RuntimeException {
        MemoryFault(String message) {
            super(message);
        }
    }

    static final class PageFault extends MemoryFault {
        PageFault(String message) {
            super(message);
        }
    }

    static final class ProtectionFault extends MemoryFault {
        ProtectionFault(String message) {
            super(message);
        }
    }

    static final class SegmentFault extends MemoryFault {
        SegmentFault(String message) {
            super(message);
        }
    }

    record PageTableEntry(
        int frame,
        boolean present,
        boolean readable,
        boolean writable,
        boolean executable,
        boolean user,
        boolean accessed,
        boolean dirty
    ) {
        PageTableEntry accessed() {
            return new PageTableEntry(
                frame, present, readable, writable,
                executable, user, true, dirty
            );
        }

        PageTableEntry dirty() {
            return new PageTableEntry(
                frame, present, readable, writable,
                executable, user, true, true
            );
        }

        boolean permits(AccessType access) {
            return switch (access) {
                case READ -> readable;
                case WRITE -> writable;
                case EXECUTE -> executable;
            };
        }
    }

    record SegmentDescriptor(
        String name,
        int base,
        int limit,
        boolean readable,
        boolean writable,
        boolean executable
    ) {
        boolean permits(AccessType access) {
            return switch (access) {
                case READ -> readable;
                case WRITE -> writable;
                case EXECUTE -> executable;
            };
        }
    }

    record LogicalAddress(String segment, int offset) {}

    record Translation(
        LogicalAddress logical,
        int linearAddress,
        int physicalAddress,
        int page,
        int frame,
        boolean tlbHit
    ) {}

    static final class Tlb {
        private final int capacity;
        private final Map<Integer, Integer> entries = new HashMap<>();
        private final Queue<Integer> fifoOrder = new ArrayDeque<>();
        private long hits;
        private long misses;

        Tlb(int capacity) {
            if (capacity <= 0) {
                throw new IllegalArgumentException("TLB capacity must be positive");
            }
            this.capacity = capacity;
        }

        Optional<Integer> lookup(int page) {
            Integer frame = entries.get(page);
            if (frame == null) {
                misses++;
                return Optional.empty();
            }
            hits++;
            return Optional.of(frame);
        }

        void insert(int page, int frame) {
            if (entries.containsKey(page)) {
                entries.put(page, frame);
                return;
            }

            if (entries.size() >= capacity) {
                Integer victim = fifoOrder.remove();
                entries.remove(victim);
            }

            entries.put(page, frame);
            fifoOrder.add(page);
        }

        void invalidate(int page) {
            entries.remove(page);
            fifoOrder.remove(page);
        }

        long hits() {
            return hits;
        }

        long misses() {
            return misses;
        }
    }

    interface PermissionPolicy {
        boolean allows(SegmentDescriptor segment, AccessType access);
        boolean allows(PageTableEntry page, AccessType access);
    }

    static final class StandardPermissionPolicy implements PermissionPolicy {
        @Override
        public boolean allows(SegmentDescriptor segment, AccessType access) {
            return segment.permits(access);
        }

        @Override
        public boolean allows(PageTableEntry page, AccessType access) {
            return page.permits(access);
        }
    }

    static final class MemoryManagementService {
        private static final int PAGE_SIZE = 256;
        private static final int VIRTUAL_SIZE = 65536;

        private final Map<Integer, PageTableEntry> pageTable = new HashMap<>();
        private final Map<String, SegmentDescriptor> segments = new HashMap<>();
        private final Tlb tlb;
        private final PermissionPolicy policy;

        MemoryManagementService(Tlb tlb, PermissionPolicy policy) {
            this.tlb = Objects.requireNonNull(tlb);
            this.policy = Objects.requireNonNull(policy);
        }

        void registerSegment(SegmentDescriptor segment) {
            if (segment.base() < 0 ||
                segment.limit() < 0 ||
                segment.base() + segment.limit() >= VIRTUAL_SIZE) {
                throw new IllegalArgumentException(
                    "Segment exceeds linear address space"
                );
            }
            segments.put(segment.name(), segment);
        }

        void mapPage(
            int page,
            int frame,
            boolean readable,
            boolean writable,
            boolean executable
        ) {
            if (page < 0 || page >= 256) {
                throw new IllegalArgumentException("Invalid page");
            }

            pageTable.put(
                page,
                new PageTableEntry(
                    frame,
                    true,
                    readable,
                    writable,
                    executable,
                    true,
                    false,
                    false
                )
            );
            tlb.invalidate(page);
        }

        Translation translate(
            LogicalAddress logical,
            AccessType access
        ) {
            SegmentDescriptor segment = segments.get(logical.segment());

            if (segment == null) {
                throw new SegmentFault(
                    "Unknown segment: " + logical.segment()
                );
            }

            if (logical.offset() < 0 ||
                logical.offset() > segment.limit()) {
                throw new SegmentFault(
                    "Segment limit exceeded for " + segment.name()
                );
            }

            if (!policy.allows(segment, access)) {
                throw new ProtectionFault(
                    "Segment denies " + access
                );
            }

            int linearAddress = segment.base() + logical.offset();
            int page = linearAddress / PAGE_SIZE;
            int offset = linearAddress % PAGE_SIZE;

            Optional<Integer> cachedFrame = tlb.lookup(page);
            boolean tlbHit = cachedFrame.isPresent();

            PageTableEntry entry = pageTable.get(page);

            if (cachedFrame.isEmpty()) {
                if (entry == null || !entry.present()) {
                    throw new PageFault(
                        "Page " + page + " is not present"
                    );
                }

                cachedFrame = Optional.of(entry.frame());
                tlb.insert(page, entry.frame());
            }

            if (entry == null || !entry.present()) {
                throw new PageFault("Page table entry is unavailable");
            }

            if (!policy.allows(entry, access)) {
                throw new ProtectionFault(
                    "Page " + page + " denies " + access
                );
            }

            entry = entry.accessed();

            if (access == AccessType.WRITE) {
                entry = entry.dirty();
            }

            pageTable.put(page, entry);

            int physicalAddress =
                cachedFrame.get() * PAGE_SIZE + offset;

            return new Translation(
                logical,
                linearAddress,
                physicalAddress,
                page,
                cachedFrame.get(),
                tlbHit
            );
        }

        List<String> pageTableReport() {
            List<String> report = new ArrayList<>();

            pageTable.entrySet().stream()
                .sorted(Map.Entry.comparingByKey())
                .forEach(entry -> {
                    PageTableEntry pte = entry.getValue();
                    report.add(
                        "page=" + entry.getKey() +
                        " frame=" + pte.frame() +
                        " R=" + pte.readable() +
                        " W=" + pte.writable() +
                        " X=" + pte.executable() +
                        " accessed=" + pte.accessed() +
                        " dirty=" + pte.dirty()
                    );
                });

            return report;
        }
    }

    static void printTranslation(Translation translation) {
        System.out.printf(
            "%s:%04x -> linear=%04x -> physical=%04x " +
            "page=%d frame=%d %s%n",
            translation.logical().segment(),
            translation.logical().offset(),
            translation.linearAddress(),
            translation.physicalAddress(),
            translation.page(),
            translation.frame(),
            translation.tlbHit() ? "TLB hit" : "page-table lookup"
        );
    }

    public static void main(String[] args) {
        PermissionPolicy policy = new StandardPermissionPolicy();
        MemoryManagementService memory =
            new MemoryManagementService(new Tlb(3), policy);

        memory.registerSegment(
            new SegmentDescriptor(
                "code", 0x1000, 0x01ff,
                true, false, true
            )
        );

        memory.registerSegment(
            new SegmentDescriptor(
                "data", 0x3000, 0x02ff,
                true, true, false
            )
        );

        memory.mapPage(0x10, 4, true, false, true);
        memory.mapPage(0x11, 5, true, false, true);
        memory.mapPage(0x30, 8, true, true, false);
        memory.mapPage(0x31, 9, true, true, false);

        System.out.println("=== Enterprise memory-management model ===");

        List<LogicalAddress> workload = List.of(
            new LogicalAddress("code", 0x20),
            new LogicalAddress("data", 0x40),
            new LogicalAddress("data", 0x41),
            new LogicalAddress("data", 0x42)
        );

        for (LogicalAddress address : workload) {
            AccessType access =
                address.segment().equals("code")
                    ? AccessType.EXECUTE
                    : AccessType.WRITE;

            try {
                Translation translation =
                    memory.translate(address, access);
                printTranslation(translation);
            } catch (MemoryFault error) {
                System.out.println(
                    "Rejected " + address + ": " + error.getMessage()
                );
            }
        }

        try {
            memory.translate(
                new LogicalAddress("code", 0x20),
                AccessType.WRITE
            );
        } catch (MemoryFault error) {
            System.out.println(
                "Expected write rejection: " + error.getMessage()
            );
        }

        try {
            memory.translate(
                new LogicalAddress("code", 0x200),
                AccessType.EXECUTE
            );
        } catch (MemoryFault error) {
            System.out.println(
                "Expected segment rejection: " + error.getMessage()
            );
        }

        try {
            memory.translate(
                new LogicalAddress("data", 0x500),
                AccessType.READ
            );
        } catch (MemoryFault error) {
            System.out.println(
                "Expected limit rejection: " + error.getMessage()
            );
        }

        System.out.println("\n=== Page-table audit ===");
        memory.pageTableReport().forEach(System.out::println);

        System.out.println("\n=== TLB audit ===");
        // The TLB is intentionally exposed through statistics rather than
        // direct mutation, preserving the service's ownership of translation.
        System.out.println("hits=" + memory.tlb.hits());
        System.out.println("misses=" + memory.tlb.misses());

        System.out.println(
            "\nThe model separates logical segment validation, linear-address "
            + "formation, TLB lookup, page-table resolution, and page-level "
            + "permission enforcement."
        );
    }
}
