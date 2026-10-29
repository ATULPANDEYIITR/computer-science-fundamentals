#include <algorithm>
#include <cassert>
#include <exception>
#include <iostream>
#include <limits>
#include <optional>
#include <queue>
#include <stdexcept>
#include <string>
#include <vector>

enum class TraversalOrder {
    Preorder,
    Inorder,
    Postorder,
    LevelOrder
};

struct TreeNode {
    int value;
    TreeNode* left;
    TreeNode* right;

    explicit TreeNode(int value)
        : value(value), left(nullptr), right(nullptr) {}
};

class BinaryTree {
protected:
    TreeNode* root_ = nullptr;

    static void destroy(TreeNode* node) noexcept {
        if (!node) {
            return;
        }
        destroy(node->left);
        destroy(node->right);
        delete node;
    }

public:
    BinaryTree() = default;

    BinaryTree(const BinaryTree&) = delete;
    BinaryTree& operator=(const BinaryTree&) = delete;

    virtual ~BinaryTree() {
        destroy(root_);
    }

    std::vector<int> preorder() const {
        std::vector<int> result;
        if (!root_) {
            return result;
        }

        std::vector<TreeNode*> stack{root_};

        while (!stack.empty()) {
            TreeNode* node = stack.back();
            stack.pop_back();

            result.push_back(node->value);

            if (node->right) {
                stack.push_back(node->right);
            }
            if (node->left) {
                stack.push_back(node->left);
            }
        }

        return result;
    }

    std::vector<int> inorder() const {
        std::vector<int> result;
        std::vector<TreeNode*> stack;
        TreeNode* current = root_;

        while (current || !stack.empty()) {
            while (current) {
                stack.push_back(current);
                current = current->left;
            }

            current = stack.back();
            stack.pop_back();

            result.push_back(current->value);
            current = current->right;
        }

        return result;
    }

    std::vector<int> postorder() const {
        std::vector<int> result;
        if (!root_) {
            return result;
        }

        std::vector<std::pair<TreeNode*, bool>> stack;
        stack.push_back({root_, false});

        while (!stack.empty()) {
            auto [node, expanded] = stack.back();
            stack.pop_back();

            if (expanded) {
                result.push_back(node->value);
                continue;
            }

            stack.push_back({node, true});

            if (node->right) {
                stack.push_back({node->right, false});
            }
            if (node->left) {
                stack.push_back({node->left, false});
            }
        }

        return result;
    }

    std::vector<int> levelOrder() const {
        std::vector<int> result;
        if (!root_) {
            return result;
        }

        std::queue<TreeNode*> queue;
        queue.push(root_);

        while (!queue.empty()) {
            TreeNode* node = queue.front();
            queue.pop();

            result.push_back(node->value);

            if (node->left) {
                queue.push(node->left);
            }
            if (node->right) {
                queue.push(node->right);
            }
        }

        return result;
    }

    int height() const {
        if (!root_) {
            return 0;
        }

        std::queue<TreeNode*> queue;
        queue.push(root_);
        int height = 0;

        while (!queue.empty()) {
            const std::size_t levelSize = queue.size();
            ++height;

            for (std::size_t i = 0; i < levelSize; ++i) {
                TreeNode* node = queue.front();
                queue.pop();

                if (node->left) {
                    queue.push(node->left);
                }
                if (node->right) {
                    queue.push(node->right);
                }
            }
        }

        return height;
    }

    const TreeNode* root() const noexcept {
        return root_;
    }
};

class BinarySearchTree final : public BinaryTree {
private:
    static bool validateNode(
        const TreeNode* node,
        std::optional<int> lower,
        std::optional<int> upper
    ) {
        if (!node) {
            return true;
        }

        if (lower && node->value <= *lower) {
            return false;
        }

        if (upper && node->value >= *upper) {
            return false;
        }

        return validateNode(node->left, lower, node->value) &&
               validateNode(node->right, node->value, upper);
    }

public:
    void insert(int value) {
        if (!root_) {
            root_ = new TreeNode(value);
            return;
        }

        TreeNode* current = root_;

        while (true) {
            if (value == current->value) {
                throw std::invalid_argument("Duplicate keys are not permitted.");
            }

            if (value < current->value) {
                if (!current->left) {
                    current->left = new TreeNode(value);
                    return;
                }
                current = current->left;
            } else {
                if (!current->right) {
                    current->right = new TreeNode(value);
                    return;
                }
                current = current->right;
            }
        }
    }

    bool contains(int value) const {
        const TreeNode* current = root_;

        while (current) {
            if (current->value == value) {
                return true;
            }
            current = value < current->value
                ? current->left
                : current->right;
        }

        return false;
    }

    bool isValid() const {
        return validateNode(root_, std::nullopt, std::nullopt);
    }

    std::vector<int> rangeQuery(int low, int high) const {
        if (low > high) {
            throw std::invalid_argument("Invalid range.");
        }

        std::vector<int> result;

        // The BST ordering lets us prune subtrees that cannot contain
        // values in the requested interval.
        std::vector<const TreeNode*> stack;
        if (root_) {
            stack.push_back(root_);
        }

        while (!stack.empty()) {
            const TreeNode* node = stack.back();
            stack.pop_back();

            if (node->value >= low && node->value <= high) {
                result.push_back(node->value);
            }

            if (node->left && node->value > low) {
                stack.push_back(node->left);
            }

            if (node->right && node->value < high) {
                stack.push_back(node->right);
            }
        }

        std::sort(result.begin(), result.end());
        return result;
    }
};

class RepositoryTreeIndex {
private:
    BinarySearchTree index_;

public:
    void addCommitId(int commitId) {
        if (commitId < 0) {
            throw std::invalid_argument("Commit identifiers cannot be negative.");
        }
        index_.insert(commitId);
    }

    bool containsCommit(int commitId) const {
        return index_.contains(commitId);
    }

    std::vector<int> commitsInRange(int first, int last) const {
        return index_.rangeQuery(first, last);
    }

    bool healthy() const {
        return index_.isValid();
    }
};

void printVector(const std::string& label, const std::vector<int>& values) {
    std::cout << label << ": [";

    for (std::size_t i = 0; i < values.size(); ++i) {
        if (i != 0) {
            std::cout << ", ";
        }
        std::cout << values[i];
    }

    std::cout << "]\n";
}

int main() {
    try {
        BinarySearchTree tree;

        for (int value : {50, 30, 70, 20, 40, 60, 80, 65}) {
            tree.insert(value);
        }

        assert(tree.isValid());
        assert(tree.contains(65));
        assert(!tree.contains(99));
        assert(tree.height() == 4);

        printVector("Preorder", tree.preorder());
        printVector("Inorder", tree.inorder());
        printVector("Postorder", tree.postorder());
        printVector("Level order", tree.levelOrder());
        printVector("Range 35..70", tree.rangeQuery(35, 70));

        RepositoryTreeIndex commitIndex;

        for (int commitId : {1001, 1007, 1012, 1020, 1035}) {
            commitIndex.addCommitId(commitId);
        }

        assert(commitIndex.healthy());
        assert(commitIndex.containsCommit(1020));
        assert(!commitIndex.containsCommit(999));

        printVector(
            "Indexed commits 1000..1020",
            commitIndex.commitsInRange(1000, 1020)
        );

        try {
            tree.insert(50);
        } catch (const std::invalid_argument& error) {
            std::cout << "Expected duplicate failure: "
                      << error.what() << '\n';
        }

        try {
            commitIndex.addCommitId(-4);
        } catch (const std::invalid_argument& error) {
            std::cout << "Expected validation failure: "
                      << error.what() << '\n';
        }

        // Complexity:
        // Traversals are O(n) time.
        // BFS uses O(w) space, where w is maximum tree width.
        // BST operations are O(h), with O(log n) expected for balanced
        // trees and O(n) for a completely skewed tree.
        //
        // Ownership:
        // BinaryTree owns all nodes and recursively releases them in its
        // destructor. Copying is disabled to prevent double deletion.
        //
        // Production trade-off:
        // This deliberately uses an unbalanced BST to expose the effect
        // of tree shape. A production index requiring predictable latency
        // should use an AVL tree, red-black tree, or another balanced index.

        std::cout << "Tree case study completed successfully.\n";
    } catch (const std::exception& error) {
        std::cerr << "Fatal error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
