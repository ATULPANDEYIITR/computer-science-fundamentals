import java.util.*;
import java.util.concurrent.atomic.AtomicLong;
import java.util.function.Predicate;
import java.util.stream.Collectors;

/**
 * Algorithm Fundamentals
 *
 * Enterprise batch-processing and algorithm verification system.
 * Requires Java 17.
 */
public class Main {

    enum ExecutionState {
        REGISTERED,
        READY,
        RUNNING,
        PASSED,
        FAILED
    }

    enum ComplexityClass {
        CONSTANT,
        LOGARITHMIC,
        LINEAR,
        LINEARITHMIC,
        QUADRATIC
    }

    record AlgorithmMetadata(
        String name,
        String category,
        String timeComplexity,
        String spaceComplexity
    ) {
        AlgorithmMetadata {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException(
                    "Algorithm name is required."
                );
            }

            Objects.requireNonNull(category);
            Objects.requireNonNull(timeComplexity);
            Objects.requireNonNull(spaceComplexity);
        }
    }

    record AlgorithmResult<T>(
        T output,
        long comparisons,
        long operations,
        long elapsedNanoseconds,
        ExecutionState state
    ) {}

    record TestCase(
        String name,
        List<Integer> input,
        List<Integer> expected
    ) {
        TestCase {
            Objects.requireNonNull(name);
            input = List.copyOf(input);
            expected = List.copyOf(expected);
        }
    }

    static class AlgorithmException extends RuntimeException {
        AlgorithmException(String message) {
            super(message);
        }
    }

    interface SortingAlgorithm {
        List<Integer> sort(List<Integer> input);

        AlgorithmMetadata metadata();
    }

    static final class MergeSort implements SortingAlgorithm {

        @Override
        public List<Integer> sort(List<Integer> input) {
            Objects.requireNonNull(input);

            if (input.size() <= 1) {
                return new ArrayList<>(input);
            }

            int middle = input.size() / 2;

            List<Integer> left = sort(
                input.subList(0, middle)
            );

            List<Integer> right = sort(
                input.subList(middle, input.size())
            );

            List<Integer> result = new ArrayList<>(
                input.size()
            );

            int i = 0;
            int j = 0;

            while (i < left.size() && j < right.size()) {
                if (left.get(i) <= right.get(j)) {
                    result.add(left.get(i++));
                } else {
                    result.add(right.get(j++));
                }
            }

            while (i < left.size()) {
                result.add(left.get(i++));
            }

            while (j < right.size()) {
                result.add(right.get(j++));
            }

            return result;
        }

        @Override
        public AlgorithmMetadata metadata() {
            return new AlgorithmMetadata(
                "Merge Sort",
                "Sorting",
                "O(n log n)",
                "O(n)"
            );
        }
    }

    static final class BinarySearch {

        static int find(List<Integer> values, int target) {
            Objects.requireNonNull(values);

            for (int i = 1; i < values.size(); i++) {
                if (values.get(i - 1) > values.get(i)) {
                    throw new IllegalArgumentException(
                        "Input must be sorted."
                    );
                }
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
    }

    static final class BatchJob {
        private final String id;
        private final int priority;
        private final long submissionOrder;

        BatchJob(
            String id,
            int priority,
            long submissionOrder
        ) {
            if (id == null || id.isBlank()) {
                throw new IllegalArgumentException(
                    "Job ID is required."
                );
            }

            if (priority < 1 || priority > 10) {
                throw new IllegalArgumentException(
                    "Priority must be between 1 and 10."
                );
            }

            this.id = id;
            this.priority = priority;
            this.submissionOrder = submissionOrder;
        }

        String id() {
            return id;
        }

        int priority() {
            return priority;
        }

        long submissionOrder() {
            return submissionOrder;
        }

        @Override
        public String toString() {
            return id + " (priority=" + priority + ")";
        }
    }

    static final class BatchScheduler {
        private final AtomicLong sequence = new AtomicLong();

        private final List<BatchJob> jobs = new ArrayList<>();

        void submit(String id, int priority) {
            jobs.add(
                new BatchJob(
                    id,
                    priority,
                    sequence.getAndIncrement()
                )
            );
        }

        List<BatchJob> schedule() {
            // Higher priority first. Submission order resolves ties.
            return jobs.stream()
                .sorted(
                    Comparator
                        .comparingInt(BatchJob::priority)
                        .reversed()
                        .thenComparingLong(
                            BatchJob::submissionOrder
                        )
                )
                .collect(Collectors.toUnmodifiableList());
        }

        List<BatchJob> snapshot() {
            return List.copyOf(jobs);
        }
    }

    static final class AlgorithmExecutionService {

        private final Map<String, ExecutionState> states =
            new HashMap<>();

        private final Map<String, AlgorithmMetadata> registry =
            new HashMap<>();

        void register(AlgorithmMetadata metadata) {
            if (registry.containsKey(metadata.name())) {
                throw new AlgorithmException(
                    "Algorithm already registered."
                );
            }

            registry.put(metadata.name(), metadata);
            states.put(
                metadata.name(),
                ExecutionState.REGISTERED
            );
        }

        <T> AlgorithmResult<T> execute(
            String algorithmName,
            java.util.function.Supplier<T> operation,
            Predicate<T> correctnessCheck
        ) {
            if (!registry.containsKey(algorithmName)) {
                throw new AlgorithmException(
                    "Unknown algorithm."
                );
            }

            ExecutionState current = states.get(algorithmName);

            if (current == ExecutionState.RUNNING) {
                throw new AlgorithmException(
                    "Algorithm is already running."
                );
            }

            states.put(
                algorithmName,
                ExecutionState.RUNNING
            );

            long start = System.nanoTime();

            try {
                T output = operation.get();

                long elapsed = System.nanoTime() - start;

                if (!correctnessCheck.test(output)) {
                    throw new AlgorithmException(
                        "Correctness verification failed."
                    );
                }

                states.put(
                    algorithmName,
                    ExecutionState.PASSED
                );

                return new AlgorithmResult<>(
                    output,
                    0,
                    0,
                    elapsed,
                    ExecutionState.PASSED
                );
            } catch (RuntimeException error) {
                states.put(
                    algorithmName,
                    ExecutionState.FAILED
                );

                throw error;
            }
        }

        ExecutionState getState(String name) {
            return states.get(name);
        }
    }

    static final class TestRunner {

        private int passed;
        private int failed;

        void execute(TestCase testCase, SortingAlgorithm algorithm) {
            try {
                List<Integer> actual = algorithm.sort(
                    testCase.input()
                );

                if (!actual.equals(testCase.expected())) {
                    throw new AlgorithmException(
                        "Expected " + testCase.expected() +
                        " but received " + actual
                    );
                }

                passed++;

                System.out.println(
                    "[PASS] " + testCase.name()
                );
            } catch (RuntimeException error) {
                failed++;

                System.out.println(
                    "[FAIL] " + testCase.name() +
                    ": " + error.getMessage()
                );
            }
        }

        void report() {
            System.out.println("\nCorrectness Report");
            System.out.println("Passed: " + passed);
            System.out.println("Failed: " + failed);
            System.out.println(
                "Success rate: " +
                (passed + failed == 0
                    ? 0
                    : 100.0 * passed / (passed + failed)) +
                "%"
            );

            if (failed > 0) {
                throw new AlgorithmException(
                    "One or more correctness tests failed."
                );
            }
        }
    }

    static void demonstrateAlgorithms() {
        MergeSort mergeSort = new MergeSort();

        AlgorithmExecutionService service =
            new AlgorithmExecutionService();

        service.register(mergeSort.metadata());

        List<TestCase> cases = List.of(
            new TestCase(
                "Unsorted batch",
                List.of(8, 3, 6, 1, 9),
                List.of(1, 3, 6, 8, 9)
            ),
            new TestCase(
                "Duplicate values",
                List.of(4, 4, 2, 2, 1),
                List.of(1, 2, 2, 4, 4)
            ),
            new TestCase(
                "Negative values",
                List.of(-8, 5, -2, 0),
                List.of(-8, -2, 0, 5)
            ),
            new TestCase(
                "Empty collection",
                List.of(),
                List.of()
            )
        );

        TestRunner runner = new TestRunner();

        for (TestCase testCase : cases) {
            runner.execute(testCase, mergeSort);
        }

        runner.report();

        List<Integer> values = List.of(
            3, 8, 12, 18, 25, 31, 44, 50
        );

        int position = BinarySearch.find(values, 25);

        System.out.println(
            "\nBinary search result: " + position
        );

        System.out.println(
            "Search complexity: O(log n)"
        );

        AlgorithmResult<List<Integer>> result =
            service.execute(
                "Merge Sort",
                () -> mergeSort.sort(
                    List.of(45, 12, 67, 2, 19, 5)
                ),
                output -> {
                    List<Integer> expected = new ArrayList<>(
                        List.of(45, 12, 67, 2, 19, 5)
                    );

                    Collections.sort(expected);

                    return output.equals(expected);
                }
            );

        System.out.println(
            "\nEnterprise batch result: " + result.output()
        );

        System.out.println(
            "Execution time: " +
            result.elapsedNanoseconds() + " ns"
        );

        System.out.println(
            "Execution state: " + result.state()
        );

        BatchScheduler scheduler = new BatchScheduler();

        scheduler.submit("JOB-101", 3);
        scheduler.submit("JOB-102", 9);
        scheduler.submit("JOB-103", 5);
        scheduler.submit("JOB-104", 9);
        scheduler.submit("JOB-105", 1);

        System.out.println("\nPriority-based batch scheduling");

        for (BatchJob job : scheduler.schedule()) {
            System.out.println(job);
        }

        System.out.println(
            "\nScheduling complexity: O(n log n)"
        );
    }

    public static void main(String[] args) {
        try {
            demonstrateAlgorithms();

            System.out.println(
                "\nAll enterprise algorithm operations completed."
            );
        } catch (Exception error) {
            System.err.println(
                "Execution failure: " + error.getMessage()
            );

            System.exit(1);
        }
    }
}
