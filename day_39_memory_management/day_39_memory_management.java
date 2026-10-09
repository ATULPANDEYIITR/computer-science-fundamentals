import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

public class MemoryManagementEnterpriseDemo {

    enum AllocationStrategy {
        FIRST_FIT,
        BEST_FIT,
        WORST_FIT
    }

    enum BlockState {
        FREE,
        ALLOCATED
    }

    record AllocationRequest(String processId, int size) {
        AllocationRequest {
            if (processId == null || processId.isBlank()) {
                throw new IllegalArgumentException("processId is required");
            }
            if (size <= 0) {
                throw new IllegalArgumentException("size must be positive");
            }
        }
    }

    static final class MemoryBlock {
        private int start;
        private final int size;
        private BlockState state;
        private String processId;

        MemoryBlock(int start, int size) {
            this(start, size, BlockState.FREE, null);
        }

        MemoryBlock(
                int start,
                int size,
                BlockState state,
                String processId
        ) {
            this.start = start;
            this.size = size;
            this.state = state;
            this.processId = processId;
        }

        int start() {
            return start;
        }

        int size() {
            return size;
        }

        int end() {
            return start + size;
        }

        boolean isFree() {
            return state == BlockState.FREE;
        }

        String processId() {
            return processId;
        }

        void allocateTo(String processId) {
            this.state = BlockState.ALLOCATED;
            this.processId = processId;
        }

        void release() {
            this.state = BlockState.FREE;
            this.processId = null;
        }

        void moveTo(int newStart) {
            this.start = newStart;
        }
    }

    static final class MemoryAllocationException extends RuntimeException {
        MemoryAllocationException(String message) {
            super(message);
        }
    }

    /*
     * Enterprise scenario:
     * A shared analytics platform runs jobs with different memory demands.
     * The allocation service exposes explicit lifecycle operations and keeps
     * policy decisions separate from the physical memory representation.
     */
    static final class MemoryAllocationService {
        private final int capacity;
        private final AllocationStrategy strategy;
        private final List<MemoryBlock> blocks = new ArrayList<>();

        MemoryAllocationService(int capacity, AllocationStrategy strategy) {
            if (capacity <= 0) {
                throw new IllegalArgumentException("capacity must be positive");
            }

            this.capacity = capacity;
            this.strategy = Objects.requireNonNull(strategy);
            blocks.add(new MemoryBlock(0, capacity));
        }

        int allocate(AllocationRequest request) {
            if (blocks.stream().anyMatch(
                    block -> !block.isFree()
                            && request.processId().equals(block.processId())
            )) {
                throw new MemoryAllocationException(
                        "process already owns an allocation"
                );
            }

            int index = selectBlock(request.size());
            MemoryBlock target = blocks.get(index);

            if (target.size() == request.size()) {
                target.allocateTo(request.processId());
                return target.start();
            }

            MemoryBlock allocated = new MemoryBlock(
                    target.start(),
                    request.size(),
                    BlockState.ALLOCATED,
                    request.processId()
            );

            MemoryBlock remainder = new MemoryBlock(
                    target.start() + request.size(),
                    target.size() - request.size()
            );

            blocks.remove(index);
            blocks.add(index, remainder);
            blocks.add(index, allocated);

            return allocated.start();
        }

        void release(String processId) {
            MemoryBlock target = blocks.stream()
                    .filter(block -> !block.isFree()
                            && processId.equals(block.processId()))
                    .findFirst()
                    .orElseThrow(() -> new MemoryAllocationException(
                            "allocation does not exist: " + processId
                    ));

            target.release();
            coalesce();
        }

        private int selectBlock(int requested) {
            List<Integer> candidates = new ArrayList<>();

            for (int i = 0; i < blocks.size(); i++) {
                MemoryBlock block = blocks.get(i);
                if (block.isFree() && block.size() >= requested) {
                    candidates.add(i);
                }
            }

            if (candidates.isEmpty()) {
                throw new MemoryAllocationException(
                        "no contiguous block can satisfy " + requested
                );
            }

            if (strategy == AllocationStrategy.FIRST_FIT) {
                return candidates.getFirst();
            }

            Comparator<Integer> comparator = Comparator.comparingInt(
                    index -> blocks.get(index).size()
            );

            return strategy == AllocationStrategy.BEST_FIT
                    ? candidates.stream().min(comparator).orElseThrow()
                    : candidates.stream().max(comparator).orElseThrow();
        }

        private void coalesce() {
            for (int i = 0; i < blocks.size() - 1;) {
                MemoryBlock left = blocks.get(i);
                MemoryBlock right = blocks.get(i + 1);

                if (left.isFree() && right.isFree()) {
                    MemoryBlock merged = new MemoryBlock(
                            left.start(),
                            left.size() + right.size()
                    );

                    blocks.set(i, merged);
                    blocks.remove(i + 1);
                } else {
                    i++;
                }
            }
        }

        void compact() {
            int cursor = 0;

            for (MemoryBlock block : blocks) {
                if (!block.isFree()) {
                    block.moveTo(cursor);
                    cursor += block.size();
                }
            }

            List<MemoryBlock> compacted = new ArrayList<>();

            for (MemoryBlock block : blocks) {
                if (!block.isFree()) {
                    compacted.add(block);
                }
            }

            if (cursor < capacity) {
                compacted.add(new MemoryBlock(cursor, capacity - cursor));
            }

            blocks.clear();
            blocks.addAll(compacted);
        }

        int freeMemory() {
            return blocks.stream()
                    .filter(MemoryBlock::isFree)
                    .mapToInt(MemoryBlock::size)
                    .sum();
        }

        int largestFreeBlock() {
            return blocks.stream()
                    .filter(MemoryBlock::isFree)
                    .mapToInt(MemoryBlock::size)
                    .max()
                    .orElse(0);
        }

        int externalFragmentation() {
            return freeMemory() - largestFreeBlock();
        }

        void printState(String title) {
            System.out.println("\n" + title);
            System.out.println("---------------------------------------");

            for (MemoryBlock block : blocks) {
                System.out.printf(
                        "%4d-%-4d %-10s %s%n",
                        block.start(),
                        block.end() - 1,
                        block.isFree() ? "FREE" : "ALLOCATED",
                        block.isFree() ? "-" : block.processId()
                );
            }

            System.out.println("Free memory: " + freeMemory());
            System.out.println(
                    "Largest free block: " + largestFreeBlock()
            );
            System.out.println(
                    "External fragmentation: " + externalFragmentation()
            );
        }
    }

    private static void runEnterpriseScenario() {
        MemoryAllocationService service =
                new MemoryAllocationService(
                        512,
                        AllocationStrategy.BEST_FIT
                );

        service.allocate(new AllocationRequest("ETL-01", 96));
        service.allocate(new AllocationRequest("MODEL-01", 128));
        service.allocate(new AllocationRequest("REPORT-01", 64));
        service.allocate(new AllocationRequest("CACHE-01", 80));

        service.printState("Initial job allocation");

        service.release("MODEL-01");
        service.release("REPORT-01");

        service.printState("After job completion");

        try {
            service.allocate(new AllocationRequest("MODEL-02", 170));
        } catch (MemoryAllocationException error) {
            System.out.println(
                    "\nMODEL-02 rejected: " + error.getMessage()
            );
            System.out.println(
                    "The rejection can occur even when total free memory "
                            + "looks sufficient because the request requires "
                            + "one contiguous region."
            );
        }

        service.compact();

        service.allocate(new AllocationRequest("MODEL-02", 170));
        service.printState("After compaction and successful allocation");
    }

    private static void demonstrateFixedPartitionWaste() {
        System.out.println("\n=== Fixed-partition internal fragmentation ===");

        int partitionSize = 32;
        int[] requests = {5, 11, 19, 30};

        int requested = 0;

        for (int request : requests) {
            requested += request;
        }

        int reserved = partitionSize * requests.length;

        System.out.println("Requested memory: " + requested);
        System.out.println("Reserved memory: " + reserved);
        System.out.println(
                "Internal fragmentation: " + (reserved - requested)
        );
    }

    private static void compareStrategies() {
        System.out.println("\n=== Policy comparison ===");

        Map<AllocationStrategy, Integer> fragmentation =
                new EnumMap<>(AllocationStrategy.class);

        for (AllocationStrategy strategy : AllocationStrategy.values()) {
            MemoryAllocationService service =
                    new MemoryAllocationService(200, strategy);

            service.allocate(new AllocationRequest("A", 40));
            service.allocate(new AllocationRequest("B", 70));
            service.allocate(new AllocationRequest("C", 25));
            service.allocate(new AllocationRequest("D", 20));

            service.release("B");
            service.release("D");

            fragmentation.put(
                    strategy,
                    service.externalFragmentation()
            );
        }

        fragmentation.forEach(
                (strategy, value) ->
                        System.out.println(
                                strategy + " -> external fragmentation="
                                        + value
                        )
        );
    }

    public static void main(String[] args) {
        try {
            runEnterpriseScenario();
            demonstrateFixedPartitionWaste();
            compareStrategies();
        } catch (RuntimeException error) {
            System.err.println(
                    "Memory-management operation failed: "
                            + error.getMessage()
            );
            System.exit(1);
        }
    }
}
