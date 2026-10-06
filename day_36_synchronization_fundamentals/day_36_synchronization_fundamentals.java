/*
 * Synchronization Fundamentals: Enterprise Job Reservation Service
 *
 * Java 17+
 *
 * Demonstrates:
 *   - race conditions
 *   - critical sections
 *   - synchronized mutual exclusion
 *   - ReentrantLock
 *   - condition variables
 *   - atomic counters
 *   - explicit domain validation
 *   - multi-resource locking
 *
 * Compile:
 *   javac SynchronizationFundamentals.java
 *
 * Run:
 *   java SynchronizationFundamentals
 */

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;
import java.util.Queue;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.ReentrantLock;

public class SynchronizationFundamentals {

    private static final class UnsafeCounter {
        private int value;

        void increment() {
            int observed = value;

            try {
                Thread.sleep(1);
            } catch (InterruptedException exception) {
                Thread.currentThread().interrupt();
                throw new IllegalStateException("Counter worker interrupted", exception);
            }

            value = observed + 1;
        }

        int getValue() {
            return value;
        }
    }

    private static final class SafeCounter {
        private int value;

        /*
         * synchronized places mutual exclusion around the method. Only one
         * thread can execute this method for a given SafeCounter instance.
         */
        synchronized void increment() {
            value++;
        }

        synchronized int getValue() {
            return value;
        }
    }

    private static void demonstrateRaceCondition() throws InterruptedException {
        System.out.println("\n=== Race Condition ===");

        UnsafeCounter counter = new UnsafeCounter();
        List<Thread> workers = new ArrayList<>();

        int threadCount = 8;
        int incrementsPerThread = 500;

        for (int index = 0; index < threadCount; index++) {
            Thread worker = new Thread(() -> {
                for (int iteration = 0; iteration < incrementsPerThread; iteration++) {
                    counter.increment();
                }
            });

            workers.add(worker);
            worker.start();
        }

        for (Thread worker : workers) {
            worker.join();
        }

        int expected = threadCount * incrementsPerThread;

        System.out.println("Expected: " + expected);
        System.out.println("Actual:   " + counter.getValue());

        if (counter.getValue() != expected) {
            System.out.println("The read-modify-write critical section lost updates.");
        }
    }

    private static void demonstrateMutualExclusion() throws InterruptedException {
        System.out.println("\n=== Mutual Exclusion ===");

        SafeCounter counter = new SafeCounter();
        List<Thread> workers = new ArrayList<>();

        int threadCount = 8;
        int incrementsPerThread = 500;

        for (int index = 0; index < threadCount; index++) {
            Thread worker = new Thread(() -> {
                for (int iteration = 0; iteration < incrementsPerThread; iteration++) {
                    counter.increment();
                }
            });

            workers.add(worker);
            worker.start();
        }

        for (Thread worker : workers) {
            worker.join();
        }

        System.out.println("Expected: " + threadCount * incrementsPerThread);
        System.out.println("Actual:   " + counter.getValue());
    }

    private enum ReservationStatus {
        ACCEPTED,
        REJECTED_CAPACITY
    }

    private static final class ReservationService {
        private final ReentrantLock lock = new ReentrantLock();
        private int remainingCapacity;

        ReservationService(int capacity) {
            if (capacity < 0) {
                throw new IllegalArgumentException("Capacity cannot be negative.");
            }

            remainingCapacity = capacity;
        }

        ReservationStatus reserve(int quantity) {
            if (quantity <= 0) {
                throw new IllegalArgumentException("Reservation must be positive.");
            }

            lock.lock();

            try {
                /*
                 * The capacity check and decrement form one critical section.
                 * Releasing the lock between these operations would permit two
                 * callers to reserve the same remaining capacity.
                 */
                if (quantity > remainingCapacity) {
                    return ReservationStatus.REJECTED_CAPACITY;
                }

                remainingCapacity -= quantity;
                return ReservationStatus.ACCEPTED;
            } finally {
                lock.unlock();
            }
        }

        int remainingCapacity() {
            lock.lock();

            try {
                return remainingCapacity;
            } finally {
                lock.unlock();
            }
        }
    }

    private static void demonstrateReservationService() throws InterruptedException {
        System.out.println("\n=== Enterprise Reservation Service ===");

        ReservationService service = new ReservationService(100);
        List<Thread> workers = new ArrayList<>();
        AtomicInteger accepted = new AtomicInteger();

        for (int index = 0; index < 40; index++) {
            Thread worker = new Thread(() -> {
                ReservationStatus status = service.reserve(3);

                if (status == ReservationStatus.ACCEPTED) {
                    accepted.incrementAndGet();
                }
            });

            workers.add(worker);
            worker.start();
        }

        for (Thread worker : workers) {
            worker.join();
        }

        System.out.println("Accepted reservations: " + accepted.get());
        System.out.println("Remaining capacity:    " + service.remainingCapacity());
    }

    private static final class JobQueue {
        private final Queue<String> jobs = new ArrayDeque<>();
        private final ReentrantLock lock = new ReentrantLock();
        private final Condition jobAvailable = lock.newCondition();

        private boolean shuttingDown;

        void submit(String job) {
            if (job == null || job.isBlank()) {
                throw new IllegalArgumentException("Job cannot be empty.");
            }

            lock.lock();

            try {
                if (shuttingDown) {
                    throw new IllegalStateException("Queue is shutting down.");
                }

                jobs.add(job);
                jobAvailable.signal();
            } finally {
                lock.unlock();
            }
        }

        String take() throws InterruptedException {
            lock.lock();

            try {
                while (jobs.isEmpty() && !shuttingDown) {
                    /*
                     * await releases the lock while waiting and reacquires it
                     * before returning. The while loop protects against
                     * spurious wakeups and state changes by competing threads.
                     */
                    jobAvailable.await();
                }

                if (jobs.isEmpty() && shuttingDown) {
                    return null;
                }

                return jobs.remove();
            } finally {
                lock.unlock();
            }
        }

        void shutdown() {
            lock.lock();

            try {
                shuttingDown = true;
                jobAvailable.signalAll();
            } finally {
                lock.unlock();
            }
        }
    }

    private static void demonstrateProducerConsumer() throws InterruptedException {
        System.out.println("\n=== Producer-Consumer Coordination ===");

        JobQueue queue = new JobQueue();
        AtomicInteger processed = new AtomicInteger();

        Thread consumer = new Thread(() -> {
            try {
                while (true) {
                    String job = queue.take();

                    if (job == null) {
                        return;
                    }

                    processed.incrementAndGet();
                }
            } catch (InterruptedException exception) {
                Thread.currentThread().interrupt();
            }
        });

        consumer.start();

        for (int index = 0; index < 50; index++) {
            queue.submit("repository-analysis-" + index);
        }

        queue.shutdown();
        consumer.join();

        System.out.println("Processed jobs: " + processed.get());
    }

    private static final class Account {
        private final int id;
        private int balance;
        private final ReentrantLock lock = new ReentrantLock();

        Account(int id, int balance) {
            if (balance < 0) {
                throw new IllegalArgumentException("Balance cannot be negative.");
            }

            this.id = id;
            this.balance = balance;
        }
    }

    private static boolean transfer(
            Account source,
            Account target,
            int amount
    ) {
        if (source == target) {
            throw new IllegalArgumentException("Accounts must differ.");
        }

        if (amount <= 0) {
            throw new IllegalArgumentException("Transfer amount must be positive.");
        }

        Account first = source.id < target.id ? source : target;
        Account second = source.id < target.id ? target : source;

        /*
         * Every transfer follows the same lock ordering. This prevents the
         * classic cycle where one thread holds A and waits for B while another
         * holds B and waits for A.
         */
        first.lock.lock();

        try {
            second.lock.lock();

            try {
                if (source.balance < amount) {
                    return false;
                }

                source.balance -= amount;
                target.balance += amount;
                return true;
            } finally {
                second.lock.unlock();
            }
        } finally {
            first.lock.unlock();
        }
    }

    private static int total(Account first, Account second) {
        Account lower = first.id < second.id ? first : second;
        Account higher = first.id < second.id ? second : first;

        lower.lock.lock();

        try {
            higher.lock.lock();

            try {
                return first.balance + second.balance;
            } finally {
                higher.lock.unlock();
            }
        } finally {
            lower.lock.unlock();
        }
    }

    private static void demonstrateDeadlockAvoidance() throws InterruptedException {
        System.out.println("\n=== Multiple Locks and Deadlock Avoidance ===");

        Account first = new Account(1, 1_000);
        Account second = new Account(2, 1_000);

        List<Thread> workers = new ArrayList<>();

        for (int index = 0; index < 100; index++) {
            workers.add(new Thread(() -> transfer(first, second, 1)));
            workers.add(new Thread(() -> transfer(second, first, 1)));
        }

        for (Thread worker : workers) {
            worker.start();
        }

        for (Thread worker : workers) {
            worker.join();
        }

        System.out.println("Account 1: " + first.balance);
        System.out.println("Account 2: " + second.balance);
        System.out.println("Total:     " + total(first, second));
    }

    private static void demonstrateTimedLock() throws InterruptedException {
        System.out.println("\n=== Timed Lock ===");

        ReentrantLock lock = new ReentrantLock();
        lock.lock();

        Thread worker = new Thread(() -> {
            try {
                if (lock.tryLock(50, TimeUnit.MILLISECONDS)) {
                    try {
                        System.out.println("Worker acquired the lock.");
                    } finally {
                        lock.unlock();
                    }
                } else {
                    System.out.println("Worker timed out instead of waiting indefinitely.");
                }
            } catch (InterruptedException exception) {
                Thread.currentThread().interrupt();
                System.out.println("Worker was interrupted.");
            }
        });

        worker.start();
        worker.join();

        lock.unlock();
    }

    private static void demonstrateAtomicCounter() throws InterruptedException {
        System.out.println("\n=== Atomic Counter ===");

        AtomicInteger counter = new AtomicInteger();

        int threadCount = 8;
        int incrementsPerThread = 10_000;

        List<Thread> workers = new ArrayList<>();

        for (int index = 0; index < threadCount; index++) {
            workers.add(new Thread(() -> {
                for (int iteration = 0; iteration < incrementsPerThread; iteration++) {
                    counter.incrementAndGet();
                }
            }));
        }

        for (Thread worker : workers) {
            worker.start();
        }

        for (Thread worker : workers) {
            worker.join();
        }

        System.out.println("Expected: " + threadCount * incrementsPerThread);
        System.out.println("Actual:   " + counter.get());
    }

    public static void main(String[] args) {
        try {
            System.out.println("Synchronization Fundamentals");
            System.out.println("Race Conditions | Critical Sections | Mutual Exclusion");

            demonstrateRaceCondition();
            demonstrateMutualExclusion();
            demonstrateReservationService();
            demonstrateProducerConsumer();
            demonstrateDeadlockAvoidance();
            demonstrateTimedLock();
            demonstrateAtomicCounter();

            System.out.println("\nEnterprise synchronization case study completed.");
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
            System.err.println("Main thread interrupted: " + exception.getMessage());
        }
    }
}
