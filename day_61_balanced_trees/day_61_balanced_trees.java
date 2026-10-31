import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

public class BalancedTreeGovernance {

    enum Color {
        RED, BLACK
    }

    record Repository(int id, String name) {
        Repository {
            if (id < 1) throw new IllegalArgumentException("Repository ID must be positive");
            Objects.requireNonNull(name, "Repository name");
            if (name.isBlank()) throw new IllegalArgumentException("Repository name is blank");
        }
    }

    record MergeCandidate(int repositoryId, int riskScore, boolean checksPassing) {}

    static final class AVLNode {
        int key;
        int height = 1;
        AVLNode left;
        AVLNode right;

        AVLNode(int key) {
            this.key = key;
        }
    }

    static final class AVLIndex {
        private AVLNode root;

        private static int height(AVLNode n) {
            return n == null ? 0 : n.height;
        }

        private static void update(AVLNode n) {
            n.height = 1 + Math.max(height(n.left), height(n.right));
        }

        private static int balance(AVLNode n) {
            return n == null ? 0 : height(n.left) - height(n.right);
        }

        private AVLNode rotateLeft(AVLNode x) {
            AVLNode y = x.right;
            if (y == null) throw new IllegalStateException("Missing right child");

            x.right = y.left;
            y.left = x;

            update(x);
            update(y);
            return y;
        }

        private AVLNode rotateRight(AVLNode y) {
            AVLNode x = y.left;
            if (x == null) throw new IllegalStateException("Missing left child");

            y.left = x.right;
            x.right = y;

            update(y);
            update(x);
            return x;
        }

        void insert(int key) {
            if (key < 1) throw new IllegalArgumentException("Key must be positive");
            root = insert(root, key);
        }

        private AVLNode insert(AVLNode node, int key) {
            if (node == null) return new AVLNode(key);

            if (key < node.key) node.left = insert(node.left, key);
            else if (key > node.key) node.right = insert(node.right, key);
            else throw new IllegalArgumentException("Duplicate key: " + key);

            update(node);
            int b = balance(node);

            if (b > 1 && key < node.left.key) return rotateRight(node);
            if (b < -1 && key > node.right.key) return rotateLeft(node);

            if (b > 1 && key > node.left.key) {
                node.left = rotateLeft(node.left);
                return rotateRight(node);
            }

            if (b < -1 && key < node.right.key) {
                node.right = rotateRight(node.right);
                return rotateLeft(node);
            }

            return node;
        }

        boolean contains(int key) {
            AVLNode current = root;
            while (current != null) {
                if (current.key == key) return true;
                current = key < current.key ? current.left : current.right;
            }
            return false;
        }

        int height() {
            return height(root);
        }

        List<Integer> sorted() {
            List<Integer> result = new ArrayList<>();
            traverse(root, result);
            return List.copyOf(result);
        }

        private static void traverse(AVLNode node, List<Integer> result) {
            if (node == null) return;
            traverse(node.left, result);
            result.add(node.key);
            traverse(node.right, result);
        }

        void validate() {
            validate(root, Optional.empty(), Optional.empty());
        }

        private int validate(AVLNode node, Optional<Integer> low, Optional<Integer> high) {
            if (node == null) return 0;

            if (low.isPresent() && node.key <= low.get())
                throw new IllegalStateException("BST ordering violation");

            if (high.isPresent() && node.key >= high.get())
                throw new IllegalStateException("BST ordering violation");

            int left = validate(node.left, low, Optional.of(node.key));
            int right = validate(node.right, Optional.of(node.key), high);

            int expectedHeight = 1 + Math.max(left, right);
            if (node.height != expectedHeight)
                throw new IllegalStateException("Height metadata violation");

            if (Math.abs(left - right) > 1)
                throw new IllegalStateException("AVL balance violation");

            return expectedHeight;
        }
    }

    interface MergePolicy {
        boolean eligible(MergeCandidate candidate);
    }

    static final class ProtectedRepositoryPolicy implements MergePolicy {
        private final int maximumRisk;

        ProtectedRepositoryPolicy(int maximumRisk) {
            if (maximumRisk < 0) throw new IllegalArgumentException("Negative risk limit");
            this.maximumRisk = maximumRisk;
        }

        @Override
        public boolean eligible(MergeCandidate candidate) {
            Objects.requireNonNull(candidate);
            return candidate.checksPassing()
                    && candidate.riskScore() <= maximumRisk;
        }
    }

    static final class RepositoryService {
        private final AVLIndex repositoryIndex = new AVLIndex();
        private final MergePolicy mergePolicy;

        RepositoryService(MergePolicy mergePolicy) {
            this.mergePolicy = Objects.requireNonNull(mergePolicy);
        }

        void register(Repository repository) {
            repositoryIndex.insert(repository.id());
        }

        boolean canMerge(MergeCandidate candidate) {
            return repositoryIndex.contains(candidate.repositoryId())
                    && mergePolicy.eligible(candidate);
        }

        String healthReport() {
            repositoryIndex.validate();
            return "Indexed repositories: "
                    + repositoryIndex.sorted()
                    + ", AVL height=" + repositoryIndex.height();
        }
    }

    public static void main(String[] args) {
        MergePolicy protectedPolicy = new ProtectedRepositoryPolicy(40);
        RepositoryService service = new RepositoryService(protectedPolicy);

        List<Repository> repositories = List.of(
                new Repository(10, "payments-api"),
                new Repository(20, "identity-service"),
                new Repository(30, "risk-engine"),
                new Repository(40, "audit-service"),
                new Repository(50, "data-platform"),
                new Repository(60, "release-service")
        );

        repositories.forEach(service::register);

        List<MergeCandidate> candidates = List.of(
                new MergeCandidate(30, 25, true),
                new MergeCandidate(50, 25, false),
                new MergeCandidate(99, 5, true),
                new MergeCandidate(60, 75, true)
        );

        for (MergeCandidate candidate : candidates) {
            System.out.printf(
                    "repository=%d risk=%d checks=%s eligible=%s%n",
                    candidate.repositoryId(),
                    candidate.riskScore(),
                    candidate.checksPassing(),
                    service.canMerge(candidate)
            );
        }

        System.out.println(service.healthReport());

        try {
            service.register(new Repository(30, "duplicate"));
        } catch (IllegalArgumentException ex) {
            System.out.println("Expected duplicate registration failure: " + ex.getMessage());
        }

        /*
         * AVL trees provide tighter height control than Red-Black trees.
         * Red-Black trees normally provide cheaper update balancing and are
         * common when update-heavy workloads matter more than strict height.
         * Both preserve logarithmic search/update bounds.
         */
    }
}
