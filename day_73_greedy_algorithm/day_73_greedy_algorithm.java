import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.PriorityQueue;
import java.util.Set;
import java.util.TreeMap;
import java.util.stream.Collectors;

public class GreedyAlgorithms {

    enum AlgorithmStatus {
        COMPLETED,
        REJECTED,
        FAILED
    }

    static class AlgorithmException extends RuntimeException {
        public AlgorithmException(String message) {
            super(message);
        }
    }

    record Activity(String id, int start, int finish) {
        public Activity {
            if (id == null || id.isBlank()) {
                throw new AlgorithmException("Invalid activity ID.");
            }

            if (start < 0 || finish <= start) {
                throw new AlgorithmException(
                    "Invalid activity interval."
                );
            }
        }
    }

    record SelectionReport(
        List<Activity> selected,
        List<Activity> rejected,
        AlgorithmStatus status
    ) {
        public SelectionReport {
            selected = List.copyOf(selected);
            rejected = List.copyOf(rejected);
        }
    }

    interface SelectionPolicy<T> {
        boolean shouldSelect(T candidate, int currentBoundary);
    }

    static final class EarliestFinishPolicy
            implements SelectionPolicy<Activity> {

        @Override
        public boolean shouldSelect(
                Activity candidate,
                int currentBoundary
        ) {
            return candidate.start() >= currentBoundary;
        }
    }

    static final class ActivitySchedulingService {

        private final SelectionPolicy<Activity> policy;

        ActivitySchedulingService(
                SelectionPolicy<Activity> policy
        ) {
            this.policy = policy;
        }

        SelectionReport schedule(List<Activity> activities) {
            Set<String> identifiers = new HashSet<>();

            for (Activity activity : activities) {
                if (!identifiers.add(activity.id())) {
                    throw new AlgorithmException(
                        "Duplicate activity ID: " + activity.id()
                    );
                }
            }

            // Immutable source input is retained.
            List<Activity> ordered = new ArrayList<>(activities);

            ordered.sort(
                Comparator.comparingInt(Activity::finish)
                    .thenComparingInt(Activity::start)
                    .thenComparing(Activity::id)
            );

            List<Activity> selected = new ArrayList<>();
            List<Activity> rejected = new ArrayList<>();

            int boundary = -1;

            for (Activity activity : ordered) {
                if (policy.shouldSelect(activity, boundary)) {
                    selected.add(activity);
                    boundary = activity.finish();
                } else {
                    rejected.add(activity);
                }
            }

            return new SelectionReport(
                selected,
                rejected,
                AlgorithmStatus.COMPLETED
            );
        }
    }

    record Item(String id, double value, double weight) {
        public Item {
            if (id == null || id.isBlank()) {
                throw new AlgorithmException("Invalid item ID.");
            }

            if (!Double.isFinite(value) || value < 0 ||
                !Double.isFinite(weight) || weight <= 0) {
                throw new AlgorithmException(
                    "Invalid item value or weight."
                );
            }
        }

        double ratio() {
            return value / weight;
        }
    }

    record Allocation(
        String itemId,
        double fraction,
        double allocatedValue,
        double allocatedWeight
    ) {}

    record KnapsackReport(
        List<Allocation> allocations,
        double totalValue,
        double usedCapacity
    ) {
        public KnapsackReport {
            allocations = List.copyOf(allocations);
        }
    }

    static final class FractionalKnapsackService {

        KnapsackReport optimize(
                List<Item> items,
                double capacity
        ) {
            if (!Double.isFinite(capacity) || capacity < 0) {
                throw new AlgorithmException(
                    "Invalid knapsack capacity."
                );
            }

            Set<String> identifiers = new HashSet<>();

            for (Item item : items) {
                if (!identifiers.add(item.id())) {
                    throw new AlgorithmException(
                        "Duplicate item ID."
                    );
                }
            }

            List<Item> ordered = new ArrayList<>(items);

            ordered.sort(
                Comparator.comparingDouble(Item::ratio)
                    .reversed()
                    .thenComparing(Item::id)
            );

            List<Allocation> allocations = new ArrayList<>();
            double remaining = capacity;
            double totalValue = 0;

            for (Item item : ordered) {
                if (remaining <= 0) break;

                double fraction = Math.min(
                    1.0,
                    remaining / item.weight()
                );

                if (fraction <= 0) continue;

                double weight = fraction * item.weight();
                double value = fraction * item.value();

                allocations.add(
                    new Allocation(
                        item.id(),
                        fraction,
                        value,
                        weight
                    )
                );

                remaining = Math.max(0, remaining - weight);
                totalValue += value;
            }

            return new KnapsackReport(
                allocations,
                totalValue,
                capacity - remaining
            );
        }
    }

    static final class HuffmanNode {
        final Character symbol;
        final long frequency;
        final HuffmanNode left;
        final HuffmanNode right;

        HuffmanNode(
                Character symbol,
                long frequency,
                HuffmanNode left,
                HuffmanNode right
        ) {
            this.symbol = symbol;
            this.frequency = frequency;
            this.left = left;
            this.right = right;
        }

        boolean isLeaf() {
            return left == null && right == null;
        }
    }

    static final class HuffmanCodec {

        private final HuffmanNode root;
        private final Map<Character, String> codes =
            new TreeMap<>();

        HuffmanCodec(Map<Character, Long> frequencies) {
            if (frequencies == null || frequencies.isEmpty()) {
                throw new AlgorithmException(
                    "Frequency table cannot be empty."
                );
            }

            Comparator<HuffmanNode> comparator =
                Comparator.comparingLong(
                    (HuffmanNode node) -> node.frequency
                ).thenComparingInt(
                    node -> node.symbol == null
                        ? Integer.MAX_VALUE
                        : node.symbol
                );

            PriorityQueue<HuffmanNode> queue =
                new PriorityQueue<>(comparator);

            for (Map.Entry<Character, Long> entry :
                    frequencies.entrySet()) {

                Character symbol = entry.getKey();
                Long frequency = entry.getValue();

                if (symbol == null || frequency == null ||
                    frequency <= 0) {
                    throw new AlgorithmException(
                        "Invalid Huffman frequency."
                    );
                }

                queue.add(
                    new HuffmanNode(
                        symbol,
                        frequency,
                        null,
                        null
                    )
                );
            }

            while (queue.size() > 1) {
                HuffmanNode left = queue.remove();
                HuffmanNode right = queue.remove();

                long combined;

                try {
                    combined = Math.addExact(
                        left.frequency,
                        right.frequency
                    );
                } catch (ArithmeticException exception) {
                    throw new AlgorithmException(
                        "Frequency overflow."
                    );
                }

                queue.add(
                    new HuffmanNode(
                        null,
                        combined,
                        left,
                        right
                    )
                );
            }

            root = queue.remove();
            generateCodes(root, "");
        }

        private void generateCodes(
                HuffmanNode node,
                String prefix
        ) {
            if (node.isLeaf()) {
                codes.put(
                    node.symbol,
                    prefix.isEmpty() ? "0" : prefix
                );
                return;
            }

            generateCodes(node.left, prefix + "0");
            generateCodes(node.right, prefix + "1");
        }

        String encode(String message) {
            if (message == null) {
                throw new AlgorithmException(
                    "Message cannot be null."
                );
            }

            StringBuilder output = new StringBuilder();

            for (int i = 0; i < message.length(); i++) {
                char symbol = message.charAt(i);
                String code = codes.get(symbol);

                if (code == null) {
                    throw new AlgorithmException(
                        "Unknown symbol: " + symbol
                    );
                }

                output.append(code);
            }

            return output.toString();
        }

        String decode(String encoded) {
            if (encoded == null ||
                !encoded.matches("[01]*")) {
                throw new AlgorithmException(
                    "Invalid binary sequence."
                );
            }

            if (root.isLeaf()) {
                return String.valueOf(root.symbol)
                    .repeat(encoded.length());
            }

            StringBuilder output = new StringBuilder();
            HuffmanNode current = root;

            for (char bit : encoded.toCharArray()) {
                current = bit == '0'
                    ? current.left
                    : current.right;

                if (current == null) {
                    throw new AlgorithmException(
                        "Invalid Huffman path."
                    );
                }

                if (current.isLeaf()) {
                    output.append(current.symbol);
                    current = root;
                }
            }

            if (current != root) {
                throw new AlgorithmException(
                    "Incomplete Huffman codeword."
                );
            }

            return output.toString();
        }

        Map<Character, String> getCodes() {
            return Map.copyOf(codes);
        }

        long weightedPathLength(
                Map<Character, Long> frequencies
        ) {
            long total = 0;

            for (Map.Entry<Character, String> entry :
                    codes.entrySet()) {

                long contribution = Math.multiplyExact(
                    frequencies.get(entry.getKey()),
                    entry.getValue().length()
                );

                total = Math.addExact(total, contribution);
            }

            return total;
        }
    }

    static final class ZeroOneKnapsackService {

        long optimize(List<Item> items, int capacity) {
            if (capacity < 0) {
                throw new AlgorithmException(
                    "Capacity cannot be negative."
                );
            }

            long[] dp = new long[capacity + 1];

            for (Item item : items) {
                if (item.weight() != Math.floor(item.weight()) ||
                    item.value() != Math.floor(item.value())) {
                    throw new AlgorithmException(
                        "Integer values and weights are required."
                    );
                }

                if (item.weight() > capacity) continue;

                int weight = (int) item.weight();
                long value = (long) item.value();

                for (int w = capacity; w >= weight; w--) {
                    dp[w] = Math.max(
                        dp[w],
                        Math.addExact(dp[w - weight], value)
                    );
                }
            }

            return dp[capacity];
        }
    }

    private static void runTests() {
        ActivitySchedulingService scheduler =
            new ActivitySchedulingService(
                new EarliestFinishPolicy()
            );

        SelectionReport selection = scheduler.schedule(
            List.of(
                new Activity("A", 1, 3),
                new Activity("B", 3, 5),
                new Activity("C", 2, 4)
            )
        );

        if (selection.selected().size() != 2) {
            throw new AssertionError(
                "Activity scheduling test failed."
            );
        }

        FractionalKnapsackService fractional =
            new FractionalKnapsackService();

        KnapsackReport report = fractional.optimize(
            List.of(
                new Item("A", 60, 10),
                new Item("B", 100, 20),
                new Item("C", 120, 30)
            ),
            50
        );

        if (Math.abs(report.totalValue() - 240) > 1e-9) {
            throw new AssertionError(
                "Fractional knapsack test failed."
            );
        }

        Map<Character, Long> frequencies = Map.of(
            'a', 45L,
            'b', 13L,
            'c', 12L,
            'd', 16L,
            'e', 9L,
            'f', 5L
        );

        HuffmanCodec codec = new HuffmanCodec(frequencies);

        String message = "abcdef";

        if (!codec.decode(codec.encode(message)).equals(message)) {
            throw new AssertionError(
                "Huffman round-trip test failed."
            );
        }

        ZeroOneKnapsackService exact =
            new ZeroOneKnapsackService();

        long optimal = exact.optimize(
            List.of(
                new Item("A", 60, 10),
                new Item("B", 100, 20),
                new Item("C", 120, 30)
            ),
            50
        );

        if (optimal != 220) {
            throw new AssertionError(
                "0/1 knapsack test failed."
            );
        }

        System.out.println("All Java 17 tests passed.");
    }

    public static void main(String[] args) {
        try {
            runTests();

            ActivitySchedulingService scheduler =
                new ActivitySchedulingService(
                    new EarliestFinishPolicy()
                );

            List<Activity> activities = List.of(
                new Activity("A101", 1, 4),
                new Activity("A102", 3, 5),
                new Activity("A103", 0, 6),
                new Activity("A104", 5, 7),
                new Activity("A105", 8, 9),
                new Activity("A106", 5, 9),
                new Activity("A107", 2, 3)
            );

            SelectionReport selection =
                scheduler.schedule(activities);

            System.out.println("\nACTIVITY SCHEDULING");

            selection.selected().forEach(activity ->
                System.out.println(
                    activity.id() + ": " +
                    activity.start() + "-" +
                    activity.finish()
                )
            );

            FractionalKnapsackService fractional =
                new FractionalKnapsackService();

            KnapsackReport knapsack =
                fractional.optimize(
                    List.of(
                        new Item("Gold", 60, 10),
                        new Item("Silver", 100, 20),
                        new Item("Copper", 120, 30)
                    ),
                    50
                );

            System.out.println("\nFRACTIONAL KNAPSACK");

            knapsack.allocations().forEach(allocation ->
                System.out.printf(
                    "%s: %.2f%%, value %.2f%n",
                    allocation.itemId(),
                    allocation.fraction() * 100,
                    allocation.allocatedValue()
                )
            );

            System.out.printf(
                "Total value: %.2f%n",
                knapsack.totalValue()
            );

            Map<Character, Long> frequencies =
                new HashMap<>();

            String message = "greedy algorithms";

            for (char character : message.toCharArray()) {
                frequencies.merge(character, 1L, Long::sum);
            }

            HuffmanCodec codec = new HuffmanCodec(frequencies);
            String encoded = codec.encode(message);

            System.out.println("\nHUFFMAN CODING");

            codec.getCodes().forEach((symbol, code) ->
                System.out.println(symbol + " -> " + code)
            );

            System.out.println("Encoded: " + encoded);
            System.out.println("Decoded: " + codec.decode(encoded));

            System.out.println(
                "Weighted path length: " +
                codec.weightedPathLength(frequencies)
            );

            ZeroOneKnapsackService exact =
                new ZeroOneKnapsackService();

            long exactValue = exact.optimize(
                List.of(
                    new Item("A", 60, 10),
                    new Item("B", 100, 20),
                    new Item("C", 120, 30)
                ),
                50
            );

            System.out.println("\n0/1 KNAPSACK");
            System.out.println(
                "Optimal dynamic programming value: " +
                exactValue
            );

            System.out.println("\nExecution completed.");

        } catch (AlgorithmException | ArithmeticException exception) {
            System.err.println(
                "Algorithm execution failed: " +
                exception.getMessage()
            );

            System.exit(1);
        }
    }
}
