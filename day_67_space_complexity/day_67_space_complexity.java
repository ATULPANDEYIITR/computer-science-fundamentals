import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.function.ToLongFunction;

/*
 * SPACE COMPLEXITY
 *
 * Enterprise memory governance and algorithm analysis.
 *
 * Java 17 implementation:
 * - Explicit memory policies
 * - Algorithmic memory estimates
 * - Immutable reports
 * - Auxiliary-space classification
 * - Recursion and iterative alternatives
 * - Dynamic programming optimization
 * - Streaming aggregation
 * - Resource allocation
 * - Validation and failure handling
 */

public class SpaceComplexityManager {

    enum Complexity {
        CONSTANT("O(1)"),
        LOGARITHMIC("O(log n)"),
        LINEAR("O(n)"),
        QUADRATIC("O(n^2)");

        private final String notation;

        Complexity(String notation) {
            this.notation = notation;
        }

        public String notation() {
            return notation;
        }
    }

    enum MemoryStatus {
        ACCEPTED,
        REJECTED
    }

    record MemoryReport(
        String algorithm,
        long inputSize,
        long auxiliaryBytes,
        Complexity complexity,
        String explanation
    ) {
        public MemoryReport {
            if (algorithm == null || algorithm.isBlank()) {
                throw new IllegalArgumentException(
                    "Algorithm name is required."
                );
            }

            if (inputSize < 0 || auxiliaryBytes < 0) {
                throw new IllegalArgumentException(
                    "Memory values cannot be negative."
                );
            }

            if (complexity == null) {
                throw new IllegalArgumentException(
                    "Complexity classification is required."
                );
            }
        }

        public void display() {
            System.out.println("\nAlgorithm: " + algorithm);
            System.out.println("Input size: " + inputSize);
            System.out.println("Auxiliary bytes: " + auxiliaryBytes);
            System.out.println(
                "Complexity: " + complexity.notation()
            );
            System.out.println("Details: " + explanation);
        }
    }

    record BudgetDecision(
        MemoryStatus status,
        long requiredBytes,
        long availableBytes,
        String message
    ) {}

    static class MemoryBudgetException extends RuntimeException {
        public MemoryBudgetException(String message) {
            super(message);
        }
    }

    static class MemoryPolicy {
        private final long maximumBytes;

        public MemoryPolicy(long maximumBytes) {
            if (maximumBytes <= 0) {
                throw new IllegalArgumentException(
                    "Maximum memory must be positive."
                );
            }

            this.maximumBytes = maximumBytes;
        }

        public BudgetDecision evaluate(long requiredBytes) {
            if (requiredBytes < 0) {
                throw new IllegalArgumentException(
                    "Required memory cannot be negative."
                );
            }

            if (requiredBytes > maximumBytes) {
                return new BudgetDecision(
                    MemoryStatus.REJECTED,
                    requiredBytes,
                    maximumBytes,
                    "Memory requirement exceeds policy."
                );
            }

            return new BudgetDecision(
                MemoryStatus.ACCEPTED,
                requiredBytes,
                maximumBytes,
                "Memory requirement accepted."
            );
        }

        public void enforce(long requiredBytes) {
            BudgetDecision decision = evaluate(requiredBytes);

            if (decision.status() == MemoryStatus.REJECTED) {
                throw new MemoryBudgetException(
                    decision.message()
                );
            }
        }
    }

    static class AlgorithmService {

        public long sumConstantSpace(int[] values) {
            validateArray(values);

            long total = 0;

            for (int value : values) {
                total += value;
            }

            return total;
        }

        public int[] copyData(int[] values) {
            validateArray(values);
            return Arrays.copyOf(values, values.length);
        }

        public void reverseInPlace(int[] values) {
            validateArray(values);

            int left = 0;
            int right = values.length - 1;

            while (left < right) {
                int temporary = values[left];
                values[left] = values[right];
                values[right] = temporary;

                left++;
                right--;
            }
        }

        public int binarySearchIterative(
            int[] values,
            int target
        ) {
            int left = 0;
            int right = values.length - 1;

            while (left <= right) {
                int middle = left + (right - left) / 2;

                if (values[middle] == target) {
                    return middle;
                }

                if (values[middle] < target) {
                    left = middle + 1;
                } else {
                    right = middle - 1;
                }
            }

            return -1;
        }

        public int binarySearchRecursive(
            int[] values,
            int target,
            int left,
            int right
        ) {
            if (left > right) {
                return -1;
            }

            int middle = left + (right - left) / 2;

            if (values[middle] == target) {
                return middle;
            }

            if (values[middle] > target) {
                return binarySearchRecursive(
                    values, target, left, middle - 1
                );
            }

            return binarySearchRecursive(
                values, target, middle + 1, right
            );
        }

        public List<Integer> uniqueValues(int[] values) {
            validateArray(values);

            Set<Integer> seen = new HashSet<>();
            List<Integer> result = new ArrayList<>();

            for (int value : values) {
                if (seen.add(value)) {
                    result.add(value);
                }
            }

            return result;
        }

        public long fibonacciFullTable(int n) {
            validateFibonacciInput(n);

            if (n == 0) {
                return 0;
            }

            long[] dp = new long[n + 1];
            dp[1] = 1;

            for (int i = 2; i <= n; i++) {
                dp[i] = Math.addExact(
                    dp[i - 1],
                    dp[i - 2]
                );
            }

            return dp[n];
        }

        public long fibonacciOptimized(int n) {
            validateFibonacciInput(n);

            long previous = 0;
            long current = 1;

            for (int i = 0; i < n; i++) {
                long next = Math.addExact(previous, current);
                previous = current;
                current = next;
            }

            return previous;
        }

        private void validateArray(int[] values) {
            if (values == null) {
                throw new IllegalArgumentException(
                    "Input array cannot be null."
                );
            }
        }

        private void validateFibonacciInput(int n) {
            if (n < 0 || n > 92) {
                throw new IllegalArgumentException(
                    "n must be between 0 and 92."
                );
            }
        }
    }

    static class KnapsackService {

        public int fullTable(
            int[] weights,
            int[] values,
            int capacity
        ) {
            validate(weights, values, capacity);

            int[][] dp = new int[weights.length + 1][capacity + 1];

            for (int i = 1; i <= weights.length; i++) {
                int weight = weights[i - 1];
                int value = values[i - 1];

                for (int current = 0; current <= capacity; current++) {
                    dp[i][current] = dp[i - 1][current];

                    if (weight <= current) {
                        dp[i][current] = Math.max(
                            dp[i][current],
                            value + dp[i - 1][current - weight]
                        );
                    }
                }
            }

            return dp[weights.length][capacity];
        }

        public int optimized(
            int[] weights,
            int[] values,
            int capacity
        ) {
            validate(weights, values, capacity);

            int[] dp = new int[capacity + 1];

            for (int i = 0; i < weights.length; i++) {
                for (
                    int current = capacity;
                    current >= weights[i];
                    current--
                ) {
                    dp[current] = Math.max(
                        dp[current],
                        values[i] + dp[current - weights[i]]
                    );
                }
            }

            return dp[capacity];
        }

        private void validate(
            int[] weights,
            int[] values,
            int capacity
        ) {
            if (weights == null || values == null) {
                throw new IllegalArgumentException(
                    "Input arrays cannot be null."
                );
            }

            if (weights.length != values.length) {
                throw new IllegalArgumentException(
                    "Array lengths must match."
                );
            }

            if (capacity < 0 || capacity > 1_000_000) {
                throw new IllegalArgumentException(
                    "Invalid capacity."
                );
            }

            for (int weight : weights) {
                if (weight <= 0) {
                    throw new IllegalArgumentException(
                        "Weights must be positive."
                    );
                }
            }

            for (int value : values) {
                if (value < 0) {
                    throw new IllegalArgumentException(
                        "Values cannot be negative."
                    );
                }
            }
        }
    }

    static class MemoryAnalyzer {

        public long estimateLinear(
            long elements,
            long bytesPerElement
        ) {
            if (elements < 0 || bytesPerElement < 0) {
                throw new IllegalArgumentException(
                    "Memory parameters cannot be negative."
                );
            }

            return Math.multiplyExact(
                elements,
                bytesPerElement
            );
        }

        public long estimateMatrix(
            long rows,
            long columns,
            long bytesPerElement
        ) {
            if (rows < 0 || columns < 0 || bytesPerElement < 0) {
                throw new IllegalArgumentException(
                    "Matrix dimensions cannot be negative."
                );
            }

            return Math.multiplyExact(
                Math.multiplyExact(rows, columns),
                bytesPerElement
            );
        }

        public List<MemoryReport> generateReports(int n) {
            if (n < 0 || n > 1_000_000) {
                throw new IllegalArgumentException(
                    "Input size is outside the permitted range."
                );
            }

            long linear = estimateLinear(n, Integer.BYTES);
            long quadratic = estimateMatrix(
                n, n, Integer.BYTES
            );

            return List.of(
                new MemoryReport(
                    "Constant-space aggregation",
                    n,
                    Long.BYTES,
                    Complexity.CONSTANT,
                    "One accumulator."
                ),
                new MemoryReport(
                    "Integer array copy",
                    n,
                    linear,
                    Complexity.LINEAR,
                    "One additional integer array."
                ),
                new MemoryReport(
                    "Two-dimensional matrix",
                    n,
                    quadratic,
                    Complexity.QUADRATIC,
                    "n by n integer storage, excluding array headers."
                ),
                new MemoryReport(
                    "Binary search recursion",
                    n,
                    n == 0 ? 0 :
                        64L * (64 - Long.numberOfLeadingZeros(n)),
                    Complexity.LOGARITHMIC,
                    "Approximate stack consumption."
                )
            );
        }
    }

    static class StreamingService {

        public long countUnique(Iterable<Integer> source) {
            if (source == null) {
                throw new IllegalArgumentException(
                    "Source cannot be null."
                );
            }

            Set<Integer> unique = new HashSet<>();

            for (Integer value : source) {
                if (value == null) {
                    throw new IllegalArgumentException(
                        "Null elements are not accepted."
                    );
                }

                unique.add(value);
            }

            return unique.size();
        }

        public long sumStreaming(Iterable<Integer> source) {
            if (source == null) {
                throw new IllegalArgumentException(
                    "Source cannot be null."
                );
            }

            long total = 0;

            for (Integer value : source) {
                if (value == null) {
                    throw new IllegalArgumentException(
                        "Null elements are not accepted."
                    );
                }

                total = Math.addExact(total, value);
            }

            return total;
        }
    }

    private static void runTests() {
        AlgorithmService algorithms = new AlgorithmService();
        KnapsackService knapsack = new KnapsackService();
        MemoryAnalyzer analyzer = new MemoryAnalyzer();

        int[] input = {1, 2, 3, 4};

        if (algorithms.sumConstantSpace(input) != 10) {
            throw new AssertionError("Sum test failed.");
        }

        int[] copy = algorithms.copyData(input);

        if (copy == input || !Arrays.equals(copy, input)) {
            throw new AssertionError("Copy test failed.");
        }

        algorithms.reverseInPlace(copy);

        if (!Arrays.equals(copy, new int[]{4, 3, 2, 1})) {
            throw new AssertionError("Reverse test failed.");
        }

        int[] sorted = {1, 3, 5, 7, 9};

        if (algorithms.binarySearchIterative(sorted, 7) != 3) {
            throw new AssertionError("Iterative search failed.");
        }

        if (algorithms.binarySearchRecursive(
                sorted, 5, 0, sorted.length - 1
            ) != 2) {
            throw new AssertionError("Recursive search failed.");
        }

        if (!algorithms.uniqueValues(
                new int[]{1, 1, 2, 3}
            ).equals(List.of(1, 2, 3))) {
            throw new AssertionError("Unique-value test failed.");
        }

        if (algorithms.fibonacciFullTable(10) != 55 ||
            algorithms.fibonacciOptimized(10) != 55) {
            throw new AssertionError("Fibonacci test failed.");
        }

        int[] weights = {2, 3, 4, 5};
        int[] values = {3, 4, 5, 6};

        if (knapsack.fullTable(weights, values, 5) != 7 ||
            knapsack.optimized(weights, values, 5) != 7) {
            throw new AssertionError("Knapsack test failed.");
        }

        if (analyzer.estimateMatrix(10, 10, 4) != 400) {
            throw new AssertionError("Memory estimate failed.");
        }

        MemoryPolicy policy = new MemoryPolicy(1024);
        policy.enforce(512);

        boolean rejected = false;

        try {
            policy.enforce(2048);
        } catch (MemoryBudgetException exception) {
            rejected = true;
        }

        if (!rejected) {
            throw new AssertionError("Memory policy test failed.");
        }

        System.out.println("All Java 17 tests passed.");
    }

    public static void main(String[] args) {
        try {
            System.out.println("SPACE COMPLEXITY MANAGEMENT");
            System.out.println("===========================");

            runTests();

            AlgorithmService algorithms = new AlgorithmService();
            KnapsackService knapsack = new KnapsackService();
            MemoryAnalyzer analyzer = new MemoryAnalyzer();
            StreamingService streaming = new StreamingService();

            System.out.println("\nMEMORY ANALYSIS");

            for (MemoryReport report :
                analyzer.generateReports(1000)) {
                report.display();
            }

            System.out.println("\nALGORITHM COMPARISON");

            System.out.println(
                "Full-table Fibonacci: " +
                algorithms.fibonacciFullTable(30)
            );

            System.out.println(
                "Optimized Fibonacci: " +
                algorithms.fibonacciOptimized(30)
            );

            int[] weights = {2, 3, 4, 5};
            int[] values = {3, 4, 5, 6};

            System.out.println(
                "Full-table knapsack: " +
                knapsack.fullTable(weights, values, 5)
            );

            System.out.println(
                "Optimized knapsack: " +
                knapsack.optimized(weights, values, 5)
            );

            System.out.println("\nSTREAMING OPERATIONS");

            List<Integer> data = Arrays.asList(
                1, 2, 2, 3, 4, 4, 5
            );

            System.out.println(
                "Unique count: " +
                streaming.countUnique(data)
            );

            System.out.println(
                "Streaming sum: " +
                streaming.sumStreaming(data)
            );

            System.out.println("\nRUNTIME MEMORY INFORMATION");

            Runtime runtime = Runtime.getRuntime();

            System.out.println(
                "Used heap bytes: " +
                (runtime.totalMemory() - runtime.freeMemory())
            );

            System.out.println(
                "Maximum heap bytes: " +
                runtime.maxMemory()
            );

            System.out.println(
                "Estimated linear allocation for 100,000 integers: " +
                analyzer.estimateLinear(100000, Integer.BYTES)
            );

            System.out.println("\nPROCESS COMPLETE");

        } catch (Exception exception) {
            System.err.println(
                "Execution failed: " + exception.getMessage()
            );

            System.exit(1);
        }
    }
}
