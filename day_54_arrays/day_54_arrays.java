import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

public class ArrayOperationsDemo {

    enum Operation {
        ACCESS, SEARCH, INSERT, DELETE, UPDATE
    }

    static final class ArrayOperationException extends RuntimeException {
        ArrayOperationException(String message) {
            super(message);
        }
    }

    record OperationStats(
            int accesses,
            int searches,
            int insertions,
            int deletions,
            int updates) {

        OperationStats record(Operation operation) {
            return switch (operation) {
                case ACCESS -> new OperationStats(
                        accesses + 1, searches, insertions, deletions, updates);
                case SEARCH -> new OperationStats(
                        accesses, searches + 1, insertions, deletions, updates);
                case INSERT -> new OperationStats(
                        accesses, searches, insertions + 1, deletions, updates);
                case DELETE -> new OperationStats(
                        accesses, searches, insertions, deletions + 1, updates);
                case UPDATE -> new OperationStats(
                        accesses, searches, insertions, deletions, updates + 1);
            };
        }
    }

    interface SearchStrategy {
        int find(List<Integer> values, int target);
    }

    static final class LinearSearch implements SearchStrategy {
        @Override
        public int find(List<Integer> values, int target) {
            for (int i = 0; i < values.size(); i++) {
                if (values.get(i) == target) {
                    return i;
                }
            }
            return -1;
        }
    }

    static final class BinarySearch implements SearchStrategy {
        @Override
        public int find(List<Integer> values, int target) {
            if (!isSorted(values)) {
                throw new ArrayOperationException(
                        "Binary search requires sorted data.");
            }

            int low = 0;
            int high = values.size() - 1;

            while (low <= high) {
                int middle = low + (high - low) / 2;
                int value = values.get(middle);

                if (value == target) {
                    return middle;
                }

                if (value < target) {
                    low = middle + 1;
                } else {
                    high = middle - 1;
                }
            }

            return -1;
        }

        private boolean isSorted(List<Integer> values) {
            for (int i = 1; i < values.size(); i++) {
                if (values.get(i - 1) > values.get(i)) {
                    return false;
                }
            }
            return true;
        }
    }

    static final class RepositoryArray {
        private final List<Integer> values = new ArrayList<>();
        private int capacity;
        private OperationStats stats = new OperationStats(0, 0, 0, 0, 0);

        RepositoryArray(int capacity) {
            if (capacity <= 0) {
                throw new IllegalArgumentException(
                        "Capacity must be positive.");
            }
            this.capacity = capacity;
        }

        int size() {
            return values.size();
        }

        int capacity() {
            return capacity;
        }

        private void validateIndex(int index, boolean allowEnd) {
            int upper = allowEnd ? values.size() : values.size() - 1;

            if (index < 0 || index > upper) {
                throw new ArrayOperationException(
                        "Invalid index: " + index);
            }
        }

        private void growIfRequired() {
            if (values.size() >= capacity) {
                capacity *= 2;
            }
        }

        int access(int index) {
            validateIndex(index, false);
            stats = stats.record(Operation.ACCESS);
            return values.get(index);
        }

        void update(int index, int value) {
            validateIndex(index, false);
            values.set(index, value);
            stats = stats.record(Operation.UPDATE);
        }

        void insert(int index, int value) {
            validateIndex(index, true);
            growIfRequired();

            /*
             * ArrayList maintains contiguous logical ordering and shifts
             * the suffix when an arbitrary position receives a new value.
             */
            values.add(index, value);
            stats = stats.record(Operation.INSERT);
        }

        void append(int value) {
            insert(values.size(), value);
        }

        int delete(int index) {
            validateIndex(index, false);
            int removed = values.remove(index);
            stats = stats.record(Operation.DELETE);
            return removed;
        }

        int search(int value, SearchStrategy strategy) {
            Objects.requireNonNull(strategy, "Search strategy is required.");
            stats = stats.record(Operation.SEARCH);
            return strategy.find(values, value);
        }

        void reverse() {
            Collections.reverse(values);
        }

        List<Integer> snapshot() {
            return List.copyOf(values);
        }

        OperationStats stats() {
            return stats;
        }
    }

    private static void require(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }

    private static void runTests() {
        RepositoryArray array = new RepositoryArray(2);

        array.append(10);
        array.append(20);
        array.append(30);
        array.append(40);

        require(array.size() == 4, "size");
        require(array.capacity() >= 4, "capacity");
        require(array.access(2) == 30, "access");

        array.update(1, 25);
        require(array.search(25, new LinearSearch()) == 1, "update/search");

        array.insert(2, 27);
        require(array.access(2) == 27, "insert");

        require(array.delete(1) == 25, "delete");

        array.reverse();
        require(array.access(0) == 40, "reverse");

        RepositoryArray sorted = new RepositoryArray(4);
        for (int value : List.of(10, 20, 30, 40, 50)) {
            sorted.append(value);
        }

        require(sorted.search(40, new BinarySearch()) == 3, "binary search");
        require(sorted.search(999, new BinarySearch()) == -1,
                "binary search miss");
    }

    private static void demonstrateFailures() {
        RepositoryArray array = new RepositoryArray(2);
        array.append(10);

        try {
            array.access(5);
        } catch (ArrayOperationException exception) {
            System.out.println("Invalid access rejected: "
                    + exception.getMessage());
        }

        try {
            array.insert(5, 20);
        } catch (ArrayOperationException exception) {
            System.out.println("Invalid insertion rejected: "
                    + exception.getMessage());
        }

        try {
            RepositoryArray unsorted = new RepositoryArray(3);
            unsorted.append(30);
            unsorted.append(10);
            unsorted.search(10, new BinarySearch());
        } catch (ArrayOperationException exception) {
            System.out.println("Invalid binary search rejected: "
                    + exception.getMessage());
        }
    }

    public static void main(String[] args) {
        runTests();

        RepositoryArray array = new RepositoryArray(2);
        for (int value : List.of(101, 203, 305, 407, 509)) {
            array.append(value);
        }

        array.update(2, 306);
        array.insert(1, 150);

        System.out.println("Repository data: " + array.snapshot());
        System.out.println("306 found at: "
                + array.search(306, new LinearSearch()));
        System.out.println("Deleted: " + array.delete(1));
        System.out.println("After deletion: " + array.snapshot());

        System.out.println("Statistics: " + array.stats());

        demonstrateFailures();

        System.out.println("\nComplexity:");
        System.out.println("Indexed access: O(1)");
        System.out.println("Linear search: O(n)");
        System.out.println("Binary search: O(log n), sorted input required");
        System.out.println("Indexed insertion/deletion: O(n)");
        System.out.println("Append: amortized O(1)");
        System.out.println("Traversal: O(n)");
    }
}
