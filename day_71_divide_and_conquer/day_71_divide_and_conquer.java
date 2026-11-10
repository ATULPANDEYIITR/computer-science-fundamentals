import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.Objects;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicLong;
import java.util.stream.Collectors;

/**
 * Divide and Conquer Enterprise Algorithm Service.
 *
 * Java 17 implementation featuring:
 * - Immutable algorithm requests and results
 * - Strategy-based algorithm execution
 * - Recursive sorting and searching
 * - Maximum subarray computation
 * - Recurrence analysis
 * - Execution auditing
 * - Input validation and service-level controls
 */
public class Main {

    enum AlgorithmType {
        MERGE_SORT,
        QUICK_SORT,
        BINARY_SEARCH,
        MAXIMUM_SUBARRAY
    }

    enum ExecutionStatus {
        ACCEPTED,
        RUNNING,
        COMPLETED,
        REJECTED,
        FAILED
    }

    record AlgorithmRequest(
        String requestId,
        AlgorithmType algorithm,
        List<Integer> input,
        Integer target
    ) {
        AlgorithmRequest {
            if (requestId == null || requestId.isBlank()) {
                throw new IllegalArgumentException("Request ID is required.");
            }

            Objects.requireNonNull(algorithm, "Algorithm is required.");
            Objects.requireNonNull(input, "Input is required.");

            input = List.copyOf(input);

            if (input.size() > 1_000_000) {
                throw new IllegalArgumentException("Input exceeds size limit.");
            }

            if (input.stream().anyMatch(Objects::isNull)) {
                throw new IllegalArgumentException("Null input elements are not allowed.");
            }

            if (algorithm == AlgorithmType.BINARY_SEARCH && target == null) {
                throw new IllegalArgumentException("Binary search requires a target.");
            }

            if (algorithm == AlgorithmType.MAXIMUM_SUBARRAY && input.isEmpty()) {
                throw new IllegalArgumentException("Maximum subarray requires input.");
            }
        }
    }

    record AlgorithmResult(
        String requestId,
        AlgorithmType algorithm,
        ExecutionStatus status,
        Object output,
        long recursiveCalls,
        long executionNanos,
        String message
    ) {}

    record MaximumSubarray(
        long sum,
        int startIndex,
        int endIndex
    ) {}

    record Recurrence(
        String name,
        int a,
        int b,
        double d
    ) {
        Recurrence {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("Recurrence name required.");
            }

            if (a < 1 || b < 2 || d < 0) {
                throw new IllegalArgumentException("Invalid recurrence parameters.");
            }
        }

        double criticalExponent() {
            return Math.log(a) / Math.log(b);
        }

        String complexity() {
            double critical = criticalExponent();
            double epsilon = 1e-10;

            if (d < critical - epsilon) {
                return String.format("Theta(n^%.3f)", critical);
            }

            if (Math.abs(d - critical) <= epsilon) {
                return String.format("Theta(n^%.3f log n)", critical);
            }

            return String.format("Theta(n^%.3f)", d);
        }
    }

    interface AlgorithmStrategy {
        Object execute(AlgorithmRequest request);
        long recursiveCalls();
    }

    static class AlgorithmException extends RuntimeException {
        AlgorithmException(String message) {
            super(message);
        }
    }

    static class MergeSortStrategy implements AlgorithmStrategy {

        private long calls;

        @Override
        public Object execute(AlgorithmRequest request) {
            calls = 0;
            return sort(request.input());
        }

        private List<Integer> sort(List<Integer> values) {
            calls++;

            if (values.size() <= 1) {
                return new ArrayList<>(values);
            }

            int middle = values.size() / 2;

            List<Integer> left = sort(
                values.subList(0, middle)
            );

            List<Integer> right = sort(
                values.subList(middle, values.size())
            );

            return merge(left, right);
        }

        private List<Integer> merge(
            List<Integer> left,
            List<Integer> right
        ) {
            List<Integer> output = new ArrayList<>(
                left.size() + right.size()
            );

            int i = 0;
            int j = 0;

            while (i < left.size() && j < right.size()) {
                if (left.get(i) <= right.get(j)) {
                    output.add(left.get(i++));
                } else {
                    output.add(right.get(j++));
                }
            }

            output.addAll(left.subList(i, left.size()));
            output.addAll(right.subList(j, right.size()));

            return output;
        }

        @Override
        public long recursiveCalls() {
            return calls;
        }
    }

    static class QuickSortStrategy implements AlgorithmStrategy {

        private long calls;

        @Override
        public Object execute(AlgorithmRequest request) {
            calls = 0;
            List<Integer> result = new ArrayList<>(request.input());
            sort(result, 0, result.size() - 1);
            return List.copyOf(result);
        }

        private void sort(List<Integer> values, int low, int high) {
            if (low >= high) return;

            calls++;

            int middle = low + (high - low) / 2;
            int pivot = values.get(middle);

            int i = low;
            int j = high;

            while (i <= j) {
                while (values.get(i) < pivot) i++;
                while (values.get(j) > pivot) j--;

                if (i <= j) {
                    Collections.swap(values, i, j);
                    i++;
                    j--;
                }
            }

            if (low < j) sort(values, low, j);
            if (i < high) sort(values, i, high);
        }

        @Override
        public long recursiveCalls() {
            return calls;
        }
    }

    static class BinarySearchStrategy implements AlgorithmStrategy {

        @Override
        public Object execute(AlgorithmRequest request) {
            List<Integer> values = request.input();

            for (int i = 1; i < values.size(); i++) {
                if (values.get(i - 1) > values.get(i)) {
                    throw new AlgorithmException(
                        "Binary search requires sorted input."
                    );
                }
            }

            int left = 0;
            int right = values.size() - 1;

            while (left <= right) {
                int middle = left + (right - left) / 2;
                int value = values.get(middle);

                if (value == request.target()) return middle;

                if (value < request.target()) {
                    left = middle + 1;
                } else {
                    right = middle - 1;
                }
            }

            return -1;
        }

        @Override
        public long recursiveCalls() {
            return 0;
        }
    }

    static class MaximumSubarrayStrategy implements AlgorithmStrategy {

        private long calls;
        private List<Integer> values;

        @Override
        public Object execute(AlgorithmRequest request) {
            values = request.input();
            calls = 0;

            return solve(0, values.size() - 1);
        }

        private MaximumSubarray solve(int left, int right) {
            calls++;

            if (left == right) {
                return new MaximumSubarray(
                    values.get(left), left, right
                );
            }

            int middle = left + (right - left) / 2;

            MaximumSubarray first = solve(left, middle);
            MaximumSubarray second = solve(middle + 1, right);

            long sum = 0;
            long bestLeft = Long.MIN_VALUE;
            int start = middle;

            for (int i = middle; i >= left; i--) {
                sum += values.get(i);

                if (sum > bestLeft) {
                    bestLeft = sum;
                    start = i;
                }
            }

            sum = 0;
            long bestRight = Long.MIN_VALUE;
            int end = middle + 1;

            for (int i = middle + 1; i <= right; i++) {
                sum += values.get(i);

                if (sum > bestRight) {
                    bestRight = sum;
                    end = i;
                }
            }

            MaximumSubarray cross = new MaximumSubarray(
                bestLeft + bestRight,
                start,
                end
            );

            return List.of(first, second, cross)
                .stream()
                .max(Comparator.comparingLong(MaximumSubarray::sum))
                .orElseThrow();
        }

        @Override
        public long recursiveCalls() {
            return calls;
        }
    }

    static class AuditService {

        private final List<AlgorithmResult> records =
            Collections.synchronizedList(new ArrayList<>());

        void record(AlgorithmResult result) {
            records.add(result);
        }

        List<AlgorithmResult> history() {
            synchronized (records) {
                return List.copyOf(records);
            }
        }

        Map<ExecutionStatus, Long> aggregate() {
            return history().stream().collect(
                Collectors.groupingBy(
                    AlgorithmResult::status,
                    Collectors.counting()
                )
            );
        }
    }

    static class AlgorithmExecutionService {

        private final Map<AlgorithmType, AlgorithmStrategy> strategies =
            new HashMap<>();

        private final AuditService audit = new AuditService();

        AlgorithmExecutionService() {
            strategies.put(
                AlgorithmType.MERGE_SORT,
                new MergeSortStrategy()
            );

            strategies.put(
                AlgorithmType.QUICK_SORT,
                new QuickSortStrategy()
            );

            strategies.put(
                AlgorithmType.BINARY_SEARCH,
                new BinarySearchStrategy()
            );

            strategies.put(
                AlgorithmType.MAXIMUM_SUBARRAY,
                new MaximumSubarrayStrategy()
            );
        }

        AlgorithmResult execute(AlgorithmRequest request) {
            Objects.requireNonNull(request, "Request cannot be null.");

            AlgorithmStrategy strategy = strategies.get(
                request.algorithm()
            );

            if (strategy == null) {
                throw new AlgorithmException("Unsupported algorithm.");
            }

            long start = System.nanoTime();

            try {
                Object output = strategy.execute(request);

                AlgorithmResult result = new AlgorithmResult(
                    request.requestId(),
                    request.algorithm(),
                    ExecutionStatus.COMPLETED,
                    output,
                    strategy.recursiveCalls(),
                    System.nanoTime() - start,
                    "Execution completed."
                );

                audit.record(result);
                return result;

            } catch (RuntimeException exception) {
                AlgorithmResult result = new AlgorithmResult(
                    request.requestId(),
                    request.algorithm(),
                    ExecutionStatus.FAILED,
                    null,
                    strategy.recursiveCalls(),
                    System.nanoTime() - start,
                    exception.getMessage()
                );

                audit.record(result);
                throw exception;
            }
        }

        AuditService audit() {
            return audit;
        }
    }

    public static void main(String[] args) {

        AlgorithmExecutionService service =
            new AlgorithmExecutionService();

        System.out.println("DIVIDE AND CONQUER ENTERPRISE ENGINE");
        System.out.println("====================================");

        AlgorithmRequest mergeRequest = new AlgorithmRequest(
            UUID.randomUUID().toString(),
            AlgorithmType.MERGE_SORT,
            List.of(38, 27, 43, 3, 9, 82, 10, 27),
            null
        );

        AlgorithmResult mergeResult = service.execute(mergeRequest);

        System.out.println("\n1. MERGE SORT");
        System.out.println(mergeResult.output());
        System.out.println("Recursive calls: " + mergeResult.recursiveCalls());

        @SuppressWarnings("unchecked")
        List<Integer> sorted = (List<Integer>) mergeResult.output();

        AlgorithmRequest searchRequest = new AlgorithmRequest(
            UUID.randomUUID().toString(),
            AlgorithmType.BINARY_SEARCH,
            sorted,
            27
        );

        AlgorithmResult searchResult = service.execute(searchRequest);

        System.out.println("\n2. BINARY SEARCH");
        System.out.println("Position: " + searchResult.output());

        AlgorithmRequest quickRequest = new AlgorithmRequest(
            UUID.randomUUID().toString(),
            AlgorithmType.QUICK_SORT,
            List.of(9, 3, 7, 3, 1, 8, 2),
            null
        );

        System.out.println("\n3. QUICK SORT");
        System.out.println(service.execute(quickRequest).output());

        AlgorithmRequest maximumRequest = new AlgorithmRequest(
            UUID.randomUUID().toString(),
            AlgorithmType.MAXIMUM_SUBARRAY,
            List.of(-2, 1, -3, 4, -1, 2, 1, -5, 4),
            null
        );

        System.out.println("\n4. MAXIMUM SUBARRAY");
        System.out.println(service.execute(maximumRequest).output());

        System.out.println("\n5. RECURRENCE ANALYSIS");

        List<Recurrence> recurrences = List.of(
            new Recurrence("Binary Search", 1, 2, 0),
            new Recurrence("Merge Sort", 2, 2, 1),
            new Recurrence("Karatsuba", 3, 2, 1),
            new Recurrence("Strassen", 7, 2, 2),
            new Recurrence("Quadratic Combine", 2, 2, 2)
        );

        recurrences.forEach(recurrence ->
            System.out.println(
                recurrence.name() + ": " + recurrence.complexity()
            )
        );

        System.out.println("\n6. EXECUTION AUDIT");

        service.audit().history().forEach(result ->
            System.out.printf(
                "%s | %s | %s | %.3f ms%n",
                result.algorithm(),
                result.status(),
                result.message(),
                result.executionNanos() / 1_000_000.0
            )
        );

        System.out.println("\n7. STATUS AGGREGATION");
        System.out.println(service.audit().aggregate());

        System.out.println("\nAll Java 17 demonstrations completed.");
    }
}
