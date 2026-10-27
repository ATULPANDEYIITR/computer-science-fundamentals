import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.Deque;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.PriorityQueue;
import java.util.Set;

public class QueueEnterpriseModel {

    static class QueueEmptyException extends RuntimeException {
        QueueEmptyException(String message) {
            super(message);
        }
    }

    static class QueueFullException extends RuntimeException {
        QueueFullException(String message) {
            super(message);
        }
    }

    static class ValidationException extends RuntimeException {
        ValidationException(String message) {
            super(message);
        }
    }

    interface QueueLike<T> {
        void enqueue(T value);
        T dequeue();
        T peek();
        boolean isEmpty();
        int size();
    }

    static final class FifoQueue<T> implements QueueLike<T> {
        private final Deque<T> data = new ArrayDeque<>();

        @Override
        public void enqueue(T value) {
            data.addLast(Objects.requireNonNull(value, "queue values cannot be null"));
        }

        @Override
        public T dequeue() {
            if (data.isEmpty()) {
                throw new QueueEmptyException("FIFO queue is empty");
            }
            return data.removeFirst();
        }

        @Override
        public T peek() {
            if (data.isEmpty()) {
                throw new QueueEmptyException("FIFO queue is empty");
            }
            return data.peekFirst();
        }

        @Override
        public boolean isEmpty() {
            return data.isEmpty();
        }

        @Override
        public int size() {
            return data.size();
        }
    }

    static final class CircularQueue<T> implements QueueLike<T> {
        private final Object[] buffer;
        private int head;
        private int tail;
        private int size;

        CircularQueue(int capacity) {
            if (capacity <= 0) {
                throw new ValidationException("capacity must be positive");
            }
            buffer = new Object[capacity];
        }

        @Override
        public void enqueue(T value) {
            Objects.requireNonNull(value, "queue values cannot be null");

            if (isFull()) {
                throw new QueueFullException("circular queue is full");
            }

            buffer[tail] = value;
            tail = (tail + 1) % buffer.length;
            size++;
        }

        @SuppressWarnings("unchecked")
        @Override
        public T dequeue() {
            if (isEmpty()) {
                throw new QueueEmptyException("circular queue is empty");
            }

            T value = (T) buffer[head];
            buffer[head] = null;
            head = (head + 1) % buffer.length;
            size--;
            return value;
        }

        @SuppressWarnings("unchecked")
        @Override
        public T peek() {
            if (isEmpty()) {
                throw new QueueEmptyException("circular queue is empty");
            }
            return (T) buffer[head];
        }

        boolean isFull() {
            return size == buffer.length;
        }

        @Override
        public boolean isEmpty() {
            return size == 0;
        }

        @Override
        public int size() {
            return size;
        }

        @SuppressWarnings("unchecked")
        List<T> snapshot() {
            List<T> result = new ArrayList<>(size);

            for (int i = 0; i < size; i++) {
                result.add((T) buffer[(head + i) % buffer.length]);
            }

            return List.copyOf(result);
        }
    }

    static final class DequeModel<T> {
        private final Deque<T> data = new ArrayDeque<>();

        void pushFront(T value) {
            data.addFirst(Objects.requireNonNull(value));
        }

        void pushBack(T value) {
            data.addLast(Objects.requireNonNull(value));
        }

        T popFront() {
            if (data.isEmpty()) {
                throw new QueueEmptyException("deque is empty");
            }
            return data.removeFirst();
        }

        T popBack() {
            if (data.isEmpty()) {
                throw new QueueEmptyException("deque is empty");
            }
            return data.removeLast();
        }

        T peekFront() {
            if (data.isEmpty()) {
                throw new QueueEmptyException("deque is empty");
            }
            return data.peekFirst();
        }

        T peekBack() {
            if (data.isEmpty()) {
                throw new QueueEmptyException("deque is empty");
            }
            return data.peekLast();
        }
    }

    record Job(int id, String name, int priority) {
        Job {
            if (id <= 0) {
                throw new ValidationException("job id must be positive");
            }
            if (name == null || name.isBlank()) {
                throw new ValidationException("job name must not be blank");
            }
            if (priority < 0) {
                throw new ValidationException("priority cannot be negative");
            }
        }
    }

    enum JobState {
        QUEUED,
        RUNNING,
        COMPLETED,
        FAILED
    }

    record JobStatus(Job job, JobState state) {}

    interface DispatchPolicy {
        Comparator<Job> comparator();
    }

    static final class PriorityDispatchPolicy implements DispatchPolicy {
        @Override
        public Comparator<Job> comparator() {
            return Comparator
                .comparingInt(Job::priority)
                .thenComparingInt(Job::id);
        }
    }

    static final class EnterpriseJobService {
        private final CircularQueue<Job> intake;
        private final PriorityQueue<Job> ready;
        private final Map<Integer, JobState> states = new HashMap<>();
        private final Set<Integer> registeredIds = new HashSet<>();

        EnterpriseJobService(int capacity, DispatchPolicy policy) {
            intake = new CircularQueue<>(capacity);
            ready = new PriorityQueue<>(policy.comparator());
        }

        void submit(Job job) {
            Objects.requireNonNull(job, "job cannot be null");

            if (!registeredIds.add(job.id())) {
                throw new ValidationException("duplicate job id: " + job.id());
            }

            intake.enqueue(job);
            states.put(job.id(), JobState.QUEUED);
        }

        void stage() {
            while (!intake.isEmpty()) {
                ready.add(intake.dequeue());
            }
        }

        Optional<Job> dispatch() {
            Job job = ready.poll();

            if (job == null) {
                return Optional.empty();
            }

            transition(job.id(), JobState.RUNNING);
            return Optional.of(job);
        }

        void complete(int jobId) {
            transition(jobId, JobState.COMPLETED);
        }

        void fail(int jobId) {
            transition(jobId, JobState.FAILED);
        }

        JobState state(int jobId) {
            JobState state = states.get(jobId);

            if (state == null) {
                throw new ValidationException("unknown job id: " + jobId);
            }

            return state;
        }

        List<JobStatus> statusReport() {
            return states.entrySet()
                .stream()
                .map(entry -> {
                    Job job = findJob(entry.getKey());
                    return new JobStatus(job, entry.getValue());
                })
                .toList();
        }

        private final Map<Integer, Job> jobs = new HashMap<>();

        private Job findJob(int id) {
            Job job = jobs.get(id);

            if (job == null) {
                throw new ValidationException("job metadata unavailable");
            }

            return job;
        }

        private void transition(int jobId, JobState target) {
            JobState current = state(jobId);

            boolean valid = switch (current) {
                case QUEUED -> target == JobState.RUNNING;
                case RUNNING -> target == JobState.COMPLETED
                    || target == JobState.FAILED;
                case COMPLETED, FAILED -> false;
            };

            if (!valid) {
                throw new ValidationException(
                    "invalid transition " + current + " -> " + target
                );
            }

            states.put(jobId, target);
        }

        void registerJobMetadata(Job job) {
            jobs.put(job.id(), job);
        }
    }

    public static void main(String[] args) {
        System.out.println("=== FIFO Queue ===");

        FifoQueue<String> fifo = new FifoQueue<>();
        fifo.enqueue("request-1");
        fifo.enqueue("request-2");
        fifo.enqueue("request-3");

        System.out.println(fifo.dequeue());
        System.out.println(fifo.peek());

        System.out.println("\n=== Circular Queue ===");

        CircularQueue<Integer> circular = new CircularQueue<>(3);
        circular.enqueue(10);
        circular.enqueue(20);
        circular.enqueue(30);

        circular.dequeue();
        circular.enqueue(40);

        System.out.println(circular.snapshot());

        try {
            circular.enqueue(50);
            circular.enqueue(60);
        } catch (QueueFullException error) {
            System.out.println("expected failure: " + error.getMessage());
        }

        System.out.println("\n=== Deque ===");

        DequeModel<String> deque = new DequeModel<>();
        deque.pushFront("security");
        deque.pushBack("build");
        deque.pushFront("validation");
        deque.pushBack("deployment");

        System.out.println(deque.popFront());
        System.out.println(deque.popBack());
        System.out.println(deque.peekFront());

        System.out.println("\n=== Enterprise Job Service ===");

        EnterpriseJobService service =
            new EnterpriseJobService(4, new PriorityDispatchPolicy());

        List<Job> jobs = List.of(
            new Job(101, "documentation", 30),
            new Job(102, "security-scan", 5),
            new Job(103, "release-build", 10),
            new Job(104, "unit-tests", 20)
        );

        for (Job job : jobs) {
            service.registerJobMetadata(job);
            service.submit(job);
        }

        service.stage();

        while (true) {
            Optional<Job> next = service.dispatch();

            if (next.isEmpty()) {
                break;
            }

            Job job = next.get();

            System.out.printf(
                "dispatch id=%d name=%s priority=%d%n",
                job.id(),
                job.name(),
                job.priority()
            );

            if (job.id() == 102) {
                service.fail(job.id());
            } else {
                service.complete(job.id());
            }

            System.out.println("state=" + service.state(job.id()));
        }

        System.out.println("\n=== Policy and State Validation ===");

        try {
            service.complete(999);
        } catch (ValidationException error) {
            System.out.println("expected failure: " + error.getMessage());
        }

        try {
            service.complete(101);
        } catch (ValidationException error) {
            System.out.println("expected transition failure: " + error.getMessage());
        }

        System.out.println("\n=== Stream-Based Report ===");

        service.statusReport()
            .stream()
            .sorted(Comparator.comparingInt(status -> status.job().id()))
            .forEach(status ->
                System.out.printf(
                    "%d %-18s %s%n",
                    status.job().id(),
                    status.job().name(),
                    status.state()
                )
            );

        System.out.println("\n=== Assertions ===");

        FifoQueue<Integer> q = new FifoQueue<>();
        q.enqueue(1);
        q.enqueue(2);
        assert q.dequeue() == 1;
        assert q.dequeue() == 2;

        CircularQueue<Integer> cq = new CircularQueue<>(2);
        cq.enqueue(1);
        cq.enqueue(2);
        assert cq.dequeue() == 1;
        cq.enqueue(3);
        assert cq.snapshot().equals(List.of(2, 3));

        DequeModel<Integer> dm = new DequeModel<>();
        dm.pushBack(2);
        dm.pushFront(1);
        dm.pushBack(3);
        assert dm.popFront() == 1;
        assert dm.popBack() == 3;

        System.out.println("all queue invariants passed");
    }
}
