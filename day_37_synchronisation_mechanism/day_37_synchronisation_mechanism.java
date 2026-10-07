/*
 * Synchronization mechanisms: enterprise repository build service.
 *
 * Java 17 implementation demonstrating:
 * - synchronized monitor semantics
 * - ReentrantLock
 * - Condition
 * - Semaphore
 * - explicit state transitions
 * - immutable records
 * - validation and exception handling
 * - lock ordering for deadlock avoidance
 *
 * Compile:
 *   javac SynchronizationEnterpriseDemo.java
 *
 * Run:
 *   java SynchronizationEnterpriseDemo
 */

import java.time.Instant;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.EnumSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.concurrent.Semaphore;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.ReentrantLock;

public class SynchronizationEnterpriseDemo {

    enum BuildState {
        QUEUED,
        RUNNING,
        SUCCEEDED,
        FAILED
    }

    enum FailureReason {
        VALIDATION,
        COMPILER,
        TIMEOUT
    }

    record BuildRequest(
            long id,
            String repository,
            String branch,
            boolean shouldFail
    ) {
        BuildRequest {
            if (id <= 0) {
                throw new IllegalArgumentException("Build ID must be positive");
            }
            if (repository == null || repository.isBlank()) {
                throw new IllegalArgumentException("Repository is required");
            }
            if (branch == null || branch.isBlank()) {
                throw new IllegalArgumentException("Branch is required");
            }
        }
    }

    record BuildResult(
            long requestId,
            BuildState state,
            FailureReason failureReason,
            Instant completedAt
    ) {
    }

    static final class BuildJob {
        private final BuildRequest request;
        private BuildState state = BuildState.QUEUED;
        private FailureReason failureReason;

        BuildJob(BuildRequest request) {
            this.request = Objects.requireNonNull(request);
        }

        /*
         * synchronized makes the job itself a monitor. State transitions are
         * guarded so another thread cannot observe a partially updated state.
         */
        public synchronized void transitionTo(BuildState next) {
            if (!isAllowedTransition(state, next)) {
                throw new IllegalStateException(
                        "Invalid transition " + state + " -> " + next
                );
            }

            state = next;
        }

        public synchronized void fail(FailureReason reason) {
            if (state != BuildState.RUNNING) {
                throw new IllegalStateException(
                        "Only running jobs can fail"
                );
            }

            failureReason = Objects.requireNonNull(reason);
            state = BuildState.FAILED;
        }

        public synchronized BuildResult result() {
            return new BuildResult(
                    request.id(),
                    state,
                    failureReason,
                    Instant.now()
            );
        }

        public BuildRequest request() {
            return request;
        }

        private static boolean isAllowedTransition(
                BuildState current,
                BuildState next
        ) {
            return switch (current) {
                case QUEUED -> next == BuildState.RUNNING;
                case RUNNING -> next == BuildState.SUCCEEDED;
                case SUCCEEDED, FAILED -> false;
                case FAILED -> false;
            };
        }
    }

    static final class BoundedBuildQueue {

        private final int capacity;
        private final Deque<BuildJob> jobs = new ArrayDeque<>();

        /*
         * One explicit lock controls queue state. Two conditions represent
         * two distinct predicates:
         *   notEmpty -> consumers may retrieve work
         *   notFull  -> producers may enqueue work
         */
        private final ReentrantLock lock = new ReentrantLock();
        private final Condition notEmpty = lock.newCondition();
        private final Condition notFull = lock.newCondition();

        private boolean closed;

        BoundedBuildQueue(int capacity) {
            if (capacity <= 0) {
                throw new IllegalArgumentException(
                        "Queue capacity must be positive"
                );
            }
            this.capacity = capacity;
        }

        void put(BuildJob job) throws InterruptedException {
            Objects.requireNonNull(job);

            lock.lockInterruptibly();

            try {
                while (jobs.size() == capacity && !closed) {
                    notFull.await();
                }

                if (closed) {
                    throw new IllegalStateException("Queue is closed");
                }

                jobs.addLast(job);
                notEmpty.signal();
            } finally {
                lock.unlock();
            }
        }

        BuildJob take() throws InterruptedException {
            lock.lockInterruptibly();

            try {
                while (jobs.isEmpty() && !closed) {
                    notEmpty.await();
                }

                if (jobs.isEmpty() && closed) {
                    return null;
                }

                BuildJob job = jobs.removeFirst();
                notFull.signal();
                return job;
            } finally {
                lock.unlock();
            }
        }

        void close() {
            lock.lock();

            try {
                closed = true;

                /*
                 * Every waiter must be awakened because closing changes both
                 * the producer and consumer predicates.
                 */
                notEmpty.signalAll();
                notFull.signalAll();
            } finally {
                lock.unlock();
            }
        }
    }

    static final class CompilerLicensePool {

        private final Semaphore semaphore;

        CompilerLicensePool(int licenses) {
            if (licenses <= 0) {
                throw new IllegalArgumentException(
                        "At least one compiler license is required"
                );
            }

            /*
             * Fairness can reduce starvation by granting permits roughly in
             * request order. It is not free: fairness can reduce throughput
             * in workloads where strict ordering is unnecessary.
             */
            semaphore = new Semaphore(licenses, true);
        }

        void acquire(long timeoutMillis) throws InterruptedException {
            if (!semaphore.tryAcquire(timeoutMillis, TimeUnit.MILLISECONDS)) {
                throw new IllegalStateException(
                        "No compiler license became available"
                );
            }
        }

        void release() {
            semaphore.release();
        }
    }

    static final class BuildMetrics {

        private final AtomicInteger completed = new AtomicInteger();
        private final AtomicInteger failed = new AtomicInteger();
        private final AtomicInteger active = new AtomicInteger();
        private final AtomicInteger peakActive = new AtomicInteger();

        void started() {
            int current = active.incrementAndGet();

            peakActive.accumulateAndGet(
                    current,
                    Math::max
            );
        }

        void completed() {
            active.decrementAndGet();
            completed.incrementAndGet();
        }

        void failed() {
            active.decrementAndGet();
            failed.incrementAndGet();
        }

        Map<String, Integer> snapshot() {
            return Map.of(
                    "completed", completed.get(),
                    "failed", failed.get(),
                    "peakActive", peakActive.get()
            );
        }
    }

    static final class RepositoryBuildService {

        private final BoundedBuildQueue queue;
        private final CompilerLicensePool licensePool;
        private final BuildMetrics metrics = new BuildMetrics();

        RepositoryBuildService(
                int queueCapacity,
                int compilerLicenses
        ) {
            queue = new BoundedBuildQueue(queueCapacity);
            licensePool = new CompilerLicensePool(compilerLicenses);
        }

        void submit(BuildRequest request) throws InterruptedException {
            BuildJob job = new BuildJob(request);
            queue.put(job);
        }

        void worker(String workerName) {
            while (!Thread.currentThread().isInterrupted()) {
                try {
                    BuildJob job = queue.take();

                    if (job == null) {
                        return;
                    }

                    execute(workerName, job);
                } catch (InterruptedException interrupted) {
                    Thread.currentThread().interrupt();
                    return;
                }
            }
        }

        private void execute(
                String workerName,
                BuildJob job
        ) throws InterruptedException {

            licensePool.acquire(1_000);

            metrics.started();

            try {
                job.transitionTo(BuildState.RUNNING);

                System.out.printf(
                        "%s started build %d for %s:%s%n",
                        workerName,
                        job.request().id(),
                        job.request().repository(),
                        job.request().branch()
                );

                Thread.sleep(
                        20L + (job.request().id() % 4) * 15L
                );

                if (job.request().shouldFail()) {
                    job.fail(FailureReason.COMPILER);
                    metrics.failed();

                    System.out.printf(
                            "Build %d failed%n",
                            job.request().id()
                    );

                    return;
                }

                job.transitionTo(BuildState.SUCCEEDED);
                metrics.completed();

                System.out.printf(
                        "Build %d succeeded%n",
                        job.request().id()
                );
            } catch (InterruptedException interrupted) {
                /*
                 * Interruption is a cooperative cancellation mechanism.
                 * Preserve the interrupt status after releasing resources.
                 */
                throw interrupted;
            } catch (RuntimeException failure) {
                if (job.result().state() == BuildState.RUNNING) {
                    job.fail(FailureReason.VALIDATION);
                }

                metrics.failed();
                throw failure;
            } finally {
                licensePool.release();
            }
        }

        void close() {
            queue.close();
        }

        Map<String, Integer> metrics() {
            return metrics.snapshot();
        }
    }

    static final class BankAccount {

        private final String id;
        private int balance;

        private final ReentrantLock lock = new ReentrantLock();

        BankAccount(String id, int balance) {
            if (id == null || id.isBlank()) {
                throw new IllegalArgumentException("Account ID is required");
            }

            if (balance < 0) {
                throw new IllegalArgumentException(
                        "Balance cannot be negative"
                );
            }

            this.id = id;
            this.balance = balance;
        }

        String id() {
            return id;
        }

        int balance() {
            lock.lock();

            try {
                return balance;
            } finally {
                lock.unlock();
            }
        }
    }

    static final class TransferService {

        static void transfer(
                BankAccount source,
                BankAccount destination,
                int amount
        ) {
            if (source == destination) {
                throw new IllegalArgumentException(
                        "Accounts must be different"
                );
            }

            if (amount <= 0) {
                throw new IllegalArgumentException(
                        "Transfer amount must be positive"
                );
            }

            /*
             * All transfer operations acquire account locks according to the
             * same stable ordering. This eliminates circular wait caused by
             * opposite acquisition order.
             */
            BankAccount first =
                    source.id().compareTo(destination.id()) < 0
                            ? source
                            : destination;

            BankAccount second =
                    first == source
                            ? destination
                            : source;

            first.lock.lock();

            try {
                second.lock.lock();

                try {
                    if (source.balance < amount) {
                        throw new IllegalStateException(
                                "Insufficient funds"
                        );
                    }

                    source.balance -= amount;
                    destination.balance += amount;
                } finally {
                    second.lock.unlock();
                }
            } finally {
                first.lock.unlock();
            }
        }
    }

    private static void runBuildService() throws InterruptedException {
        System.out.println(
                "=== Enterprise build service synchronization ==="
        );

        RepositoryBuildService service =
                new RepositoryBuildService(4, 2);

        List<Thread> workers = new ArrayList<>();

        for (int worker = 1; worker <= 4; worker++) {
            String workerName = "build-worker-" + worker;

            Thread thread = new Thread(
                    () -> service.worker(workerName),
                    workerName
            );

            workers.add(thread);
            thread.start();
        }

        for (long id = 1; id <= 10; id++) {
            service.submit(
                    new BuildRequest(
                            id,
                            id % 2 == 0
                                    ? "payments-service"
                                    : "inventory-service",
                            id % 3 == 0
                                    ? "feature/cache"
                                    : "main",
                            id == 7
                    )
            );
        }

        service.close();

        for (Thread worker : workers) {
            worker.join();
        }

        System.out.println("Metrics: " + service.metrics());
    }

    private static void runDeadlockSafeTransfers()
            throws InterruptedException {

        System.out.println(
                "\n=== Explicit lock ordering ==="
        );

        BankAccount accountA =
                new BankAccount("A", 1_000);

        BankAccount accountB =
                new BankAccount("B", 1_000);

        List<Thread> transfers = new ArrayList<>();

        for (int i = 0; i < 4; i++) {
            transfers.add(
                    new Thread(
                            () -> TransferService.transfer(
                                    accountA,
                                    accountB,
                                    100
                            )
                    )
            );

            transfers.add(
                    new Thread(
                            () -> TransferService.transfer(
                                    accountB,
                                    accountA,
                                    100
                            )
                    )
            );
        }

        for (Thread transfer : transfers) {
            transfer.start();
        }

        for (Thread transfer : transfers) {
            transfer.join();
        }

        System.out.println(
                "Account A balance: " + accountA.balance()
        );

        System.out.println(
                "Account B balance: " + accountB.balance()
        );

        System.out.println(
                "Total balance: "
                        + (accountA.balance() + accountB.balance())
        );
    }

    private static void demonstrateValidation() {
        System.out.println(
                "\n=== Synchronization-specific validation ==="
        );

        try {
            new CompilerLicensePool(0);
        } catch (IllegalArgumentException error) {
            System.out.println(
                    "Rejected invalid semaphore capacity: "
                            + error.getMessage()
            );
        }

        try {
            BuildRequest invalid =
                    new BuildRequest(
                            0,
                            "repository",
                            "main",
                            false
                    );

            System.out.println(invalid);
        } catch (IllegalArgumentException error) {
            System.out.println(
                    "Rejected invalid build request: "
                            + error.getMessage()
            );
        }

        /*
         * EnumSet documents the legal terminal states explicitly. This is
         * useful when a larger enterprise policy needs to distinguish
         * transient states from states that cannot transition further.
         */
        EnumSet<BuildState> terminalStates =
                EnumSet.of(
                        BuildState.SUCCEEDED,
                        BuildState.FAILED
                );

        System.out.println(
                "Terminal states: " + terminalStates
        );
    }

    public static void main(String[] args)
            throws Exception {

        runBuildService();
        runDeadlockSafeTransfers();
        demonstrateValidation();

        System.out.println(
                "\nSynchronization design distinction:"
        );
        System.out.println(
                "A lock controls exclusive ownership of a critical section."
        );
        System.out.println(
                "A semaphore controls the number of concurrent permit holders."
        );
        System.out.println(
                "A condition represents a predicate on protected state."
        );
        System.out.println(
                "A monitor combines state protection with synchronized operations."
        );
        System.out.println(
                "ReentrantLock supplies explicit locking and Condition objects."
        );
        System.out.println(
                "Java synchronized methods and blocks provide monitor-style mutual exclusion."
        );
    }
}
