import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Deque;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.OptionalInt;
import java.util.function.Consumer;
import java.util.stream.Collectors;

public class TreeGovernanceDemo {

    enum TraversalOrder {
        PREORDER,
        INORDER,
        POSTORDER,
        LEVEL_ORDER
    }

    enum NodeState {
        ACTIVE,
        DELETED
    }

    record TreeNode(int value, TreeNode left, TreeNode right) {
        TreeNode {
            if (value < 0) {
                throw new IllegalArgumentException("Tree keys must be non-negative.");
            }
        }
    }

    static final class MutableNode {
        final int value;
        MutableNode left;
        MutableNode right;
        NodeState state = NodeState.ACTIVE;

        MutableNode(int value) {
            if (value < 0) {
                throw new IllegalArgumentException("Tree keys must be non-negative.");
            }
            this.value = value;
        }
    }

    interface TreePolicy {
        boolean accepts(int value);

        default void validate(int value) {
            if (!accepts(value)) {
                throw new IllegalArgumentException(
                    "Value violates the configured tree policy: " + value
                );
            }
        }
    }

    static final class NonNegativePolicy implements TreePolicy {
        @Override
        public boolean accepts(int value) {
            return value >= 0;
        }
    }

    static final class BinarySearchTreeService {
        private MutableNode root;
        private final TreePolicy policy;
        private final List<Consumer<Integer>> insertionListeners = new ArrayList<>();

        BinarySearchTreeService(TreePolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        void onInsertion(Consumer<Integer> listener) {
            insertionListeners.add(Objects.requireNonNull(listener));
        }

        void insert(int value) {
            policy.validate(value);

            if (root == null) {
                root = new MutableNode(value);
                notifyInsertion(value);
                return;
            }

            MutableNode current = root;

            while (true) {
                if (current.state == NodeState.DELETED) {
                    throw new IllegalStateException("Cannot insert through deleted node.");
                }

                if (value == current.value) {
                    throw new DuplicateTreeKeyException(value);
                }

                if (value < current.value) {
                    if (current.left == null) {
                        current.left = new MutableNode(value);
                        notifyInsertion(value);
                        return;
                    }
                    current = current.left;
                } else {
                    if (current.right == null) {
                        current.right = new MutableNode(value);
                        notifyInsertion(value);
                        return;
                    }
                    current = current.right;
                }
            }
        }

        private void notifyInsertion(int value) {
            for (Consumer<Integer> listener : List.copyOf(insertionListeners)) {
                listener.accept(value);
            }
        }

        boolean contains(int value) {
            MutableNode current = root;

            while (current != null) {
                if (current.state == NodeState.DELETED) {
                    return false;
                }

                if (value == current.value) {
                    return true;
                }

                current = value < current.value
                    ? current.left
                    : current.right;
            }

            return false;
        }

        List<Integer> traverse(TraversalOrder order) {
            return switch (order) {
                case PREORDER -> preorder();
                case INORDER -> inorder();
                case POSTORDER -> postorder();
                case LEVEL_ORDER -> levelOrder();
            };
        }

        private List<Integer> preorder() {
            List<Integer> result = new ArrayList<>();
            if (root == null) return result;

            Deque<MutableNode> stack = new ArrayDeque<>();
            stack.push(root);

            while (!stack.isEmpty()) {
                MutableNode node = stack.pop();
                if (node.state == NodeState.DELETED) continue;

                result.add(node.value);

                if (node.right != null) stack.push(node.right);
                if (node.left != null) stack.push(node.left);
            }

            return List.copyOf(result);
        }

        private List<Integer> inorder() {
            List<Integer> result = new ArrayList<>();
            Deque<MutableNode> stack = new ArrayDeque<>();
            MutableNode current = root;

            while (current != null || !stack.isEmpty()) {
                while (current != null) {
                    stack.push(current);
                    current = current.left;
                }

                current = stack.pop();

                if (current.state == NodeState.ACTIVE) {
                    result.add(current.value);
                }

                current = current.right;
            }

            return List.copyOf(result);
        }

        private List<Integer> postorder() {
            List<Integer> result = new ArrayList<>();
            if (root == null) return result;

            Deque<Map.Entry<MutableNode, Boolean>> stack = new ArrayDeque<>();
            stack.push(Map.entry(root, false));

            while (!stack.isEmpty()) {
                Map.Entry<MutableNode, Boolean> entry = stack.pop();
                MutableNode node = entry.getKey();

                if (entry.getValue()) {
                    if (node.state == NodeState.ACTIVE) {
                        result.add(node.value);
                    }
                    continue;
                }

                stack.push(Map.entry(node, true));
                if (node.right != null) {
                    stack.push(Map.entry(node.right, false));
                }
                if (node.left != null) {
                    stack.push(Map.entry(node.left, false));
                }
            }

            return List.copyOf(result);
        }

        private List<Integer> levelOrder() {
            if (root == null) return List.of();

            List<Integer> result = new ArrayList<>();
            Deque<MutableNode> queue = new ArrayDeque<>();
            queue.add(root);

            while (!queue.isEmpty()) {
                MutableNode node = queue.remove();

                if (node.state == NodeState.ACTIVE) {
                    result.add(node.value);
                }

                if (node.left != null) queue.add(node.left);
                if (node.right != null) queue.add(node.right);
            }

            return List.copyOf(result);
        }

        boolean validate() {
            record Bound(MutableNode node, OptionalInt lower, OptionalInt upper) {}

            Deque<Bound> stack = new ArrayDeque<>();
            if (root != null) {
                stack.push(new Bound(root, OptionalInt.empty(), OptionalInt.empty()));
            }

            while (!stack.isEmpty()) {
                Bound bound = stack.pop();
                MutableNode node = bound.node();

                if (node.state == NodeState.DELETED) {
                    return false;
                }

                if (bound.lower().isPresent() && node.value <= bound.lower().getAsInt()) {
                    return false;
                }

                if (bound.upper().isPresent() && node.value >= bound.upper().getAsInt()) {
                    return false;
                }

                if (node.left != null) {
                    stack.push(new Bound(
                        node.left,
                        bound.lower(),
                        OptionalInt.of(node.value)
                    ));
                }

                if (node.right != null) {
                    stack.push(new Bound(
                        node.right,
                        OptionalInt.of(node.value),
                        bound.upper()
                    ));
                }
            }

            return true;
        }

        List<Integer> range(int low, int high) {
            if (low > high) {
                throw new IllegalArgumentException("Invalid range.");
            }

            return inorder().stream()
                .filter(value -> value >= low && value <= high)
                .collect(Collectors.toUnmodifiableList());
        }

        int height() {
            if (root == null) return 0;

            int height = 0;
            Deque<MutableNode> queue = new ArrayDeque<>();
            queue.add(root);

            while (!queue.isEmpty()) {
                int levelSize = queue.size();
                height++;

                for (int i = 0; i < levelSize; i++) {
                    MutableNode node = queue.remove();
                    if (node.left != null) queue.add(node.left);
                    if (node.right != null) queue.add(node.right);
                }
            }

            return height;
        }
    }

    static final class DuplicateTreeKeyException extends RuntimeException {
        DuplicateTreeKeyException(int value) {
            super("Duplicate tree key: " + value);
        }
    }

    record TreeMetrics(int height, int nodeCount, boolean valid) {}

    static TreeMetrics inspect(BinarySearchTreeService tree) {
        List<Integer> values = tree.traverse(TraversalOrder.INORDER);
        return new TreeMetrics(tree.height(), values.size(), tree.validate());
    }

    public static void main(String[] args) {
        BinarySearchTreeService tree =
            new BinarySearchTreeService(new NonNegativePolicy());

        tree.onInsertion(
            value -> System.out.println("audit: inserted tree key " + value)
        );

        List<Integer> keys = List.of(
            50, 30, 70, 20, 40, 60, 80, 65
        );

        keys.forEach(tree::insert);

        if (!tree.validate()) {
            throw new IllegalStateException("BST invariant has been violated.");
        }

        System.out.println("\nEnterprise tree model");

        for (TraversalOrder order : TraversalOrder.values()) {
            System.out.printf(
                "%-12s: %s%n",
                order,
                tree.traverse(order)
            );
        }

        System.out.println("Contains 65: " + tree.contains(65));
        System.out.println("Contains 99: " + tree.contains(99));
        System.out.println("Range 35..70: " + tree.range(35, 70));

        TreeMetrics metrics = inspect(tree);
        System.out.println("Metrics: " + metrics);

        try {
            tree.insert(50);
        } catch (DuplicateTreeKeyException error) {
            System.out.println("Expected failure: " + error.getMessage());
        }

        try {
            tree.insert(-10);
        } catch (IllegalArgumentException error) {
            System.out.println("Expected policy failure: " + error.getMessage());
        }

        // Java's immutable records are useful for values such as TreeMetrics
        // because callers cannot mutate the result after validation.
        //
        // The service keeps mutable domain state private and exposes
        // traversal results as immutable lists.
        //
        // Traversals are O(n). BST search and insertion are O(h), where h
        // is tree height. An unbalanced tree can degrade to O(n).
        //
        // A production enterprise implementation should select a balanced
        // search structure when worst-case latency matters and should apply
        // authorization before exposing mutation operations to callers.
    }
}
