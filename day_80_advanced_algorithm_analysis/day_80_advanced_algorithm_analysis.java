import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Random;
import java.util.Set;
import java.util.TreeMap;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.IntUnaryOperator;
import java.util.stream.Collectors;

/*
 * Advanced Algorithm Analysis
 *
 * Java 17 enterprise-oriented implementation.
 *
 * Components:
 * - Disjoint Set Union with path compression and union by rank.
 * - Probabilistic two-choice request distribution.
 * - Randomized algorithm simulation.
 * - Concurrent experiment execution.
 * - Statistical reporting and validation.
 */

public class AdvancedAlgorithmAnalysis {

    enum ExperimentStatus {
        PENDING,
        RUNNING,
        COMPLETED,
        FAILED
    }

    record ExperimentConfig(
        String name,
        int repetitions,
        int inputSize,
        long seed
    ) {
        ExperimentConfig {
            Objects.requireNonNull(name, "Experiment name is required.");

            if (name.isBlank()) {
                throw new IllegalArgumentException(
                    "Experiment name cannot be blank."
                );
            }

            if (repetitions <= 0 || inputSize <= 0) {
                throw new IllegalArgumentException(
                    "Experiment dimensions must be positive."
                );
            }
        }
    }

    record ExperimentResult(
        String name,
        int repetitions,
        double observedMean,
        double theoreticalMean,
        double standardDeviation,
        double minimum,
        double maximum,
        ExperimentStatus status
    ) {}

    record ServerLoad(
        int serverId,
        int assignedRequests
    ) {}

    static class ExperimentException extends RuntimeException {
        ExperimentException(String message) {
            super(message);
        }

        ExperimentException(String message, Throwable cause) {
            super(message, cause);
        }
    }

    /*
     * Disjoint Set Union.
     *
     * Operations:
     * - find: path compression.
     * - union: union by rank.
     *
     * With both optimizations, amortized complexity per
     * operation is O(alpha(n)), where alpha is the
     * inverse Ackermann function.
     */

    static final class DisjointSetUnion {

        private final int[] parent;
        private final int[] rank;
        private int components;

        DisjointSetUnion(int size) {
            if (size <= 0) {
                throw new IllegalArgumentException(
                    "DSU size must be positive."
                );
            }

            parent = new int[size];
            rank = new int[size];
            components = size;

            for (int i = 0; i < size; i++) {
                parent[i] = i;
            }
        }

        public int find(int element) {
            validateElement(element);

            if (parent[element] != element) {
                parent[element] = find(parent[element]);
            }

            return parent[element];
        }

        public boolean union(int first, int second) {
            int rootFirst = find(first);
            int rootSecond = find(second);

            if (rootFirst == rootSecond) {
                return false;
            }

            if (rank[rootFirst] < rank[rootSecond]) {
                parent[rootFirst] = rootSecond;
            } else if (rank[rootFirst] > rank[rootSecond]) {
                parent[rootSecond] = rootFirst;
            } else {
                parent[rootSecond] = rootFirst;
                rank[rootFirst]++;
            }

            components--;
            return true;
        }

        public boolean connected(int first, int second) {
            return find(first) == find(second);
        }

        public int componentCount() {
            return components;
        }

        private void validateElement(int element) {
            if (element < 0 || element >= parent.length) {
                throw new IndexOutOfBoundsException(
                    "Invalid DSU element: " + element
                );
            }
        }
    }

    /*
     * Enterprise request distribution model.
     *
     * The service selects two randomly sampled servers
     * and assigns each request to the less-loaded server.
     *
     * This models the power-of-two-choices strategy.
     */

    static final class LoadBalancer {

        private final int serverCount;
        private final int[] loads;
        private final Random random;

        LoadBalancer(int serverCount, long seed) {
            if (serverCount <= 0) {
                throw new IllegalArgumentException(
                    "Server count must be positive."
                );
            }

            this.serverCount = serverCount;
            this.loads = new int[serverCount];
            this.random = new Random(seed);
        }

        public void assignRequests(int requestCount) {
            if (requestCount < 0) {
                throw new IllegalArgumentException(
                    "Request count cannot be negative."
                );
            }

            for (int i = 0; i < requestCount; i++) {
                int first = random.nextInt(serverCount);
                int second = random.nextInt(serverCount);

                int selected = loads[first] <= loads[second]
                    ? first
                    : second;

                loads[selected]++;
            }
        }

        public List<ServerLoad> getServerLoads() {
            List<ServerLoad> result = new ArrayList<>();

            for (int i = 0; i < serverCount; i++) {
                result.add(new ServerLoad(i, loads[i]));
            }

            return List.copyOf(result);
        }

        public int maximumLoad() {
            return Arrays.stream(loads).max().orElse(0);
        }

        public int minimumLoad() {
            return Arrays.stream(loads).min().orElse(0);
        }

        public double averageLoad() {
            return Arrays.stream(loads).average().orElse(0.0);
        }

        public int loadSpread() {
            return maximumLoad() - minimumLoad();
        }
    }

    /*
     * Randomized quicksort with deterministic seeding.
     *
     * Expected comparisons:
     * 2(n + 1)H(n) - 4n for distinct elements.
     */

    static final class RandomizedSorter {

        private final Random random;
        private long comparisons;
        private long swaps;

        RandomizedSorter(long seed) {
            random = new Random(seed);
        }

        public int[] sort(int[] input) {
            int[] result = input.clone();

            comparisons = 0;
            swaps = 0;

            if (result.length > 1) {
                sortRange(result, 0, result.length - 1);
            }

            return result;
        }

        private void sortRange(int[] values, int low, int high) {
            while (low < high) {
                int pivot = partition(values, low, high);

                if (pivot - low < high - pivot) {
                    sortRange(values, low, pivot - 1);
                    low = pivot + 1;
                } else {
                    sortRange(values, pivot + 1, high);
                    high = pivot - 1;
                }
            }
        }

        private int partition(int[] values, int low, int high) {
            int pivotIndex = low + random.nextInt(high - low + 1);

            swap(values, pivotIndex, high);

            int pivot = values[high];
            int boundary = low - 1;

            for (int i = low; i < high; i++) {
                comparisons++;

                if (values[i] <= pivot) {
                    boundary++;
                    swap(values, boundary, i);
                }
            }

            swap(values, boundary + 1, high);

            return boundary + 1;
        }

        private void swap(int[] values, int first, int second) {
            if (first != second) {
                int temporary = values[first];
                values[first] = values[second];
                values[second] = temporary;
                swaps++;
            }
        }

        public long comparisons() {
            return comparisons;
        }

        public long swaps() {
            return swaps;
        }
    }

    static double harmonicNumber(int n) {
        if (n < 0) {
            throw new IllegalArgumentException(
                "Input cannot be negative."
            );
        }

        double result = 0.0;

        for (int i = 1; i <= n; i++) {
            result += 1.0 / i;
        }

        return result;
    }

    static double expectedQuickSortComparisons(int n) {
        if (n < 0) {
            throw new IllegalArgumentException(
                "Input cannot be negative."
            );
        }

        if (n <= 1) return 0.0;

        return 2.0 * (n + 1) * harmonicNumber(n) - 4.0 * n;
    }

    /*
     * Coupon collector experiment.
     *
     * Each trial measures the number of independent draws
     * needed to observe every coupon type.
     *
     * The expected value is n * H(n).
     */

    static double simulateCouponCollector(
        int couponTypes,
        Random random
    ) {
        if (couponTypes <= 0) {
            throw new IllegalArgumentException(
                "Coupon count must be positive."
            );
        }

        Set<Integer> collected = new HashSet<>();
        long draws = 0;

        while (collected.size() < couponTypes) {
            collected.add(random.nextInt(couponTypes));
            draws++;
        }

        return draws;
    }

    /*
     * Concurrent experiment execution.
     *
     * Each worker receives an independent deterministic
     * seed derived from the experiment seed.
     */

    static final class ExperimentService implements AutoCloseable {

        private final ExecutorService executor;

        ExperimentService(int workerCount) {
            if (workerCount <= 0) {
                throw new IllegalArgumentException(
                    "Worker count must be positive."
                );
            }

            executor = Executors.newFixedThreadPool(workerCount);
        }

        public CompletableFuture<ExperimentResult> execute(
            ExperimentConfig config
        ) {
            return CompletableFuture.supplyAsync(
                () -> executeSynchronously(config),
                executor
            );
        }

        private ExperimentResult executeSynchronously(
            ExperimentConfig config
        ) {
            AtomicInteger completed = new AtomicInteger();

            double[] observations = new double[config.repetitions()];

            for (int i = 0; i < config.repetitions(); i++) {
                long trialSeed = config.seed() + i * 7919L;

                Random random = new Random(trialSeed);

                observations[i] = simulateCouponCollector(
                    config.inputSize(),
                    random
                );

                completed.incrementAndGet();
            }

            double average = Arrays.stream(observations)
                .average()
                .orElseThrow();

            double variance = Arrays.stream(observations)
                .map(value -> Math.pow(value - average, 2))
                .average()
                .orElse(0.0);

            double minimum = Arrays.stream(observations)
                .min()
                .orElseThrow();

            double maximum = Arrays.stream(observations)
                .max()
                .orElseThrow();

            return new ExperimentResult(
                config.name(),
                completed.get(),
                average,
                config.inputSize()
                    * harmonicNumber(config.inputSize()),
                Math.sqrt(variance),
                minimum,
                maximum,
                ExperimentStatus.COMPLETED
            );
        }

        @Override
        public void close() {
            executor.shutdown();

            try {
                if (!executor.awaitTermination(30, TimeUnit.SECONDS)) {
                    executor.shutdownNow();
                }
            } catch (InterruptedException exception) {
                executor.shutdownNow();
                Thread.currentThread().interrupt();

                throw new ExperimentException(
                    "Experiment service interrupted.",
                    exception
                );
            }
        }
    }

    /*
     * A randomized hashing experiment using the built-in
     * HashMap. This measures observed lookup behavior rather
     * than claiming a deterministic worst-case guarantee.
     */

    static Map<Integer, Integer> buildFrequencyMap(int[] values) {
        Map<Integer, Integer> frequencies = new TreeMap<>();

        for (int value : values) {
            frequencies.merge(value, 1, Integer::sum);
        }

        return Map.copyOf(frequencies);
    }

    static void validateResults() {
        DisjointSetUnion dsu = new DisjointSetUnion(100);

        for (int i = 1; i < 100; i++) {
            dsu.union(i - 1, i);
        }

        if (dsu.componentCount() != 1) {
            throw new ExperimentException(
                "DSU component invariant failed."
            );
        }

        if (!dsu.connected(0, 99)) {
            throw new ExperimentException(
                "Connectivity validation failed."
            );
        }

        RandomizedSorter sorter = new RandomizedSorter(42);

        int[] sorted = sorter.sort(
            new int[]{9, 3, 7, 1, 5, 2, 8, 4, 6}
        );

        if (!Arrays.equals(
            sorted,
            new int[]{1, 2, 3, 4, 5, 6, 7, 8, 9}
        )) {
            throw new ExperimentException(
                "Sorting validation failed."
            );
        }

        if (expectedQuickSortComparisons(2) != 1.0) {
            throw new ExperimentException(
                "Expected comparison formula failed."
            );
        }

        int[] empty = sorter.sort(new int[]{});

        if (empty.length != 0) {
            throw new ExperimentException(
                "Empty input validation failed."
            );
        }

        System.out.println("All validation tests passed.");
    }

    static void displayLoadReport(LoadBalancer balancer) {
        System.out.println("Server allocation:");

        balancer.getServerLoads().stream()
            .sorted(
                Comparator.comparingInt(ServerLoad::assignedRequests)
                    .reversed()
            )
            .forEach(load -> System.out.printf(
                "Server %d: %d requests%n",
                load.serverId(),
                load.assignedRequests()
            ));

        System.out.printf(
            "Average load: %.2f%n",
            balancer.averageLoad()
        );

        System.out.printf(
            "Load spread: %d%n",
            balancer.loadSpread()
        );
    }

    public static void main(String[] args) {
        try {
            System.out.println("ADVANCED ALGORITHM ANALYSIS");

            /*
             * Amortized analysis: Disjoint Set Union.
             */

            System.out.println("\nDISJOINT SET UNION");

            DisjointSetUnion dsu = new DisjointSetUnion(10000);

            for (int i = 1; i < 10000; i++) {
                dsu.union(i - 1, i);
            }

            System.out.println(
                "Remaining components: " + dsu.componentCount()
            );

            System.out.println(
                "All vertices connected: " + dsu.connected(0, 9999)
            );

            /*
             * Randomized algorithm: sorting.
             */

            System.out.println("\nRANDOMIZED QUICKSORT");

            int[] input = new Random(2026)
                .ints(10000, 0, 100000)
                .toArray();

            RandomizedSorter sorter = new RandomizedSorter(12345);
            int[] sorted = sorter.sort(input);

            System.out.println(
                "Sorted successfully: " +
                Arrays.equals(
                    sorted,
                    Arrays.stream(input).sorted().toArray()
                )
            );

            System.out.println(
                "Comparisons: " + sorter.comparisons()
            );

            System.out.println(
                "Expected comparisons for distinct elements: " +
                expectedQuickSortComparisons(input.length)
            );

            /*
             * Probabilistic analysis: request distribution.
             */

            System.out.println("\nPROBABILISTIC LOAD BALANCING");

            LoadBalancer balancer = new LoadBalancer(50, 2026);
            balancer.assignRequests(10000);

            displayLoadReport(balancer);

            /*
             * Concurrent Monte Carlo experiments.
             */

            System.out.println("\nMONTE CARLO EXPERIMENT");

            try (ExperimentService service = new ExperimentService(4)) {

                ExperimentConfig config = new ExperimentConfig(
                    "Coupon Collector",
                    5000,
                    30,
                    2026
                );

                ExperimentResult result = service.execute(config).join();

                System.out.println(result);
            }

            System.out.println("\nFREQUENCY ANALYSIS");

            int[] sample = {
                10, 20, 10, 30, 20, 10, 40, 30, 20, 10
            };

            System.out.println(buildFrequencyMap(sample));

            System.out.println("\nVALIDATION");

            validateResults();

        } catch (Exception exception) {
            System.err.println(
                "Execution failed: " + exception.getMessage()
            );

            System.exit(1);
        }
    }
}
