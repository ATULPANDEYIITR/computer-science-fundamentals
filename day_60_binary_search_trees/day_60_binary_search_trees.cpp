#include <algorithm>
#include <cmath>
#include <iostream>
#include <memory>
#include <optional>
#include <queue>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

struct Node {
    int key;
    std::string value;
    std::unique_ptr<Node> left;
    std::unique_ptr<Node> right;
    int height = 1;

    Node(int input_key, std::string input_value)
        : key(input_key), value(std::move(input_value)) {}
};

class TreeIndex {
protected:
    std::unique_ptr<Node> root;
    std::size_t count = 0;

    static void validate_value(const std::string& value) {
        if (value.empty() || value.size() > 200) {
            throw std::invalid_argument(
                "Values must contain between 1 and 200 characters"
            );
        }
    }

public:
    virtual ~TreeIndex() = default;

    virtual bool insert(int key, const std::string& value) = 0;
    virtual bool erase(int key) = 0;
    virtual bool validate() const = 0;

    std::size_t size() const {
        return count;
    }

    std::optional<std::string> find(int key) const {
        const Node* current = root.get();

        while (current != nullptr) {
            if (key == current->key) {
                return current->value;
            }

            current = key < current->key
                ? current->left.get()
                : current->right.get();
        }

        return std::nullopt;
    }

    std::vector<std::pair<int, std::string>> inorder() const {
        std::vector<std::pair<int, std::string>> result;
        std::vector<const Node*> stack;
        const Node* current = root.get();

        while (current != nullptr || !stack.empty()) {
            while (current != nullptr) {
                stack.push_back(current);
                current = current->left.get();
            }

            current = stack.back();
            stack.pop_back();

            result.emplace_back(current->key, current->value);
            current = current->right.get();
        }

        return result;
    }

    std::vector<std::pair<int, std::string>>
    range_query(int lower, int upper) const {
        if (lower > upper) {
            throw std::invalid_argument(
                "Lower bound cannot exceed upper bound"
            );
        }

        std::vector<std::pair<int, std::string>> result;
        std::vector<const Node*> stack;
        const Node* current = root.get();

        while (current != nullptr || !stack.empty()) {
            while (current != nullptr) {
                if (current->key >= lower) {
                    stack.push_back(current);
                    current = current->left.get();
                } else {
                    current = current->right.get();
                }
            }

            if (stack.empty()) {
                break;
            }

            current = stack.back();
            stack.pop_back();

            if (current->key > upper) {
                break;
            }

            result.emplace_back(current->key, current->value);
            current = current->right.get();
        }

        return result;
    }

    std::pair<int, std::string> kth_smallest(std::size_t position) const {
        if (position == 0 || position > count) {
            throw std::out_of_range("Position is outside the tree");
        }

        std::vector<const Node*> stack;
        const Node* current = root.get();
        std::size_t visited = 0;

        while (current != nullptr || !stack.empty()) {
            while (current != nullptr) {
                stack.push_back(current);
                current = current->left.get();
            }

            current = stack.back();
            stack.pop_back();
            ++visited;

            if (visited == position) {
                return {current->key, current->value};
            }

            current = current->right.get();
        }

        throw std::logic_error("Tree size and traversal are inconsistent");
    }

    int height() const {
        if (!root) {
            return 0;
        }

        std::queue<std::pair<const Node*, int>> pending;
        pending.push({root.get(), 1});

        int maximum = 0;

        while (!pending.empty()) {
            const auto [node, depth] = pending.front();
            pending.pop();

            maximum = std::max(maximum, depth);

            if (node->left) {
                pending.push({node->left.get(), depth + 1});
            }

            if (node->right) {
                pending.push({node->right.get(), depth + 1});
            }
        }

        return maximum;
    }

    void print_report(const std::string& name) const {
        std::cout << "\n" << name << "\n";
        std::cout << "Node count: " << count << "\n";
        std::cout << "Height: " << height() << "\n";
        std::cout << "Valid: " << (validate() ? "yes" : "no") << "\n";

        std::cout << "Ordered records: ";
        for (const auto& [key, value] : inorder()) {
            std::cout << "(" << key << ", " << value << ") ";
        }
        std::cout << "\n";
    }
};

class BinarySearchTree final : public TreeIndex {
public:
    bool insert(int key, const std::string& value) override {
        validate_value(value);

        // A pointer to the owning unique_ptr allows insertion without
        // allocating parent pointers or recursively traversing the tree.
        std::unique_ptr<Node>* link = &root;

        while (*link) {
            if (key == (*link)->key) {
                (*link)->value = value;
                return false;
            }

            link = key < (*link)->key
                ? &((*link)->left)
                : &((*link)->right);
        }

        *link = std::make_unique<Node>(key, value);
        ++count;
        return true;
    }

    bool erase(int key) override {
        std::unique_ptr<Node>* link = &root;

        while (*link && (*link)->key != key) {
            link = key < (*link)->key
                ? &((*link)->left)
                : &((*link)->right);
        }

        if (!*link) {
            return false;
        }

        if ((*link)->left && (*link)->right) {
            // Replace a two-child node with its inorder successor.
            Node* target = link->get();
            std::unique_ptr<Node>* successor_link = &(target->right);

            while ((*successor_link)->left) {
                successor_link = &((*successor_link)->left);
            }

            target->key = (*successor_link)->key;
            target->value = (*successor_link)->value;

            auto successor = std::move(*successor_link);
            *successor_link = std::move(successor->right);
        } else {
            // Moving unique_ptr ownership safely replaces the removed node.
            auto removed = std::move(*link);
            *link = removed->left
                ? std::move(removed->left)
                : std::move(removed->right);
        }

        --count;
        return true;
    }

    bool validate() const override {
        using Frame = std::tuple<const Node*, long long, long long>;

        std::vector<Frame> stack;

        if (root) {
            stack.emplace_back(
                root.get(),
                std::numeric_limits<long long>::lowest(),
                std::numeric_limits<long long>::max()
            );
        }

        std::size_t visited = 0;

        while (!stack.empty()) {
            const auto [node, lower, upper] = stack.back();
            stack.pop_back();

            if (node->key <= lower || node->key >= upper) {
                return false;
            }

            ++visited;

            if (node->left) {
                stack.emplace_back(node->left.get(), lower, node->key);
            }

            if (node->right) {
                stack.emplace_back(node->right.get(), node->key, upper);
            }
        }

        return visited == count;
    }
};

class AvlTree final : public TreeIndex {
    static int node_height(const std::unique_ptr<Node>& node) {
        return node ? node->height : 0;
    }

    static void refresh(Node* node) {
        node->height = 1 + std::max(
            node_height(node->left),
            node_height(node->right)
        );
    }

    static int balance_factor(const Node* node) {
        return node_height(node->left) - node_height(node->right);
    }

    static std::unique_ptr<Node> rotate_right(std::unique_ptr<Node> root) {
        if (!root || !root->left) {
            throw std::logic_error("Invalid right rotation");
        }

        auto pivot = std::move(root->left);
        root->left = std::move(pivot->right);
        pivot->right = std::move(root);

        refresh(pivot->right.get());
        refresh(pivot.get());

        return pivot;
    }

    static std::unique_ptr<Node> rotate_left(std::unique_ptr<Node> root) {
        if (!root || !root->right) {
            throw std::logic_error("Invalid left rotation");
        }

        auto pivot = std::move(root->right);
        root->right = std::move(pivot->left);
        pivot->left = std::move(root);

        refresh(pivot->left.get());
        refresh(pivot.get());

        return pivot;
    }

    static std::unique_ptr<Node> rebalance(std::unique_ptr<Node> node) {
        if (!node) {
            return nullptr;
        }

        refresh(node.get());
        const int balance = balance_factor(node.get());

        if (balance > 1) {
            if (balance_factor(node->left.get()) < 0) {
                node->left = rotate_left(std::move(node->left));
            }

            return rotate_right(std::move(node));
        }

        if (balance < -1) {
            if (balance_factor(node->right.get()) > 0) {
                node->right = rotate_right(std::move(node->right));
            }

            return rotate_left(std::move(node));
        }

        return node;
    }

    static std::unique_ptr<Node> insert_node(
        std::unique_ptr<Node> node,
        int key,
        const std::string& value,
        bool& inserted
    ) {
        if (!node) {
            inserted = true;
            return std::make_unique<Node>(key, value);
        }

        if (key < node->key) {
            node->left = insert_node(
                std::move(node->left), key, value, inserted
            );
        } else if (key > node->key) {
            node->right = insert_node(
                std::move(node->right), key, value, inserted
            );
        } else {
            node->value = value;
            return node;
        }

        return rebalance(std::move(node));
    }

    static const Node* minimum(const Node* node) {
        while (node->left) {
            node = node->left.get();
        }

        return node;
    }

    static std::unique_ptr<Node> erase_node(
        std::unique_ptr<Node> node,
        int key,
        bool& erased
    ) {
        if (!node) {
            return nullptr;
        }

        if (key < node->key) {
            node->left = erase_node(
                std::move(node->left), key, erased
            );
        } else if (key > node->key) {
            node->right = erase_node(
                std::move(node->right), key, erased
            );
        } else {
            erased = true;

            if (!node->left) {
                return std::move(node->right);
            }

            if (!node->right) {
                return std::move(node->left);
            }

            const Node* successor = minimum(node->right.get());
            node->key = successor->key;
            node->value = successor->value;

            bool successor_erased = false;
            node->right = erase_node(
                std::move(node->right),
                successor->key,
                successor_erased
            );
        }

        return rebalance(std::move(node));
    }

    static bool validate_avl(
        const Node* node,
        long long lower,
        long long upper,
        int& calculated_height,
        std::size_t& visited
    ) {
        if (!node) {
            calculated_height = 0;
            return true;
        }

        if (node->key <= lower || node->key >= upper) {
            return false;
        }

        int left_height = 0;
        int right_height = 0;

        if (!validate_avl(
                node->left.get(), lower, node->key,
                left_height, visited
            )) {
            return false;
        }

        if (!validate_avl(
                node->right.get(), node->key, upper,
                right_height, visited
            )) {
            return false;
        }

        ++visited;
        calculated_height = 1 + std::max(left_height, right_height);

        return node->height == calculated_height &&
            std::abs(left_height - right_height) <= 1;
    }

public:
    bool insert(int key, const std::string& value) override {
        validate_value(value);

        bool inserted = false;
        root = insert_node(std::move(root), key, value, inserted);

        if (inserted) {
            ++count;
        }

        return inserted;
    }

    bool erase(int key) override {
        if (!find(key)) {
            return false;
        }

        bool erased = false;
        root = erase_node(std::move(root), key, erased);

        if (erased) {
            --count;
        }

        return erased;
    }

    bool validate() const override {
        int calculated_height = 0;
        std::size_t visited = 0;

        const bool valid = validate_avl(
            root.get(),
            std::numeric_limits<long long>::lowest(),
            std::numeric_limits<long long>::max(),
            calculated_height,
            visited
        );

        return valid && visited == count;
    }
};

void exercise_tree(TreeIndex& tree, const std::string& label) {
    const std::vector<std::pair<int, std::string>> records = {
        {50, "gateway"},
        {30, "database"},
        {70, "monitor"},
        {20, "worker"},
        {40, "cache"},
        {60, "scheduler"},
        {80, "backup"},
        {65, "logger"}
    };

    for (const auto& [key, value] : records) {
        tree.insert(key, value);
    }

    tree.insert(50, "gateway-updated");

    if (tree.find(50) != std::optional<std::string>("gateway-updated")) {
        throw std::runtime_error("Updated record was not found");
    }

    if (tree.find(999).has_value()) {
        throw std::runtime_error("Unexpected record found");
    }

    // Exercise leaf, one-child, and two-child deletion.
    if (!tree.erase(20) || !tree.erase(60) || !tree.erase(70)) {
        throw std::runtime_error("Expected deletion failed");
    }

    if (tree.erase(999)) {
        throw std::runtime_error("Missing-key deletion should fail");
    }

    if (!tree.validate()) {
        throw std::runtime_error("Tree invariant validation failed");
    }

    tree.print_report(label);

    std::cout << "Range 35..70: ";
    for (const auto& [key, value] : tree.range_query(35, 70)) {
        std::cout << "(" << key << ", " << value << ") ";
    }
    std::cout << "\n";

    const auto first = tree.kth_smallest(1);
    std::cout << "Smallest: (" << first.first << ", "
              << first.second << ")\n";
}

void compare_sorted_insertions() {
    BinarySearchTree bst;
    AvlTree avl;

    // The sorted sequence produces a degenerate ordinary BST.
    // The AVL implementation performs rotations during each update.
    for (int key = 1; key <= 1000; ++key) {
        bst.insert(key, "asset-" + std::to_string(key));
        avl.insert(key, "asset-" + std::to_string(key));
    }

    if (!bst.validate() || !avl.validate()) {
        throw std::runtime_error("Large tree validation failed");
    }

    if (bst.height() != 1000 || avl.height() > 11) {
        throw std::runtime_error("Unexpected tree height");
    }

    bst.erase(500);
    avl.erase(500);

    std::cout << "\nSorted insertion comparison\n";
    std::cout << "Input records: 1000\n";
    std::cout << "Unbalanced BST height: " << bst.height() << "\n";
    std::cout << "AVL height: " << avl.height() << "\n";
    std::cout << "BST valid: " << (bst.validate() ? "yes" : "no") << "\n";
    std::cout << "AVL valid: " << (avl.validate() ? "yes" : "no") << "\n";
}

int main() {
    try {
        BinarySearchTree ordinary_tree;
        AvlTree balanced_tree;

        exercise_tree(ordinary_tree, "Unbalanced binary search tree");
        exercise_tree(balanced_tree, "AVL balanced tree");
        compare_sorted_insertions();

        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Execution failed: " << error.what() << "\n";
        return 1;
    }
}
