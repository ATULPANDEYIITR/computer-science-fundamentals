import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicLong;
import java.util.function.LongUnaryOperator;

/*
 * Time Complexity and Enterprise Performance Governance.
 *
 * Java 17 implementation covering:
 * - Asymptotic bounds.
 * - Algorithm complexity metadata.
 * - Performance budgets.
 * - Workload execution.
 * - Search and sorting services.
 * - Enterprise policy evaluation.
 * - Validation and failure states.
 */

public class Main {

    enum ComplexityClass {
        CONSTANT("O(1)"),
        LOGARITHMIC("O(log n)"),
        LINEAR("O(n)"),
        LINEARITHMIC("O(n log n)"),
        QUADRATIC("O(n^2)"),
        CUBIC("O(n^3)"),
        EXPONENTIAL("O(2^n)");

        private final String notation;

        ComplexityClass(String notation) {
            this.notation = notation;
        }

        public String notation() {
            return notation;
        }
    }

    enum ExecutionStatus {
        ACCEPTED,
        REJECTED,
        FAILED
    }

    record ComplexityDefinition(
        String name,
        String bigO,
        String bigOmega,
        String bigTheta,
        String explanation
    ) {}

    record AlgorithmProfile(
        String algorithmName,
        ComplexityClass complexity,
        boolean stable,
        String spaceComplexity
    ) {}

    record Workload(
        String workloadId,
        String algorithmName,
        long inputSize,
        long operationCount
    ) {
        Workload {
            if (workloadId == null || workloadId.isBlank()) {
                throw new IllegalArgumentException("Workload ID is required.");
            }

            if (algorithmName == null || algorithmName.isBlank()) {
                throw new IllegalArgumentException("Algorithm name is required.");
            }

            if (inputSize < 0 || operationCount < 0) {
                throw new IllegalArgumentException("Negative workload values are invalid.");
            }
        }
    }

    record PerformancePolicy(
        long maximumInputSize,
        long maximumOperations,
        Set<ComplexityClass> permittedComplexities
    ) {
        PerformancePolicy {
            if (maximumInputSize < 0 || maximumOperations < 0) {
                throw new IllegalArgumentException("Performance limits cannot be negative.");
            }

            permittedComplexities = Set.copyOf(permittedComplexities);
        }
    }

    record EvaluationResult(
        String workloadId,
        ExecutionStatus status,
        String reason
    ) {}

    record SearchResult(
        int index,
        long comparisons,
        ComplexityClass complexity
    ) {}

    record SortResult(
        List<Integer> sortedValues,
        long comparisons,
        long moves
    ) {
        SortResult {
            sortedValues = List.copyOf(sortedValues);
        }
    }

    static class ComplexityViolationException extends RuntimeException {
        ComplexityViolationException(String message) {
            super(message);
        }
    }

    static class ComplexityAnalyzer {

        static void validateInput(long n) {
            if (n < 0 || n > 100_000) {
                throw new IllegalArgumentException(
                    "Input size must be between 0 and 100000."
                );
            }
        }

        static long constant(long n) {
            validateInput(n);
            return 1;
        }

        static long linear(long n) {
            validateInput(n);
            return n;
        }

        static long logarithmic(long n) {
            validateInput(n);

            long count = 0;

            while (n > 1) {
                n /= 2;
                count++;
            }

            return count;
        }

        static long quadratic(long n) {
            validateInput(n);
            return Math.multiplyExact(n, n);
        }

        static long triangular(long n) {
            validateInput(n);
            return Math.multiplyExact(n, n + 1) / 2;
        }

        static long linearithmic(long n) {
            validateInput(n);

            if (n <= 1) return n;

            long levels = 0;
            long width = 1;

            while (width < n) {
                width *= 2;
                levels++;
            }

            return Math.multiplyExact(n, levels);
        }

        static Map<String, Double> growthFunctions(long n) {
            validateInput(n);

            double value = n;
            double log = n > 0 ? Math.log(n) / Math.log(2) : 0;

            Map<String, Double> result = new LinkedHashMap<>();

            result.put("1", 1.0);
            result.put("log2(n)", log);
            result.put("n", value);
            result.put("n log2(n)", value * log);
            result.put("n^2", value * value);
            result.put("n^3", value * value * value);

            return Collections.unmodifiableMap(result);
        }

        static List<ComplexityDefinition> catalog() {
            return List.of(
                new ComplexityDefinition(
                    "Constant", "O(1)", "Ω(1)", "Θ(1)",
                    "Fixed amount of work."
                ),
                new ComplexityDefinition(
                    "Logarithmic", "O(log n)", "Ω(log n)", "Θ(log n)",
                    "Repeated reduction of the problem size."
                ),
                new ComplexityDefinition(
                    "Linear", "O(n)", "Ω(n)", "Θ(n)",
                    "One operation per input element."
                ),
                new ComplexityDefinition(
                    "Linearithmic", "O(n log n)", "Ω(n log n)", "Θ(n log n)",
                    "Efficient comparison sorting."
                ),
                new ComplexityDefinition(
                    "Quadratic", "O(n^2)", "Ω(n^2)", "Θ(n^2)",
                    "Two nested traversals."
                ),
                new ComplexityDefinition(
                    "Cubic", "O(n^3)", "Ω(n^3)", "Θ(n^3)",
                    "Three nested traversals."
                ),
                new ComplexityDefinition(
                    "Exponential", "O(2^n)", "Ω(2^n)", "Θ(2^n)",
                    "Exponential branching."
                )
            );
        }
    }

    static class AlgorithmService {

        SearchResult linearSearch(List<Integer> values, int target) {
            long comparisons = 0;

            for (int i = 0; i < values.size(); i++) {
                comparisons++;

                if (values.get(i) == target) {
                    return new SearchResult(
                        i, comparisons, ComplexityClass.LINEAR
                    );
                }
            }

            return new SearchResult(
                -1, comparisons, ComplexityClass.LINEAR
            );
        }

        SearchResult binarySearch(List<Integer> values, int target) {
            for (int i = 1; i < values.size(); i++) {
                if (values.get(i - 1) > values.get(i)) {
                    throw new IllegalArgumentException(
                        "Binary search requires sorted input."
                    );
                }
            }

            int left = 0;
            int right = values.size() - 1;
            long comparisons = 0;

            while (left <= right) {
                int middle = left + (right - left) / 2;
                comparisons++;

                int current = values.get(middle);

                if (current == target) {
                    return new SearchResult(
                        middle, comparisons, ComplexityClass.LOGARITHMIC
                    );
                }

                if (current < target) {
                    left = middle + 1;
                } else {
                    right = middle - 1;
                }
            }

            return new SearchResult(
                -1, comparisons, ComplexityClass.LOGARITHMIC
            );
        }

        SortResult mergeSort(List<Integer> input) {
            AtomicLong comparisons = new AtomicLong();
            AtomicLong moves = new AtomicLong();

            List<Integer> sorted = sort(
                new ArrayList<>(input),
                comparisons,
                moves
            );

            return new SortResult(
                sorted,
                comparisons.get(),
                moves.get()
            );
        }

        private List<Integer> sort(
            List<Integer> values,
            AtomicLong comparisons,
            AtomicLong moves
        ) {
            if (values.size() <= 1) return values;

            int middle = values.size() / 2;

            List<Integer> left = sort(
                new ArrayList<>(values.subList(0, middle)),
                comparisons,
                moves
            );

            List<Integer> right = sort(
                new ArrayList<>(values.subList(middle, values.size())),
                comparisons,
                moves
            );

            List<Integer> result = new ArrayList<>(values.size());

            int i = 0;
            int j = 0;

            while (i < left.size() && j < right.size()) {
                comparisons.incrementAndGet();

                if (left.get(i) <= right.get(j)) {
                    result.add(left.get(i++));
                } else {
                    result.add(right.get(j++));
                }

                moves.incrementAndGet();
            }

            while (i < left.size()) {
                result.add(left.get(i++));
                moves.incrementAndGet();
            }

            while (j < right.size()) {
                result.add(right.get(j++));
                moves.incrementAndGet();
            }

            return result;
        }
    }

    static class GovernanceService {

        private final PerformancePolicy policy;
        private final Map<String, Workload> registeredWorkloads =
            new ConcurrentHashMap<>();

        GovernanceService(PerformancePolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        EvaluationResult evaluate(
            Workload workload,
            ComplexityClass complexity
        ) {
            Objects.requireNonNull(workload);
            Objects.requireNonNull(complexity);

            Workload previous = registeredWorkloads.putIfAbsent(
                workload.workloadId(),
                workload
            );

            if (previous != null) {
                return new EvaluationResult(
                    workload.workloadId(),
                    ExecutionStatus.REJECTED,
                    "Duplicate workload identifier."
                );
            }

            if (workload.inputSize() > policy.maximumInputSize()) {
                return new EvaluationResult(
                    workload.workloadId(),
                    ExecutionStatus.REJECTED,
                    "Input exceeds policy limit."
                );
            }

            if (workload.operationCount() > policy.maximumOperations()) {
                return new EvaluationResult(
                    workload.workloadId(),
                    ExecutionStatus.REJECTED,
                    "Operation count exceeds policy limit."
                );
            }

            if (!policy.permittedComplexities().contains(complexity)) {
                return new EvaluationResult(
                    workload.workloadId(),
                    ExecutionStatus.REJECTED,
                    "Complexity class is not permitted."
                );
            }

            return new EvaluationResult(
                workload.workloadId(),
                ExecutionStatus.ACCEPTED,
                "Workload satisfies performance policy."
            );
        }

        int registeredCount() {
            return registeredWorkloads.size();
        }
    }

    static class AsyncWorkloadService {

        private final ExecutorService executor;

        AsyncWorkloadService(int parallelism) {
            if (parallelism <= 0 || parallelism > 8) {
                throw new IllegalArgumentException(
                    "Parallelism must be between 1 and 8."
                );
            }

            executor = Executors.newFixedThreadPool(parallelism);
        }

        CompletableFuture<Long> execute(
            LongUnaryOperator operation,
            long input
        ) {
            return CompletableFuture.supplyAsync(
                () -> operation.applyAsLong(input),
                executor
            );
        }

        void shutdown() {
            executor.shutdown();
        }
    }

    private static void demonstrateCatalog() {
        System.out.println("\nASYMPTOTIC COMPLEXITY DEFINITIONS");

        for (ComplexityDefinition definition :
             ComplexityAnalyzer.catalog()) {

            System.out.printf(
                "%-15s Big-O=%-15s Big-Omega=%-15s Big-Theta=%-15s%n",
                definition.name(),
                definition.bigO(),
                definition.bigOmega(),
                definition.bigTheta()
            );
        }
    }

    private static void demonstrateGrowth() {
        System.out.println("\nGROWTH FUNCTIONS");

        for (long n : List.of(10L, 100L, 1000L)) {
            System.out.println("n = " + n);

            ComplexityAnalyzer.growthFunctions(n).forEach(
                (name, value) ->
                    System.out.printf("  %-15s %.2f%n", name, value)
            );
        }
    }

    private static void demonstrateAlgorithms() {
        AlgorithmService service = new AlgorithmService();

        List<Integer> values = new ArrayList<>();

        for (int i = 0; i < 1000; i++) {
            values.add(i * 2);
        }

        System.out.println("\nSEARCH");

        System.out.println(
            "Linear: " + service.linearSearch(values, 800)
        );

        System.out.println(
            "Binary: " + service.binarySearch(values, 800)
        );

        List<Integer> input = List.of(45, 12, 89, 3, 22, 67, 1, 9);

        System.out.println("\nMERGE SORT");

        System.out.println(service.mergeSort(input));
    }

    private static void demonstrateGovernance() {
        System.out.println("\nENTERPRISE PERFORMANCE GOVERNANCE");

        PerformancePolicy policy = new PerformancePolicy(
            100_000,
            1_000_000,
            Set.of(
                ComplexityClass.CONSTANT,
                ComplexityClass.LOGARITHMIC,
                ComplexityClass.LINEAR,
                ComplexityClass.LINEARITHMIC
            )
        );

        GovernanceService governance = new GovernanceService(policy);

        Workload acceptable = new Workload(
            "JOB-001", "BinarySearch", 1000, 10
        );

        Workload expensive = new Workload(
            "JOB-002", "NestedLoop", 5000, 25_000_000
        );

        Workload quadratic = new Workload(
            "JOB-003", "QuadraticProcessor", 500, 250_000
        );

        System.out.println(
            governance.evaluate(acceptable, ComplexityClass.LOGARITHMIC)
        );

        System.out.println(
            governance.evaluate(expensive, ComplexityClass.QUADRATIC)
        );

        System.out.println(
            governance.evaluate(quadratic, ComplexityClass.QUADRATIC)
        );

        System.out.println(
            "Registered workloads: " + governance.registeredCount()
        );
    }

    private static void demonstrateAsyncExecution() {
        System.out.println("\nASYNCHRONOUS WORKLOAD EXECUTION");

        AsyncWorkloadService service = new AsyncWorkloadService(2);

        try {
            CompletableFuture<Long> linear =
                service.execute(ComplexityAnalyzer::linear, 1000);

            CompletableFuture<Long> quadratic =
                service.execute(ComplexityAnalyzer::quadratic, 1000);

            CompletableFuture.allOf(linear, quadratic).join();

            System.out.println("Linear operations: " + linear.join());
            System.out.println("Quadratic operations: " + quadratic.join());
        } finally {
            service.shutdown();
        }
    }

    private static void demonstrateValidation() {
        System.out.println("\nVALIDATION");

        if (ComplexityAnalyzer.triangular(5) != 15) {
            throw new IllegalStateException("Triangular count failed.");
        }

        if (ComplexityAnalyzer.logarithmic(1) != 0) {
            throw new IllegalStateException("Logarithmic boundary failed.");
        }

        if (ComplexityAnalyzer.linear(0) != 0) {
            throw new IllegalStateException("Empty input failed.");
        }

        try {
            ComplexityAnalyzer.linear(-5);
        } catch (IllegalArgumentException exception) {
            System.out.println("Expected error: " + exception.getMessage());
        }

        try {
            new AlgorithmService().binarySearch(
                List.of(8, 2, 4),
                2
            );
        } catch (IllegalArgumentException exception) {
            System.out.println("Expected error: " + exception.getMessage());
        }

        System.out.println("Validation tests passed.");
    }

    public static void main(String[] args) {
        try {
            System.out.println(
                "TIME COMPLEXITY AND ENTERPRISE PERFORMANCE ANALYSIS"
            );

            demonstrateCatalog();
            demonstrateGrowth();
            demonstrateAlgorithms();
            demonstrateGovernance();
            demonstrateAsyncExecution();
            demonstrateValidation();

            System.out.println("\nEXECUTION COMPLETED");
        } catch (Exception exception) {
            System.err.println(
                "Execution failed: " + exception.getMessage()
            );

            System.exit(1);
        }
    }
}
