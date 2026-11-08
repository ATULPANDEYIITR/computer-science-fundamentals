import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import java.util.function.Consumer;

/**
 * Sorting Algorithms I
 *
 * Java 17 implementation of:
 * - Bubble Sort
 * - Selection Sort
 * - Insertion Sort
 *
 * Enterprise scenario:
 * Inventory prioritization and procurement processing.
 *
 * Compile: javac SortingAlgorithms.java
 * Run: java SortingAlgorithms
 */

public class SortingAlgorithms {

    enum Algorithm {
        BUBBLE,
        SELECTION,
        INSERTION
    }

    enum SortStatus {
        COMPLETED,
        FAILED
    }

    record Metrics(
        Algorithm algorithm,
        long comparisons,
        long swaps,
        long shifts,
        long passes,
        double durationMs
    ) {}

    record SortResult<T>(
        List<T> values,
        Metrics metrics,
        SortStatus status
    ) {
        SortResult {
            values = List.copyOf(values);
            Objects.requireNonNull(metrics);
            Objects.requireNonNull(status);
        }
    }

    record InventoryItem(
        String productId,
        String productName,
        int stock,
        double price
    ) {
        InventoryItem {
            if (
                productId == null ||
                productId.isBlank() ||
                productName == null ||
                productName.isBlank()
            ) {
                throw new IllegalArgumentException(
                    "Product identity fields are required."
                );
            }

            if (stock < 0 || !Double.isFinite(price) || price < 0) {
                throw new IllegalArgumentException(
                    "Invalid stock or price."
                );
            }
        }
    }

    record ProcurementPolicy(
        int criticalStockThreshold,
        double maximumPurchasePrice
    ) {
        ProcurementPolicy {
            if (
                criticalStockThreshold < 0 ||
                !Double.isFinite(maximumPurchasePrice) ||
                maximumPurchasePrice < 0
            ) {
                throw new IllegalArgumentException(
                    "Invalid procurement policy."
                );
            }
        }

        boolean isEligible(InventoryItem item) {
            return item.stock <= criticalStockThreshold
                && item.price <= maximumPurchasePrice;
        }
    }

    static class SortingException extends RuntimeException {
        SortingException(String message) {
            super(message);
        }
    }

    static class SortingService {

        private final int maximumRecords;

        private final List<Consumer<SortResult<?>>> listeners =
            new ArrayList<>();

        SortingService(int maximumRecords) {
            if (maximumRecords < 0) {
                throw new IllegalArgumentException(
                    "Maximum records cannot be negative."
                );
            }

            this.maximumRecords = maximumRecords;
        }

        void addListener(Consumer<SortResult<?>> listener) {
            listeners.add(Objects.requireNonNull(listener));
        }

        private <T> List<T> validate(
            List<T> input,
            Comparator<? super T> comparator
        ) {
            if (input == null || comparator == null) {
                throw new SortingException(
                    "Input and comparator are required."
                );
            }

            if (input.size() > maximumRecords) {
                throw new SortingException(
                    "Dataset exceeds configured capacity."
                );
            }

            if (input.stream().anyMatch(Objects::isNull)) {
                throw new SortingException(
                    "Null elements are not supported."
                );
            }

            return new ArrayList<>(input);
        }

        <T> SortResult<T> sort(
            List<T> input,
            Algorithm algorithm,
            Comparator<? super T> comparator,
            boolean descending
        ) {
            if (algorithm == null) {
                throw new SortingException(
                    "Sorting algorithm is required."
                );
            }

            List<T> values = validate(input, comparator);

            Comparator<T> effectiveComparator =
                (a, b) -> descending
                    ? comparator.compare(b, a)
                    : comparator.compare(a, b);

            long comparisons = 0;
            long swaps = 0;
            long shifts = 0;
            long passes = 0;

            long start = System.nanoTime();

            switch (algorithm) {

                case BUBBLE -> {
                    for (int i = 0; i < values.size() - 1; i++) {
                        boolean swapped = false;
                        passes++;

                        for (
                            int j = 0;
                            j < values.size() - i - 1;
                            j++
                        ) {
                            comparisons++;

                            if (
                                effectiveComparator.compare(
                                    values.get(j),
                                    values.get(j + 1)
                                ) > 0
                            ) {
                                T temporary = values.get(j);

                                values.set(j, values.get(j + 1));
                                values.set(j + 1, temporary);

                                swaps++;
                                swapped = true;
                            }
                        }

                        if (!swapped) break;
                    }
                }

                case SELECTION -> {
                    for (int i = 0; i < values.size() - 1; i++) {
                        passes++;

                        int minimum = i;

                        for (
                            int j = i + 1;
                            j < values.size();
                            j++
                        ) {
                            comparisons++;

                            if (
                                effectiveComparator.compare(
                                    values.get(j),
                                    values.get(minimum)
                                ) < 0
                            ) {
                                minimum = j;
                            }
                        }

                        if (minimum != i) {
                            T temporary = values.get(i);

                            values.set(i, values.get(minimum));
                            values.set(minimum, temporary);

                            swaps++;
                        }
                    }
                }

                case INSERTION -> {
                    for (int i = 1; i < values.size(); i++) {
                        passes++;

                        T current = values.get(i);
                        int j = i - 1;

                        while (j >= 0) {
                            comparisons++;

                            if (
                                effectiveComparator.compare(
                                    values.get(j),
                                    current
                                ) <= 0
                            ) {
                                break;
                            }

                            values.set(j + 1, values.get(j));
                            shifts++;
                            j--;
                        }

                        values.set(j + 1, current);
                    }
                }
            }

            double duration = TimeUnit.NANOSECONDS.toNanos(
                System.nanoTime() - start
            ) / 1_000_000.0;

            Metrics metrics = new Metrics(
                algorithm,
                comparisons,
                swaps,
                shifts,
                passes,
                duration
            );

            SortResult<T> result = new SortResult<>(
                values,
                metrics,
                SortStatus.COMPLETED
            );

            // Listener failures must not invalidate a completed sort.
            for (Consumer<SortResult<?>> listener : listeners) {
                try {
                    listener.accept(result);
                } catch (RuntimeException exception) {
                    System.err.println(
                        "Notification failed: " + exception.getMessage()
                    );
                }
            }

            return result;
        }
    }

    static class InventoryService {

        private final List<InventoryItem> inventory;
        private final SortingService sortingService;

        InventoryService(
            List<InventoryItem> inventory,
            SortingService sortingService
        ) {
            Objects.requireNonNull(inventory);
            this.sortingService = Objects.requireNonNull(sortingService);

            Set<String> identifiers = new HashSet<>();

            for (InventoryItem item : inventory) {
                Objects.requireNonNull(item);

                if (!identifiers.add(item.productId())) {
                    throw new IllegalArgumentException(
                        "Duplicate product ID: " + item.productId()
                    );
                }
            }

            this.inventory = List.copyOf(inventory);
        }

        SortResult<InventoryItem> prioritizeStock() {
            return sortingService.sort(
                inventory,
                Algorithm.INSERTION,
                Comparator.comparingInt(InventoryItem::stock),
                false
            );
        }

        SortResult<InventoryItem> prioritizePrice() {
            return sortingService.sort(
                inventory,
                Algorithm.SELECTION,
                Comparator.comparingDouble(InventoryItem::price),
                false
            );
        }

        List<InventoryItem> eligibleForProcurement(
            ProcurementPolicy policy
        ) {
            Objects.requireNonNull(policy);

            return inventory.stream()
                .filter(policy::isEligible)
                .toList();
        }
    }

    static void printMetrics(Metrics metrics) {
        System.out.printf(
            "%-12s Comparisons=%-6d Swaps=%-6d "
                + "Shifts=%-6d Passes=%-5d Time=%.4f ms%n",
            metrics.algorithm(),
            metrics.comparisons(),
            metrics.swaps(),
            metrics.shifts(),
            metrics.passes(),
            metrics.durationMs()
        );
    }

    static void demonstrateBasicSorting(
        SortingService service
    ) {
        System.out.println("\n=== BASIC SORTING ===");

        List<Integer> numbers =
            List.of(64, 34, 25, 12, 22, 11, 90);

        System.out.println("Original: " + numbers);

        for (Algorithm algorithm : Algorithm.values()) {
            SortResult<Integer> result = service.sort(
                numbers,
                algorithm,
                Comparator.naturalOrder(),
                false
            );

            System.out.println(
                algorithm + ": " + result.values()
            );

            printMetrics(result.metrics());
        }
    }

    static void demonstrateInventory(
        SortingService service
    ) {
        System.out.println("\n=== ENTERPRISE INVENTORY ===");

        List<InventoryItem> items = List.of(
            new InventoryItem("P101", "Keyboard", 45, 1200),
            new InventoryItem("P102", "Monitor", 12, 9500),
            new InventoryItem("P103", "Mouse", 80, 650),
            new InventoryItem("P104", "Laptop", 8, 55000),
            new InventoryItem("P105", "Headphones", 25, 1800)
        );

        InventoryService inventoryService =
            new InventoryService(items, service);

        SortResult<InventoryItem> result =
            inventoryService.prioritizeStock();

        for (InventoryItem item : result.values()) {
            System.out.printf(
                "%s | %-12s | Stock=%3d | Price=%.2f%n",
                item.productId(),
                item.productName(),
                item.stock(),
                item.price()
            );
        }

        printMetrics(result.metrics());

        ProcurementPolicy policy =
            new ProcurementPolicy(20, 10000);

        System.out.println("\nProcurement-eligible products:");

        for (
            InventoryItem item :
            inventoryService.eligibleForProcurement(policy)
        ) {
            System.out.println(item.productName());
        }
    }

    static void benchmark(SortingService service) {
        System.out.println("\n=== PERFORMANCE BENCHMARK ===");

        java.util.Random random =
            new java.util.Random(42);

        for (int size : List.of(20, 100, 300)) {
            List<Integer> values = new ArrayList<>();

            for (int i = 0; i < size; i++) {
                values.add(random.nextInt(10000));
            }

            System.out.println("\nDataset size: " + size);

            List<Integer> expected = values.stream()
                .sorted()
                .toList();

            for (Algorithm algorithm : Algorithm.values()) {
                SortResult<Integer> result = service.sort(
                    values,
                    algorithm,
                    Comparator.naturalOrder(),
                    false
                );

                if (!result.values().equals(expected)) {
                    throw new SortingException(
                        "Benchmark verification failed."
                    );
                }

                printMetrics(result.metrics());
            }
        }
    }

    static void runTests(SortingService service) {
        System.out.println("\n=== VALIDATION TESTS ===");

        List<List<Integer>> cases = List.of(
            List.of(),
            List.of(1),
            List.of(5, 4, 3, 2, 1),
            List.of(1, 2, 3, 4, 5),
            List.of(3, 3, 3, 3),
            List.of(-5, 0, 10, -20, 7)
        );

        for (List<Integer> input : cases) {
            List<Integer> expected = input.stream()
                .sorted()
                .toList();

            for (Algorithm algorithm : Algorithm.values()) {
                SortResult<Integer> result = service.sort(
                    input,
                    algorithm,
                    Comparator.naturalOrder(),
                    false
                );

                if (!result.values().equals(expected)) {
                    throw new AssertionError(
                        algorithm + " failed for " + input
                    );
                }
            }
        }

        SortResult<Integer> descending = service.sort(
            List.of(1, 5, 3, 2),
            Algorithm.INSERTION,
            Comparator.naturalOrder(),
            true
        );

        if (!descending.values().equals(List.of(5, 3, 2, 1))) {
            throw new AssertionError("Descending test failed.");
        }

        try {
            service.sort(
                List.of(1, 2),
                Algorithm.BUBBLE,
                null,
                false
            );

            throw new AssertionError(
                "Invalid comparator was accepted."
            );

        } catch (SortingException expected) {
            System.out.println("Invalid comparator rejected.");
        }

        try {
            new InventoryItem("P999", "Invalid", -1, 100);

            throw new AssertionError(
                "Negative stock was accepted."
            );

        } catch (IllegalArgumentException expected) {
            System.out.println("Invalid inventory rejected.");
        }

        System.out.println("All tests passed.");
    }

    public static void main(String[] args) {
        System.out.println("====================================");
        System.out.println("SORTING ALGORITHMS I - JAVA 17");
        System.out.println("====================================");

        try {
            SortingService service = new SortingService(100000);

            service.addListener(result ->
                System.out.println(
                    "[EVENT] Sorting completed: "
                        + result.metrics().algorithm()
                )
            );

            demonstrateBasicSorting(service);
            demonstrateInventory(service);
            benchmark(service);
            runTests(service);

            System.out.println(
                "\nAll sorting operations completed."
            );

        } catch (RuntimeException exception) {
            System.err.println(
                "Application failure: " + exception.getMessage()
            );

            System.exit(1);
        }
    }
}
