import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.Deque;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Random;
import java.util.function.Function;
import java.util.stream.Collectors;

/*
 * Sorting Algorithms II
 * Merge Sort, Quick Sort and Heap Sort
 *
 * Java 17 enterprise-oriented sorting service.
 *
 * Features:
 * - Generic sorting service
 * - Comparator-based ordering
 * - Immutable result records
 * - Algorithm-specific metrics
 * - Input validation
 * - Stable merge sort
 * - Iterative quicksort
 * - Heap sort
 * - Benchmark reporting
 * - Automated verification
 */

public class SortingAlgorithmsII {

    enum Algorithm {
        MERGE_SORT,
        QUICK_SORT,
        HEAP_SORT
    }

    record SortMetrics(
        Algorithm algorithm,
        long comparisons,
        long swaps,
        long writes,
        long partitions,
        double elapsedMilliseconds
    ) {}

    record SortResult<T>(
        List<T> values,
        SortMetrics metrics
    ) {
        SortResult {
            values = List.copyOf(values);
            Objects.requireNonNull(metrics);
        }
    }

    record Employee(
        int id,
        String department,
        double salary
    ) {
        Employee {
            if (id <= 0) {
                throw new IllegalArgumentException(
                    "Employee ID must be positive"
                );
            }

            Objects.requireNonNull(department);

            if (!Double.isFinite(salary) || salary < 0) {
                throw new IllegalArgumentException(
                    "Invalid employee salary"
                );
            }
        }
    }

    static class SortingException extends RuntimeException {
        SortingException(String message) {
            super(message);
        }
    }

    static class MetricsCollector {
        private long comparisons;
        private long swaps;
        private long writes;
        private long partitions;

        void comparison() {
            comparisons++;
        }

        void swap() {
            swaps++;
            writes += 2;
        }

        void write() {
            writes++;
        }

        void partition() {
            partitions++;
        }

        SortMetrics build(
            Algorithm algorithm,
            double elapsed
        ) {
            return new SortMetrics(
                algorithm,
                comparisons,
                swaps,
                writes,
                partitions,
                elapsed
            );
        }
    }

    interface SortStrategy<T> {
        SortResult<T> sort(
            List<T> input,
            Comparator<? super T> comparator
        );
    }

    static <T> void validateInput(
        List<T> input,
        Comparator<? super T> comparator
    ) {
        Objects.requireNonNull(input, "Input cannot be null");
        Objects.requireNonNull(comparator, "Comparator cannot be null");

        if (input.stream().anyMatch(Objects::isNull)) {
            throw new SortingException(
                "Null elements are not supported"
            );
        }
    }

    static <T> int compare(
        T a,
        T b,
        Comparator<? super T> comparator,
        MetricsCollector metrics
    ) {
        metrics.comparison();
        return comparator.compare(a, b);
    }

    static <T> void swap(
        List<T> data,
        int i,
        int j,
        MetricsCollector metrics
    ) {
        if (i == j) return;

        T temporary = data.get(i);
        data.set(i, data.get(j));
        data.set(j, temporary);

        metrics.swap();
    }

    static class MergeSort<T> implements SortStrategy<T> {

        @Override
        public SortResult<T> sort(
            List<T> input,
            Comparator<? super T> comparator
        ) {
            validateInput(input, comparator);

            List<T> data = new ArrayList<>(input);
            MetricsCollector metrics = new MetricsCollector();

            long start = System.nanoTime();

            int n = data.size();

            if (n > 1) {
                List<T> buffer = new ArrayList<>(
                    java.util.Collections.nCopies(n, null)
                );

                merge(data, buffer, 0, n, comparator, metrics);
            }

            double elapsed =
                (System.nanoTime() - start) / 1_000_000.0;

            return new SortResult<>(
                data,
                metrics.build(Algorithm.MERGE_SORT, elapsed)
            );
        }

        private void merge(
            List<T> data,
            List<T> buffer,
            int left,
            int right,
            Comparator<? super T> comparator,
            MetricsCollector metrics
        ) {
            if (right - left <= 1) return;

            int middle = left + (right - left) / 2;

            merge(data, buffer, left, middle, comparator, metrics);
            merge(data, buffer, middle, right, comparator, metrics);

            int i = left;
            int j = middle;
            int k = left;

            while (i < middle && j < right) {
                // Choosing the left element on equality preserves stability.
                if (
                    compare(
                        data.get(i),
                        data.get(j),
                        comparator,
                        metrics
                    ) <= 0
                ) {
                    buffer.set(k++, data.get(i++));
                } else {
                    buffer.set(k++, data.get(j++));
                }

                metrics.write();
            }

            while (i < middle) {
                buffer.set(k++, data.get(i++));
                metrics.write();
            }

            while (j < right) {
                buffer.set(k++, data.get(j++));
                metrics.write();
            }

            for (int position = left; position < right; position++) {
                data.set(position, buffer.get(position));
                metrics.write();
            }
        }
    }

    static class QuickSort<T> implements SortStrategy<T> {

        private record Range(int low, int high) {}

        @Override
        public SortResult<T> sort(
            List<T> input,
            Comparator<? super T> comparator
        ) {
            validateInput(input, comparator);

            List<T> data = new ArrayList<>(input);
            MetricsCollector metrics = new MetricsCollector();

            long start = System.nanoTime();

            if (data.size() > 1) {
                Deque<Range> stack = new ArrayDeque<>();
                stack.push(new Range(0, data.size() - 1));

                while (!stack.isEmpty()) {
                    Range range = stack.pop();

                    int low = range.low();
                    int high = range.high();

                    if (low >= high) continue;

                    T pivot = median(
                        data.get(low),
                        data.get(low + (high - low) / 2),
                        data.get(high),
                        comparator,
                        metrics
                    );

                    int less = low;
                    int current = low;
                    int greater = high;

                    metrics.partition();

                    while (current <= greater) {
                        int order = compare(
                            data.get(current),
                            pivot,
                            comparator,
                            metrics
                        );

                        if (order < 0) {
                            swap(data, less++, current++, metrics);
                        } else if (order > 0) {
                            swap(data, current, greater--, metrics);
                        } else {
                            current++;
                        }
                    }

                    int leftSize = less - low;
                    int rightSize = high - greater;

                    if (leftSize < rightSize) {
                        if (greater < high) {
                            stack.push(new Range(greater + 1, high));
                        }

                        if (less - low > 1) {
                            stack.push(new Range(low, less - 1));
                        }
                    } else {
                        if (less - low > 1) {
                            stack.push(new Range(low, less - 1));
                        }

                        if (greater < high) {
                            stack.push(new Range(greater + 1, high));
                        }
                    }
                }
            }

            double elapsed =
                (System.nanoTime() - start) / 1_000_000.0;

            return new SortResult<>(
                data,
                metrics.build(Algorithm.QUICK_SORT, elapsed)
            );
        }

        private T median(
            T a,
            T b,
            T c,
            Comparator<? super T> comparator,
            MetricsCollector metrics
        ) {
            if (compare(a, b, comparator, metrics) > 0) {
                T temporary = a;
                a = b;
                b = temporary;
            }

            if (compare(b, c, comparator, metrics) > 0) {
                T temporary = b;
                b = c;
                c = temporary;
            }

            if (compare(a, b, comparator, metrics) > 0) {
                T temporary = a;
                a = b;
                b = temporary;
            }

            return b;
        }
    }

    static class HeapSort<T> implements SortStrategy<T> {

        @Override
        public SortResult<T> sort(
            List<T> input,
            Comparator<? super T> comparator
        ) {
            validateInput(input, comparator);

            List<T> data = new ArrayList<>(input);
            MetricsCollector metrics = new MetricsCollector();

            long start = System.nanoTime();

            int n = data.size();

            for (int root = n / 2 - 1; root >= 0; root--) {
                siftDown(
                    data, root, n, comparator, metrics
                );
            }

            for (int end = n - 1; end > 0; end--) {
                swap(data, 0, end, metrics);

                siftDown(
                    data, 0, end, comparator, metrics
                );
            }

            double elapsed =
                (System.nanoTime() - start) / 1_000_000.0;

            return new SortResult<>(
                data,
                metrics.build(Algorithm.HEAP_SORT, elapsed)
            );
        }

        private void siftDown(
            List<T> data,
            int root,
            int end,
            Comparator<? super T> comparator,
            MetricsCollector metrics
        ) {
            while (true) {
                int child = 2 * root + 1;

                if (child >= end) return;

                if (
                    child + 1 < end &&
                    compare(
                        data.get(child),
                        data.get(child + 1),
                        comparator,
                        metrics
                    ) < 0
                ) {
                    child++;
                }

                if (
                    compare(
                        data.get(root),
                        data.get(child),
                        comparator,
                        metrics
                    ) >= 0
                ) {
                    return;
                }

                swap(data, root, child, metrics);
                root = child;
            }
        }
    }

    static class SortingService<T> {

        private final Map<Algorithm, SortStrategy<T>> strategies;

        SortingService() {
            Map<Algorithm, SortStrategy<T>> registry =
                new HashMap<>();

            registry.put(
                Algorithm.MERGE_SORT,
                new MergeSort<>()
            );

            registry.put(
                Algorithm.QUICK_SORT,
                new QuickSort<>()
            );

            registry.put(
                Algorithm.HEAP_SORT,
                new HeapSort<>()
            );

            strategies = Map.copyOf(registry);
        }

        SortResult<T> sort(
            List<T> input,
            Algorithm algorithm,
            Comparator<? super T> comparator
        ) {
            Objects.requireNonNull(algorithm);

            SortStrategy<T> strategy = strategies.get(algorithm);

            if (strategy == null) {
                throw new SortingException(
                    "Sorting strategy is unavailable"
                );
            }

            return strategy.sort(input, comparator);
        }
    }

    static <T> void verify(
        List<T> original,
        SortResult<T> result,
        Comparator<? super T> comparator
    ) {
        List<T> expected = new ArrayList<>(original);
        List<T> actual = new ArrayList<>(result.values());

        expected.sort(comparator);
        actual.sort(comparator);

        if (!expected.equals(actual)) {
            throw new SortingException(
                "Element preservation verification failed"
            );
        }

        List<T> values = result.values();

        for (int i = 1; i < values.size(); i++) {
            if (
                comparator.compare(values.get(i - 1), values.get(i)) > 0
            ) {
                throw new SortingException(
                    "Ordering verification failed"
                );
            }
        }
    }

    static void runTests() {
        SortingService<Integer> service = new SortingService<>();

        Comparator<Integer> comparator = Integer::compare;

        List<List<Integer>> cases = List.of(
            List.of(),
            List.of(1),
            List.of(2, 1),
            List.of(5, 3, 8, 1, 2),
            List.of(4, 4, 4, 4),
            List.of(-10, 0, 10, -5),
            List.of(100, 90, 80, 70, 60)
        );

        for (List<Integer> values : cases) {
            List<Integer> expected = new ArrayList<>(values);
            expected.sort(comparator);

            for (Algorithm algorithm : Algorithm.values()) {
                SortResult<Integer> result = service.sort(
                    values,
                    algorithm,
                    comparator
                );

                if (!result.values().equals(expected)) {
                    throw new AssertionError(
                        "Sorting test failed: " + algorithm
                    );
                }

                verify(values, result, comparator);
            }
        }

        // Validate stable sorting of business records.
        List<Employee> employees = List.of(
            new Employee(1, "Engineering", 80000),
            new Employee(2, "Research", 70000),
            new Employee(3, "Security", 80000),
            new Employee(4, "Operations", 70000)
        );

        Comparator<Employee> salaryComparator =
            Comparator.comparingDouble(Employee::salary);

        SortingService<Employee> employeeService =
            new SortingService<>();

        SortResult<Employee> stable = employeeService.sort(
            employees,
            Algorithm.MERGE_SORT,
            salaryComparator
        );

        List<Integer> stableIds = stable.values()
            .stream()
            .map(Employee::id)
            .collect(Collectors.toList());

        if (!stableIds.equals(List.of(2, 4, 1, 3))) {
            throw new AssertionError(
                "Merge sort stability test failed"
            );
        }

        try {
            service.sort(
                null,
                Algorithm.MERGE_SORT,
                comparator
            );

            throw new AssertionError(
                "Null input should be rejected"
            );
        } catch (NullPointerException expected) {
            // Expected validation behavior.
        }

        System.out.println("All Java 17 sorting tests passed.");
    }

    static void runBenchmark(int size) {
        if (size < 0 || size > 1_000_000) {
            throw new IllegalArgumentException(
                "Benchmark size must be between 0 and 1000000"
            );
        }

        Random random = new Random(42);

        List<Integer> randomValues = new ArrayList<>();
        List<Integer> sortedValues = new ArrayList<>();
        List<Integer> reverseValues = new ArrayList<>();
        List<Integer> duplicates = new ArrayList<>();

        for (int i = 0; i < size; i++) {
            randomValues.add(random.nextInt(200001) - 100000);
            sortedValues.add(i);
            reverseValues.add(size - i);
            duplicates.add(random.nextInt(10));
        }

        Map<String, List<Integer>> datasets = Map.of(
            "random", randomValues,
            "sorted", sortedValues,
            "reverse", reverseValues,
            "duplicates", duplicates
        );

        SortingService<Integer> service = new SortingService<>();

        System.out.printf(
            "%-14s %-14s %-14s %-12s%n",
            "Dataset",
            "Algorithm",
            "Comparisons",
            "Time(ms)"
        );

        for (Map.Entry<String, List<Integer>> entry :
             datasets.entrySet()) {

            for (Algorithm algorithm : Algorithm.values()) {
                SortResult<Integer> result = service.sort(
                    entry.getValue(),
                    algorithm,
                    Integer::compare
                );

                verify(
                    entry.getValue(),
                    result,
                    Integer::compare
                );

                SortMetrics metrics = result.metrics();

                System.out.printf(
                    "%-14s %-14s %-14d %-12.4f%n",
                    entry.getKey(),
                    algorithm,
                    metrics.comparisons(),
                    metrics.elapsedMilliseconds()
                );
            }
        }
    }

    public static void main(String[] args) {
        try {
            runTests();

            SortingService<Integer> service =
                new SortingService<>();

            List<Integer> sample = List.of(
                38, 27, 43, 3, 9, 82, 10, 3
            );

            System.out.println("\nSample results");

            for (Algorithm algorithm : Algorithm.values()) {
                SortResult<Integer> result = service.sort(
                    sample,
                    algorithm,
                    Integer::compare
                );

                System.out.println(
                    algorithm + ": " + result.values()
                );

                System.out.println(
                    "Metrics: " + result.metrics()
                );
            }

            System.out.println("\nBenchmark");

            runBenchmark(10000);

        } catch (Exception error) {
            System.err.println(
                "Execution failed: " + error.getMessage()
            );

            System.exit(1);
        }
    }
}
