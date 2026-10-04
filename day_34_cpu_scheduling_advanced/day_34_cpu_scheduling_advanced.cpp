/*
    Advanced CPU Scheduling Case Study
    ===================================

    Scenario:
        A production-like operating-system scheduler serves three classes of
        workloads:

        - Interactive processes need low response time.
        - Service processes perform short CPU bursts separated by I/O.
        - Batch processes perform long CPU-intensive work.

    The program models:
        - Multilevel Queue Scheduling
        - Multilevel Feedback Queue Scheduling
        - Round-robin time slices
        - Queue demotion and promotion
        - Periodic priority boosts
        - Context-switch overhead
        - Preemption
        - CPU and I/O bursts
        - Scheduling metrics
        - Merge-free event timeline generation

    Build:
        g++ -std=c++17 -O2 -Wall -Wextra -pedantic scheduler.cpp -o scheduler

    Run:
        ./scheduler
*/

#include <algorithm>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <optional>
#include <queue>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

enum class ProcessState {
    New,
    Ready,
    Running,
    Blocked,
    Terminated
};

enum class QueuePolicy {
    FCFS,
    RoundRobin,
    Priority
};

struct Burst {
    int cpu;
    int io;

    Burst(int cpuDuration, int ioDuration = 0)
        : cpu(cpuDuration), io(ioDuration) {
        if (cpu <= 0) {
            throw std::invalid_argument(
                "CPU burst must be positive."
            );
        }

        if (io < 0) {
            throw std::invalid_argument(
                "I/O duration cannot be negative."
            );
        }
    }
};

struct Process {
    std::string pid;
    int arrivalTime;
    std::vector<Burst> bursts;
    int basePriority;
    int queueLevel;

    ProcessState state = ProcessState::New;

    std::size_t burstIndex = 0;
    int remainingCpu = 0;

    std::optional<int> firstRunTime;
    std::optional<int> completionTime;
    std::optional<int> responseTime;

    int waitingTime = 0;
    int readySince = -1;
    int cpuTime = 0;

    int preemptions = 0;
    int demotions = 0;
    int promotions = 0;

    Process(
        std::string processId,
        int arrival,
        std::vector<Burst> processBursts,
        int priority,
        int initialQueue
    )
        : pid(std::move(processId)),
          arrivalTime(arrival),
          bursts(std::move(processBursts)),
          basePriority(priority),
          queueLevel(initialQueue) {

        if (pid.empty()) {
            throw std::invalid_argument(
                "Process ID cannot be empty."
            );
        }

        if (arrivalTime < 0) {
            throw std::invalid_argument(
                "Arrival time cannot be negative."
            );
        }

        if (bursts.empty()) {
            throw std::invalid_argument(
                "A process needs at least one CPU burst."
            );
        }

        if (basePriority < 0) {
            throw std::invalid_argument(
                "Priority cannot be negative."
            );

        remainingCpu = bursts.front().cpu;
    }

    bool completed() const {
        return state == ProcessState::Terminated;
    }

    const Burst& currentBurst() const {
        return bursts.at(burstIndex);
    }

    void beginWaiting(int now) {
        if (readySince < 0) {
            readySince = now;
        }
    }

    void endWaiting(int now) {
        if (readySince >= 0) {
            waitingTime += now - readySince;
            readySince = -1;
        }
    }
};

struct QueueConfig {
    std::string name;
    QueuePolicy policy;
    int quantum = 0;

    QueueConfig(
        std::string queueName,
        QueuePolicy queuePolicy,
        int timeQuantum = 0
    )
        : name(std::move(queueName)),
          policy(queuePolicy),
          quantum(timeQuantum) {

        if (
            policy == QueuePolicy::RoundRobin &&
            quantum <= 0
        ) {
            throw std::invalid_argument(
                "Round-robin requires a positive quantum."
            );
        }
    }
};

struct Event {
    int start;
    int end;
    std::string type;
    std::string pid;
    int queue = -1;
};

class Scheduler {
protected:
    std::vector<Process> processes;
    std::vector<QueueConfig> queues;

    std::vector<std::deque<int>> readyQueues;
    std::map<int, int> blockedUntil;

    std::optional<int> running;
    int currentTime = 0;
    int quantumUsed = 0;

    int contextSwitchCost;
    int contextSwitches = 0;
    int contextSwitchTime = 0;

    std::vector<Event> events;

    void addEvent(
        int start,
        int end,
        const std::string& type,
        const std::string& pid = "",
        int queue = -1
    ) {
        if (end <= start) {
            return;
        }

        events.push_back({
            start,
            end,
            type,
            pid,
            queue
        });
    }

    bool allCompleted() const {
        return std::all_of(
            processes.begin(),
            processes.end(),
            [](const Process& process) {
                return process.completed();
            }
        );
    }

    void admitArrivals() {
        for (std::size_t i = 0; i < processes.size(); ++i) {
            Process& process = processes[i];

            if (
                process.state == ProcessState::New &&
                process.arrivalTime <= currentTime
            ) {
                enqueue(process, static_cast<int>(i));
            }
        }
    }

    void releaseBlockedProcesses() {
        std::vector<int> released;

        for (const auto& [index, readyAt] : blockedUntil) {
            if (readyAt <= currentTime) {
                released.push_back(index);
            }
        }

        for (int index : released) {
            blockedUntil.erase(index);

            Process& process = processes[index];

            ++process.burstIndex;
            process.remainingCpu =
                process.currentBurst().cpu;

            enqueue(process, index);
        }
    }

    void enqueue(Process& process, int index, bool front = false) {
        process.state = ProcessState::Ready;
        process.beginWaiting(currentTime);

        const int level = std::clamp(
            process.queueLevel,
            0,
            static_cast<int>(readyQueues.size()) - 1
        );

        process.queueLevel = level;

        if (front) {
            readyQueues[level].push_front(index);
        } else {
            readyQueues[level].push_back(index);
        }
    }

    std::optional<int> highestReadyLevel() const {
        for (
            int level = 0;
            level < static_cast<int>(readyQueues.size());
            ++level
        ) {
            if (!readyQueues[level].empty()) {
                return level;
            }
        }

        return std::nullopt;
    }

    std::optional<int> selectFromQueue(int level) {
        if (readyQueues[level].empty()) {
            return std::nullopt;
        }

        QueueConfig& config = queues[level];

        if (config.policy == QueuePolicy::Priority) {
            auto best = readyQueues[level].begin();

            for (
                auto iterator = readyQueues[level].begin();
                iterator != readyQueues[level].end();
                ++iterator
            ) {
                if (
                    processes[*iterator].basePriority <
                    processes[*best].basePriority
                ) {
                    best = iterator;
                }
            }

            const int selected = *best;
            readyQueues[level].erase(best);
            return selected;
        }

        const int selected = readyQueues[level].front();
        readyQueues[level].pop_front();
        return selected;
    }

    std::optional<int> selectNextProcess() {
        for (
            int level = 0;
            level < static_cast<int>(readyQueues.size());
            ++level
        ) {
            if (auto selected = selectFromQueue(level)) {
                return selected;
            }
        }

        return std::nullopt;
    }

    void dispatch(int index) {
        Process& process = processes[index];

        process.endWaiting(currentTime);

        if (!process.firstRunTime.has_value()) {
            process.firstRunTime = currentTime;
            process.responseTime =
                currentTime - process.arrivalTime;
        }

        process.state = ProcessState::Running;
        running = index;
        quantumUsed = 0;

        ++contextSwitches;

        if (contextSwitchCost > 0) {
            const int start = currentTime;

            currentTime += contextSwitchCost;
            contextSwitchTime += contextSwitchCost;

            addEvent(
                start,
                currentTime,
                "CONTEXT_SWITCH",
                process.pid,
                process.queueLevel
            );
        }
    }

    void finishCpuBurst() {
        if (!running.has_value()) {
            return;
        }

        Process& process = processes[*running];

        ++process.burstIndex;

        if (process.burstIndex >= process.bursts.size()) {
            process.state = ProcessState::Terminated;
            process.completionTime = currentTime;
            running.reset();
            quantumUsed = 0;
            return;
        }

        const int ioDuration =
            process.bursts[process.burstIndex - 1].io;

        if (ioDuration > 0) {
            process.state = ProcessState::Blocked;

            blockedUntil[*running] =
                currentTime + ioDuration;

            /*
                A process that blocks before exhausting a CPU quantum is
                behaving like an interactive/I/O-bound workload. In this
                MLFQ policy it is promoted by one queue when it returns.
            */
            if (process.queueLevel > 0) {
                --process.queueLevel;
                ++process.promotions;
            }
        } else {
            process.remainingCpu =
                process.currentBurst().cpu;

            enqueue(process, *running);
        }

        running.reset();
        quantumUsed = 0;
    }

    void executeOneTick() {
        if (!running.has_value()) {
            return;
        }

        Process& process = processes[*running];

        --process.remainingCpu;
        ++process.cpuTime;
        ++quantumUsed;

        addEvent(
            currentTime,
            currentTime + 1,
            "CPU",
            process.pid,
            process.queueLevel
        );

        ++currentTime;

        if (process.remainingCpu == 0) {
            finishCpuBurst();
            return;
        }

        const QueueConfig& config =
            queues[process.queueLevel];

        if (
            config.policy == QueuePolicy::RoundRobin &&
            quantumUsed >= config.quantum
        ) {
            if (
                process.queueLevel + 1 <
                static_cast<int>(queues.size())
            ) {
                ++process.queueLevel;
                ++process.demotions;
            }

            ++process.preemptions;

            enqueue(process, *running);

            running.reset();
            quantumUsed = 0;
        }
    }

    void preemptForHigherQueue() {
        if (!running.has_value()) {
            return;
        }

        auto highest = highestReadyLevel();

        if (
            highest.has_value() &&
            *highest < processes[*running].queueLevel
        ) {
            Process& process = processes[*running];

            ++process.preemptions;

            enqueue(process, *running);

            addEvent(
                currentTime,
                currentTime,
                "HIGHER_QUEUE_PREEMPT",
                process.pid,
                process.queueLevel
            );

            running.reset();
            quantumUsed = 0;
        }
    }

    void printEvents() const {
        std::cout << "\nCPU EVENT TIMELINE\n";
        std::cout << std::string(82, '-') << '\n';

        for (const Event& event : events) {
            std::cout
                << '['
                << std::setw(3)
                << event.start
                << " -> "
                << std::setw(3)
                << event.end
                << "] "
                << std::left
                << std::setw(22)
                << event.type
                << std::setw(12)
                << event.pid;

            if (event.queue >= 0) {
                std::cout << "Q" << event.queue;
            }

            std::cout << std::right << '\n';
        }
    }

public:
    Scheduler(
        std::vector<Process> processList,
        std::vector<QueueConfig> queueList,
        int switchCost
    )
        : processes(std::move(processList)),
          queues(std::move(queueList)),
          readyQueues(queues.size()),
          contextSwitchCost(switchCost) {

        if (queues.empty()) {
            throw std::invalid_argument(
                "Scheduler requires at least one queue."
            );
        }

        if (switchCost < 0) {
            throw std::invalid_argument(
                "Context-switch cost cannot be negative."
            );
        }
    }

    virtual ~Scheduler() = default;

    virtual void run(int maxTime = 10000) = 0;

    void printReport() const {
        std::cout << "\nPROCESS REPORT\n";
        std::cout << std::string(100, '-') << '\n';

        std::cout
            << std::left
            << std::setw(12) << "PID"
            << std::setw(8) << "Queue"
            << std::setw(9) << "CPU"
            << std::setw(9) << "Wait"
            << std::setw(9) << "Resp"
            << std::setw(9) << "Turn"
            << std::setw(10) << "Preempt"
            << std::setw(10) << "Demote"
            << std::setw(10) << "Promote"
            << '\n';

        for (const Process& process : processes) {
            int turnaround = 0;

            if (process.completionTime.has_value()) {
                turnaround =
                    *process.completionTime -
                    process.arrivalTime;
            }

            std::cout
                << std::left
                << std::setw(12) << process.pid
                << std::setw(8)
                << ("Q" + std::to_string(process.queueLevel))
                << std::setw(9) << process.cpuTime
                << std::setw(9) << process.waitingTime
                << std::setw(9)
                << process.responseTime.value_or(-1)
                << std::setw(9) << turnaround
                << std::setw(10) << process.preemptions
                << std::setw(10) << process.demotions
                << std::setw(10) << process.promotions
                << '\n';
        }
    }

    void printMetrics() const {
        std::cout << "\nSCHEDULING METRICS\n";
        std::cout << std::string(46, '-') << '\n';

        int completed = 0;
        int totalWaiting = 0;
        int totalTurnaround = 0;
        int totalResponse = 0;
        int totalCpu = 0;

        for (const Process& process : processes) {
            if (!process.completionTime.has_value()) {
                continue;
            }

            ++completed;
            totalWaiting += process.waitingTime;
            totalCpu += process.cpuTime;

            totalTurnaround +=
                *process.completionTime -
                process.arrivalTime;

            totalResponse +=
                process.responseTime.value_or(0);
        }

        if (completed == 0) {
            return;
        }

        const double averageWaiting =
            static_cast<double>(totalWaiting) /
            completed;

        const double averageTurnaround =
            static_cast<double>(totalTurnaround) /
            completed;

        const double averageResponse =
            static_cast<double>(totalResponse) /
            completed;

        const double utilization =
            100.0 *
            static_cast<double>(totalCpu) /
            std::max(1, currentTime);

        std::cout
            << std::fixed
            << std::setprecision(2);

        std::cout
            << std::left
            << std::setw(32)
            << "Average waiting time"
            << averageWaiting
            << '\n';

        std::cout
            << std::setw(32)
            << "Average turnaround time"
            << averageTurnaround
            << '\n';

        std::cout
            << std::setw(32)
            << "Average response time"
            << averageResponse
            << '\n';

        std::cout
            << std::setw(32)
            << "CPU utilization"
            << utilization
            << "%\n";

        std::cout
            << std::setw(32)
            << "Context switches"
            << contextSwitches
            << '\n';

        std::cout
            << std::setw(32)
            << "Context-switch time"
            << contextSwitchTime
            << '\n';
    }
};

class MLFQScheduler final : public Scheduler {
private:
    int boostInterval;

    void priorityBoost() {
        if (
            boostInterval <= 0 ||
            currentTime == 0 ||
            currentTime % boostInterval != 0
        ) {
            return;
        }

        /*
            Priority boosting addresses starvation. Every waiting process is
            moved to the highest queue. This deliberately changes queue
            membership, which is what distinguishes MLFQ from static MLQ.
        */
        for (
            int level = 1;
            level < static_cast<int>(readyQueues.size());
            ++level
        ) {
            while (!readyQueues[level].empty()) {
                int index = readyQueues[level].front();
                readyQueues[level].pop_front();

                processes[index].queueLevel = 0;
                ++processes[index].promotions;

                readyQueues[0].push_back(index);
            }
        }

        addEvent(
            currentTime,
            currentTime,
            "PRIORITY_BOOST"
        );
    }

public:
    MLFQScheduler(
        std::vector<Process> processList,
        std::vector<QueueConfig> queueList,
        int switchCost,
        int boost
    )
        : Scheduler(
              std::move(processList),
              std::move(queueList),
              switchCost
          ),
          boostInterval(boost) {}

    void run(int maxTime = 10000) override {
        while (!allCompleted()) {
            if (currentTime > maxTime) {
                throw std::runtime_error(
                    "MLFQ simulation exceeded maximum time."
                );
            }

            admitArrivals();
            releaseBlockedProcesses();
            priorityBoost();
            preemptForHigherQueue();

            if (!running.has_value()) {
                auto selected = selectNextProcess();

                if (selected.has_value()) {
                    dispatch(*selected);
                    continue;
                }

                addEvent(
                    currentTime,
                    currentTime + 1,
                    "IDLE"
                );

                ++currentTime;
                continue;
            }

            executeOneTick();
        }
    }
};

class MLQScheduler final : public Scheduler {
public:
    MLQScheduler(
        std::vector<Process> processList,
        std::vector<QueueConfig> queueList,
        int switchCost
    )
        : Scheduler(
              std::move(processList),
              std::move(queueList),
              switchCost
          ) {}

    void run(int maxTime = 10000) override {
        /*
            MLQ uses fixed queue membership. A process can be scheduled by a
            different policy inside its queue, but it never changes queue as
            a consequence of CPU consumption.

            This case study uses CPU-only bursts to isolate the static queue
            distinction from MLFQ's adaptive feedback behavior.
        */
        while (!allCompleted()) {
            if (currentTime > maxTime) {
                throw std::runtime_error(
                    "MLQ simulation exceeded maximum time."
                );
            }

            admitArrivals();

            if (!running.has_value()) {
                auto selected = selectNextProcess();

                if (!selected.has_value()) {
                    addEvent(
                        currentTime,
                        currentTime + 1,
                        "IDLE"
                    );

                    ++currentTime;
                    continue;
                }

                dispatch(*selected);
                continue;
            }

            executeOneTick();
        }
    }
};

std::vector<Process> makeMLFQWorkload() {
    return {
        Process(
            "TERMINAL",
            0,
            {
                Burst(2, 5),
                Burst(1, 4),
                Burst(2)
            },
            1,
            0
        ),

        Process(
            "API",
            1,
            {
                Burst(3, 3),
                Burst(2, 4),
                Burst(2)
            },
            2,
            0
        ),

        Process(
            "COMPILER",
            0,
            {
                Burst(12)
            },
            6,
            0
        ),

        Process(
            "BACKUP",
            2,
            {
                Burst(15)
            },
            9,
            0
        ),

        Process(
            "LOGGER",
            4,
            {
                Burst(1, 6),
                Burst(1, 5),
                Burst(1)
            },
            3,
            0
        )
    };
}

void runMLFQCaseStudy() {
    std::cout
        << "============================================================\n"
        << "MLFQ REPOSITORY-BUILD SERVER CASE STUDY\n"
        << "============================================================\n";

    std::vector<QueueConfig> queues = {
        QueueConfig(
            "Interactive",
            QueuePolicy::RoundRobin,
            2
        ),
        QueueConfig(
            "Standard",
            QueuePolicy::RoundRobin,
            4
        ),
        QueueConfig(
            "Batch",
            QueuePolicy::FCFS
        )
    };

    MLFQScheduler scheduler(
        makeMLFQWorkload(),
        queues,
        1,
        15
    );

    scheduler.run();
    scheduler.printEvents();
    scheduler.printReport();
    scheduler.printMetrics();
}

void runMLQCaseStudy() {
    std::cout
        << "\n"
        << "============================================================\n"
        << "STATIC MLQ SERVER CASE STUDY\n"
        << "============================================================\n";

    std::vector<Process> processes = {
        Process(
            "SYSTEM",
            0,
            {Burst(4)},
            0,
            0
        ),

        Process(
            "UI",
            0,
            {Burst(6)},
            2,
            1
        ),

        Process(
            "BATCH",
            0,
            {Burst(10)},
            5,
            2
        )
    };

    std::vector<QueueConfig> queues = {
        QueueConfig(
            "System",
            QueuePolicy::Priority
        ),
        QueueConfig(
            "Interactive",
            QueuePolicy::RoundRobin,
            2
        ),
        QueueConfig(
            "Batch",
            QueuePolicy::FCFS
        )
    };

    MLQScheduler scheduler(
        std::move(processes),
        std::move(queues),
        1
    );

    scheduler.run();
    scheduler.printEvents();
    scheduler.printReport();
    scheduler.printMetrics();
}

void demonstrateContextSwitchCost() {
    std::cout
        << "\n"
        << "============================================================\n"
        << "CONTEXT-SWITCH COST COMPARISON\n"
        << "============================================================\n";

    for (int switchCost : {0, 1, 2}) {
        std::vector<Process> processes = {
            Process(
                "A",
                0,
                {Burst(5)},
                1,
                0
            ),
            Process(
                "B",
                0,
                {Burst(5)},
                2,
                0
            )
        };

        std::vector<QueueConfig> queues = {
            QueueConfig(
                "RR",
                QueuePolicy::RoundRobin,
                1
            )
        };

        MLFQScheduler scheduler(
            std::move(processes),
            std::move(queues),
            switchCost,
            0
        );

        scheduler.run();

        std::cout
            << "Switch cost = "
            << switchCost
            << " | switches = "
            << scheduler.contextSwitches
            << " | switch time = "
            << scheduler.contextSwitchTime
            << '\n';
    }
}

void demonstrateValidation() {
    std::cout
        << "\n"
        << "============================================================\n"
        << "VALIDATION BEHAVIOR\n"
        << "============================================================\n";

    try {
        QueueConfig invalid(
            "Broken RR",
            QueuePolicy::RoundRobin,
            0
        );
    } catch (const std::exception& error) {
        std::cout
            << "Rejected invalid queue: "
            << error.what()
            << '\n';
    }

    try {
        Burst invalidBurst(0);
    } catch (const std::exception& error) {
        std::cout
            << "Rejected invalid burst: "
            << error.what()
            << '\n';
    }

    try {
        Process invalidProcess(
            "",
            0,
            {Burst(1)},
            1,
            0
        );
    } catch (const std::exception& error) {
        std::cout
            << "Rejected invalid process: "
            << error.what()
            << '\n';
    }
}

int main() {
    try {
        runMLFQCaseStudy();
        runMLQCaseStudy();
        demonstrateContextSwitchCost();
        demonstrateValidation();
    } catch (const std::exception& error) {
        std::cerr
            << "Fatal scheduler error: "
            << error.what()
            << '\n';

        return 1;
    }

    return 0;
}
