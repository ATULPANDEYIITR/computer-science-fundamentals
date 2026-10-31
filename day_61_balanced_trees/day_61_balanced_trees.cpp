#include <algorithm>
#include <cassert>
#include <iostream>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

enum class Color { Red, Black };

struct RBNode {
    int key;
    Color color;
    RBNode* left;
    RBNode* right;
    RBNode* parent;

    explicit RBNode(int value)
        : key(value), color(Color::Red), left(nullptr), right(nullptr), parent(nullptr) {}
};

class RepositoryIndex {
private:
    struct AVLNode {
        int key;
        int height{1};
        std::unique_ptr<AVLNode> left;
        std::unique_ptr<AVLNode> right;

        explicit AVLNode(int value) : key(value) {}
    };

    std::unique_ptr<AVLNode> avlRoot_;
    RBNode* rbRoot_{nullptr};
    std::vector<std::unique_ptr<RBNode>> rbStorage_;

    static int height(const std::unique_ptr<AVLNode>& node) {
        return node ? node->height : 0;
    }

    static void updateHeight(AVLNode* node) {
        node->height = 1 + std::max(height(node->left), height(node->right));
    }

    static int balance(const AVLNode* node) {
        return node ? height(node->left) - height(node->right) : 0;
    }

    static std::unique_ptr<AVLNode> rotateLeft(std::unique_ptr<AVLNode> x) {
        if (!x || !x->right) throw std::logic_error("Invalid AVL left rotation");

        auto y = std::move(x->right);
        x->right = std::move(y->left);
        updateHeight(x.get());
        y->left = std::move(x);
        updateHeight(y.get());
        return y;
    }

    static std::unique_ptr<AVLNode> rotateRight(std::unique_ptr<AVLNode> y) {
        if (!y || !y->left) throw std::logic_error("Invalid AVL right rotation");

        auto x = std::move(y->left);
        y->left = std::move(x->right);
        updateHeight(y.get());
        x->right = std::move(y);
        updateHeight(x.get());
        return x;
    }

    static std::unique_ptr<AVLNode> avlInsert(
        std::unique_ptr<AVLNode> node, int key) {

        if (!node) return std::make_unique<AVLNode>(key);

        if (key < node->key) {
            node->left = avlInsert(std::move(node->left), key);
        } else if (key > node->key) {
            node->right = avlInsert(std::move(node->right), key);
        } else {
            throw std::invalid_argument("Duplicate repository key");
        }

        updateHeight(node.get());
        const int b = balance(node.get());

        if (b > 1 && key < node->left->key)
            return rotateRight(std::move(node));

        if (b < -1 && key > node->right->key)
            return rotateLeft(std::move(node));

        if (b > 1 && key > node->left->key) {
            node->left = rotateLeft(std::move(node->left));
            return rotateRight(std::move(node));
        }

        if (b < -1 && key < node->right->key) {
            node->right = rotateRight(std::move(node->right));
            return rotateLeft(std::move(node));
        }

        return node;
    }

    static bool avlContains(const AVLNode* node, int key) {
        while (node) {
            if (key == node->key) return true;
            node = key < node->key ? node->left.get() : node->right.get();
        }
        return false;
    }

    static void inorder(const AVLNode* node, std::vector<int>& output) {
        if (!node) return;
        inorder(node->left.get(), output);
        output.push_back(node->key);
        inorder(node->right.get(), output);
    }

    static Color colorOf(const RBNode* node) {
        return node ? node->color : Color::Black;
    }

    void leftRotate(RBNode* x) {
        RBNode* y = x->right;
        if (!y) throw std::logic_error("Invalid Red-Black left rotation");

        x->right = y->left;
        if (y->left) y->left->parent = x;

        y->parent = x->parent;
        if (!x->parent) rbRoot_ = y;
        else if (x == x->parent->left) x->parent->left = y;
        else x->parent->right = y;

        y->left = x;
        x->parent = y;
    }

    void rightRotate(RBNode* y) {
        RBNode* x = y->left;
        if (!x) throw std::logic_error("Invalid Red-Black right rotation");

        y->left = x->right;
        if (x->right) x->right->parent = y;

        x->parent = y->parent;
        if (!y->parent) rbRoot_ = x;
        else if (y == y->parent->left) y->parent->left = x;
        else y->parent->right = x;

        x->right = y;
        y->parent = x;
    }

    void fixRedBlackInsert(RBNode* z) {
        while (z->parent && z->parent->color == Color::Red) {
            RBNode* parent = z->parent;
            RBNode* grand = parent->parent;
            if (!grand) break;

            if (parent == grand->left) {
                RBNode* uncle = grand->right;

                if (colorOf(uncle) == Color::Red) {
                    parent->color = Color::Black;
                    uncle->color = Color::Black;
                    grand->color = Color::Red;
                    z = grand;
                } else {
                    if (z == parent->right) {
                        z = parent;
                        leftRotate(z);
                        parent = z->parent;
                    }

                    parent->color = Color::Black;
                    grand->color = Color::Red;
                    rightRotate(grand);
                }
            } else {
                RBNode* uncle = grand->left;

                if (colorOf(uncle) == Color::Red) {
                    parent->color = Color::Black;
                    uncle->color = Color::Black;
                    grand->color = Color::Red;
                    z = grand;
                } else {
                    if (z == parent->left) {
                        z = parent;
                        rightRotate(z);
                        parent = z->parent;
                    }

                    parent->color = Color::Black;
                    grand->color = Color::Red;
                    leftRotate(grand);
                }
            }
        }

        if (rbRoot_) rbRoot_->color = Color::Black;
    }

public:
    void addRepositoryId(int id) {
        if (id < 0) throw std::invalid_argument("Repository ID cannot be negative");

        avlRoot_ = avlInsert(std::move(avlRoot_), id);

        auto node = std::make_unique<RBNode>(id);
        RBNode* raw = node.get();
        rbStorage_.push_back(std::move(node));

        RBNode* parent = nullptr;
        RBNode* current = rbRoot_;

        while (current) {
            parent = current;
            if (id < current->key) current = current->left;
            else if (id > current->key) current = current->right;
            else throw std::logic_error("RB tree diverged from AVL tree");
        }

        raw->parent = parent;
        if (!parent) rbRoot_ = raw;
        else if (id < parent->key) parent->left = raw;
        else parent->right = raw;

        fixRedBlackInsert(raw);
    }

    bool contains(int id) const {
        return avlContains(avlRoot_.get(), id);
    }

    std::vector<int> sortedIds() const {
        std::vector<int> result;
        inorder(avlRoot_.get(), result);
        return result;
    }

    int avlHeight() const {
        return height(avlRoot_);
    }

    void validateAVL() const {
        std::function<int(const AVLNode*, std::optional<int>, std::optional<int>)> check;
        check = [&](const AVLNode* node,
                    std::optional<int> low,
                    std::optional<int> high) -> int {
            if (!node) return 0;
            if (low && node->key <= *low) throw std::logic_error("AVL BST violation");
            if (high && node->key >= *high) throw std::logic_error("AVL BST violation");

            int left = check(node->left.get(), low, node->key);
            int right = check(node->right.get(), node->key, high);

            if (node->height != 1 + std::max(left, right))
                throw std::logic_error("AVL height violation");

            if (std::abs(left - right) > 1)
                throw std::logic_error("AVL balance violation");

            return node->height;
        };

        check(avlRoot_.get(), std::nullopt, std::nullopt);
    }

    void validateRB() const {
        if (rbRoot_ && rbRoot_->color != Color::Black)
            throw std::logic_error("Red-Black root must be black");

        std::function<int(const RBNode*)> check;
        check = [&](const RBNode* node) -> int {
            if (!node) return 1;

            if (node->color == Color::Red &&
                (colorOf(node->left) == Color::Red ||
                 colorOf(node->right) == Color::Red)) {
                throw std::logic_error("Consecutive red nodes");
            }

            int left = check(node->left);
            int right = check(node->right);

            if (left != right)
                throw std::logic_error("Red-Black black-height violation");

            return left + (node->color == Color::Black ? 1 : 0);
        };

        check(rbRoot_);
    }
};

int main() {
    try {
        RepositoryIndex index;

        // Sequential repository identifiers expose the difference between
        // an ordinary BST and balanced trees.
        for (int id = 1; id <= 64; ++id)
            index.addRepositoryId(id);

        index.validateAVL();
        index.validateRB();

        std::cout << "AVL height: " << index.avlHeight() << '\n';
        std::cout << "Contains repository 42: "
                  << std::boolalpha << index.contains(42) << '\n';
        std::cout << "Contains repository 999: "
                  << index.contains(999) << '\n';

        const auto ids = index.sortedIds();
        std::cout << "Smallest ID: " << ids.front() << '\n';
        std::cout << "Largest ID: " << ids.back() << '\n';

        try {
            index.addRepositoryId(42);
        } catch (const std::exception& ex) {
            std::cout << "Expected duplicate failure: " << ex.what() << '\n';
        }

        try {
            index.addRepositoryId(-7);
        } catch (const std::exception& ex) {
            std::cout << "Expected validation failure: " << ex.what() << '\n';
        }

        std::cout << "Both balanced-tree invariants validated.\n";
    } catch (const std::exception& ex) {
        std::cerr << "Fatal error: " << ex.what() << '\n';
        return 1;
    }

    return 0;
}
