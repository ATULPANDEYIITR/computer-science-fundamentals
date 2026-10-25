import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/**
 * Enterprise-oriented linked-list domain model.
 *
 * The program models three structures separately because their pointer
 * invariants and operational trade-offs are different.
 */
public class LinkedListEnterpriseDemo {

    enum ListKind {
        SINGLY,
        DOUBLY,
        CIRCULAR
    }

    static final class InvalidIndexException extends RuntimeException {
        InvalidIndexException(String message) {
            super(message);
        }
    }

    static final class SinglyNode<T> {
        private final T value;
        private SinglyNode<T> next;

        SinglyNode(T value) {
            this.value = value;
        }
    }

    static final class DoublyNode<T> {
        private final T value;
        private DoublyNode<T> previous;
        private DoublyNode<T> next;

        DoublyNode(T value) {
            this.value = value;
        }
    }

    interface LinkedSequence<T> {
        void addFirst(T value);
        void addLast(T value);
        T remove(int index);
        T get(int index);
        int size();
        List<T> toList();
    }

    static final class SinglyLinkedList<T> implements LinkedSequence<T> {
        private SinglyNode<T> head;
        private SinglyNode<T> tail;
        private int size;

        @Override
        public void addFirst(T value) {
            Objects.requireNonNull(value, "value cannot be null");

            SinglyNode<T> node = new SinglyNode<>(value);
            node.next = head;
            head = node;

            if (tail == null) {
                tail = node;
            }

            size++;
        }

        @Override
        public void addLast(T value) {
            Objects.requireNonNull(value, "value cannot be null");

            SinglyNode<T> node = new SinglyNode<>(value);

            if (tail == null) {
                head = tail = node;
            } else {
                tail.next = node;
                tail = node;
            }

            size++;
        }

        @Override
        public T get(int index) {
            return nodeAt(index).value;
        }

        private SinglyNode<T> nodeAt(int index) {
            validateIndex(index);

            SinglyNode<T> current = head;

            for (int i = 0; i < index; i++) {
                current = current.next;
            }

            return current;
        }

        @Override
        public T remove(int index) {
            validateIndex(index);

            if (index == 0) {
                T value = head.value;
                head = head.next;
                size--;

                if (size == 0) {
                    tail = null;
                }

                return value;
            }

            SinglyNode<T> previous = nodeAt(index - 1);
            SinglyNode<T> removed = previous.next;

            previous.next = removed.next;

            if (removed == tail) {
                tail = previous;
            }

            size--;
            return removed.value;
        }

        public void reverse() {
            SinglyNode<T> previous = null;
            SinglyNode<T> current = head;

            tail = head;

            while (current != null) {
                SinglyNode<T> following = current.next;
                current.next = previous;
                previous = current;
                current = following;
            }

            head = previous;
        }

        @Override
        public int size() {
            return size;
        }

        @Override
        public List<T> toList() {
            List<T> result = new ArrayList<>(size);
            SinglyNode<T> current = head;

            while (current != null) {
                result.add(current.value);
                current = current.next;
            }

            return List.copyOf(result);
        }

        private void validateIndex(int index) {
            if (index < 0 || index >= size) {
                throw new InvalidIndexException("Invalid singly-list index: " + index);
            }
        }
    }

    static final class DoublyLinkedList<T> implements LinkedSequence<T> {
        private DoublyNode<T> head;
        private DoublyNode<T> tail;
        private int size;

        @Override
        public void addFirst(T value) {
            Objects.requireNonNull(value, "value cannot be null");

            DoublyNode<T> node = new DoublyNode<>(value);
            node.next = head;

            if (head == null) {
                head = tail = node;
            } else {
                head.previous = node;
                head = node;
            }

            size++;
        }

        @Override
        public void addLast(T value) {
            Objects.requireNonNull(value, "value cannot be null");

            DoublyNode<T> node = new DoublyNode<>(value);
            node.previous = tail;

            if (tail == null) {
                head = tail = node;
            } else {
                tail.next = node;
                tail = node;
            }

            size++;
        }

        private DoublyNode<T> nodeAt(int index) {
            validateIndex(index);

            if (index <= size / 2) {
                DoublyNode<T> current = head;

                for (int i = 0; i < index; i++) {
                    current = current.next;
                }

                return current;
            }

            DoublyNode<T> current = tail;

            for (int i = size - 1; i > index; i--) {
                current = current.previous;
            }

            return current;
        }

        @Override
        public T get(int index) {
            return nodeAt(index).value;
        }

        @Override
        public T remove(int index) {
            DoublyNode<T> node = nodeAt(index);

            if (node.previous == null) {
                head = node.next;
            } else {
                node.previous.next = node.next;
            }

            if (node.next == null) {
                tail = node.previous;
            } else {
                node.next.previous = node.previous;
            }

            size--;
            return node.value;
        }

        public List<T> backward() {
            List<T> result = new ArrayList<>(size);
            DoublyNode<T> current = tail;

            while (current != null) {
                result.add(current.value);
                current = current.previous;
            }

            return List.copyOf(result);
        }

        @Override
        public int size() {
            return size;
        }

        @Override
        public List<T> toList() {
            List<T> result = new ArrayList<>(size);
            DoublyNode<T> current = head;

            while (current != null) {
                result.add(current.value);
                current = current.next;
            }

            return List.copyOf(result);
        }

        private void validateIndex(int index) {
            if (index < 0 || index >= size) {
                throw new InvalidIndexException("Invalid doubly-list index: " + index);
            }
        }
    }

    static final class CircularLinkedList<T> implements LinkedSequence<T> {
        private SinglyNode<T> head;
        private SinglyNode<T> tail;
        private int size;

        @Override
        public void addFirst(T value) {
            Objects.requireNonNull(value, "value cannot be null");

            if (size == 0) {
                addLast(value);
                return;
            }

            SinglyNode<T> node = new SinglyNode<>(value);
            node.next = head;
            head = node;
            tail.next = head;
            size++;
        }

        @Override
        public void addLast(T value) {
            Objects.requireNonNull(value, "value cannot be null");

            SinglyNode<T> node = new SinglyNode<>(value);

            if (size == 0) {
                head = tail = node;
                node.next = node;
            } else {
                node.next = head;
                tail.next = node;
                tail = node;
            }

            size++;
        }

        private SinglyNode<T> nodeAt(int index) {
            validateIndex(index);

            SinglyNode<T> current = head;

            for (int i = 0; i < index; i++) {
                current = current.next;
            }

            return current;
        }

        @Override
        public T get(int index) {
            return nodeAt(index).value;
        }

        @Override
        public T remove(int index) {
            validateIndex(index);

            if (size == 1) {
                T value = head.value;
                head = tail = null;
                size = 0;
                return value;
            }

            if (index == 0) {
                T value = head.value;
                head = head.next;
                tail.next = head;
                size--;
                return value;
            }

            SinglyNode<T> previous = nodeAt(index - 1);
            SinglyNode<T> removed = previous.next;
            previous.next = removed.next;

            if (removed == tail) {
                tail = previous;
            }

            size--;
            return removed.value;
        }

        public void rotate(int steps) {
            if (size == 0) {
                return;
            }

            int normalized = Math.floorMod(steps, size);

            for (int i = 0; i < normalized; i++) {
                head = head.next;
                tail = tail.next;
            }
        }

        @Override
        public int size() {
            return size;
        }

        @Override
        public List<T> toList() {
            List<T> result = new ArrayList<>(size);
            SinglyNode<T> current = head;

            for (int i = 0; i < size; i++) {
                result.add(current.value);
                current = current.next;
            }

            return List.copyOf(result);
        }

        private void validateIndex(int index) {
            if (index < 0 || index >= size) {
                throw new InvalidIndexException("Invalid circular-list index: " + index);
            }
        }
    }

    record ListReport(
            ListKind kind,
            int size,
            List<Integer> values,
            String primaryStrength
    ) {}

    static final class LinkedListService {
        static <T> List<T> mergeSorted(
                LinkedSequence<T> first,
                LinkedSequence<T> second,
                java.util.Comparator<T> comparator
        ) {
            List<T> result = new ArrayList<>();
            int left = 0;
            int right = 0;
            List<T> a = first.toList();
            List<T> b = second.toList();

            while (left < a.size() && right < b.size()) {
                if (comparator.compare(a.get(left), b.get(right)) <= 0) {
                    result.add(a.get(left++));
                } else {
                    result.add(b.get(right++));
                }
            }

            while (left < a.size()) {
                result.add(a.get(left++));
            }

            while (right < b.size()) {
                result.add(b.get(right++));
            }

            return List.copyOf(result);
        }

        static ListReport inspect(
                ListKind kind,
                LinkedSequence<Integer> sequence
        ) {
            String strength = switch (kind) {
                case SINGLY -> "Low pointer overhead and efficient sequential traversal";
                case DOUBLY -> "Bidirectional traversal and efficient local deletion";
                case CIRCULAR -> "Natural repeated traversal without a null terminal link";
            };

            return new ListReport(kind, sequence.size(), sequence.toList(), strength);
        }
    }

    public static void main(String[] args) {
        SinglyLinkedList<Integer> singly = new SinglyLinkedList<>();
        singly.addLast(10);
        singly.addLast(20);
        singly.addFirst(5);
        singly.remove(1);
        singly.reverse();

        DoublyLinkedList<Integer> doubly = new DoublyLinkedList<>();
        doubly.addLast(10);
        doubly.addLast(20);
        doubly.addLast(30);
        doubly.addFirst(5);

        CircularLinkedList<Integer> circular = new CircularLinkedList<>();
        circular.addLast(100);
        circular.addLast(200);
        circular.addLast(300);
        circular.addLast(400);
        circular.rotate(2);

        System.out.println(LinkedListService.inspect(
                ListKind.SINGLY, singly
        ));

        System.out.println(LinkedListService.inspect(
                ListKind.DOUBLY, doubly
        ));

        System.out.println(LinkedListService.inspect(
                ListKind.CIRCULAR, circular
        ));

        System.out.println("Doubly backward: " + doubly.backward());

        SinglyLinkedList<Integer> sortedA = new SinglyLinkedList<>();
        sortedA.addLast(1);
        sortedA.addLast(3);
        sortedA.addLast(5);

        SinglyLinkedList<Integer> sortedB = new SinglyLinkedList<>();
        sortedB.addLast(2);
        sortedB.addLast(4);
        sortedB.addLast(6);

        System.out.println(
                "Merged sorted lists: " +
                LinkedListService.mergeSorted(sortedA, sortedB, Integer::compare)
        );

        try {
            circular.get(100);
        } catch (InvalidIndexException error) {
            System.out.println("Expected validation failure: " + error.getMessage());
        }

        if (circular.size() > 0) {
            Optional<Integer> firstValue =
                    circular.toList().stream().findFirst();

            System.out.println("Circular first value: " + firstValue.orElseThrow());
        }

        System.out.println("Linked-list enterprise workflow completed.");
    }
}
