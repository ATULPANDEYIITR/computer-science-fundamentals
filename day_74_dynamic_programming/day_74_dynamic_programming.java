import java.util.*;
import java.util.function.IntUnaryOperator;
import java.util.stream.Collectors;

/*
 * DYNAMIC PROGRAMMING: ENTERPRISE RESOURCE SCHEDULING
 *
 * Java 17 implementation.
 *
 * Concepts:
 * - Memoization
 * - Tabulation
 * - Optimal substructure
 * - Overlapping subproblems
 * - Weighted interval scheduling
 * - Resource allocation
 * - State transitions
 * - Immutable domain objects
 * - Enterprise validation
 *
 * Compile:
 * javac DynamicProgramming.java
 *
 * Run:
 * java DynamicProgramming
 */

public class DynamicProgramming {

    // ========================================================
    // 1. DOMAIN TYPES
    // ========================================================

    enum Algorithm {
        MEMOIZATION,
        TABULATION
    }

    enum TaskStatus {
        PROPOSED,
        APPROVED,
        REJECTED,
        SCHEDULED
    }

    record Project(
        String id,
        String name,
        int resourceCost,
        int expectedValue
    ) {

        Project {

            if (id == null || id.isBlank()) {
                throw new IllegalArgumentException("Project ID required.");
            }

            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("Project name required.");
            }

            if (resourceCost <= 0) {
                throw new IllegalArgumentException(
                    "Resource cost must be positive."
                );
            }

            if (expectedValue < 0) {
                throw new IllegalArgumentException(
                    "Expected value cannot be negative."
                );
            }
        }
    }

    record ScheduledTask(
        String id,
        int start,
        int end,
        int benefit,
        TaskStatus status
    ) {

        ScheduledTask {

            if (id == null || id.isBlank()) {
                throw new IllegalArgumentException("Task ID required.");
            }

            if (start < 0 || end <= start) {
                throw new IllegalArgumentException("Invalid task interval.");
            }

            if (benefit < 0) {
                throw new IllegalArgumentException("Benefit cannot be negative.");
            }

            Objects.requireNonNull(status, "Status is required.");
        }
    }

    record OptimizationResult(
        int maximumValue,
        int totalResourceCost,
        List<String> selectedProjects,
        Algorithm algorithm,
        long statesComputed
    ) {

        OptimizationResult {
            selectedProjects = List.copyOf(selectedProjects);
        }
    }

    record SchedulingResult(
        int totalBenefit,
        List<ScheduledTask> scheduledTasks
    ) {

        SchedulingResult {
            scheduledTasks = List.copyOf(scheduledTasks);
        }
    }

    // ========================================================
    // 2. CUSTOM EXCEPTIONS
    // ========================================================

    static class OptimizationException extends RuntimeException {

        OptimizationException(String message) {
            super(message);
        }
    }

    static class PolicyException extends RuntimeException {

        PolicyException(String message) {
            super(message);
        }
    }

    // ========================================================
    // 3. FIBONACCI SERVICE
    // ========================================================

    static final class FibonacciService {

        private final Map<Integer, Long> cache = new HashMap<>();

        FibonacciService() {
            cache.put(0, 0L);
            cache.put(1, 1L);
        }

        public long memoized(int n) {

            if (n < 0 || n > 92) {
                throw new IllegalArgumentException(
                    "Fibonacci index must be between 0 and 92."
                );
            }

            if (cache.containsKey(n)) {
                return cache.get(n);
            }

            long result =
                memoized(n - 1) + memoized(n - 2);

            cache.put(n, result);

            return result;
        }

        public long tabulated(int n) {

            if (n < 0 || n > 92) {
                throw new IllegalArgumentException("Invalid Fibonacci index.");
            }

            if (n <= 1) {
                return n;
            }

            long previous = 0;
            long current = 1;

            for (int i = 2; i <= n; i++) {

                long next = previous + current;

                previous = current;
                current = next;
            }

            return current;
        }
    }

    // ========================================================
    // 4. RESOURCE ALLOCATION POLICY
    // ========================================================

    record AllocationPolicy(
        int maximumBudget,
        int maximumProjects,
        boolean requirePositiveProjectValue
    ) {

        AllocationPolicy {

            if (maximumBudget < 0 || maximumBudget > 100000) {
                throw new IllegalArgumentException("Invalid maximum budget.");
            }

            if (maximumProjects <= 0 || maximumProjects > 500) {
                throw new IllegalArgumentException("Invalid project limit.");
            }
        }

        void validate(List<Project> projects, int budget) {

            if (budget < 0 || budget > maximumBudget) {
                throw new PolicyException("Budget violates allocation policy.");
            }

            if (projects.size() > maximumProjects) {
                throw new PolicyException("Project count exceeds policy.");
            }

            Set<String> ids = new HashSet<>();

            for (Project project : projects) {

                if (!ids.add(project.id())) {
                    throw new PolicyException(
                        "Duplicate project ID: " + project.id()
                    );
                }

                if (
                    requirePositiveProjectValue
                    && project.expectedValue() <= 0
                ) {
                    throw new PolicyException(
                        "Project value must be positive: " + project.id()
                    );
                }
            }
        }
    }

    // ========================================================
    // 5. KNAPSACK OPTIMIZATION SERVICE
    // ========================================================

    static final class ResourceAllocationService {

        private final AllocationPolicy policy;

        ResourceAllocationService(AllocationPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        OptimizationResult optimize(
            List<Project> projects,
            int budget,
            Algorithm algorithm
        ) {

            Objects.requireNonNull(projects);
            Objects.requireNonNull(algorithm);

            List<Project> input = List.copyOf(projects);

            policy.validate(input, budget);

            return switch (algorithm) {

                case MEMOIZATION ->
                    optimizeMemoized(input, budget);

                case TABULATION ->
                    optimizeTabulated(input, budget);
            };
        }

        private OptimizationResult optimizeMemoized(
            List<Project> projects,
            int budget
        ) {

            int n = projects.size();

            int[][] memo = new int[n + 1][budget + 1];
            boolean[][] computed = new boolean[n + 1][budget + 1];

            long[] states = {0};

            class Solver {

                int solve(int index, int remaining) {

                    if (index == n) {
                        return 0;
                    }

                    if (computed[index][remaining]) {
                        return memo[index][remaining];
                    }

                    computed[index][remaining] = true;
                    states[0]++;

                    Project project = projects.get(index);

                    int exclude = solve(index + 1, remaining);

                    int include = 0;

                    if (project.resourceCost() <= remaining) {

                        include =
                            project.expectedValue()
                            + solve(
                                index + 1,
                                remaining - project.resourceCost()
                            );
                    }

                    memo[index][remaining] =
                        Math.max(include, exclude);

                    return memo[index][remaining];
                }
            }

            Solver solver = new Solver();

            int maximumValue = solver.solve(0, budget);

            List<String> selected = new ArrayList<>();

            int remaining = budget;
            int totalCost = 0;

            for (int i = 0; i < n; i++) {

                Project project = projects.get(i);

                int exclude = solver.solve(i + 1, remaining);

                if (project.resourceCost() <= remaining) {

                    int include =
                        project.expectedValue()
                        + solver.solve(
                            i + 1,
                            remaining - project.resourceCost()
                        );

                    if (include > exclude) {

                        selected.add(project.id());
                        remaining -= project.resourceCost();
                        totalCost += project.resourceCost();
                    }
                }
            }

            return new OptimizationResult(
                maximumValue,
                totalCost,
                selected,
                Algorithm.MEMOIZATION,
                states[0]
            );
        }

        private OptimizationResult optimizeTabulated(
            List<Project> projects,
            int budget
        ) {

            int n = projects.size();

            int[][] dp = new int[n + 1][budget + 1];

            for (int i = 1; i <= n; i++) {

                Project project = projects.get(i - 1);

                for (int capacity = 0; capacity <= budget; capacity++) {

                    int exclude = dp[i - 1][capacity];
                    int include = 0;

                    if (project.resourceCost() <= capacity) {

                        include =
                            project.expectedValue()
                            + dp[
                                i - 1
                            ][
                                capacity - project.resourceCost()
                            ];
                    }

                    dp[i][capacity] = Math.max(include, exclude);
                }
            }

            List<String> selected = new ArrayList<>();

            int remaining = budget;
            int totalCost = 0;

            for (int i = n; i > 0; i--) {

                if (dp[i][remaining] != dp[i - 1][remaining]) {

                    Project project = projects.get(i - 1);

                    selected.add(project.id());

                    remaining -= project.resourceCost();
                    totalCost += project.resourceCost();
                }
            }

            Collections.reverse(selected);

            return new OptimizationResult(
                dp[n][budget],
                totalCost,
                selected,
                Algorithm.TABULATION,
                (long) (n + 1) * (budget + 1)
            );
        }
    }

    // ========================================================
    // 6. WEIGHTED INTERVAL SCHEDULING
    // ========================================================

    static final class TaskSchedulingService {

        SchedulingResult optimize(List<ScheduledTask> tasks) {

            Objects.requireNonNull(tasks);

            Set<String> identifiers = new HashSet<>();

            for (ScheduledTask task : tasks) {

                if (!identifiers.add(task.id())) {
                    throw new PolicyException(
                        "Duplicate task ID: " + task.id()
                    );
                }

                if (task.status() != TaskStatus.APPROVED) {
                    throw new PolicyException(
                        "Only approved tasks can be scheduled: " + task.id()
                    );
                }
            }

            List<ScheduledTask> sorted = tasks.stream()
                .sorted(
                    Comparator.comparingInt(ScheduledTask::end)
                        .thenComparingInt(ScheduledTask::start)
                        .thenComparing(ScheduledTask::id)
                )
                .toList();

            int n = sorted.size();

            int[] predecessor = new int[n];

            for (int i = 0; i < n; i++) {

                int low = 0;
                int high = i - 1;
                int answer = -1;

                while (low <= high) {

                    int middle = (low + high) >>> 1;

                    if (
                        sorted.get(middle).end()
                        <= sorted.get(i).start()
                    ) {

                        answer = middle;
                        low = middle + 1;

                    } else {

                        high = middle - 1;
                    }
                }

                predecessor[i] = answer;
            }

            int[] dp = new int[n + 1];

            for (int i = 1; i <= n; i++) {

                ScheduledTask task = sorted.get(i - 1);

                int include =
                    task.benefit()
                    + dp[predecessor[i - 1] + 1];

                int exclude = dp[i - 1];

                dp[i] = Math.max(include, exclude);
            }

            List<ScheduledTask> selected = new ArrayList<>();

            int i = n;

            while (i > 0) {

                ScheduledTask task = sorted.get(i - 1);

                int include =
                    task.benefit()
                    + dp[predecessor[i - 1] + 1];

                if (include > dp[i - 1]) {

                    selected.add(task);
                    i = predecessor[i - 1] + 1;

                } else {

                    i--;
                }
            }

            Collections.reverse(selected);

            return new SchedulingResult(
                dp[n],
                selected
            );
        }
    }

    // ========================================================
    // 7. TESTING
    // ========================================================

    static void runTests() {

        FibonacciService fibonacci = new FibonacciService();

        if (fibonacci.memoized(20) != 6765) {
            throw new AssertionError("Memoization failed.");
        }

        if (fibonacci.tabulated(20) != 6765) {
            throw new AssertionError("Tabulation failed.");
        }

        AllocationPolicy policy = new AllocationPolicy(
            1000,
            100,
            true
        );

        ResourceAllocationService service =
            new ResourceAllocationService(policy);

        List<Project> projects = List.of(
            new Project("P1", "Infrastructure", 4, 70),
            new Project("P2", "Security", 3, 60),
            new Project("P3", "Monitoring", 2, 40),
            new Project("P4", "Backup", 5, 90)
        );

        OptimizationResult memo = service.optimize(
            projects,
            7,
            Algorithm.MEMOIZATION
        );

        OptimizationResult table = service.optimize(
            projects,
            7,
            Algorithm.TABULATION
        );

        if (memo.maximumValue() != 130) {
            throw new AssertionError("Unexpected knapsack result.");
        }

        if (memo.maximumValue() != table.maximumValue()) {
            throw new AssertionError("Algorithms disagree.");
        }

        if (memo.totalResourceCost() > 7) {
            throw new AssertionError("Budget exceeded.");
        }

        List<ScheduledTask> tasks = List.of(
            new ScheduledTask("T1", 1, 3, 50, TaskStatus.APPROVED),
            new ScheduledTask("T2", 3, 5, 60, TaskStatus.APPROVED),
            new ScheduledTask("T3", 2, 6, 80, TaskStatus.APPROVED),
            new ScheduledTask("T4", 5, 7, 40, TaskStatus.APPROVED)
        );

        SchedulingResult schedule =
            new TaskSchedulingService().optimize(tasks);

        if (schedule.totalBenefit() != 150) {
            throw new AssertionError("Scheduling test failed.");
        }

        try {

            new TaskSchedulingService().optimize(
                List.of(
                    new ScheduledTask(
                        "T5", 1, 2, 100, TaskStatus.PROPOSED
                    )
                )
            );

            throw new AssertionError("Policy failure was not detected.");

        } catch (PolicyException expected) {
            // Expected validation failure.
        }

        System.out.println("All Java 17 tests passed.");
    }

    // ========================================================
    // 8. EXECUTABLE APPLICATION
    // ========================================================

    public static void main(String[] args) {

        try {

            System.out.println("\nENTERPRISE DYNAMIC PROGRAMMING");
            System.out.println("==============================");

            // Fibonacci.
            System.out.println("\n1. Fibonacci");

            FibonacciService fibonacci = new FibonacciService();

            System.out.println(
                "Memoization: " + fibonacci.memoized(40)
            );

            System.out.println(
                "Tabulation: " + fibonacci.tabulated(40)
            );

            // Resource allocation.
            System.out.println("\n2. Enterprise Resource Allocation");

            List<Project> projects = List.of(
                new Project("P001", "Infrastructure", 5, 100),
                new Project("P002", "Security", 3, 80),
                new Project("P003", "Monitoring", 2, 50),
                new Project("P004", "Backup", 6, 120),
                new Project("P005", "Automation", 2, 40)
            );

            AllocationPolicy policy = new AllocationPolicy(
                100,
                100,
                true
            );

            ResourceAllocationService allocationService =
                new ResourceAllocationService(policy);

            OptimizationResult memo = allocationService.optimize(
                projects,
                10,
                Algorithm.MEMOIZATION
            );

            OptimizationResult table = allocationService.optimize(
                projects,
                10,
                Algorithm.TABULATION
            );

            System.out.println("Memoized value: " + memo.maximumValue());
            System.out.println("Tabulated value: " + table.maximumValue());

            System.out.println(
                "Selected projects: " + table.selectedProjects()
            );

            System.out.println(
                "Resource usage: " + table.totalResourceCost()
            );

            // Scheduling.
            System.out.println("\n3. Enterprise Task Scheduling");

            List<ScheduledTask> tasks = List.of(
                new ScheduledTask(
                    "DEV", 1, 4, 100, TaskStatus.APPROVED
                ),
                new ScheduledTask(
                    "TEST", 4, 6, 80, TaskStatus.APPROVED
                ),
                new ScheduledTask(
                    "DEPLOY", 6, 8, 120, TaskStatus.APPROVED
                ),
                new ScheduledTask(
                    "RESEARCH", 2, 7, 150, TaskStatus.APPROVED
                )
            );

            SchedulingResult result =
                new TaskSchedulingService().optimize(tasks);

            System.out.println("Maximum benefit: " + result.totalBenefit());

            System.out.println(
                "Scheduled tasks: "
                + result.scheduledTasks().stream()
                    .map(ScheduledTask::id)
                    .collect(Collectors.toList())
            );

            // Tests.
            System.out.println("\n4. Validation");
            runTests();

        } catch (RuntimeException error) {

            System.err.println(
                "Application failure: " + error.getMessage()
            );

            System.exit(1);
        }
    }
}
