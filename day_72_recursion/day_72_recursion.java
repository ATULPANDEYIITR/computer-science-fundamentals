import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.function.Function;
import java.util.stream.Collectors;

/**
 * Enterprise Recursive Computation and Dependency Management.
 *
 * Java 17.
 *
 * Features:
 * - Explicit recursive domain models
 * - Base-case validation
 * - Recursion budgets
 * - Memoized computation
 * - Divide-and-conquer sorting
 * - Recursive tree traversal
 * - Dependency resolution
 * - Cycle detection
 * - Execution state management
 * - Performance measurement
 * - Immutable result objects
 * - Automated assertions
 */
public class RecursionEnterprise {

    enum ComputationStatus {
        PENDING,
        RUNNING,
        COMPLETED,
        FAILED
    }

    enum TraversalOrder {
        PREORDER,
        INORDER,
        POSTORDER
    }

    static class RecursionException extends RuntimeException {
        RecursionException(String message) {
            super(message);
        }
    }

    static class ValidationException extends RecursionException {
        ValidationException(String message) {
            super(message);
        }
    }

    static class DepthLimitException extends RecursionException {
        DepthLimitException(String message) {
            super(message);
        }
    }

    static class DependencyCycleException extends RecursionException {
        DependencyCycleException(String message) {
            super(message);
        }
    }

    record RecursionMetrics(
        long calls,
        int maximumDepth,
        long cacheHits,
        long comparisons
    ) {}

    record ComputationResult(
        String name,
        long value,
        Duration elapsed,
        RecursionMetrics metrics,
        ComputationStatus status
    ) {}

    record DependencyTask(
        String name,
        List<String> dependencies
    ) {
        DependencyTask {
            if (name == null || name.isBlank()) {
                throw new ValidationException(
                    "Task name cannot be blank."
                );
            }

            dependencies = List.copyOf(
                Objects.requireNonNull(dependencies)
            );

            if (new HashSet<>(dependencies).size() != dependencies.size()) {
                throw new ValidationException(
                    "Duplicate dependencies are not permitted."
                );
            }
        }
    }

    static final class MetricsCollector {
        private long calls;
        private int maximumDepth;
        private long cacheHits;
        private long comparisons;

        void enter(int depth, int limit) {
            if (depth > limit) {
                throw new DepthLimitException(
                    "Recursion depth exceeds " + limit
                );
            }

            calls++;
            maximumDepth = Math.max(maximumDepth, depth);
        }

        void cacheHit() {
            cacheHits++;
        }

        void comparison() {
            comparisons++;
        }

        RecursionMetrics snapshot() {
            return new RecursionMetrics(
                calls,
                maximumDepth,
                cacheHits,
                comparisons
            );
        }
    }

    static final class RecursionContext {
        private final int maximumDepth;
        private final MetricsCollector metrics;

        RecursionContext(int maximumDepth) {
            if (maximumDepth < 1) {
                throw new ValidationException(
                    "Maximum depth must be positive."
                );
            }

            this.maximumDepth = maximumDepth;
            this.metrics = new MetricsCollector();
        }

        void enter(int depth) {
            metrics.enter(depth, maximumDepth);
        }

        MetricsCollector metrics() {
            return metrics;
        }

        RecursionMetrics snapshot() {
            return metrics.snapshot();
        }
    }

    static final class RecursiveAlgorithms {

        static long factorial(int n, RecursionContext context) {
            if (n < 0 || n > 20) {
                throw new ValidationException(
                    "Factorial input must be between 0 and 20."
                );
            }

            return factorialInternal(n, 0, context);
        }

        private static long factorialInternal(
            int n,
            int depth,
            RecursionContext context
        ) {
            context.enter(depth);

            if (n <= 1) {
                return 1;
            }

            return n * factorialInternal(
                n - 1, depth + 1, context
            );
        }

        static long fibonacciMemoized(
            int n,
            RecursionContext context
        ) {
            if (n < 0 || n > 92) {
                throw new ValidationException(
                    "Fibonacci input must be between 0 and 92."
                );
            }

            Map<Integer, Long> cache = new HashMap<>();

            return fibonacciInternal(
                n, 0, context, cache
            );
        }

        private static long fibonacciInternal(
            int n,
            int depth,
            RecursionContext context,
            Map<Integer, Long> cache
        ) {
            context.enter(depth);

            if (n <= 1) {
                return n;
            }

            if (cache.containsKey(n)) {
                context.metrics().cacheHit();
                return cache.get(n);
            }

            long result = Math.addExact(
                fibonacciInternal(
                    n - 1, depth + 1, context, cache
                ),
                fibonacciInternal(
                    n - 2, depth + 1, context, cache
                )
            );

            cache.put(n, result);
            return result;
        }

        static long fibonacciIterative(int n) {
            if (n < 0 || n > 92) {
                throw new ValidationException(
                    "Invalid Fibonacci input."
                );
            }

            long previous = 0;
            long current = 1;

            for (int i = 0; i < n; i++) {
                long next = Math.addExact(previous, current);
                previous = current;
                current = next;
            }

            return previous;
        }

        static int binarySearch(
            List<Integer> values,
            int target,
            RecursionContext context
        ) {
            Objects.requireNonNull(values);

            for (int i = 1; i < values.size(); i++) {
                if (values.get(i) < values.get(i - 1)) {
                    throw new ValidationException(
                        "Binary search requires sorted input."
                    );
                }
            }

            return binarySearchInternal(
                values,
                target,
                0,
                values.size() - 1,
                0,
                context
            );
        }

        private static int binarySearchInternal(
            List<Integer> values,
            int target,
            int left,
            int right,
            int depth,
            RecursionContext context
        ) {
            context.enter(depth);

            if (left > right) {
                return -1;
            }

            int middle = left + (right - left) / 2;
            context.metrics().comparison();

            int value = values.get(middle);

            if (value == target) {
                return middle;
            }

            if (target < value) {
                return binarySearchInternal(
                    values,
                    target,
                    left,
                    middle - 1,
                    depth + 1,
                    context
                );
            }

            return binarySearchInternal(
                values,
                target,
                middle + 1,
                right,
                depth + 1,
                context
            );
        }

        static List<Integer> mergeSort(List<Integer> values) {
            Objects.requireNonNull(values);

            List<Integer> copy = new ArrayList<>(values);

            return sort(copy);
        }

        private static List<Integer> sort(List<Integer> values) {
            if (values.size() <= 1) {
                return values;
            }

            int middle = values.size() / 2;

            List<Integer> left = sort(
                new ArrayList<>(values.subList(0, middle))
            );

            List<Integer> right = sort(
                new ArrayList<>(values.subList(middle, values.size()))
            );

            return merge(left, right);
        }

        private static List<Integer> merge(
            List<Integer> left,
            List<Integer> right
        ) {
            List<Integer> result = new ArrayList<>(
                left.size() + right.size()
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

            result.addAll(left.subList(i, left.size()));
            result.addAll(right.subList(j, right.size()));

            return result;
        }
    }

    static final class TreeNode {
        final int value;
        final TreeNode left;
        final TreeNode right;

        TreeNode(int value, TreeNode left, TreeNode right) {
            this.value = value;
            this.left = left;
            this.right = right;
        }
    }

    static final class TreeService {

        List<Integer> traverse(
            TreeNode root,
            TraversalOrder order
        ) {
            Objects.requireNonNull(order);

            List<Integer> result = new ArrayList<>();

            Set<TreeNode> visited = Collections.newSetFromMap(
                new java.util.IdentityHashMap<>()
            );

            visit(root, order, result, visited);

            return List.copyOf(result);
        }

        private void visit(
            TreeNode node,
            TraversalOrder order,
            List<Integer> result,
            Set<TreeNode> visited
        ) {
            if (node == null) {
                return;
            }

            if (!visited.add(node)) {
                throw new ValidationException(
                    "Repeated node reference detected."
                );
            }

            if (order == TraversalOrder.PREORDER) {
                result.add(node.value);
            }

            visit(node.left, order, result, visited);

            if (order == TraversalOrder.INORDER) {
                result.add(node.value);
            }

            visit(node.right, order, result, visited);

            if (order == TraversalOrder.POSTORDER) {
                result.add(node.value);
            }
        }

        int sum(TreeNode root) {
            return sumInternal(root, 0, new HashSet<>());
        }

        private int sumInternal(
            TreeNode node,
            int depth,
            Set<TreeNode> visited
        ) {
            if (node == null) {
                return 0;
            }

            if (depth > 500) {
                throw new DepthLimitException(
                    "Tree depth exceeded."
                );
            }

            if (!visited.add(node)) {
                throw new ValidationException(
                    "Tree contains a cycle."
                );
            }

            return Math.addExact(
                node.value,
                Math.addExact(
                    sumInternal(node.left, depth + 1, visited),
                    sumInternal(node.right, depth + 1, visited)
                )
            );
        }
    }

    static final class DependencyService {

        private final Map<String, DependencyTask> tasks =
            new LinkedHashMap<>();

        void register(DependencyTask task) {
            Objects.requireNonNull(task);

            if (tasks.containsKey(task.name())) {
                throw new ValidationException(
                    "Task already registered: " + task.name()
                );
            }

            tasks.put(task.name(), task);
        }

        List<String> resolveExecutionOrder() {
            for (DependencyTask task : tasks.values()) {
                for (String dependency : task.dependencies()) {
                    if (!tasks.containsKey(dependency)) {
                        throw new ValidationException(
                            "Unknown dependency " + dependency +
                            " for " + task.name()
                        );
                    }
                }
            }

            Map<String, ComputationStatus> states = new HashMap<>();
            List<String> order = new ArrayList<>();

            for (String task : tasks.keySet()) {
                visit(task, states, order);
            }

            return List.copyOf(order);
        }

        private void visit(
            String task,
            Map<String, ComputationStatus> states,
            List<String> order
        ) {
            ComputationStatus state = states.getOrDefault(
                task,
                ComputationStatus.PENDING
            );

            if (state == ComputationStatus.COMPLETED) {
                return;
            }

            if (state == ComputationStatus.RUNNING) {
                throw new DependencyCycleException(
                    "Circular dependency detected: " + task
                );
            }

            states.put(task, ComputationStatus.RUNNING);

            for (String dependency : tasks.get(task).dependencies()) {
                visit(dependency, states, order);
            }

            states.put(task, ComputationStatus.COMPLETED);
            order.add(task);
        }
    }

    static final class ComputationService {

        ComputationResult executeFactorial(int n) {
            RecursionContext context = new RecursionContext(500);

            Instant start = Instant.now();

            ComputationStatus status = ComputationStatus.RUNNING;

            try {
                long value = RecursiveAlgorithms.factorial(n, context);

                status = ComputationStatus.COMPLETED;

                return new ComputationResult(
                    "factorial",
                    value,
                    Duration.between(start, Instant.now()),
                    context.snapshot(),
                    status
                );
            } catch (RuntimeException exception) {
                status = ComputationStatus.FAILED;
                throw exception;
            }
        }
    }

    static void runTests() {
        RecursionContext context = new RecursionContext(500);

        assert RecursiveAlgorithms.factorial(0, context) == 1;
        assert RecursiveAlgorithms.factorial(5, context) == 120;

        RecursionContext fibonacciContext =
            new RecursionContext(500);

        assert RecursiveAlgorithms.fibonacciMemoized(
            40, fibonacciContext
        ) == 102334155L;

        assert RecursiveAlgorithms.fibonacciIterative(40)
            == 102334155L;

        List<Integer> values = List.of(1, 3, 5, 7, 9);

        assert RecursiveAlgorithms.binarySearch(
            values, 7, new RecursionContext(100)
        ) == 3;

        assert RecursiveAlgorithms.binarySearch(
            values, 8, new RecursionContext(100)
        ) == -1;

        assert RecursiveAlgorithms.mergeSort(
            List.of(8, 2, 4, 1, 9)
        ).equals(List.of(1, 2, 4, 8, 9));

        TreeNode root = new TreeNode(
            8,
            new TreeNode(4, null, null),
            new TreeNode(12, null, null)
        );

        TreeService treeService = new TreeService();

        assert treeService.traverse(
            root, TraversalOrder.INORDER
        ).equals(List.of(4, 8, 12));

        assert treeService.sum(root) == 24;

        DependencyService dependencies = new DependencyService();

        dependencies.register(
            new DependencyTask("deploy", List.of("test"))
        );

        dependencies.register(
            new DependencyTask("test", List.of("build"))
        );

        dependencies.register(
            new DependencyTask("build", List.of("compile"))
        );

        dependencies.register(
            new DependencyTask("compile", List.of())
        );

        assert dependencies.resolveExecutionOrder().equals(
            List.of("compile", "build", "test", "deploy")
        );

        System.out.println("All tests passed.");
    }

    public static void main(String[] args) {
        try {
            System.out.println("1. FACTORIAL");

            ComputationService service = new ComputationService();

            ComputationResult factorial =
                service.executeFactorial(5);

            System.out.println("Result: " + factorial.value());
            System.out.println("Status: " + factorial.status());
            System.out.println("Metrics: " + factorial.metrics());

            System.out.println("\n2. MEMOIZED FIBONACCI");

            RecursionContext fibonacciContext =
                new RecursionContext(500);

            long fibonacci =
                RecursiveAlgorithms.fibonacciMemoized(
                    40, fibonacciContext
                );

            System.out.println("F(40): " + fibonacci);
            System.out.println(
                "Metrics: " + fibonacciContext.snapshot()
            );

            System.out.println("\n3. BINARY SEARCH");

            List<Integer> numbers =
                List.of(2, 4, 6, 8, 10, 12, 14);

            System.out.println(
                "Position of 10: " +
                RecursiveAlgorithms.binarySearch(
                    numbers, 10, new RecursionContext(100)
                )
            );

            System.out.println("\n4. MERGE SORT");

            List<Integer> unsorted =
                List.of(45, 12, 78, 3, 29, 18, 1);

            System.out.println(
                RecursiveAlgorithms.mergeSort(unsorted)
            );

            System.out.println("\n5. TREE TRAVERSAL");

            TreeNode root = new TreeNode(
                10,
                new TreeNode(
                    5,
                    new TreeNode(2, null, null),
                    new TreeNode(7, null, null)
                ),
                new TreeNode(
                    15,
                    null,
                    new TreeNode(20, null, null)
                )
            );

            TreeService treeService = new TreeService();

            for (TraversalOrder order : TraversalOrder.values()) {
                System.out.println(
                    order + ": " +
                    treeService.traverse(root, order)
                );
            }

            System.out.println("Tree sum: " + treeService.sum(root));

            System.out.println("\n6. DEPENDENCY RESOLUTION");

            DependencyService dependencies =
                new DependencyService();

            dependencies.register(
                new DependencyTask(
                    "deploy",
                    List.of("integration-test")
                )
            );

            dependencies.register(
                new DependencyTask(
                    "integration-test",
                    List.of("unit-test")
                )
            );

            dependencies.register(
                new DependencyTask(
                    "unit-test",
                    List.of("build")
                )
            );

            dependencies.register(
                new DependencyTask("build", List.of("compile"))
            );

            dependencies.register(
                new DependencyTask("compile", List.of())
            );

            System.out.println(
                dependencies.resolveExecutionOrder()
            );

            System.out.println("\n7. PERFORMANCE");

            Instant start = Instant.now();

            List<Integer> large = new ArrayList<>();

            for (int i = 100000; i >= 1; i--) {
                large.add(i);
            }

            List<Integer> sorted =
                RecursiveAlgorithms.mergeSort(large);

            System.out.println(
                "Elements sorted: " + sorted.size()
            );

            System.out.println(
                "Elapsed: " +
                Duration.between(start, Instant.now()).toMillis() +
                " ms"
            );

            System.out.println("\n8. ASSERTION TESTS");
            runTests();

        } catch (RuntimeException exception) {
            System.err.println(
                exception.getClass().getSimpleName() +
                ": " + exception.getMessage()
            );

            System.exit(1);
        }
    }
}
