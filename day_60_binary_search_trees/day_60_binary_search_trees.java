import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashSet;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

public class Main {

    enum AssetStatus {
        ACTIVE,
        RETIRED
    }

    record Asset(int id, String name, String category, AssetStatus status) {
        Asset {
            if (id <= 0) {
                throw new IllegalArgumentException("Asset ID must be positive");
            }
            if (name == null || name.isBlank() || name.length() > 120) {
                throw new IllegalArgumentException("Invalid asset name");
            }
            if (category == null || category.isBlank() ||
                    category.length() > 80) {
                throw new IllegalArgumentException("Invalid asset category");
            }
            Objects.requireNonNull(status, "Asset status is required");
        }

        Asset withStatus(AssetStatus newStatus) {
            return new Asset(id, name, category, newStatus);
        }
    }

    static class CatalogException extends RuntimeException {
        CatalogException(String message) {
            super(message);
        }
    }

    static class Node<V> {
        int key;
        V value;
        Node<V> left;
        Node<V> right;
        int height = 1;

        Node(int key, V value) {
            this.key = key;
            this.value = value;
        }
    }

    interface TreeIndex<V> {
        boolean insert(int key, V value);

        boolean remove(int key);

        V find(int key);

        List<Map.Entry<Integer, V>> range(int lower, int upper);

        List<Map.Entry<Integer, V>> inorder();

        Map.Entry<Integer, V> kthSmallest(int position);

        int height();

        int size();

        boolean validate();
    }

    abstract static class AbstractTreeIndex<V> implements TreeIndex<V> {
        protected Node<V> root;
        protected int size;

        protected abstract boolean requiresBalance();

        @Override
        public V find(int key) {
            Node<V> current = root;

            while (current != null) {
                if (key == current.key) {
                    return current.value;
                }

                current = key < current.key
                    ? current.left
                    : current.right;
            }

            return null;
        }

        @Override
        public List<Map.Entry<Integer, V>> inorder() {
            List<Map.Entry<Integer, V>> result = new ArrayList<>();
            Deque<Node<V>> stack = new ArrayDeque<>();
            Node<V> current = root;

            while (current != null || !stack.isEmpty()) {
                while (current != null) {
                    stack.push(current);
                    current = current.left;
                }

                current = stack.pop();
                result.add(Map.entry(current.key, current.value));
                current = current.right;
            }

            return List.copyOf(result);
        }

        @Override
        public List<Map.Entry<Integer, V>> range(int lower, int upper) {
            if (lower > upper) {
                throw new IllegalArgumentException(
                    "Lower bound cannot exceed upper bound"
                );
            }

            List<Map.Entry<Integer, V>> result = new ArrayList<>();
            Deque<Node<V>> stack = new ArrayDeque<>();
            Node<V> current = root;

            while (current != null || !stack.isEmpty()) {
                while (current != null) {
                    if (current.key >= lower) {
                        stack.push(current);
                        current = current.left;
                    } else {
                        current = current.right;
                    }
                }

                if (stack.isEmpty()) {
                    break;
                }

                current = stack.pop();

                if (current.key > upper) {
                    break;
                }

                result.add(Map.entry(current.key, current.value));
                current = current.right;
            }

            return List.copyOf(result);
        }

        @Override
        public Map.Entry<Integer, V> kthSmallest(int position) {
            if (position < 1 || position > size) {
                throw new IndexOutOfBoundsException(
                    "Position is outside the tree"
                );
            }

            Deque<Node<V>> stack = new ArrayDeque<>();
            Node<V> current = root;
            int visited = 0;

            while (current != null || !stack.isEmpty()) {
                while (current != null) {
                    stack.push(current);
                    current = current.left;
                }

                current = stack.pop();
                visited++;

                if (visited == position) {
                    return Map.entry(current.key, current.value);
                }

                current = current.right;
            }

            throw new IllegalStateException(
                "Tree size and traversal are inconsistent"
            );
        }

        @Override
        public int height() {
            if (root == null) {
                return 0;
            }

            record Position<V>(Node<V> node, int depth) {}

            Deque<Position<V>> queue = new ArrayDeque<>();
            queue.add(new Position<>(root, 1));
            int maximum = 0;

            while (!queue.isEmpty()) {
                Position<V> position = queue.remove();
                Node<V> node = position.node();
                maximum = Math.max(maximum, position.depth());

                if (node.left != null) {
                    queue.add(new Position<>(node.left, position.depth() + 1));
                }

                if (node.right != null) {
                    queue.add(new Position<>(node.right, position.depth() + 1));
                }
            }

            return maximum;
        }

        @Override
        public int size() {
            return size;
        }

        @Override
        public boolean validate() {
            record Frame<V>(Node<V> node, long lower, long upper) {}

            Deque<Frame<V>> stack = new ArrayDeque<>();
            Set<Node<V>> seen = java.util.Collections.newSetFromMap(
                new IdentityHashMap<>()
            );

            if (root != null) {
                stack.push(new Frame<>(
                    root,
                    Long.MIN_VALUE,
                    Long.MAX_VALUE
                ));
            }

            int visited = 0;

            while (!stack.isEmpty()) {
                Frame<V> frame = stack.pop();
                Node<V> node = frame.node();

                if (!seen.add(node)) {
                    return false;
                }

                if (node.key <= frame.lower() ||
                        node.key >= frame.upper()) {
                    return false;
                }

                visited++;

                if (node.left != null) {
                    stack.push(new Frame<>(
                        node.left,
                        frame.lower(),
                        node.key
                    ));
                }

                if (node.right != null) {
                    stack.push(new Frame<>(
                        node.right,
                        node.key,
                        frame.upper()
                    ));
                }
            }

            if (visited != size) {
                return false;
            }

            if (requiresBalance() && root != null) {
                return validateBalanced(root).valid();
            }

            return true;
        }

        private record HeightCheck(boolean valid, int height) {}

        private HeightCheck validateBalanced(Node<V> node) {
            if (node == null) {
                return new HeightCheck(true, 0);
            }

            HeightCheck left = validateBalanced(node.left);
            if (!left.valid()) {
                return new HeightCheck(false, 0);
            }

            HeightCheck right = validateBalanced(node.right);
            if (!right.valid()) {
                return new HeightCheck(false, 0);
            }

            int expectedHeight = 1 + Math.max(left.height(), right.height());
            boolean valid = node.height == expectedHeight &&
                Math.abs(left.height() - right.height()) <= 1;

            return new HeightCheck(valid, expectedHeight);
        }
    }

    static final class UnbalancedBstIndex<V> extends AbstractTreeIndex<V> {
        @Override
        protected boolean requiresBalance() {
            return false;
        }

        @Override
        public boolean insert(int key, V value) {
            Objects.requireNonNull(value, "Indexed values cannot be null");

            if (root == null) {
                root = new Node<>(key, value);
                size = 1;
                return true;
            }

            Node<V> current = root;

            while (true) {
                if (key == current.key) {
                    current.value = value;
                    return false;
                }

                if (key < current.key) {
                    if (current.left == null) {
                        current.left = new Node<>(key, value);
                        size++;
                        return true;
                    }
                    current = current.left;
                } else {
                    if (current.right == null) {
                        current.right = new Node<>(key, value);
                        size++;
                        return true;
                    }
                    current = current.right;
                }
            }
        }

        @Override
        public boolean remove(int key) {
            Node<V> parent = null;
            Node<V> current = root;

            while (current != null && current.key != key) {
                parent = current;
                current = key < current.key
                    ? current.left
                    : current.right;
            }

            if (current == null) {
                return false;
            }

            if (current.left != null && current.right != null) {
                Node<V> successorParent = current;
                Node<V> successor = current.right;

                while (successor.left != null) {
                    successorParent = successor;
                    successor = successor.left;
                }

                current.key = successor.key;
                current.value = successor.value;

                if (successorParent == current) {
                    successorParent.right = successor.right;
                } else {
                    successorParent.left = successor.right;
                }
            } else {
                Node<V> replacement = current.left != null
                    ? current.left
                    : current.right;

                if (parent == null) {
                    root = replacement;
                } else if (parent.left == current) {
                    parent.left = replacement;
                } else {
                    parent.right = replacement;
                }
            }

            size--;
            return true;
        }
    }

    static final class AvlIndex<V> extends AbstractTreeIndex<V> {
        @Override
        protected boolean requiresBalance() {
            return true;
        }

        private static int nodeHeight(Node<?> node) {
            return node == null ? 0 : node.height;
        }

        private static void refresh(Node<?> node) {
            node.height = 1 + Math.max(
                nodeHeight(node.left),
                nodeHeight(node.right)
            );
        }

        private static int balance(Node<?> node) {
            return nodeHeight(node.left) - nodeHeight(node.right);
        }

        private Node<V> rotateRight(Node<V> root) {
            Node<V> pivot = root.left;

            if (pivot == null) {
                throw new IllegalStateException("Invalid right rotation");
            }

            root.left = pivot.right;
            pivot.right = root;

            refresh(root);
            refresh(pivot);

            return pivot;
        }

        private Node<V> rotateLeft(Node<V> root) {
            Node<V> pivot = root.right;

            if (pivot == null) {
                throw new IllegalStateException("Invalid left rotation");
            }

            root.right = pivot.left;
            pivot.left = root;

            refresh(root);
            refresh(pivot);

            return pivot;
        }

        private Node<V> rebalance(Node<V> node) {
            if (node == null) {
                return null;
            }

            refresh(node);
            int balance = balance(node);

            if (balance > 1) {
                if (balance(node.left) < 0) {
                    node.left = rotateLeft(node.left);
                }
                return rotateRight(node);
            }

            if (balance < -1) {
                if (balance(node.right) > 0) {
                    node.right = rotateRight(node.right);
                }
                return rotateLeft(node);
            }

            return node;
        }

        private Node<V> insertNode(
                Node<V> node,
                int key,
                V value,
                boolean[] inserted) {
            if (node == null) {
                inserted[0] = true;
                return new Node<>(key, value);
            }

            if (key < node.key) {
                node.left = insertNode(node.left, key, value, inserted);
            } else if (key > node.key) {
                node.right = insertNode(node.right, key, value, inserted);
            } else {
                node.value = value;
                return node;
            }

            return rebalance(node);
        }

        @Override
        public boolean insert(int key, V value) {
            Objects.requireNonNull(value, "Indexed values cannot be null");

            boolean[] inserted = {false};
            root = insertNode(root, key, value, inserted);

            if (inserted[0]) {
                size++;
            }

            return inserted[0];
        }

        private Node<V> minimum(Node<V> node) {
            while (node.left != null) {
                node = node.left;
            }
            return node;
        }

        private Node<V> removeNode(
                Node<V> node,
                int key,
                boolean[] removed) {
            if (node == null) {
                return null;
            }

            if (key < node.key) {
                node.left = removeNode(node.left, key, removed);
            } else if (key > node.key) {
                node.right = removeNode(node.right, key, removed);
            } else {
                removed[0] = true;

                if (node.left == null) {
                    return node.right;
                }

                if (node.right == null) {
                    return node.left;
                }

                Node<V> successor = minimum(node.right);
                node.key = successor.key;
                node.value = successor.value;

                boolean successorRemoved = false;
                node.right = removeNode(
                    node.right,
                    successor.key,
                    new boolean[]{false}
                );
            }

            return rebalance(node);
        }

        @Override
        public boolean remove(int key) {
            if (find(key) == null) {
                return false;
            }

            boolean[] removed = {false};
            root = removeNode(root, key, removed);

            if (removed[0]) {
                size--;
            }

            return removed[0];
        }
    }

    /**
     * Applies catalog lifecycle rules independently from tree balancing.
     * Retired records remain in the audit map but leave the active index.
     */
    static final class AssetCatalogService {
        private final TreeIndex<Asset> activeIndex;
        private final Map<Integer, Asset> records = new java.util.HashMap<>();

        AssetCatalogService(TreeIndex<Asset> activeIndex) {
            this.activeIndex = Objects.requireNonNull(activeIndex);
        }

        public void register(Asset asset) {
            Objects.requireNonNull(asset, "Asset is required");

            if (records.containsKey(asset.id())) {
                throw new CatalogException(
                    "Asset ID already exists: " + asset.id()
                );
            }

            if (asset.status() != AssetStatus.ACTIVE) {
                throw new CatalogException(
                    "New assets must start in ACTIVE state"
                );
            }

            activeIndex.insert(asset.id(), asset);
            records.put(asset.id(), asset);
        }

        public void retire(int id) {
            Asset existing = records.get(id);

            if (existing == null) {
                throw new CatalogException("Unknown asset ID: " + id);
            }

            if (existing.status() == AssetStatus.RETIRED) {
                throw new CatalogException("Asset is already retired: " + id);
            }

            // Remove from the searchable index before publishing the new state.
            if (!activeIndex.remove(id)) {
                throw new IllegalStateException(
                    "Active catalog index is inconsistent for ID " + id
                );
            }

            records.put(id, existing.withStatus(AssetStatus.RETIRED));
        }

        public Asset findActive(int id) {
            return activeIndex.find(id);
        }

        public List<Map.Entry<Integer, Asset>> activeRange(
                int lower,
                int upper) {
            return activeIndex.range(lower, upper);
        }

        public int activeCount() {
            return activeIndex.size();
        }

        public int indexHeight() {
            return activeIndex.height();
        }

        public boolean validateIndex() {
            return activeIndex.validate();
        }

        public int retiredCount() {
            return (int) records.values().stream()
                .filter(asset -> asset.status() == AssetStatus.RETIRED)
                .count();
        }
    }

    private static Asset asset(int id) {
        return new Asset(
            id,
            "Infrastructure Asset " + id,
            id % 2 == 0 ? "Compute" : "Network",
            AssetStatus.ACTIVE
        );
    }

    private static void exerciseCatalog(
            TreeIndex<Asset> index,
            String label) {
        AssetCatalogService catalog = new AssetCatalogService(index);

        int[] identifiers = {50, 30, 70, 20, 40, 60, 80, 65};

        for (int id : identifiers) {
            catalog.register(asset(id));
        }

        // Duplicate registration must not silently replace an existing asset.
        try {
            catalog.register(asset(50));
            throw new IllegalStateException("Duplicate registration succeeded");
        } catch (CatalogException expected) {
            System.out.println("Duplicate registration rejected");
        }

        catalog.retire(20);
        catalog.retire(60);
        catalog.retire(70);

        if (catalog.findActive(20) != null) {
            throw new IllegalStateException("Retired asset remains searchable");
        }

        if (!catalog.validateIndex()) {
            throw new IllegalStateException("Catalog index is invalid");
        }

        System.out.println("\n" + label);
        System.out.println("Active assets: " + catalog.activeCount());
        System.out.println("Retired assets: " + catalog.retiredCount());
        System.out.println("Index height: " + catalog.indexHeight());
        System.out.println("Active range 35..70: " +
            catalog.activeRange(35, 70));
        System.out.println("Index valid: " + catalog.validateIndex());
    }

    private static void compareSortedInsertion() {
        TreeIndex<Integer> bst = new UnbalancedBstIndex<>();
        TreeIndex<Integer> avl = new AvlIndex<>();

        for (int id = 1; id <= 1000; id++) {
            bst.insert(id, id);
            avl.insert(id, id);
        }

        if (!bst.validate() || !avl.validate()) {
            throw new IllegalStateException(
                "Large index validation failed"
            );
        }

        if (bst.height() != 1000 || avl.height() > 11) {
            throw new IllegalStateException(
                "Unexpected tree height after sorted insertion"
            );
        }

        bst.remove(500);
        avl.remove(500);

        System.out.println("\nSorted insertion comparison");
        System.out.println("Input records: 1000");
        System.out.println("Unbalanced BST height: " + bst.height());
        System.out.println("AVL height: " + avl.height());
        System.out.println("BST valid: " + bst.validate());
        System.out.println("AVL valid: " + avl.validate());
    }

    public static void main(String[] args) {
        try {
            exerciseCatalog(
                new UnbalancedBstIndex<>(),
                "Unbalanced asset catalog"
            );

            exerciseCatalog(
                new AvlIndex<>(),
                "AVL asset catalog"
            );

            compareSortedInsertion();
        } catch (RuntimeException exception) {
            System.err.println("Catalog operation failed: " +
                exception.getMessage());
            System.exit(1);
        }
    }
}
