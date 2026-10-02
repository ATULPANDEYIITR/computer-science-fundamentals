#include <algorithm>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <queue>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using namespace std;

/*
 * Repository Build Farm Scheduling Case Study
 *
 * Scenario:
 * A software build farm receives independent compilation and test
 * jobs. Every job needs CPU service, arrives at a known time, and may
 * have an operational priority.
 *
 * The scheduling engine supports:
 *   FCFS
 *   SJF
 *   SRTF
 *   Non-preemptive Priority
 *   Preemptive Priority
 *   Round Robin
 *
 * The program is deliberately designed as a scheduling-policy engine:
 * process state is kept separate from the policy that chooses the next
 * process. This makes the behavior easier to inspect and compare.
 *
 * Compile:
 *   g++ -std=c++17 -O2 scheduler.cpp -o scheduler
 */

struct Process {
    string id;
    int arrival;
    int burst;
    int priority;

    Process(string processId, int arrivalTime, int burstTime, int priorityValue)
        : id(std::move(processId)),
          arrival(arrivalTime),
          burst(burstTime),
          priority(priorityValue) {
        if (id.empty()) {
            throw invalid_argument("Process ID cannot be empty.");
        }
        if (arrival < 0) {
            throw invalid_argument("Arrival time cannot be negative.");
        }
        if (burst <= 0) {
            throw invalid_argument("Burst time must be positive.");
        }
    }
};

struct Interval {
    int start;
    int end;
    string processId;
};

struct Metric {
    string id;
    int arrival;
    int burst;
    int priority;
    int completion;
    int turnaround;
    int waiting;
    int response;
};

struct ScheduleResult {
    string algorithm;
    vector<Process> processes;
    map<string, int> completion;
    map<string, int> firstStart;
    vector<Interval> timeline;
    int contextSwitches = 0;

    vector<Metric> metrics() const {
        vector<Metric> rows;

        for (const auto& process : processes) {
            int completionTime = completion.at(process.id);
            int turnaround = completionTime - process.arrival;
            int waiting = turnaround - process.burst;
            int response = firstStart.at(process.id) - process.arrival;

            rows.push_back({
                process.id,
                process.arrival,
                process.burst,
                process.priority,
                completionTime,
                turnaround,
                waiting,
                response
            });
        }

        return rows;
    }

    double averageWaiting() const {
        const auto rows = metrics();

        double total = 0.0;
        for (const auto& row : rows) {
            total += row.waiting;
        }

        return total / rows.size();
    }

    double averageTurnaround() const {
        const auto rows = metrics();

        double total = 0.0;
        for (const auto& row : rows) {
            total += row.turnaround;
        }

        return total / rows.size();
    }

    double averageResponse() const {
        const auto rows = metrics();

        double total = 0.0;
        for (const auto& row : rows) {
            total += row.response;
        }

        return total / rows.size();
    }

    int makespan() const {
        int result = 0;

        for (const auto& [id, completionTime] : completion) {
            result = max(result, completionTime);
        }

        return result;
    }

    int busyTime() const {
        int result = 0;

        for (const auto& process : processes) {
            result += process.burst;
        }

        return result;
    }

    double cpuUtilization() const {
        if (makespan() == 0) {
            return 0.0;
        }

        return 100.0 * busyTime() / makespan();
    }

    double throughput() const {
        if (makespan() == 0) {
            return 0.0;
        }

        return static_cast<double>(processes.size()) / makespan();
    }
};

void validateProcesses(const vector<Process>& processes) {
    if (processes.empty()) {
        throw invalid_argument("At least one process is required.");
    }

    map<string, bool> seen;

    for (const auto& process : processes) {
        if (seen[process.id]) {
            throw invalid_argument(
                "Duplicate process ID: " + process.id
            );
        }

        seen[process.id] = true;
    }
}

vector<Process> normalized(vector<Process> processes) {
    validateProcesses(processes);

    sort(
        processes.begin(),
        processes.end(),
        [](const Process& a, const Process& b) {
            if (a.arrival != b.arrival) {
                return a.arrival < b.arrival;
            }
            return a.id < b.id;
        }
    );

    return processes;
}

void addInterval(
    vector<Interval>& timeline,
    int start,
    int end,
    const string& processId
) {
    if (end <= start) {
        return;
    }

    if (
        !timeline.empty() &&
        timeline.back().end == start &&
        timeline.back().processId == processId
    ) {
        timeline.back().end = end;
        return;
    }

    timeline.push_back({start, end, processId});
}

ScheduleResult finalize(
    const string& algorithm,
    const vector<Process>& processes,
    const map<string, int>& completion,
    const map<string, int>& firstStart,
    const vector<Interval>& timeline
) {
    ScheduleResult result{
        algorithm,
        processes,
        completion,
        firstStart,
        timeline,
        0
    };

    string previous;

    for (const auto& interval : timeline) {
        if (interval.processId == "IDLE") {
            previous.clear();
            continue;
        }

        if (!previous.empty() && previous != interval.processId) {
            result.contextSwitches++;
        }

        previous = interval.processId;
    }

    return result;
}

ScheduleResult fcfs(vector<Process> processes) {
    processes = normalized(std::move(processes));

    map<string, int> completion;
    map<string, int> firstStart;
    vector<Interval> timeline;

    int time = 0;

    for (const auto& process : processes) {
        if (time < process.arrival) {
            addInterval(
                timeline,
                time,
                process.arrival,
                "IDLE"
            );

            time = process.arrival;
        }

        firstStart[process.id] = time;

        int end = time + process.burst;

        addInterval(
            timeline,
            time,
            end,
            process.id
        );

        completion[process.id] = end;
        time = end;
    }

    return finalize(
        "FCFS",
        processes,
        completion,
        firstStart,
        timeline
    );
}

ScheduleResult sjf(vector<Process> processes) {
    processes = normalized(std::move(processes));

    vector<Process> remaining = processes;
    map<string, int> completion;
    map<string, int> firstStart;
    vector<Interval> timeline;

    int time = 0;

    while (!remaining.empty()) {
        vector<int> candidates;

        for (int i = 0; i < static_cast<int>(remaining.size()); ++i) {
            if (remaining[i].arrival <= time) {
                candidates.push_back(i);
            }
        }

        if (candidates.empty()) {
            int nextArrival = numeric_limits<int>::max();

            for (const auto& process : remaining) {
                nextArrival = min(nextArrival, process.arrival);
            }

            addInterval(
                timeline,
                time,
                nextArrival,
                "IDLE"
            );

            time = nextArrival;
            continue;
        }

        int selected = candidates.front();

        for (int index : candidates) {
            const auto& candidate = remaining[index];
            const auto& current = remaining[selected];

            if (
                candidate.burst < current.burst ||
                (
                    candidate.burst == current.burst &&
                    (
                        candidate.arrival < current.arrival ||
                        (
                            candidate.arrival == current.arrival &&
                            candidate.id < current.id
                        )
                    )
                )
            ) {
                selected = index;
            }
        }

        Process process = remaining[selected];
        remaining.erase(remaining.begin() + selected);

        firstStart[process.id] = time;

        int end = time + process.burst;

        addInterval(
            timeline,
            time,
            end,
            process.id
        );

        completion[process.id] = end;
        time = end;
    }

    return finalize(
        "SJF",
        processes,
        completion,
        firstStart,
        timeline
    );
}

ScheduleResult srtf(vector<Process> processes) {
    processes = normalized(std::move(processes));

    map<string, int> remaining;
    map<string, Process> lookup;

    for (const auto& process : processes) {
        remaining[process.id] = process.burst;
        lookup[process.id] = process;
    }

    map<string, int> completion;
    map<string, int> firstStart;
    vector<Interval> timeline;

    int time = 0;
    int completed = 0;

    while (completed < static_cast<int>(processes.size())) {
        vector<const Process*> candidates;

        for (const auto& process : processes) {
            if (
                process.arrival <= time &&
                remaining[process.id] > 0
            ) {
                candidates.push_back(&process);
            }
        }

        if (candidates.empty()) {
            int nextArrival = numeric_limits<int>::max();

            for (const auto& process : processes) {
                if (
                    remaining[process.id] > 0 &&
                    process.arrival > time
                ) {
                    nextArrival = min(
                        nextArrival,
                        process.arrival
                    );
                }
            }

            addInterval(
                timeline,
                time,
                nextArrival,
                "IDLE"
            );

            time = nextArrival;
            continue;
        }

        const Process* selected = candidates.front();

        for (const Process* candidate : candidates) {
            const int candidateRemaining =
                remaining[candidate->id];

            const int selectedRemaining =
                remaining[selected->id];

            if (
                candidateRemaining < selectedRemaining ||
                (
                    candidateRemaining == selectedRemaining &&
                    (
                        candidate->arrival < selected->arrival ||
                        (
                            candidate->arrival == selected->arrival &&
                            candidate->id < selected->id
                        )
                    )
                )
            ) {
                selected = candidate;
            }
        }

        if (!firstStart.count(selected->id)) {
            firstStart[selected->id] = time;
        }

        int nextArrival = numeric_limits<int>::max();

        for (const auto& process : processes) {
            if (
                process.arrival > time &&
                remaining[process.id] > 0
            ) {
                nextArrival = min(
                    nextArrival,
                    process.arrival
                );
            }
        }

        int finishTime =
            time + remaining[selected->id];

        int runUntil = min(finishTime, nextArrival);
        int elapsed = runUntil - time;

        addInterval(
            timeline,
            time,
            runUntil,
            selected->id
        );

        remaining[selected->id] -= elapsed;
        time = runUntil;

        if (remaining[selected->id] == 0) {
            completion[selected->id] = time;
            completed++;
        }
    }

    return finalize(
        "SRTF",
        processes,
        completion,
        firstStart,
        timeline
    );
}

ScheduleResult priorityNonPreemptive(
    vector<Process> processes
) {
    processes = normalized(std::move(processes));

    vector<Process> remaining = processes;
    map<string, int> completion;
    map<string, int> firstStart;
    vector<Interval> timeline;

    int time = 0;

    while (!remaining.empty()) {
        vector<int> candidates;

        for (int i = 0; i < static_cast<int>(remaining.size()); ++i) {
            if (remaining[i].arrival <= time) {
                candidates.push_back(i);
            }
        }

        if (candidates.empty()) {
            int nextArrival = numeric_limits<int>::max();

            for (const auto& process : remaining) {
                nextArrival = min(
                    nextArrival,
                    process.arrival
                );
            }

            addInterval(
                timeline,
                time,
                nextArrival,
                "IDLE"
            );

            time = nextArrival;
            continue;
        }

        int selected = candidates.front();

        for (int index : candidates) {
            const auto& candidate = remaining[index];
            const auto& current = remaining[selected];

            if (
                candidate.priority < current.priority ||
                (
                    candidate.priority == current.priority &&
                    (
                        candidate.arrival < current.arrival ||
                        (
                            candidate.arrival == current.arrival &&
                            candidate.id < current.id
                        )
                    )
                )
            ) {
                selected = index;
            }
        }

        Process process = remaining[selected];
        remaining.erase(remaining.begin() + selected);

        firstStart[process.id] = time;

        int end = time + process.burst;

        addInterval(
            timeline,
            time,
            end,
            process.id
        );

        completion[process.id] = end;
        time = end;
    }

    return finalize(
        "Priority (Non-Preemptive)",
        processes,
        completion,
        firstStart,
        timeline
    );
}

ScheduleResult priorityPreemptive(
    vector<Process> processes
) {
    processes = normalized(std::move(processes));

    map<string, int> remaining;

    for (const auto& process : processes) {
        remaining[process.id] = process.burst;
    }

    map<string, int> completion;
    map<string, int> firstStart;
    vector<Interval> timeline;

    int time = 0;
    int completed = 0;

    while (completed < static_cast<int>(processes.size())) {
        vector<const Process*> candidates;

        for (const auto& process : processes) {
            if (
                process.arrival <= time &&
                remaining[process.id] > 0
            ) {
                candidates.push_back(&process);
            }
        }

        if (candidates.empty()) {
            int nextArrival = numeric_limits<int>::max();

            for (const auto& process : processes) {
                if (
                    process.arrival > time &&
                    remaining[process.id] > 0
                ) {
                    nextArrival = min(
                        nextArrival,
                        process.arrival
                    );
                }
            }

            addInterval(
                timeline,
                time,
                nextArrival,
                "IDLE"
            );

            time = nextArrival;
            continue;
        }

        const Process* selected = candidates.front();

        for (const Process* candidate : candidates) {
            if (
                candidate->priority < selected->priority ||
                (
                    candidate->priority == selected->priority &&
                    (
                        candidate->arrival < selected->arrival ||
                        (
                            candidate->arrival == selected->arrival &&
                            candidate->id < selected->id
                        )
                    )
                )
            ) {
                selected = candidate;
            }
        }

        if (!firstStart.count(selected->id)) {
            firstStart[selected->id] = time;
        }

        int nextArrival = numeric_limits<int>::max();

        for (const auto& process : processes) {
            if (
                process.arrival > time &&
                remaining[process.id] > 0
            ) {
                nextArrival = min(
                    nextArrival,
                    process.arrival
                );
            }
        }

        int finishTime =
            time + remaining[selected->id];

        int runUntil = min(
            finishTime,
            nextArrival
        );

        int elapsed = runUntil - time;

        addInterval(
            timeline,
            time,
            runUntil,
            selected->id
        );

        remaining[selected->id] -= elapsed;
        time = runUntil;

        if (remaining[selected->id] == 0) {
            completion[selected->id] = time;
            completed++;
        }
    }

    return finalize(
        "Priority (Preemptive)",
        processes,
        completion,
        firstStart,
        timeline
    );
}

ScheduleResult roundRobin(
    vector<Process> processes,
    int quantum
) {
    if (quantum <= 0) {
        throw invalid_argument(
            "Round Robin quantum must be positive."
        );
    }

    processes = normalized(std::move(processes));

    map<string, int> remaining;

    for (const auto& process : processes) {
        remaining[process.id] = process.burst;
    }

    map<string, int> completion;
    map<string, int> firstStart;
    vector<Interval> timeline;

    queue<int> readyQueue;
    int index = 0;
    int time = 0;
    int completed = 0;

    while (completed < static_cast<int>(processes.size())) {
        while (
            index < static_cast<int>(processes.size()) &&
            processes[index].arrival <= time
        ) {
            readyQueue.push(index);
            index++;
        }

        if (readyQueue.empty()) {
            int nextArrival = processes[index].arrival;

            addInterval(
                timeline,
                time,
                nextArrival,
                "IDLE"
            );

            time = nextArrival;
            continue;
        }

        int selectedIndex = readyQueue.front();
        readyQueue.pop();

        const auto& process = processes[selectedIndex];

        if (remaining[process.id] <= 0) {
            continue;
        }

        if (!firstStart.count(process.id)) {
            firstStart[process.id] = time;
        }

        int runTime = min(
            quantum,
            remaining[process.id]
        );

        int end = time + runTime;

        addInterval(
            timeline,
            time,
            end,
            process.id
        );

        while (
            index < static_cast<int>(processes.size()) &&
            processes[index].arrival <= end
        ) {
            readyQueue.push(index);
            index++;
        }

        remaining[process.id] -= runTime;
        time = end;

        if (remaining[process.id] == 0) {
            completion[process.id] = time;
            completed++;
        } else {
            readyQueue.push(selectedIndex);
        }
    }

    return finalize(
        "Round Robin",
        processes,
        completion,
        firstStart,
        timeline
    );
}

void printResult(const ScheduleResult& result) {
    cout << "\n" << result.algorithm << "\n";
    cout << string(105, '-') << "\n";

    cout << "Timeline: ";

    for (size_t i = 0; i < result.timeline.size(); ++i) {
        const auto& interval = result.timeline[i];

        cout << "["
             << interval.start
             << ","
             << interval.end
             << ") "
             << interval.processId;

        if (i + 1 < result.timeline.size()) {
            cout << " | ";
        }
    }

    cout << "\n\n";

    cout << left
         << setw(8) << "PID"
         << right
         << setw(6) << "AT"
         << setw(6) << "BT"
         << setw(7) << "PR"
         << setw(7) << "CT"
         << setw(7) << "TAT"
         << setw(7) << "WT"
         << setw(7) << "RT"
         << "\n";

    for (const auto& row : result.metrics()) {
        cout << left
             << setw(8) << row.id
             << right
             << setw(6) << row.arrival
             << setw(6) << row.burst
             << setw(7) << row.priority
             << setw(7) << row.completion
             << setw(7) << row.turnaround
             << setw(7) << row.waiting
             << setw(7) << row.response
             << "\n";
    }

    cout << fixed << setprecision(2);

    cout << "\nAverage waiting time : "
         << result.averageWaiting()
         << "\n";

    cout << "Average turnaround   : "
         << result.averageTurnaround()
         << "\n";

    cout << "Average response     : "
         << result.averageResponse()
         << "\n";

    cout << "CPU utilization      : "
         << result.cpuUtilization()
         << "%\n";

    cout << "Throughput           : "
         << result.throughput()
         << " processes/unit\n";

    cout << "Context switches     : "
         << result.contextSwitches
         << "\n";
}

void printComparison(
    const vector<ScheduleResult>& results
) {
    cout << "\nScheduling policy comparison\n";
    cout << string(105, '-') << "\n";

    cout << left
         << setw(28) << "Algorithm"
         << right
         << setw(12) << "Avg WT"
         << setw(12) << "Avg TAT"
         << setw(12) << "Avg RT"
         << setw(12) << "CPU %"
         << setw(12) << "Switches"
         << "\n";

    cout << string(88, '-') << "\n";

    for (const auto& result : results) {
        cout << left
             << setw(28) << result.algorithm
             << right
             << setw(12) << fixed << setprecision(2)
             << result.averageWaiting()
             << setw(12)
             << result.averageTurnaround()
             << setw(12)
             << result.averageResponse()
             << setw(12)
             << result.cpuUtilization()
             << setw(12)
             << result.contextSwitches
             << "\n";
    }
}

void demonstrateStarvationScenario() {
    /*
     * Priority scheduling can repeatedly favor newly arriving high
     * priority work. The example is intentionally small so the
     * scheduling effect can be observed in the timeline.
     */
    vector<Process> workload{
        Process("LONG-LOW", 0, 12, 5),
        Process("URGENT-1", 1, 2, 1),
        Process("URGENT-2", 3, 2, 1),
        Process("URGENT-3", 5, 2, 1),
        Process("URGENT-4", 7, 2, 1)
    };

    cout << "\nPriority-preemption case study\n";
    cout << "A lower-priority long job can be delayed by later "
            "higher-priority arrivals.\n";

    printResult(priorityPreemptive(workload));
}

void demonstrateIdleCPU() {
    /*
     * A scheduler cannot execute a process before its arrival.
     * Explicit IDLE intervals make this constraint visible.
     */
    vector<Process> workload{
        Process("BUILD-A", 4, 3, 2),
        Process("BUILD-B", 8, 2, 1)
    };

    cout << "\nIdle CPU case\n";
    printResult(fcfs(workload));
}

void demonstrateValidation() {
    cout << "\nValidation cases\n";

    try {
        Process invalid("BAD", -1, 3, 1);
    } catch (const exception& error) {
        cout << "Rejected invalid process: "
             << error.what()
             << "\n";
    }

    try {
        roundRobin(
            {Process("P1", 0, 3, 1)},
            0
        );
    } catch (const exception& error) {
        cout << "Rejected invalid quantum: "
             << error.what()
             << "\n";
    }
}

int main() {
    try {
        /*
         * The workload represents build jobs arriving at a shared
         * CI worker. Lower numeric priority means higher priority.
         */
        vector<Process> workload{
            Process("COMPILE-A", 0, 8, 2),
            Process("TEST-B", 1, 4, 1),
            Process("LINT-C", 2, 2, 3),
            Process("PACKAGE-D", 3, 6, 2),
            Process("DEPLOY-E", 5, 3, 1)
        };

        cout << "PROCESS SCHEDULING CASE STUDY\n";
        cout << string(105, '=') << "\n";

        cout << left
             << setw(16) << "Process"
             << right
             << setw(10) << "Arrival"
             << setw(10) << "Burst"
             << setw(10) << "Priority"
             << "\n";

        for (const auto& process : workload) {
            cout << left
                 << setw(16) << process.id
                 << right
                 << setw(10) << process.arrival
                 << setw(10) << process.burst
                 << setw(10) << process.priority
                 << "\n";
        }

        vector<ScheduleResult> results;

        results.push_back(fcfs(workload));
        results.push_back(sjf(workload));
        results.push_back(srtf(workload));
        results.push_back(
            priorityNonPreemptive(workload)
        );
        results.push_back(
            priorityPreemptive(workload)
        );
        results.push_back(
            roundRobin(workload, 3)
        );

        for (const auto& result : results) {
            printResult(result);
        }

        printComparison(results);
        demonstrateStarvationScenario();
        demonstrateIdleCPU();
        demonstrateValidation();

        cout << "\nMetric relationships\n";
        cout << "Turnaround = completion - arrival\n";
        cout << "Waiting    = turnaround - burst\n";
        cout << "Response   = first CPU start - arrival\n";

    } catch (const exception& error) {
        cerr << "Fatal scheduling error: "
             << error.what()
             << "\n";

        return 1;
    }

    return 0;
}
