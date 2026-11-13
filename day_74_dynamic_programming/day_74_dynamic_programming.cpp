#include <algorithm>
#include <cstdint>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>

using namespace std;

// ============================================================
// DYNAMIC PROGRAMMING: PROJECT PORTFOLIO OPTIMIZATION
//
// C++17 implementation covering:
// - Memoization
// - Tabulation
// - Optimal substructure
// - Overlapping subproblems
// - Knapsack optimization
// - Solution reconstruction
// - Longest common subsequence
// - Input validation
// ============================================================

struct Project {
    string name;
    int cost;
    int value;

    Project(string n, int c, int v)
        : name(move(n)), cost(c), value(v) {

        if (name.empty()) {
            throw invalid_argument("Project name cannot be empty.");
        }

        if (cost <= 0) {
            throw invalid_argument("Project cost must be positive.");
        }

        if (value < 0) {
            throw invalid_argument("Project value cannot be negative.");
        }
    }
};

struct OptimizationResult {
    int maximumValue;
    int totalCost;
    vector<string> selectedProjects;
    size_t statesComputed;
};

enum class Algorithm {
    Memoization,
    Tabulation
};

// ============================================================
// 1. FIBONACCI WITH MEMOIZATION
// ============================================================

class FibonacciSolver {

private:
    vector<uint64_t> memo;
    vector<bool> computed;

    uint64_t solveInternal(int n) {

        if (computed[n]) {
            return memo[n];
        }

        computed[n] =
            true;

        memo[n] =
            solveInternal(n - 1)
            + solveInternal(n - 2);

        return memo[n];
    }

public:

    explicit FibonacciSolver(int maximumN)
        : memo(maximumN + 1, 0),
          computed(maximumN + 1, false) {

        if (maximumN < 0 || maximumN > 92) {
            throw invalid_argument(
                "Maximum Fibonacci index must be between 0 and 92."
            );
        }

        memo[0] = 0;
        computed[0] = true;

        if (maximumN >= 1) {
            memo[1] = 1;
            computed[1] = true;
        }
    }

    uint64_t memoized(int n) {

        if (n < 0 || n >= static_cast<int>(memo.size())) {
            throw out_of_range("Invalid Fibonacci index.");
        }

        return n <= 1 ? memo[n] : solveInternal(n);
    }

    static uint64_t tabulated(int n) {

        if (n < 0 || n > 92) {
            throw out_of_range("Fibonacci index must be between 0 and 92.");
        }

        if (n <= 1) {
            return static_cast<uint64_t>(n);
        }

        uint64_t previous = 0;
        uint64_t current = 1;

        for (int i = 2; i <= n; ++i) {

            uint64_t next = previous + current;

            previous = current;
            current = next;
        }

        return current;
    }
};

// ============================================================
// 2. PROJECT PORTFOLIO: MEMOIZATION
// ============================================================

class PortfolioOptimizer {

private:
    const vector<Project>& projects;
    int budget;

    vector<vector<int>> memo;
    vector<vector<bool>> computed;

    size_t stateCount = 0;

    int solve(int index, int remaining) {

        if (index == static_cast<int>(projects.size())) {
            return 0;
        }

        if (computed[index][remaining]) {
            return memo[index][remaining];
        }

        computed[index][remaining] = true;
        ++stateCount;

        const Project& project = projects[index];

        int exclude = solve(index + 1, remaining);

        int include = 0;

        if (project.cost <= remaining) {
            include =
                project.value
                + solve(index + 1, remaining - project.cost);
        }

        memo[index][remaining] = max(include, exclude);

        return memo[index][remaining];
    }

public:

    PortfolioOptimizer(
        const vector<Project>& input,
        int availableBudget
    )
        : projects(input),
          budget(availableBudget) {

        if (budget < 0 || budget > 100000) {
            throw invalid_argument("Budget must be between 0 and 100000.");
        }

        unordered_set<string> names;

        for (const auto& project : projects) {

            if (!names.insert(project.name).second) {
                throw invalid_argument("Duplicate project name.");
            }
        }

        if (projects.size() > 500) {
            throw invalid_argument("Too many projects.");
        }

        memo.assign(
            projects.size() + 1,
            vector<int>(budget + 1, 0)
        );

        computed.assign(
            projects.size() + 1,
            vector<bool>(budget + 1, false)
        );
    }

    OptimizationResult solveMemoized() {

        stateCount = 0;

        int best = solve(0, budget);

        vector<string> selected;
        int remaining = budget;
        int totalCost = 0;

        for (int i = 0; i < static_cast<int>(projects.size()); ++i) {

            const Project& project = projects[i];

            int exclude = solve(i + 1, remaining);

            if (project.cost <= remaining) {

                int include =
                    project.value
                    + solve(i + 1, remaining - project.cost);

                if (include > exclude) {

                    selected.push_back(project.name);
                    remaining -= project.cost;
                    totalCost += project.cost;
                }
            }
        }

        return {
            best,
            totalCost,
            selected,
            stateCount
        };
    }
};

// ============================================================
// 3. PROJECT PORTFOLIO: TABULATION
// ============================================================

OptimizationResult solveTabulated(
    const vector<Project>& projects,
    int budget
) {

    if (budget < 0 || budget > 100000) {
        throw invalid_argument("Invalid budget.");
    }

    const int n = static_cast<int>(projects.size());

    // dp[i][w] = maximum value from first i projects
    // with available budget w.

    vector<vector<int>> dp(
        n + 1,
        vector<int>(budget + 1, 0)
    );

    for (int i = 1; i <= n; ++i) {

        const Project& project = projects[i - 1];

        for (int capacity = 0; capacity <= budget; ++capacity) {

            int exclude = dp[i - 1][capacity];
            int include = 0;

            if (project.cost <= capacity) {

                include =
                    project.value
                    + dp[i - 1][capacity - project.cost];
            }

            dp[i][capacity] = max(include, exclude);
        }
    }

    vector<string> selected;

    int remaining = budget;
    int totalCost = 0;

    for (int i = n; i > 0; --i) {

        if (dp[i][remaining] != dp[i - 1][remaining]) {

            const Project& project = projects[i - 1];

            selected.push_back(project.name);
            remaining -= project.cost;
            totalCost += project.cost;
        }
    }

    reverse(selected.begin(), selected.end());

    return {
        dp[n][budget],
        totalCost,
        selected,
        static_cast<size_t>((n + 1) * (budget + 1))
    };
}

// ============================================================
// 4. SPACE-OPTIMIZED 0/1 KNAPSACK
// ============================================================

int solveSpaceOptimized(
    const vector<Project>& projects,
    int budget
) {

    if (budget < 0) {
        throw invalid_argument("Budget cannot be negative.");
    }

    vector<int> dp(budget + 1, 0);

    for (const Project& project : projects) {

        // Descending iteration prevents selecting an item twice.
        for (int capacity = budget;
             capacity >= project.cost;
             --capacity) {

            dp[capacity] = max(
                dp[capacity],
                project.value + dp[capacity - project.cost]
            );
        }
    }

    return dp[budget];
}

// ============================================================
// 5. LONGEST COMMON SUBSEQUENCE
// ============================================================

struct LCSResult {
    int length;
    string sequence;
};

LCSResult longestCommonSubsequence(
    const string& first,
    const string& second
) {

    const int n = static_cast<int>(first.size());
    const int m = static_cast<int>(second.size());

    vector<vector<int>> dp(
        n + 1,
        vector<int>(m + 1, 0)
    );

    for (int i = 1; i <= n; ++i) {

        for (int j = 1; j <= m; ++j) {

            if (first[i - 1] == second[j - 1]) {

                dp[i][j] = dp[i - 1][j - 1] + 1;

            } else {

                dp[i][j] = max(
                    dp[i - 1][j],
                    dp[i][j - 1]
                );
            }
        }
    }

    string sequence;

    int i = n;
    int j = m;

    while (i > 0 && j > 0) {

        if (first[i - 1] == second[j - 1]) {

            sequence.push_back(first[i - 1]);
            --i;
            --j;

        } else if (dp[i - 1][j] >= dp[i][j - 1]) {

            --i;

        } else {

            --j;
        }
    }

    reverse(sequence.begin(), sequence.end());

    return {
        dp[n][m],
        sequence
    };
}

// ============================================================
// 6. AUTOMATED VALIDATION
// ============================================================

void runTests() {

    FibonacciSolver fibonacci(92);

    if (fibonacci.memoized(20) != 6765) {
        throw runtime_error("Fibonacci memoization test failed.");
    }

    if (FibonacciSolver::tabulated(20) != 6765) {
        throw runtime_error("Fibonacci tabulation test failed.");
    }

    vector<Project> projects = {
        {"Infrastructure", 4, 70},
        {"Security", 3, 60},
        {"Monitoring", 2, 40},
        {"Backup", 5, 90}
    };

    PortfolioOptimizer memoOptimizer(projects, 7);

    OptimizationResult memoResult =
        memoOptimizer.solveMemoized();

    OptimizationResult tableResult =
        solveTabulated(projects, 7);

    if (memoResult.maximumValue != tableResult.maximumValue) {
        throw runtime_error("Knapsack algorithms disagree.");
    }

    if (memoResult.maximumValue != 130) {
        throw runtime_error("Knapsack expected value mismatch.");
    }

    if (
        solveSpaceOptimized(projects, 7)
        != tableResult.maximumValue
    ) {
        throw runtime_error("Space optimization test failed.");
    }

    LCSResult lcs = longestCommonSubsequence(
        "ABCBDAB",
        "BDCABA"
    );

    if (lcs.length != 4) {
        throw runtime_error("LCS test failed.");
    }

    if (longestCommonSubsequence("", "ABC").length != 0) {
        throw runtime_error("Empty LCS test failed.");
    }

    cout << "All C++17 tests passed.\n";
}

// ============================================================
// 7. MAIN
// ============================================================

int main() {

    try {

        cout << "\nDYNAMIC PROGRAMMING ENGINE\n";
        cout << "==========================\n";

        // Fibonacci comparison.
        cout << "\n1. Fibonacci\n";

        FibonacciSolver fibonacci(92);

        cout << "Memoization: "
             << fibonacci.memoized(40) << '\n';

        cout << "Tabulation: "
             << FibonacciSolver::tabulated(40) << '\n';

        // Enterprise project selection.
        cout << "\n2. Project Portfolio Optimization\n";

        vector<Project> projects = {
            {"Infrastructure", 4, 70},
            {"Security", 3, 60},
            {"Monitoring", 2, 40},
            {"Backup", 5, 90},
            {"Analytics", 3, 55},
            {"Automation", 2, 35}
        };

        const int budget = 10;

        PortfolioOptimizer optimizer(projects, budget);

        OptimizationResult memoResult =
            optimizer.solveMemoized();

        OptimizationResult tableResult =
            solveTabulated(projects, budget);

        OptimizationResult spaceResult = {
            solveSpaceOptimized(projects, budget),
            0,
            {},
            0
        };

        cout << "\nMemoization\n";
        cout << "Maximum value: "
             << memoResult.maximumValue << '\n';

        cout << "Selected projects:\n";

        for (const string& name : memoResult.selectedProjects) {
            cout << " - " << name << '\n';
        }

        cout << "States computed: "
             << memoResult.statesComputed << '\n';

        cout << "\nTabulation\n";

        cout << "Maximum value: "
             << tableResult.maximumValue << '\n';

        cout << "Total cost: "
             << tableResult.totalCost << '\n';

        cout << "Selected projects:\n";

        for (const string& name : tableResult.selectedProjects) {
            cout << " - " << name << '\n';
        }

        cout << "\nSpace-optimized value: "
             << spaceResult.maximumValue << '\n';

        // LCS example.
        cout << "\n3. Longest Common Subsequence\n";

        LCSResult lcs = longestCommonSubsequence(
            "DYNAMICPROGRAMMING",
            "PROGRAMMING"
        );

        cout << "Length: " << lcs.length << '\n';
        cout << "Sequence: " << lcs.sequence << '\n';

        // Tests.
        cout << "\n4. Validation\n";
        runTests();

    } catch (const exception& error) {

        cerr << "Error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
