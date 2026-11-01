import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.NoSuchElementException;
import java.util.PriorityQueue;
import java.util.Random;
import java.util.Set;
import java.util.HashSet;
import java.util.stream.Collectors;

public class HeapPriorityQueueCaseStudy {

    enum HeapType {
        MIN,
        MAX
    }

    static final class BinaryHeap<T> {
        private final List<T> data = new ArrayList<>();
        private final Comparator<? super T> comparator;

        BinaryHeap(Comparator<? super T> comparator) {
            this.comparator = comparator;
        }

        int size() {
            return data.size();
        }

        boolean isEmpty() {
            return data.isEmpty();
        }

        private int parent(int index) {
            return (index - 1) / 2;
        }

        private int left(int index) {
            return index * 2 + 1;
        }

        private int right(int index) {
            return index * 2 + 2;
        }

        private void swap(int a, int b) {
            T value = data.get(a);
            data.set(a, data.get(b));
            data.set(b, value);
        }

        private void siftUp(int index) {
            while (index > 0) {
                int parent = parent(index);

                if (comparator.compare(data.get(index), data.get(parent)) >= 0) {
                    return;
                }

                swap(index, parent);
                index = parent;
            }
        }

        private void siftDown(int index) {
            while (true) {
                int left = left(index);
                int right = right(index);
                int best = index;

                if (
                    left < size()
                    && comparator.compare(data.get(left), data.get(best)) < 0
                ) {
                    best = left;
                }

                if (
                    right < size()
                    && comparator.compare(data.get(right), data.get(best)) < 0
                ) {
                    best = right;
                }

                if (best == index) {
                    return;
                }

                swap(index, best);
                index = best;
            }
        }

        void add(T value) {
            if (value == null) {
                throw new IllegalArgumentException("null values are not allowed");
            }

            data.add(value);
            siftUp(size() - 1);
        }

        T peek() {
            if (isEmpty()) {
                throw new NoSuchElementException("empty heap");
            }

            return data.get(0);
        }

        T remove() {
            if (isEmpty()) {
                throw new NoSuchElementException("empty heap");
            }

            T result = data.get(0);
            T last = data.remove(size() - 1);

            if (!isEmpty()) {
                data.set(0, last);
                siftDown(0);
            }

            return result;
        }

        void heapify(List<T> values) {
            data.clear();

            for (T value : values) {
                if (value == null) {
                    throw new IllegalArgumentException("null values are not allowed");
                }
                data.add(value);
            }

            for (int i = size() / 2 - 1; i >= 0; i--) {
                siftDown(i);
            }
        }

        T replaceRoot(T value) {
            if (isEmpty()) {
                throw new NoSuchElementException("empty heap");
            }

            T old = data.get(0);
            data.set(0, value);
            siftDown(0);
            return old;
        }

        boolean validate() {
            for (int child = 1; child < size(); child++) {
                int parent = parent(child);

                if (comparator.compare(data.get(child), data.get(parent)) < 0) {
                    return false;
                }
            }

            return true;
        }
    }

    record Job(
        String name,
        int priority,
        int duration,
        long sequence
    ) {
        Job {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("job name is required");
            }

            if (priority < 0) {
                throw new IllegalArgumentException(
                    "priority cannot be negative"
                );
            }

            if (duration <= 0) {
                throw new IllegalArgumentException(
                    "duration must be positive"
                );
            }
        }
    }

    interface SchedulingPolicy {
        boolean accepts(Job job);
    }

    static final class ProductionSchedulingPolicy
        implements SchedulingPolicy {

        private final int maximumDuration;

        ProductionSchedulingPolicy(int maximumDuration) {
            if (maximumDuration <= 0) {
                throw new IllegalArgumentException(
                    "maximum duration must be positive"
                );
            }

            this.maximumDuration = maximumDuration;
        }

        @Override
        public boolean accepts(Job job) {
            return job.duration() <= maximumDuration;
        }
    }

    static final class SchedulerService {
        private final PriorityQueue<Job> queue;
        private final SchedulingPolicy policy;
        private long sequence = 0;

        SchedulerService(SchedulingPolicy policy) {
            this.policy = policy;

            this.queue = new PriorityQueue<>(
                Comparator
                    .comparingInt(Job::priority)
                    .thenComparingLong(Job::sequence)
            );
        }

        void submit(String name, int priority, int duration) {
            Job job = new Job(name, priority, duration, sequence++);

            if (!policy.accepts(job)) {
                throw new IllegalStateException(
                    "job rejected by scheduling policy: " + name
                );
            }

            queue.offer(job);
        }

        List<Job> executeAll() {
            List<Job> completed = new ArrayList<>();

            while (!queue.isEmpty()) {
                completed.add(queue.poll());
            }

            return completed;
        }
    }

    static List<Integer> topK(List<Integer> values, int k) {
        if (values == null || values.isEmpty()) {
            return List.of();
        }

        if (k < 1 || k > values.size()) {
            throw new IllegalArgumentException(
                "k must be between 1 and values.size()"
            );
        }

        PriorityQueue<Integer> heap = new PriorityQueue<>();

        for (Integer value : values) {
            if (value == null) {
                throw new IllegalArgumentException("null value");
            }

            if (heap.size() < k) {
                heap.offer(value);
            } else if (value > heap.peek()) {
                heap.poll();
                heap.offer(value);
            }
        }

        List<Integer> result = new ArrayList<>(heap);
        result.sort(Comparator.reverseOrder());
        return result;
    }

    static void heapDemo() {
        System.out.println("=== Custom Min Heap ===");

        BinaryHeap<Integer> heap =
            new BinaryHeap<>(Comparator.naturalOrder());

        heap.heapify(List.of(9, 4, 7, 1, 3, 8, 2));

        System.out.println("Minimum: " + heap.peek());
        System.out.println("Valid: " + heap.validate());

        List<Integer> sorted = new ArrayList<>();

        while (!heap.isEmpty()) {
            sorted.add(heap.remove());
        }

        System.out.println("Ascending: " + sorted);

        System.out.println("\n=== Custom Max Heap ===");

        BinaryHeap<Integer> maxHeap =
            new BinaryHeap<>(Comparator.reverseOrder());

        maxHeap.heapify(List.of(9, 4, 7, 1, 3, 8, 2));

        List<Integer> descending = new ArrayList<>();

        while (!maxHeap.isEmpty()) {
            descending.add(maxHeap.remove());
        }

        System.out.println("Descending: " + descending);
    }

    static void enterpriseSchedulerDemo() {
        System.out.println("\n=== Enterprise Scheduler ===");

        SchedulerService service =
            new SchedulerService(new ProductionSchedulingPolicy(60));

        service.submit("security-alert", 0, 5);
        service.submit("incident-analysis", 1, 30);
        service.submit("database-backup", 2, 45);
        service.submit("report-generation", 3, 20);

        List<Job> executionOrder = service.executeAll();

        executionOrder.forEach(job ->
            System.out.println(
                job.name()
                    + " priority=" + job.priority()
                    + " duration=" + job.duration()
            )
        );

        try {
            service.submit("invalid-job", 1, 100);
        } catch (IllegalStateException ex) {
            System.out.println("Rejected: " + ex.getMessage());
        }
    }

    static void topKDemo() {
        System.out.println("\n=== Top-K ===");

        List<Integer> values =
            List.of(17, 4, 29, 11, 35, 8, 42, 19);

        System.out.println("Top three: " + topK(values, 3));
    }

    static void standardPriorityQueueDemo() {
        System.out.println("\n=== Java PriorityQueue ===");

        PriorityQueue<Integer> minQueue = new PriorityQueue<>();
        minQueue.addAll(List.of(8, 3, 7, 1, 5));

        List<Integer> ascending = new ArrayList<>();

        while (!minQueue.isEmpty()) {
            ascending.add(minQueue.poll());
        }

        System.out.println("Ascending: " + ascending);

        PriorityQueue<Integer> maxQueue =
            new PriorityQueue<>(Comparator.reverseOrder());

        maxQueue.addAll(List.of(8, 3, 7, 1, 5));

        System.out.println(
            "Maximum: " + maxQueue.peek()
        );
    }

    static void edgeCaseDemo() {
        System.out.println("\n=== Edge Cases ===");

        BinaryHeap<Integer> heap =
            new BinaryHeap<>(Comparator.naturalOrder());

        try {
            heap.remove();
        } catch (NoSuchElementException ex) {
            System.out.println("Expected failure: " + ex.getMessage());
        }

        try {
            topK(List.of(1, 2, 3), 0);
        } catch (IllegalArgumentException ex) {
            System.out.println("Invalid k: " + ex.getMessage());
        }

        Set<Integer> uniqueValues =
            new HashSet<>(List.of(4, 4, 2, 7, 2));

        System.out.println("Unique values: " + uniqueValues);
    }

    public static void main(String[] args) {
        heapDemo();
        enterpriseSchedulerDemo();
        topKDemo();
        standardPriorityQueueDemo();
        edgeCaseDemo();
    }
}
