#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstddef>
#include <iostream>
#include <limits>
#include <queue>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

using namespace std;

class GreedyError : public runtime_error {
public:
    explicit GreedyError(const string& message)
        : runtime_error(message) {}
};

struct Activity {
    string id;
    int start;
    int finish;
};

struct ActivityResult {
    vector<Activity> selected;
    vector<Activity> rejected;
};

class ActivitySelection {
public:
    static ActivityResult solve(const vector<Activity>& activities) {
        unordered_set<string> ids;

        for (const auto& activity : activities) {
            if (activity.id.empty()) {
                throw GreedyError("Activity ID cannot be empty.");
            }

            if (activity.start < 0 ||
                activity.finish <= activity.start) {
                throw GreedyError("Invalid activity interval.");
            }

            if (!ids.insert(activity.id).second) {
                throw GreedyError("Duplicate activity ID.");
            }
        }

        vector<Activity> ordered = activities;

        sort(
            ordered.begin(),
            ordered.end(),
            [](const Activity& a, const Activity& b) {
                if (a.finish != b.finish)
                    return a.finish < b.finish;

                if (a.start != b.start)
                    return a.start < b.start;

                return a.id < b.id;
            }
        );

        ActivityResult result;
        int lastFinish = -1;

        for (const auto& activity : ordered) {
            if (activity.start >= lastFinish) {
                result.selected.push_back(activity);
                lastFinish = activity.finish;
            } else {
                result.rejected.push_back(activity);
            }
        }

        return result;
    }
};

struct Item {
    string id;
    double value;
    double weight;
};

struct KnapsackResult {
    vector<pair<string, double>> selectedFractions;
    double totalValue = 0.0;
    double usedWeight = 0.0;
};

class FractionalKnapsack {
public:
    static KnapsackResult solve(
        vector<Item> items,
        double capacity
    ) {
        if (!isfinite(capacity) || capacity < 0) {
            throw GreedyError("Invalid capacity.");
        }

        unordered_set<string> ids;

        for (const auto& item : items) {
            if (item.id.empty()) {
                throw GreedyError("Item ID cannot be empty.");
            }

            if (!ids.insert(item.id).second) {
                throw GreedyError("Duplicate item ID.");
            }

            if (!isfinite(item.value) || item.value < 0 ||
                !isfinite(item.weight) || item.weight <= 0) {
                throw GreedyError("Invalid item value or weight.");
            }
        }

        // Descending value-to-weight ratio.
        sort(
            items.begin(),
            items.end(),
            [](const Item& a, const Item& b) {
                const double ratioA = a.value / a.weight;
                const double ratioB = b.value / b.weight;

                if (ratioA != ratioB)
                    return ratioA > ratioB;

                return a.id < b.id;
            }
        );

        KnapsackResult result;
        double remaining = capacity;

        for (const auto& item : items) {
            if (remaining <= 0) break;

            const double fraction = min(
                1.0,
                remaining / item.weight
            );

            if (fraction <= 0) continue;

            result.selectedFractions.emplace_back(
                item.id,
                fraction
            );

            result.totalValue += fraction * item.value;
            result.usedWeight += fraction * item.weight;
            remaining = max(0.0, capacity - result.usedWeight);
        }

        return result;
    }
};

class HuffmanCoding {
private:
    struct Node {
        char symbol;
        unsigned long long frequency;
        Node* left;
        Node* right;

        Node(char s, unsigned long long f)
            : symbol(s), frequency(f),
              left(nullptr), right(nullptr) {}

        Node(Node* l, Node* r)
            : symbol('\0'),
              frequency(l->frequency + r->frequency),
              left(l), right(r) {}

        bool isLeaf() const {
            return left == nullptr && right == nullptr;
        }
    };

    struct Compare {
        bool operator()(const Node* a, const Node* b) const {
            return a->frequency > b->frequency;
        }
    };

    Node* root = nullptr;
    unordered_map<char, string> codes;

    void generateCodes(Node* node, const string& prefix) {
        if (!node) return;

        if (node->isLeaf()) {
            codes[node->symbol] = prefix.empty() ? "0" : prefix;
            return;
        }

        generateCodes(node->left, prefix + "0");
        generateCodes(node->right, prefix + "1");
    }

    static void destroy(Node* node) {
        if (!node) return;

        destroy(node->left);
        destroy(node->right);
        delete node;
    }

public:
    explicit HuffmanCoding(
        const unordered_map<char, unsigned long long>& frequencies
    ) {
        if (frequencies.empty()) {
            throw GreedyError("Frequency table cannot be empty.");
        }

        priority_queue<Node*, vector<Node*>, Compare> heap;

        vector<pair<char, unsigned long long>> entries(
            frequencies.begin(),
            frequencies.end()
        );

        sort(entries.begin(), entries.end());

        try {
            for (const auto& entry : entries) {
                if (entry.second == 0) {
                    throw GreedyError("Frequencies must be positive.");
                }

                heap.push(new Node(entry.first, entry.second));
            }

            while (heap.size() > 1) {
                Node* left = heap.top();
                heap.pop();

                Node* right = heap.top();
                heap.pop();

                if (left->frequency >
                    numeric_limits<unsigned long long>::max()
                    - right->frequency) {
                    destroy(left);
                    destroy(right);

                    throw GreedyError("Frequency overflow.");
                }

                Node* parent = new Node(left, right);
                heap.push(parent);
            }

            root = heap.top();
            heap.pop();

            generateCodes(root, "");
        } catch (...) {
            while (!heap.empty()) {
                destroy(heap.top());
                heap.pop();
            }

            throw;
        }
    }

    HuffmanCoding(const HuffmanCoding&) = delete;
    HuffmanCoding& operator=(const HuffmanCoding&) = delete;

    ~HuffmanCoding() {
        destroy(root);
    }

    string encode(const string& message) const {
        string encoded;

        for (char symbol : message) {
            auto it = codes.find(symbol);

            if (it == codes.end()) {
                throw GreedyError("Unknown symbol in message.");
            }

            encoded += it->second;
        }

        return encoded;
    }

    string decode(const string& encoded) const {
        for (char bit : encoded) {
            if (bit != '0' && bit != '1') {
                throw GreedyError("Invalid binary character.");
            }
        }

        if (root->isLeaf()) {
            return string(encoded.size(), root->symbol);
        }

        string decoded;
        Node* current = root;

        for (char bit : encoded) {
            current = (bit == '0')
                ? current->left
                : current->right;

            if (!current) {
                throw GreedyError("Invalid encoded sequence.");
            }

            if (current->isLeaf()) {
                decoded.push_back(current->symbol);
                current = root;
            }
        }

        if (current != root) {
            throw GreedyError("Incomplete Huffman codeword.");
        }

        return decoded;
    }

    const unordered_map<char, string>& getCodes() const {
        return codes;
    }
};

class ZeroOneKnapsack {
public:
    static long long solve(
        const vector<Item>& items,
        int capacity
    ) {
        if (capacity < 0) {
            throw GreedyError("Capacity cannot be negative.");
        }

        vector<long long> dp(capacity + 1, 0);

        for (const auto& item : items) {
            if (!isfinite(item.value) || item.value < 0 ||
                !isfinite(item.weight) ||
                item.weight <= 0 ||
                floor(item.weight) != item.weight ||
                floor(item.value) != item.value) {
                throw GreedyError(
                    "Dynamic programming requires nonnegative "
                    "integer values and positive integer weights."
                );
            }

            if (item.weight > capacity) continue;

            const int weight = static_cast<int>(item.weight);
            const long long value =
                static_cast<long long>(item.value);

            for (int w = capacity; w >= weight; --w) {
                dp[w] = max(
                    dp[w],
                    dp[w - weight] + value
                );
            }
        }

        return dp[capacity];
    }
};

void runTests() {
    const auto result = ActivitySelection::solve({
        {"A", 1, 3},
        {"B", 3, 5},
        {"C", 2, 4}
    });

    assert(result.selected.size() == 2);
    assert(result.selected[0].id == "A");
    assert(result.selected[1].id == "B");

    const auto fractional = FractionalKnapsack::solve({
        {"A", 60, 10},
        {"B", 100, 20},
        {"C", 120, 30}
    }, 50);

    assert(abs(fractional.totalValue - 240.0) < 1e-9);

    HuffmanCoding codec({
        {'a', 45},
        {'b', 13},
        {'c', 12},
        {'d', 16},
        {'e', 9},
        {'f', 5}
    });

    const string message = "abcdef";
    assert(codec.decode(codec.encode(message)) == message);

    const long long optimal = ZeroOneKnapsack::solve({
        {"A", 60, 10},
        {"B", 100, 20},
        {"C", 120, 30}
    }, 50);

    assert(optimal == 220);

    cout << "All C++17 tests passed.\n";
}

int main() {
    try {
        runTests();

        const vector<Activity> activities = {
            {"A101", 1, 4},
            {"A102", 3, 5},
            {"A103", 0, 6},
            {"A104", 5, 7},
            {"A105", 8, 9},
            {"A106", 5, 9},
            {"A107", 2, 3}
        };

        const auto activityResult =
            ActivitySelection::solve(activities);

        cout << "\nACTIVITY SELECTION\n";

        for (const auto& activity : activityResult.selected) {
            cout << activity.id
                 << " [" << activity.start
                 << ", " << activity.finish << "]\n";
        }

        cout << "Selected count: "
             << activityResult.selected.size() << '\n';

        const vector<Item> items = {
            {"Gold", 60, 10},
            {"Silver", 100, 20},
            {"Copper", 120, 30}
        };

        const auto fractional =
            FractionalKnapsack::solve(items, 50);

        cout << "\nFRACTIONAL KNAPSACK\n";

        for (const auto& selection :
             fractional.selectedFractions) {
            cout << selection.first
                 << ": " << selection.second * 100
                 << "%\n";
        }

        cout << "Maximum value: "
             << fractional.totalValue << '\n';

        const unordered_map<char, unsigned long long> frequencies = {
            {'a', 45},
            {'b', 13},
            {'c', 12},
            {'d', 16},
            {'e', 9},
            {'f', 5}
        };

        HuffmanCoding codec(frequencies);

        const string message = "greedy algorithms";
        const string encoded = codec.encode(message);

        cout << "\nHUFFMAN CODING\n";

        vector<pair<char, string>> codes(
            codec.getCodes().begin(),
            codec.getCodes().end()
        );

        sort(codes.begin(), codes.end());

        for (const auto& entry : codes) {
            cout << entry.first << " -> "
                 << entry.second << '\n';
        }

        cout << "Encoded bits: " << encoded << '\n';
        cout << "Decoded message: "
             << codec.decode(encoded) << '\n';

        cout << "\nGREEDY VS EXACT OPTIMIZATION\n";

        double greedyValue = 0;
        double remaining = 50;

        vector<Item> ordered = items;

        sort(
            ordered.begin(),
            ordered.end(),
            [](const Item& a, const Item& b) {
                return a.value / a.weight >
                       b.value / b.weight;
            }
        );

        for (const auto& item : ordered) {
            if (item.weight <= remaining) {
                greedyValue += item.value;
                remaining -= item.weight;
            }
        }

        const long long optimal =
            ZeroOneKnapsack::solve(items, 50);

        cout << "0/1 greedy value: " << greedyValue << '\n';
        cout << "0/1 optimal value: " << optimal << '\n';

        cout << "\nExecution completed successfully.\n";

    } catch (const exception& error) {
        cerr << "Execution error: "
             << error.what() << '\n';

        return 1;
    }

    return 0;
}
