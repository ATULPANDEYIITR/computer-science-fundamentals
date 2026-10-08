import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Enterprise-oriented deadlock governance model.
 *
 * The domain models jobs, resource pools, allocation requests, safety
 * evaluation, wait-for graphs, detection, and recovery.
 *
 * Compile:
 *   javac DeadlockGovernance.java
 *
 * Run:
 *   java DeadlockGovernance
 */
public class DeadlockGovernance {

    enum ProcessState {
        READY,
        RUNNING,
        WAITING,
        COMPLETED,
        ABORTED
    }

    static final class ResourcePool {
        private final Map<String, Integer> capacity;
        private final Map<String, Integer> available;

        ResourcePool(Map<String, Integer> capacity) {
            this.capacity = new LinkedHashMap<>(capacity);
            this.available = new LinkedHashMap<>(capacity);

            for (Map.Entry<String, Integer> entry : capacity.entrySet()) {
                if (entry.getValue() <= 0) {
                    throw new IllegalArgumentException(
                        "Resource capacity must be positive: " + entry.getKey()
                    );
                }
            }
        }

        boolean canAllocate(Map<String, Integer> request) {
            for (Map.Entry<String, Integer> entry : request.entrySet()) {
                String resource = entry.getKey();
                int amount = entry.getValue();

                if (!capacity.containsKey(resource)
                        || amount < 0
                        || amount > available.get(resource)) {
                    return false;
                }
            }

            return true;
        }

        void allocate(Map<String, Integer> request) {
            if (!canAllocate(request)) {
                throw new IllegalStateException(
                    "Requested resources are not currently available."
                );
            }

            request.forEach(
                (resource, amount) ->
                    available.put(resource, available.get(resource) - amount)
            );
        }

        void release(Map<String, Integer> resources) {
            for (Map.Entry<String, Integer> entry : resources.entrySet()) {
                String resource = entry.getKey();
                int amount = entry.getValue();

                if (!capacity.containsKey(resource)) {
                    throw new IllegalArgumentException(
                        "Unknown resource: " + resource
                    );
                }

                int next = available.get(resource) + amount;

                if (next > capacity.get(resource)) {
                    throw new IllegalStateException(
                        "Release exceeds resource capacity: " + resource
                    );
                }

                available.put(resource, next);
            }
        }

        Map<String, Integer> snapshot() {
            return Map.copyOf(available);
        }
    }

    static final class Job {
        private final String name;
        private final Map<String, Integer> maximum;
        private final Map<String, Integer> allocation;
        private ProcessState state = ProcessState.READY;

        Job(String name, Map<String, Integer> maximum) {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("Job name is required.");
            }

            this.name = name;
            this.maximum = new LinkedHashMap<>(maximum);
            this.allocation = new LinkedHashMap<>();

            for (Map.Entry<String, Integer> entry : maximum.entrySet()) {
                if (entry.getValue() < 0) {
                    throw new IllegalArgumentException(
                        "Maximum claim cannot be negative."
                    );
                }

                allocation.put(entry.getKey(), 0);
            }
        }

        String name() {
            return name;
        }

        ProcessState state() {
            return state;
        }

        void state(ProcessState state) {
            this.state = state;
        }

        Map<String, Integer> maximum() {
            return Map.copyOf(maximum);
        }

        Map<String, Integer> allocation() {
            return Map.copyOf(allocation);
        }

        Map<String, Integer> need() {
            Map<String, Integer> need = new LinkedHashMap<>();

            for (Map.Entry<String, Integer> entry : maximum.entrySet()) {
                int held = allocation.getOrDefault(entry.getKey(), 0);

                need.put(entry.getKey(), entry.getValue() - held);
            }

            return need;
        }

        void allocate(Map<String, Integer> request) {
            for (Map.Entry<String, Integer> entry : request.entrySet()) {
                String resource = entry.getKey();
                int amount = entry.getValue();

                int current = allocation.getOrDefault(resource, 0);
                int maximumAmount = maximum.getOrDefault(resource, -1);

                if (maximumAmount < 0 || current + amount > maximumAmount) {
                    throw new IllegalStateException(
                        name + " exceeds maximum claim for " + resource
                    );
                }

                allocation.put(resource, current + amount);
            }
        }

        Map<String, Integer> releaseAll() {
            Map<String, Integer> released = new LinkedHashMap<>(allocation);

            for (String resource : allocation.keySet()) {
                allocation.put(resource, 0);
            }

            return released;
        }
    }

    static final class DeadlockDetectedException extends RuntimeException {
        DeadlockDetectedException(String message) {
            super(message);
        }
    }

    static final class DeadlockEngine {
        private final ResourcePool resources;
        private final Map<String, Job> jobs = new LinkedHashMap<>();
        private final Map<String, Set<String>> waitingFor =
            new LinkedHashMap<>();

        DeadlockEngine(Map<String, Integer> capacities) {
            this.resources = new ResourcePool(capacities);
        }

        void register(Job job) {
            if (jobs.containsKey(job.name())) {
                throw new IllegalArgumentException(
                    "Duplicate job: " + job.name()
                );
            }

            for (String resource : job.maximum().keySet()) {
                if (!resources.capacity.containsKey(resource)) {
                    throw new IllegalArgumentException(
                        "Unknown resource: " + resource
                    );
                }
            }

            jobs.put(job.name(), job);
            waitingFor.put(job.name(), new LinkedHashSet<>());
        }

        boolean request(
            String jobName,
            Map<String, Integer> request,
            boolean avoidUnsafeState
        ) {
            Job job = requireJob(jobName);

            validateRequest(job, request);

            if (!resources.canAllocate(request)) {
                job.state(ProcessState.WAITING);
                waitingFor.get(jobName).addAll(request.keySet());
                return false;
            }

            if (avoidUnsafeState && !safeAfter(jobName, request)) {
                job.state(ProcessState.WAITING);
                waitingFor.get(jobName).addAll(request.keySet());
                return false;
            }

            resources.allocate(request);
            job.allocate(request);
            job.state(ProcessState.RUNNING);
            waitingFor.get(jobName).clear();

            return true;
        }

        private void validateRequest(
            Job job,
            Map<String, Integer> request
        ) {
            Map<String, Integer> need = job.need();

            for (Map.Entry<String, Integer> entry : request.entrySet()) {
                String resource = entry.getKey();
                int amount = entry.getValue();

                if (!resources.capacity.containsKey(resource)) {
                    throw new IllegalArgumentException(
                        "Unknown resource: " + resource
                    );
                }

                if (amount < 0) {
                    throw new IllegalArgumentException(
                        "Negative resource request."
                    );
                }

                if (amount > need.getOrDefault(resource, 0)) {
                    throw new IllegalArgumentException(
                        job.name()
                            + " exceeds remaining need for "
                            + resource
                    );
                }
            }
        }

        private boolean safeAfter(
            String jobName,
            Map<String, Integer> request
        ) {
            Job job = requireJob(jobName);

            resources.allocate(request);

            try {
                job.allocate(request);
                return isSafe();
            } finally {
                Map<String, Integer> rollback = new LinkedHashMap<>();

                for (Map.Entry<String, Integer> entry : request.entrySet()) {
                    rollback.put(entry.getKey(), entry.getValue());
                }

                resources.release(rollback);

                for (Map.Entry<String, Integer> entry : request.entrySet()) {
                    int current =
                        job.allocation.getOrDefault(entry.getKey(), 0);

                    job.allocation.put(
                        entry.getKey(),
                        current - entry.getValue()
                    );
                }
            }
        }

        boolean isSafe() {
            Map<String, Integer> work =
                new LinkedHashMap<>(resources.snapshot());

            Set<String> active = new LinkedHashSet<>();

            for (Job job : jobs.values()) {
                if (job.state() != ProcessState.ABORTED
                    && job.state() != ProcessState.COMPLETED) {
                    active.add(job.name());
                }
            }

            Set<String> finished = new HashSet<>();

            boolean changed = true;

            while (changed) {
                changed = false;

                for (String jobName : active) {
                    if (finished.contains(jobName)) {
                        continue;
                    }

                    Job job = jobs.get(jobName);
                    boolean canFinish = true;

                    for (Map.Entry<String, Integer> entry
                            : job.need().entrySet()) {

                        if (entry.getValue()
                                > work.getOrDefault(entry.getKey(), 0)) {
                            canFinish = false;
                            break;
                        }
                    }

                    if (canFinish) {
                        for (Map.Entry<String, Integer> entry
                                : job.allocation.entrySet()) {

                            work.put(
                                entry.getKey(),
                                work.getOrDefault(entry.getKey(), 0)
                                    + entry.getValue()
                            );
                        }

                        finished.add(jobName);
                        changed = true;
                    }
                }
            }

            return finished.size() == active.size();
        }

        List<String> safeSequence() {
            Map<String, Integer> work =
                new LinkedHashMap<>(resources.snapshot());

            Set<String> remaining = new LinkedHashSet<>();

            for (Job job : jobs.values()) {
                if (job.state() != ProcessState.ABORTED
                    && job.state() != ProcessState.COMPLETED) {
                    remaining.add(job.name());
                }
            }

            List<String> sequence = new ArrayList<>();

            while (!remaining.isEmpty()) {
                String candidate = null;

                for (String jobName : remaining) {
                    Job job = jobs.get(jobName);
                    boolean canFinish = true;

                    for (Map.Entry<String, Integer> entry
                            : job.need().entrySet()) {

                        if (entry.getValue()
                                > work.getOrDefault(entry.getKey(), 0)) {
                            canFinish = false;
                            break;
                        }
                    }

                    if (canFinish) {
                        candidate = jobName;
                        break;
                    }
                }

                if (candidate == null) {
                    return List.of();
                }

                Job job = jobs.get(candidate);

                for (Map.Entry<String, Integer> entry
                        : job.allocation.entrySet()) {

                    work.put(
                        entry.getKey(),
                        work.getOrDefault(entry.getKey(), 0)
                            + entry.getValue()
                    );
                }

                sequence.add(candidate);
                remaining.remove(candidate);
            }

            return List.copyOf(sequence);
        }

        Map<String, Set<String>> waitForGraph() {
            Map<String, Set<String>> graph = new LinkedHashMap<>();

            for (String jobName : jobs.keySet()) {
                graph.put(jobName, new LinkedHashSet<>());
            }

            Map<String, Set<String>> holders = new LinkedHashMap<>();

            for (Job job : jobs.values()) {
                if (job.state() == ProcessState.ABORTED) {
                    continue;
                }

                for (Map.Entry<String, Integer> entry
                        : job.allocation.entrySet()) {

                    if (entry.getValue() > 0) {
                        holders
                            .computeIfAbsent(
                                entry.getKey(),
                                ignored -> new LinkedHashSet<>()
                            )
                            .add(job.name());
                    }
                }
            }

            Map<String, Integer> available = resources.snapshot();

            for (Map.Entry<String, Set<String>> waiting
                    : waitingFor.entrySet()) {

                for (String resource : waiting.getValue()) {
                    if (available.getOrDefault(resource, 0) == 0) {
                        graph
                            .get(waiting.getKey())
                            .addAll(
                                holders.getOrDefault(
                                    resource,
                                    Set.of()
                                )
                            );
                    }
                }
            }

            return graph;
        }

        Set<String> detectDeadlock() {
            Map<String, Set<String>> graph = waitForGraph();

            Set<String> visited = new HashSet<>();
            Set<String> active = new HashSet<>();
            Set<String> deadlocked = new LinkedHashSet<>();

            for (String node : graph.keySet()) {
                detectFrom(
                    node,
                    graph,
                    visited,
                    active,
                    new ArrayList<>(),
                    deadlocked
                );
            }

            return deadlocked;
        }

        private void detectFrom(
            String node,
            Map<String, Set<String>> graph,
            Set<String> visited,
            Set<String> active,
            List<String> path,
            Set<String> deadlocked
        ) {
            if (active.contains(node)) {
                int index = path.indexOf(node);

                if (index >= 0) {
                    deadlocked.addAll(path.subList(index, path.size()));
                }

                return;
            }

            if (visited.contains(node)) {
                return;
            }

            visited.add(node);
            active.add(node);
            path.add(node);

            for (String neighbor : graph.getOrDefault(node, Set.of())) {
                detectFrom(
                    neighbor,
                    graph,
                    visited,
                    active,
                    path,
                    deadlocked
                );
            }

            path.remove(path.size() - 1);
            active.remove(node);
        }

        void recoverByAbort(String jobName) {
            Job job = requireJob(jobName);

            Map<String, Integer> released = job.releaseAll();
            resources.release(released);

            job.state(ProcessState.ABORTED);
            waitingFor.get(jobName).clear();
        }

        void complete(String jobName) {
            Job job = requireJob(jobName);

            Map<String, Integer> released = job.releaseAll();
            resources.release(released);

            job.state(ProcessState.COMPLETED);
            waitingFor.get(jobName).clear();
        }

        Job requireJob(String jobName) {
            Job job = jobs.get(jobName);

            if (job == null) {
                throw new IllegalArgumentException(
                    "Unknown job: " + jobName
                );
            }

            return job;
        }

        void printState() {
            System.out.println("\nAvailable: " + resources.snapshot());

            for (Job job : jobs.values()) {
                System.out.println(
                    job.name()
                        + " state=" + job.state()
                        + " allocation=" + job.allocation()
                        + " need=" + job.need()
                );
            }
        }
    }

    private static DeadlockEngine createDeadlockedSystem() {
        DeadlockEngine engine = new DeadlockEngine(
            Map.of(
                "DatabaseConnection", 1,
                "AuditLock", 1
            )
        );

        engine.register(
            new Job(
                "BillingTransaction",
                Map.of(
                    "DatabaseConnection", 1,
                    "AuditLock", 1
                )
            )
        );

        engine.register(
            new Job(
                "AuditTransaction",
                Map.of(
                    "DatabaseConnection", 1,
                    "AuditLock", 1
                )
            )
        );

        engine.request(
            "BillingTransaction",
            Map.of("DatabaseConnection", 1),
            false
        );

        engine.request(
            "AuditTransaction",
            Map.of("AuditLock", 1),
            false
        );

        engine.request(
            "BillingTransaction",
            Map.of("AuditLock", 1),
            false
        );

        engine.request(
            "AuditTransaction",
            Map.of("DatabaseConnection", 1),
            false
        );

        return engine;
    }

    private static void demonstrateConditions() {
        System.out.println("=== Coffman Conditions ===");
        System.out.println(
            "Mutual exclusion: a non-shareable resource has one effective holder."
        );
        System.out.println(
            "Hold and wait: a job retains allocated resources while waiting."
        );
        System.out.println(
            "No preemption: the system cannot simply reclaim the held resource."
        );
        System.out.println(
            "Circular wait: the dependency graph contains a directed cycle."
        );
    }

    private static void demonstratePrevention() {
        System.out.println("\n=== Prevention Policy ===");

        Map<String, Integer> resourceOrder = Map.of(
            "DatabaseConnection", 1,
            "AuditLock", 2
        );

        String held = "AuditLock";
        String requested = "DatabaseConnection";

        boolean valid =
            resourceOrder.get(held) < resourceOrder.get(requested);

        System.out.println(
            "Requesting " + requested
                + " while holding " + held
                + ": "
                + (valid ? "allowed" : "rejected")
        );

        System.out.println(
            "A global acquisition order removes circular wait by preventing "
                + "descending resource-order requests."
        );
    }

    private static void demonstrateAvoidance() {
        System.out.println("\n=== Avoidance ===");

        DeadlockEngine engine = new DeadlockEngine(
            Map.of("A", 10, "B", 5, "C", 7)
        );

        engine.register(
            new Job(
                "P0",
                Map.of("A", 7, "B", 5, "C", 3)
            )
        );

        engine.register(
            new Job(
                "P1",
                Map.of("A", 3, "B", 2, "C", 2)
            )
        );

        engine.register(
            new Job(
                "P2",
                Map.of("A", 9, "B", 0, "C", 2)
            )
        );

        engine.register(
            new Job(
                "P3",
                Map.of("A", 2, "B", 2, "C", 2)
            )
        );

        engine.register(
            new Job(
                "P4",
                Map.of("A", 4, "B", 3, "C", 3)
            )
        );

        engine.request("P0", Map.of("B", 1), false);
        engine.request("P1", Map.of("A", 2), false);
        engine.request("P2", Map.of("A", 3, "C", 2), false);
        engine.request("P3", Map.of("A", 2, "B", 1, "C", 1), false);
        engine.request("P4", Map.of("C", 2), false);

        System.out.println("Safe state: " + engine.isSafe());
        System.out.println("Safe sequence: " + engine.safeSequence());

        boolean accepted = engine.request(
            "P1",
            Map.of("A", 1, "B", 1, "C", 2),
            true
        );

        System.out.println(
            "Safety-checked request accepted: " + accepted
        );
    }

    private static void demonstrateDetectionAndRecovery() {
        System.out.println("\n=== Detection and Recovery ===");

        DeadlockEngine engine = createDeadlockedSystem();

        engine.printState();

        Set<String> deadlocked = engine.detectDeadlock();

        System.out.println(
            "\nDetected deadlocked jobs: " + deadlocked
        );

        if (!deadlocked.isEmpty()) {
            // This sample uses the first cycle member as the victim.
            // Production recovery can rank candidates by rollback cost,
            // priority, transaction age, resources held, and business impact.
            String victim = deadlocked.iterator().next();

            System.out.println("Aborting recovery victim: " + victim);
            engine.recoverByAbort(victim);
        }

        System.out.println(
            "Deadlock after recovery: "
                + engine.detectDeadlock()
        );

        engine.printState();
    }

    public static void main(String[] args) {
        try {
            System.out.println(
                "DEADLOCK GOVERNANCE: ENTERPRISE RESOURCE MODEL"
            );

            demonstrateConditions();
            demonstratePrevention();
            demonstrateAvoidance();
            demonstrateDetectionAndRecovery();

            System.out.println(
                "\nArchitectural distinction:"
                    + "\nPrevention constrains how resources may be acquired."
                    + "\nAvoidance evaluates whether a proposed allocation "
                    + "preserves a safe completion sequence."
                    + "\nDetection analyzes an existing dependency graph."
                    + "\nRecovery changes process state and releases resources "
                    + "so other work can proceed."
            );
        } catch (DeadlockDetectedException error) {
            System.err.println("Deadlock detected: " + error.getMessage());
        } catch (RuntimeException error) {
            System.err.println("Execution error: " + error.getMessage());
            System.exit(1);
        }
    }
}
