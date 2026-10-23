import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Deque;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.PriorityQueue;
import java.util.Queue;
import java.util.Set;
import java.util.TreeSet;

/*
 * Enterprise-style data processing model.
 *
 * The domain is a deployment pipeline. Tasks have dependencies, urgent work
 * is prioritized, and completed tasks are tracked separately from pending work.
 */
public class DataStructuresEnterpriseDemo {

    enum TaskState {
        PENDING,
        RUNNING,
        COMPLETED,
        FAILED
    }

    record DeploymentTask(
        String id,
        String service,
        int priority,
        TaskState state
    ) {
        DeploymentTask {
            Objects.requireNonNull(id, "id");
            Objects.requireNonNull(service, "service");

            if (id.isBlank() || service.isBlank()) {
                throw new IllegalArgumentException(
                    "Task identifiers and services cannot be blank"
                );
            }

            if (priority < 1 || priority > 100) {
                throw new IllegalArgumentException(
                    "Priority must be between 1 and 100"
                );
            }
        }

        DeploymentTask withState(TaskState newState) {
            return new DeploymentTask(id, service, priority, newState);
        }
    }


    interface WorkQueue<T> {
        void add(T value);
        T remove();
        boolean isEmpty();
        int size();
    }


    static final class FifoWorkQueue<T> implements WorkQueue<T> {
        private final Deque<T> queue = new ArrayDeque<>();

        @Override
        public void add(T value) {
            queue.addLast(Objects.requireNonNull(value));
        }

        @Override
        public T remove() {
            if (queue.isEmpty()) {
                throw new IllegalStateException("Work queue is empty");
            }

            return queue.removeFirst();
        }

        @Override
        public boolean isEmpty() {
            return queue.isEmpty();
        }

        @Override
        public int size() {
            return queue.size();
        }
    }


    static final class PriorityWorkQueue<T> implements WorkQueue<T> {
        private final PriorityQueue<T> queue;

        PriorityWorkQueue(java.util.Comparator<T> comparator) {
            this.queue = new PriorityQueue<>(comparator);
        }

        @Override
        public void add(T value) {
            queue.add(Objects.requireNonNull(value));
        }

        @Override
        public T remove() {
            if (queue.isEmpty()) {
                throw new IllegalStateException("Priority queue is empty");
            }

            return queue.remove();
        }

        @Override
        public boolean isEmpty() {
            return queue.isEmpty();
        }

        @Override
        public int size() {
            return queue.size();
        }
    }


    static final class DependencyGraph {
        private final Map<String, Set<String>> dependencies = new HashMap<>();

        void addTask(String taskId) {
            validateTaskId(taskId);
            dependencies.putIfAbsent(taskId, new HashSet<>());
        }

        void addDependency(String prerequisite, String dependent) {
            validateTaskId(prerequisite);
            validateTaskId(dependent);

            if (!dependencies.containsKey(prerequisite)
                || !dependencies.containsKey(dependent)) {
                throw new IllegalArgumentException(
                    "Both tasks must already exist"
                );
            }

            if (prerequisite.equals(dependent)) {
                throw new IllegalArgumentException(
                    "A task cannot depend on itself"
                );
            }

            dependencies.get(prerequisite).add(dependent);
        }

        List<String> topologicalOrder() {
            Map<String, Integer> indegree = new HashMap<>();

            dependencies.keySet().forEach(
                task -> indegree.put(task, 0)
            );

            for (Set<String> dependents : dependencies.values()) {
                for (String dependent : dependents) {
                    indegree.merge(dependent, 1, Integer::sum);
                }
            }

            Queue<String> ready = new ArrayDeque<>();

            indegree.entrySet()
                .stream()
                .filter(entry -> entry.getValue() == 0)
                .map(Map.Entry::getKey)
                .sorted()
                .forEach(ready::add);

            List<String> result = new ArrayList<>();

            while (!ready.isEmpty()) {
                String current = ready.remove();
                result.add(current);

                for (String dependent : dependencies.get(current)) {
                    int remaining = indegree.merge(
                        dependent,
                        -1,
                        Integer::sum
                    );

                    if (remaining == 0) {
                        ready.add(dependent);
                    }
                }
            }

            if (result.size() != dependencies.size()) {
                throw new IllegalStateException(
                    "Dependency cycle prevents scheduling"
                );
            }

            return List.copyOf(result);
        }

        private static void validateTaskId(String taskId) {
            if (taskId == null || taskId.isBlank()) {
                throw new IllegalArgumentException(
                    "Task ID cannot be blank"
                );
            }
        }
    }


    static final class DeploymentService {
        private final Map<String, DeploymentTask> tasks = new HashMap<>();
        private final Set<String> completedTaskIds = new HashSet<>();

        void register(DeploymentTask task) {
            Objects.requireNonNull(task);

            if (tasks.putIfAbsent(task.id(), task) != null) {
                throw new IllegalArgumentException(
                    "Duplicate task: " + task.id()
                );
            }
        }

        void start(String taskId) {
            DeploymentTask task = requireTask(taskId);

            if (task.state() != TaskState.PENDING) {
                throw new IllegalStateException(
                    "Only pending tasks can start"
                );
            }

            tasks.put(taskId, task.withState(TaskState.RUNNING));
        }

        void complete(String taskId) {
            DeploymentTask task = requireTask(taskId);

            if (task.state() != TaskState.RUNNING) {
                throw new IllegalStateException(
                    "Only running tasks can complete"
                );
            }

            DeploymentTask completed =
                task.withState(TaskState.COMPLETED);

            tasks.put(taskId, completed);
            completedTaskIds.add(taskId);
        }

        List<DeploymentTask> findByService(String service) {
            if (service == null || service.isBlank()) {
                return List.of();
            }

            return tasks.values()
                .stream()
                .filter(task -> task.service().equals(service))
                .sorted(java.util.Comparator.comparing(
                    DeploymentTask::id
                ))
                .toList();
        }

        private DeploymentTask requireTask(String taskId) {
            DeploymentTask task = tasks.get(taskId);

            if (task == null) {
                throw new IllegalArgumentException(
                    "Unknown task: " + taskId
                );
            }

            return task;
        }
    }


    static Optional<Integer> binarySearch(
        List<Integer> sortedValues,
        int target
    ) {
        int low = 0;
        int high = sortedValues.size() - 1;

        while (low <= high) {
            int middle = low + (high - low) / 2;
            int current = sortedValues.get(middle);

            if (current == target) {
                return Optional.of(middle);
            }

            if (current < target) {
                low = middle + 1;
            } else {
                high = middle - 1;
            }
        }

        return Optional.empty();
    }


    public static void main(String[] args) {
        FifoWorkQueue<String> fifo = new FifoWorkQueue<>();
        fifo.add("request-A");
        fifo.add("request-B");
        fifo.add("request-C");

        System.out.println("FIFO removal: " + fifo.remove());
        System.out.println("FIFO remaining: " + fifo.size());

        PriorityWorkQueue<DeploymentTask> priorityQueue =
            new PriorityWorkQueue<>(
                java.util.Comparator
                    .comparingInt(DeploymentTask::priority)
                    .thenComparing(DeploymentTask::id)
            );

        priorityQueue.add(new DeploymentTask(
            "DEP-003", "billing", 60, TaskState.PENDING
        ));
        priorityQueue.add(new DeploymentTask(
            "DEP-001", "identity", 10, TaskState.PENDING
        ));
        priorityQueue.add(new DeploymentTask(
            "DEP-002", "orders", 30, TaskState.PENDING
        ));

        System.out.println(
            "Highest-priority task: " + priorityQueue.remove().id()
        );

        DeploymentService service = new DeploymentService();

        service.register(new DeploymentTask(
            "DEP-101", "identity", 10, TaskState.PENDING
        ));

        service.register(new DeploymentTask(
            "DEP-102", "identity", 20, TaskState.PENDING
        ));

        service.register(new DeploymentTask(
            "DEP-103", "orders", 30, TaskState.PENDING
        ));

        service.start("DEP-101");
        service.complete("DEP-101");

        System.out.println(
            "Identity tasks: " + service.findByService("identity")
        );

        DependencyGraph graph = new DependencyGraph();

        for (String task : List.of(
            "compile",
            "unit-test",
            "security-scan",
            "package",
            "deploy"
        )) {
            graph.addTask(task);
        }

        graph.addDependency("compile", "unit-test");
        graph.addDependency("unit-test", "security-scan");
        graph.addDependency("security-scan", "package");
        graph.addDependency("package", "deploy");

        System.out.println(
            "Deployment order: " + graph.topologicalOrder()
        );

        List<Integer> releaseNumbers =
            List.of(101, 104, 108, 115, 120, 127);

        System.out.println(
            "Binary-search result: "
            + binarySearch(releaseNumbers, 115)
        );

        /*
         * TreeSet keeps values sorted while rejecting duplicates.
         * This is useful when both uniqueness and ordered iteration matter.
         */
        TreeSet<String> affectedServices = new TreeSet<>();
        Collections.addAll(
            affectedServices,
            "orders",
            "identity",
            "orders",
            "billing"
        );

        System.out.println(
            "Affected services: " + affectedServices
        );

        /*
         * A HashSet is preferable when ordering is irrelevant and average
         * constant-time membership checks are the primary requirement.
         */
        Set<String> completed = new HashSet<>(
            List.of("DEP-101", "DEP-104", "DEP-108")
        );

        System.out.println(
            "Completed DEP-104: " + completed.contains("DEP-104")
        );

        try {
            service.complete("DEP-102");
        } catch (IllegalStateException error) {
            System.out.println(
                "Expected state failure: " + error.getMessage()
            );
        }
    }
}
