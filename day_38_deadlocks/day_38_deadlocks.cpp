#include <algorithm>
#include <iostream>
#include <map>
#include <numeric>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using ResourceMap = std::map<std::string, int>;

enum class ProcessState {
    Ready,
    Waiting,
    Running,
    Completed,
    Aborted
};

struct Process {
    std::string name;
    ResourceMap maximum;
    ResourceMap allocation;
    ProcessState state = ProcessState::Ready;

    ResourceMap need() const {
        ResourceMap result;

        for (const auto& [resource, maximumAmount] : maximum) {
            int allocated = 0;

            auto it = allocation.find(resource);
            if (it != allocation.end()) {
                allocated = it->second;
            }

            result[resource] = maximumAmount - allocated;
        }

        return result;
    }
};

class GovernanceEngine {
private:
    ResourceMap capacity_;
    std::map<std::string, Process> processes_;
    std::map<std::string, std::set<std::string>> waitingFor_;

    ResourceMap available() const {
        ResourceMap result = capacity_;

        for (const auto& [name, process] : processes_) {
            if (process.state == ProcessState::Aborted) {
                continue;
            }

            for (const auto& [resource, amount] : process.allocation) {
                result[resource] -= amount;
            }
        }

        return result;
    }

    void validateAllocation() const {
        ResourceMap totals;

        for (const auto& [name, process] : processes_) {
            if (process.state == ProcessState::Aborted) {
                continue;
            }

            for (const auto& [resource, amount] : process.allocation) {
                totals[resource] += amount;
            }
        }

        for (const auto& [resource, amount] : totals) {
            auto capacity = capacity_.at(resource);

            if (amount > capacity) {
                throw std::logic_error(
                    "Allocation exceeds resource capacity for " + resource
                );
            }
        }
    }

public:
    explicit GovernanceEngine(ResourceMap capacities)
        : capacity_(std::move(capacities)) {

        for (const auto& [resource, amount] : capacity_) {
            if (amount <= 0) {
                throw std::invalid_argument(
                    "Resource capacity must be positive: " + resource
                );
            }
        }
    }

    void addProcess(Process process) {
        if (processes_.contains(process.name)) {
            throw std::invalid_argument(
                "Duplicate process: " + process.name
            );
        }

        for (const auto& [resource, maximum] : process.maximum) {
            if (!capacity_.contains(resource)) {
                throw std::invalid_argument(
                    "Unknown resource: " + resource
                );
            }

            if (maximum < 0) {
                throw std::invalid_argument(
                    "Negative maximum claim for " + resource
                );
            }

            int allocation = 0;

            auto it = process.allocation.find(resource);
            if (it != process.allocation.end()) {
                allocation = it->second;
            }

            if (allocation < 0 || allocation > maximum) {
                throw std::invalid_argument(
                    "Invalid allocation for " + process.name
                );
            }
        }

        processes_.emplace(process.name, std::move(process));
        waitingFor_[processes_.rbegin()->first] = {};
        validateAllocation();
    }

    bool request(
        const std::string& processName,
        const ResourceMap& request,
        bool avoid = false
    ) {
        auto processIt = processes_.find(processName);

        if (processIt == processes_.end()) {
            throw std::invalid_argument("Unknown process: " + processName);
        }

        Process& process = processIt->second;

        if (process.state == ProcessState::Aborted ||
            process.state == ProcessState::Completed) {
            throw std::logic_error("Inactive process cannot request resources.");
        }

        ResourceMap need = process.need();

        for (const auto& [resource, amount] : request) {
            if (!capacity_.contains(resource)) {
                throw std::invalid_argument("Unknown resource: " + resource);
            }

            if (amount < 0) {
                throw std::invalid_argument("Negative request.");
            }

            if (amount > need[resource]) {
                throw std::invalid_argument(
                    processName + " exceeds remaining need for " + resource
                );
            }
        }

        ResourceMap free = available();

        bool immediatelyAvailable = true;

        for (const auto& [resource, amount] : request) {
            if (amount > free[resource]) {
                immediatelyAvailable = false;
                break;
            }
        }

        if (!immediatelyAvailable) {
            process.state = ProcessState::Waiting;

            for (const auto& [resource, amount] : request) {
                if (amount > free[resource]) {
                    waitingFor_[processName].insert(resource);
                }
            }

            return false;
        }

        if (avoid && !safeAfter(processName, request)) {
            process.state = ProcessState::Waiting;

            for (const auto& [resource, amount] : request) {
                waitingFor_[processName].insert(resource);
            }

            return false;
        }

        for (const auto& [resource, amount] : request) {
            process.allocation[resource] += amount;
        }

        process.state = ProcessState::Running;
        waitingFor_[processName].clear();

        validateAllocation();
        return true;
    }

    bool safeAfter(
        const std::string& processName,
        const ResourceMap& request
    ) {
        Process& process = processes_.at(processName);

        for (const auto& [resource, amount] : request) {
            process.allocation[resource] += amount;
        }

        bool safe = isSafe();

        for (const auto& [resource, amount] : request) {
            process.allocation[resource] -= amount;
        }

        return safe;
    }

    bool isSafe() const {
        ResourceMap work = available();

        std::set<std::string> active;
        std::set<std::string> finished;

        for (const auto& [name, process] : processes_) {
            if (process.state != ProcessState::Aborted &&
                process.state != ProcessState::Completed) {
                active.insert(name);
            }
        }

        bool changed = true;

        while (changed) {
            changed = false;

            for (const auto& name : active) {
                if (finished.contains(name)) {
                    continue;
                }

                const Process& process = processes_.at(name);
                ResourceMap need = process.need();

                bool canFinish = true;

                for (const auto& [resource, amount] : need) {
                    if (amount > work[resource]) {
                        canFinish = false;
                        break;
                    }
                }

                if (canFinish) {
                    for (const auto& [resource, amount] : process.allocation) {
                        work[resource] += amount;
                    }

                    finished.insert(name);
                    changed = true;
                }
            }
        }

        return finished.size() == active.size();
    }

    std::vector<std::string> safeSequence() const {
        ResourceMap work = available();

        std::set<std::string> remaining;
        std::vector<std::string> sequence;

        for (const auto& [name, process] : processes_) {
            if (process.state != ProcessState::Aborted &&
                process.state != ProcessState::Completed) {
                remaining.insert(name);
            }
        }

        while (!remaining.empty()) {
            auto candidate = remaining.end();

            for (auto it = remaining.begin(); it != remaining.end(); ++it) {
                const Process& process = processes_.at(*it);
                ResourceMap need = process.need();

                bool canFinish = true;

                for (const auto& [resource, amount] : need) {
                    if (amount > work[resource]) {
                        canFinish = false;
                        break;
                    }
                }

                if (canFinish) {
                    candidate = it;
                    break;
                }
            }

            if (candidate == remaining.end()) {
                return {};
            }

            const Process& process = processes_.at(*candidate);

            for (const auto& [resource, amount] : process.allocation) {
                work[resource] += amount;
            }

            sequence.push_back(*candidate);
            remaining.erase(candidate);
        }

        return sequence;
    }

    std::map<std::string, std::set<std::string>> waitForGraph() const {
        std::map<std::string, std::set<std::string>> graph;

        for (const auto& [name, process] : processes_) {
            graph[name] = {};
        }

        std::map<std::string, std::set<std::string>> holders;

        for (const auto& [name, process] : processes_) {
            if (process.state == ProcessState::Aborted) {
                continue;
            }

            for (const auto& [resource, amount] : process.allocation) {
                if (amount > 0) {
                    holders[resource].insert(name);
                }
            }
        }

        ResourceMap free = available();

        for (const auto& [waitingProcess, resources] : waitingFor_) {
            for (const auto& resource : resources) {
                if (free[resource] == 0) {
                    for (const auto& holder : holders[resource]) {
                        graph[waitingProcess].insert(holder);
                    }
                }
            }
        }

        return graph;
    }

    std::set<std::string> detectDeadlock() const {
        auto graph = waitForGraph();

        std::set<std::string> visited;
        std::set<std::string> active;
        std::set<std::string> deadlocked;
        std::vector<std::string> path;

        std::function<void(const std::string&)> dfs =
            [&](const std::string& node) {
                if (active.contains(node)) {
                    auto it = std::find(path.begin(), path.end(), node);

                    if (it != path.end()) {
                        for (; it != path.end(); ++it) {
                            deadlocked.insert(*it);
                        }
                    }

                    return;
                }

                if (visited.contains(node)) {
                    return;
                }

                visited.insert(node);
                active.insert(node);
                path.push_back(node);

                for (const auto& neighbor : graph.at(node)) {
                    dfs(neighbor);
                }

                path.pop_back();
                active.erase(node);
            };

        for (const auto& [node, neighbors] : graph) {
            dfs(node);
        }

        return deadlocked;
    }

    void abortProcess(const std::string& processName) {
        Process& process = processes_.at(processName);

        process.allocation.clear();
        process.state = ProcessState::Aborted;
        waitingFor_[processName].clear();

        validateAllocation();
    }

    void completeProcess(const std::string& processName) {
        Process& process = processes_.at(processName);

        process.allocation.clear();
        process.state = ProcessState::Completed;
        waitingFor_[processName].clear();

        validateAllocation();
    }

    void printState() const {
        std::cout << "\nAvailable resources:\n";

        for (const auto& [resource, amount] : available()) {
            std::cout << "  " << resource << ": " << amount << '\n';
        }

        std::cout << "\nProcess state:\n";

        for (const auto& [name, process] : processes_) {
            std::cout << "  " << name << " allocation={";

            bool first = true;
            for (const auto& [resource, amount] : process.allocation) {
                if (!first) {
                    std::cout << ", ";
                }

                std::cout << resource << "=" << amount;
                first = false;
            }

            std::cout << "} need={";

            first = true;
            for (const auto& [resource, amount] : process.need()) {
                if (!first) {
                    std::cout << ", ";
                }

                std::cout << resource << "=" << amount;
                first = false;
            }

            std::cout << "}\n";
        }
    }
};

void demonstrateCoffmanConditions() {
    std::cout << "=== Coffman Conditions ===\n";

    std::cout
        << "Mutual exclusion: at least one resource cannot be shared.\n"
        << "Hold and wait: a process holds resources while requesting more.\n"
        << "No preemption: a held resource cannot be forcibly reclaimed.\n"
        << "Circular wait: processes form a cycle of resource dependencies.\n\n";

    std::cout
        << "A classic resource deadlock requires all four conditions. "
        << "Prevention removes at least one necessary condition.\n";
}

GovernanceEngine createDeadlockedSystem() {
    GovernanceEngine engine({
        {"Database", 1},
        {"AuditLog", 1}
    });

    engine.addProcess({
        "TransactionA",
        {{"Database", 1}, {"AuditLog", 1}},
        {{"Database", 1}, {"AuditLog", 0}}
    });

    engine.addProcess({
        "TransactionB",
        {{"Database", 1}, {"AuditLog", 1}},
        {{"Database", 0}, {"AuditLog", 1}}
    });

    engine.request("TransactionA", {{"AuditLog", 1}});
    engine.request("TransactionB", {{"Database", 1}});

    return engine;
}

void demonstrateDeadlockDetectionAndRecovery() {
    std::cout << "\n=== Detection and Recovery ===\n";

    GovernanceEngine engine = createDeadlockedSystem();

    engine.printState();

    auto deadlocked = engine.detectDeadlock();

    std::cout << "\nDetected cycle:";
    for (const auto& process : deadlocked) {
        std::cout << " " << process;
    }
    std::cout << '\n';

    if (!deadlocked.empty()) {
        // A real recovery policy may consider process priority, rollback cost,
        // transaction age, resources held, and work already completed.
        const std::string victim = *deadlocked.begin();

        std::cout << "Recovery aborts: " << victim << '\n';
        engine.abortProcess(victim);
    }

    std::cout
        << "Remaining deadlocked processes: "
        << engine.detectDeadlock().size() << '\n';

    engine.printState();
}

void demonstratePrevention() {
    std::cout << "\n=== Prevention Through Resource Ordering ===\n";

    const std::map<std::string, int> order = {
        {"Database", 1},
        {"AuditLog", 2}
    };

    std::vector<std::string> held = {"Database"};
    std::string requested = "AuditLog";

    bool valid = true;

    for (const auto& resource : held) {
        if (order.at(resource) > order.at(requested)) {
            valid = false;
        }
    }

    std::cout
        << "Transaction holding Database and requesting AuditLog: "
        << (valid ? "allowed" : "rejected") << '\n';

    std::cout
        << "The global order prevents a process from holding a higher-ranked "
        << "resource while requesting a lower-ranked resource. Therefore a "
        << "circular wait cannot be constructed under the rule.\n";
}

void demonstrateAvoidance() {
    std::cout << "\n=== Banker's Algorithm ===\n";

    GovernanceEngine engine({
        {"A", 10},
        {"B", 5},
        {"C", 7}
    });

    engine.addProcess({
        "P0",
        {{"A", 7}, {"B", 5}, {"C", 3}},
        {{"A", 0}, {"B", 1}, {"C", 0}}
    });

    engine.addProcess({
        "P1",
        {{"A", 3}, {"B", 2}, {"C", 2}},
        {{"A", 2}, {"B", 0}, {"C", 0}}
    });

    engine.addProcess({
        "P2",
        {{"A", 9}, {"B", 0}, {"C", 2}},
        {{"A", 3}, {"B", 0}, {"C", 2}}
    });

    engine.addProcess({
        "P3",
        {{"A", 2}, {"B", 2}, {"C", 2}},
        {{"A", 2}, {"B", 1}, {"C", 1}}
    });

    engine.addProcess({
        "P4",
        {{"A", 4}, {"B", 3}, {"C", 3}},
        {{"A", 0}, {"B", 0}, {"C", 2}}
    });

    engine.printState();

    std::cout << "\nSafe state: "
              << (engine.isSafe() ? "yes" : "no")
              << '\n';

    auto sequence = engine.safeSequence();

    std::cout << "Safe sequence:";

    for (const auto& process : sequence) {
        std::cout << " " << process;
    }

    std::cout << '\n';

    bool accepted = engine.request(
        "P1",
        {{"A", 1}, {"B", 1}, {"C", 2}},
        true
    );

    std::cout
        << "Safety-checked request accepted: "
        << (accepted ? "yes" : "no")
        << '\n';
}

int main() {
    try {
        std::cout << "DEADLOCKS: RESOURCE GOVERNANCE CASE STUDY\n\n";

        demonstrateCoffmanConditions();
        demonstratePrevention();
        demonstrateAvoidance();
        demonstrateDeadlockDetectionAndRecovery();

        std::cout
            << "\nDesign distinction:\n"
            << "Prevention restricts the resource-allocation protocol.\n"
            << "Avoidance predicts whether a request preserves a safe state.\n"
            << "Detection searches the current wait-for structure for cycles.\n"
            << "Recovery restores progress by releasing resources through "
               "completion, rollback, or process termination.\n";
    }
    catch (const std::exception& error) {
        std::cerr << "Execution error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
