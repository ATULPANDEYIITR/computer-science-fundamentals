#include <algorithm>
#include <chrono>
#include <cstdint>
#include <exception>
#include <functional>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>

using namespace std;

enum class SearchStatus {
    Completed,
    LimitExceeded
};

struct SearchStatistics {
    uint64_t nodes = 0;
    uint64_t solutions = 0;
    uint64_t pruned = 0;
    size_t maximumDepth = 0;
    double elapsedMilliseconds = 0.0;
};

struct SearchLimits {
    uint64_t maximumNodes = 1000000;
    uint64_t maximumSolutions = 100000;
};

class SearchLimitExceeded : public runtime_error {
public:
    explicit SearchLimitExceeded(const string& message)
        : runtime_error(message) {}
};

class SearchEngine {
private:
    SearchLimits limits;
    SearchStatistics stats;

    chrono::steady_clock::time_point startTime;

public:
    explicit SearchEngine(SearchLimits configuration = {})
        : limits(configuration) {
        if (limits.maximumNodes == 0 ||
            limits.maximumSolutions == 0) {
            throw invalid_argument("Search limits must be positive");
        }
    }

    void reset() {
        stats = SearchStatistics{};
        startTime = chrono::steady_clock::now();
    }

    void visit(size_t depth) {
        ++stats.nodes;
        stats.maximumDepth = max(stats.maximumDepth, depth);

        if (stats.nodes > limits.maximumNodes) {
            throw SearchLimitExceeded("Maximum node count exceeded");
        }
    }

    void recordSolution() {
        if (stats.solutions >= limits.maximumSolutions) {
            throw SearchLimitExceeded("Maximum solution count exceeded");
        }

        ++stats.solutions;
    }

    void prune() {
        ++stats.pruned;
    }

    void finish() {
        auto endTime = chrono::steady_clock::now();

        stats.elapsedMilliseconds =
            chrono::duration<double, milli>(
                endTime - startTime
            ).count();
    }

    const SearchStatistics& statistics() const {
        return stats;
    }
};


class PermutationSolver {
private:
    vector<int> values;
    vector<int> path;
    vector<bool> used;
    vector<vector<int>> results;

    SearchEngine engine;

    void backtrack() {
        engine.visit(path.size());

        if (path.size() == values.size()) {
            engine.recordSolution();
            results.push_back(path);
            return;
        }

        for (size_t i = 0; i < values.size(); ++i) {
            if (used[i]) continue;

            if (
                i > 0 &&
                values[i] == values[i - 1] &&
                !used[i - 1]
            ) {
                engine.prune();
                continue;
            }

            used[i] = true;
            path.push_back(values[i]);

            backtrack();

            path.pop_back();
            used[i] = false;
        }
    }

public:
    explicit PermutationSolver(
        vector<int> input,
        SearchLimits limits = {}
    ) : values(move(input)), engine(limits) {
        sort(values.begin(), values.end());
        used.assign(values.size(), false);
    }

    vector<vector<int>> solve() {
        results.clear();
        path.clear();
        fill(used.begin(), used.end(), false);

        engine.reset();

        try {
            backtrack();
        } catch (...) {
            engine.finish();
            throw;
        }

        engine.finish();
        return results;
    }

    const SearchStatistics& statistics() const {
        return engine.statistics();
    }
};


class CombinationSolver {
private:
    vector<int> values;
    vector<int> path;
    vector<vector<int>> results;
    size_t selectionSize;

    SearchEngine engine;

    void backtrack(size_t start) {
        engine.visit(path.size());

        if (path.size() == selectionSize) {
            engine.recordSolution();
            results.push_back(path);
            return;
        }

        size_t remaining = selectionSize - path.size();

        if (values.size() - start < remaining) {
            engine.prune();
            return;
        }

        size_t last = values.size() - remaining;

        for (size_t i = start; i <= last; ++i) {
            if (i > start && values[i] == values[i - 1]) {
                engine.prune();
                continue;
            }

            path.push_back(values[i]);
            backtrack(i + 1);
            path.pop_back();
        }
    }

public:
    CombinationSolver(
        vector<int> input,
        size_t k,
        SearchLimits limits = {}
    ) : values(move(input)),
        selectionSize(k),
        engine(limits) {

        if (k > values.size()) {
            throw invalid_argument("Invalid combination size");
        }

        sort(values.begin(), values.end());
    }

    vector<vector<int>> solve() {
        results.clear();
        path.clear();

        engine.reset();

        try {
            backtrack(0);
        } catch (...) {
            engine.finish();
            throw;
        }

        engine.finish();
        return results;
    }

    const SearchStatistics& statistics() const {
        return engine.statistics();
    }
};


class NQueensSolver {
private:
    int n;
    uint32_t fullMask;

    vector<int> positions;
    vector<vector<int>> solutions;

    SearchEngine engine;

    void backtrack(
        int row,
        uint32_t columns,
        uint32_t leftDiagonals,
        uint32_t rightDiagonals
    ) {
        engine.visit(static_cast<size_t>(row));

        if (row == n) {
            engine.recordSolution();
            solutions.push_back(positions);
            return;
        }

        uint32_t available = fullMask & ~(
            columns | leftDiagonals | rightDiagonals
        );

        while (available != 0) {
            // Extract the rightmost available column.
            uint32_t bit = available & (~available + 1);
            available ^= bit;

            int column = __builtin_ctz(bit);

            positions[row] = column;

            backtrack(
                row + 1,
                columns | bit,
                ((leftDiagonals | bit) << 1) & fullMask,
                (rightDiagonals | bit) >> 1
            );

            positions[row] = -1;
        }
    }

public:
    explicit NQueensSolver(
        int boardSize,
        SearchLimits limits = {}
    ) : n(boardSize), engine(limits) {

        if (n < 1 || n > 15) {
            throw invalid_argument(
                "Board size must be between 1 and 15"
            );
        }

        fullMask = (1u << n) - 1u;
        positions.assign(n, -1);
    }

    vector<vector<int>> solve() {
        solutions.clear();
        fill(positions.begin(), positions.end(), -1);

        engine.reset();

        try {
            backtrack(0, 0, 0, 0);
        } catch (...) {
            engine.finish();
            throw;
        }

        engine.finish();
        return solutions;
    }

    void printBoard(const vector<int>& solution) const {
        for (int column : solution) {
            for (int j = 0; j < n; ++j) {
                cout << (j == column ? 'Q' : '.') << ' ';
            }
            cout << '\n';
        }
    }

    const SearchStatistics& statistics() const {
        return engine.statistics();
    }
};


void printStatistics(const SearchStatistics& stats) {
    cout << "Nodes visited: " << stats.nodes << '\n';
    cout << "Solutions: " << stats.solutions << '\n';
    cout << "Pruned branches: " << stats.pruned << '\n';
    cout << "Maximum depth: " << stats.maximumDepth << '\n';

    cout << fixed << setprecision(3)
         << "Elapsed milliseconds: "
         << stats.elapsedMilliseconds << "\n\n";
}


void demonstratePermutations() {
    cout << "\nPERMUTATIONS\n";

    PermutationSolver solver({1, 2, 2});
    auto results = solver.solve();

    for (const auto& result : results) {
        for (int value : result) cout << value << ' ';
        cout << '\n';
    }

    if (results.size() != 3) {
        throw runtime_error("Permutation validation failed");
    }

    printStatistics(solver.statistics());
}


void demonstrateCombinations() {
    cout << "COMBINATIONS\n";

    CombinationSolver solver({1, 2, 3, 4}, 2);
    auto results = solver.solve();

    for (const auto& result : results) {
        for (int value : result) cout << value << ' ';
        cout << '\n';
    }

    if (results.size() != 6) {
        throw runtime_error("Combination validation failed");
    }

    printStatistics(solver.statistics());
}


void demonstrateNQueens() {
    cout << "N-QUEENS\n";

    NQueensSolver solver(4);
    auto solutions = solver.solve();

    int number = 1;

    for (const auto& solution : solutions) {
        cout << "\nSolution " << number++ << '\n';
        solver.printBoard(solution);
    }

    if (solutions.size() != 2) {
        throw runtime_error("N-Queens validation failed");
    }

    printStatistics(solver.statistics());
}


void demonstrateEdgeCases() {
    cout << "EDGE CASES\n";

    PermutationSolver emptyPermutation({});
    if (emptyPermutation.solve().size() != 1) {
        throw runtime_error("Empty permutation failure");
    }

    CombinationSolver emptyCombination({}, 0);
    if (emptyCombination.solve().size() != 1) {
        throw runtime_error("Empty combination failure");
    }

    CombinationSolver completeSelection({1, 2, 3}, 3);
    if (completeSelection.solve().size() != 1) {
        throw runtime_error("Complete combination failure");
    }

    NQueensSolver oneQueen(1);
    NQueensSolver twoQueens(2);
    NQueensSolver threeQueens(3);
    NQueensSolver fiveQueens(5);

    if (oneQueen.solve().size() != 1 ||
        !twoQueens.solve().empty() ||
        !threeQueens.solve().empty() ||
        fiveQueens.solve().size() != 10) {
        throw runtime_error("N-Queens edge-case failure");
    }

    cout << "All edge cases passed.\n\n";
}


void demonstrateLimitHandling() {
    cout << "SEARCH LIMIT HANDLING\n";

    try {
        SearchLimits limits;
        limits.maximumNodes = 5;
        limits.maximumSolutions = 100;

        PermutationSolver solver({1, 2, 3, 4, 5}, limits);
        solver.solve();

        throw runtime_error("Search limit was not enforced");
    } catch (const SearchLimitExceeded& error) {
        cout << "Controlled termination: "
             << error.what() << '\n';
    }
}


int main() {
    try {
        cout << "BACKTRACKING AND STATE SPACE TREE ENGINE\n";
        cout << "========================================\n";

        demonstratePermutations();
        demonstrateCombinations();
        demonstrateNQueens();
        demonstrateEdgeCases();
        demonstrateLimitHandling();

        cout << "\nExecution completed successfully.\n";

    } catch (const exception& error) {
        cerr << "Execution failure: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
