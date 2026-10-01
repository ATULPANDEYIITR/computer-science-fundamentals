/*
 * Processes: Process Concept, PCB, Process States, and Process Lifecycle
 *
 * C++17 case study:
 * A repository-like build service is modeled as an operating-system process
 * environment. Each build task becomes a process with a PCB. The scheduler
 * dispatches processes, CPU execution advances their saved context, I/O
 * requests move them to BLOCKED, completion returns them to READY, and
 * successful execution eventually moves them to TERMINATED.
 *
 * The implementation emphasizes:
 * - Process identity
 * - Process Control Blocks
 * - Explicit state transitions
 * - Parent/child relationships
 * - Ready and blocked queues
 * - CPU context preservation
 * - Resource ownership
 * - Scheduling and preemption
 * - Lifecycle accounting
 * - Invariant validation
 */

#include <algorithm>
#include <deque>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <sstream>
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

std::string stateName(ProcessState state) {
    switch (state) {
        case ProcessState::New:
            return "NEW";
        case ProcessState::Ready:
            return "READY";
        case ProcessState::Running:
            return "RUNNING";
        case ProcessState::Blocked:
            return "BLOCKED";
        case ProcessState::Terminated:
            return "TERMINATED";
    }

    return "UNKNOWN";
}

struct CPUContext {
    /*
     * These values represent the portion of execution context that the
     * scheduler must preserve when switching away from a process.
     */
    std::uint64_t programCounter{0};
    std::uint64_t stackPointer{4096};
    std::uint64_t basePointer{4096};

    std::map<std::string, std::uint64_t> registers{
        {"R0", 0},
        {"R1", 0},
        {"R2", 0},
        {"R3", 0}
    };

    std::uint64_t flags{0};
};

struct Resource {
    std::string id;
    std::string type;
    std::optional<int> ownerPid;
};

struct LifecycleRecord {
    int tick;
    ProcessState state;
};

struct ProcessControlBlock {
    int pid;
    std::optional<int> parentPid;
    std::string name;

    ProcessState state{ProcessState::New};

    /*
     * Lower priority numbers represent higher scheduling priority in this
     * case study. The policy is intentionally explicit rather than hidden.
     */
    int priority{5};
    int timeSlice{3};
    int remainingBurst{5};

    CPUContext context;

    std::set<int> children;
    std::set<std::string> ownedResources;

    std::optional<int> waitingForChild;
    std::optional<std::string> pendingIO;

    std::optional<int> exitCode;

    int cpuTicks{0};
    int readyTicks{0};
    int blockedTicks{0};
    int contextSwitches{0};

    int createdAt{0};
    std::optional<int> startedAt;
    std::optional<int> terminatedAt;

    std::vector<LifecycleRecord> history;
};

struct KernelEvent {
    int tick;
    int pid;
    std::string event;
    std::string detail;
};

class ProcessManager {
private:
    std::map<int, ProcessControlBlock> pcbs_;
    std::deque<int> readyQueue_;

    /*
     * A blocked queue is keyed by the event that can wake processes. In an
     * actual OS, wait queues may be associated with devices, synchronization
     * objects, child-exit events, sockets, and many other kernel objects.
     */
    std::map<std::string, std::set<int>> blockedQueues_;

    std::map<std::string, Resource> resources_;

    std::vector<KernelEvent> events_;

    std::optional<int> currentPid_;

    int nextPid_{1};
    int tick_{0};
    int contextSwitchCount_{0};

    static bool legalTransition(
        ProcessState from,
        ProcessState to
    ) {
        switch (from) {
            case ProcessState::New:
                return to == ProcessState::Ready ||
                       to == ProcessState::Terminated;

            case ProcessState::Ready:
                return to == ProcessState::Running ||
                       to == ProcessState::Terminated;

            case ProcessState::Running:
                return to == ProcessState::Ready ||
                       to == ProcessState::Blocked ||
                       to == ProcessState::Terminated;

            case ProcessState::Blocked:
                return to == ProcessState::Ready ||
                       to == ProcessState::Terminated;

            case ProcessState::Terminated:
                return false;
        }

        return false;
    }

    ProcessControlBlock& pcb(int pid) {
        auto iterator = pcbs_.find(pid);

        if (iterator == pcbs_.end()) {
            throw std::runtime_error(
                "Unknown process ID: " + std::to_string(pid)
            );
        }

        return iterator->second;
    }

    const ProcessControlBlock& pcb(int pid) const {
        auto iterator = pcbs_.find(pid);

        if (iterator == pcbs_.end()) {
            throw std::runtime_error(
                "Unknown process ID: " + std::to_string(pid)
            );
        }

        return iterator->second;
    }

    void logEvent(
        int pid,
        const std::string& event,
        const std::string& detail
    ) {
        events_.push_back({
            tick_,
            pid,
            event,
            detail
        });
    }

    void changeState(
        int pid,
        ProcessState newState,
        const std::string& reason,
        bool enqueueReady
    ) {
        auto& process = pcb(pid);

        if (!legalTransition(process.state, newState)) {
            throw std::runtime_error(
                "Illegal process-state transition for PID " +
                std::to_string(pid) + ": " +
                stateName(process.state) + " -> " +
                stateName(newState)
            );
        }

        process.state = newState;
        process.history.push_back({
            tick_,
            newState
        });

        if (newState == ProcessState::Terminated) {
            process.terminatedAt = tick_;
        }

        if (enqueueReady && newState == ProcessState::Ready) {
            readyQueue_.push_back(pid);
        }

        logEvent(
            pid,
            "STATE",
            reason + " [" + stateName(newState) + "]"
        );
    }

public:
    int createProcess(
        const std::string& name,
        std::optional<int> parentPid,
        int priority,
        int cpuBurst
    ) {
        if (name.empty()) {
            throw std::invalid_argument(
                "Process name cannot be empty."
            );
        }

        if (priority < 1 || priority > 10) {
            throw std::invalid_argument(
                "Priority must be between 1 and 10."
            );
        }

        if (cpuBurst <= 0) {
            throw std::invalid_argument(
                "CPU burst must be positive."
            );
        }

        if (parentPid.has_value()) {
            auto& parent = pcb(*parentPid);

            if (parent.state == ProcessState::Terminated) {
                throw std::runtime_error(
                    "A terminated process cannot create a child."
                );
            }
        }

        const int pid = nextPid_++;

        ProcessControlBlock process{
            pid,
            parentPid,
            name,
            ProcessState::New,
            priority,
            3,
            cpuBurst
        };

        process.createdAt = tick_;
        process.history.push_back({
            tick_,
            ProcessState::New
        });

        pcbs_.emplace(pid, std::move(process));

        logEvent(
            pid,
            "CREATE",
            "Created process " + name
        );

        if (parentPid.has_value()) {
            pcb(*parentPid).children.insert(pid);
        }

        changeState(
            pid,
            ProcessState::Ready,
            "Process admitted to scheduler",
            true
        );

        return pid;
    }

    void addResource(
        const std::string& id,
        const std::string& type
    ) {
        if (resources_.contains(id)) {
            throw std::runtime_error(
                "Resource already exists: " + id
            );
        }

        resources_.emplace(
            id,
            Resource{id, type, std::nullopt}
        );
    }

    bool acquireResource(
        int pid,
        const std::string& resourceId
    ) {
        auto& process = pcb(pid);

        auto resourceIterator = resources_.find(resourceId);

        if (resourceIterator == resources_.end()) {
            throw std::runtime_error(
                "Unknown resource: " + resourceId
            );
        }

        auto& resource = resourceIterator->second;

        if (!resource.ownerPid.has_value()) {
            resource.ownerPid = pid;
            process.ownedResources.insert(resourceId);
            return true;
        }

        return resource.ownerPid == pid;
    }

    void releaseResource(
        int pid,
        const std::string& resourceId
    ) {
        auto& process = pcb(pid);

        auto resourceIterator = resources_.find(resourceId);

        if (resourceIterator == resources_.end()) {
            throw std::runtime_error(
                "Unknown resource: " + resourceId
            );
        }

        auto& resource = resourceIterator->second;

        if (
            !resource.ownerPid.has_value() ||
            *resource.ownerPid != pid
        ) {
            throw std::runtime_error(
                "Process does not own resource: " + resourceId
            );
        }

        resource.ownerPid.reset();
        process.ownedResources.erase(resourceId);
    }

    std::optional<int> dispatch() {
        if (currentPid_.has_value()) {
            return currentPid_;
        }

        if (readyQueue_.empty()) {
            return std::nullopt;
        }

        /*
         * Priority scheduling is implemented by selecting the best candidate
         * from the ready queue. The queue remains a simple container so the
         * policy can be changed without changing PCB representation.
         */
        auto best = std::min_element(
            readyQueue_.begin(),
            readyQueue_.end(),
            [this](int leftPid, int rightPid) {
                const auto& left = pcb(leftPid);
                const auto& right = pcb(rightPid);

                if (left.priority != right.priority) {
                    return left.priority < right.priority;
                }

                return left.createdAt < right.createdAt;
            }
        );

        const int pid = *best;
        readyQueue_.erase(best);

        auto& process = pcb(pid);

        changeState(
            pid,
            ProcessState::Running,
            "Dispatched to CPU",
            false
        );

        currentPid_ = pid;

        if (!process.startedAt.has_value()) {
            process.startedAt = tick_;
        }

        process.contextSwitches++;
        contextSwitchCount_++;

        logEvent(
            pid,
            "DISPATCH",
            "CPU assigned to process"
        );

        return pid;
    }

    void preempt(
        const std::string& reason = "time slice expired"
    ) {
        if (!currentPid_.has_value()) {
            return;
        }

        const int pid = *currentPid_;

        changeState(
            pid,
            ProcessState::Ready,
            reason,
            true
        );

        currentPid_.reset();

        logEvent(
            pid,
            "PREEMPT",
            reason
        );
    }

    void blockCurrent(
        const std::string& waitObject
    ) {
        if (!currentPid_.has_value()) {
            throw std::runtime_error(
                "Cannot block because no process is running."
            );
        }

        if (waitObject.empty()) {
            throw std::invalid_argument(
                "Wait object cannot be empty."
            );
        }

        const int pid = *currentPid_;

        auto& process = pcb(pid);

        changeState(
            pid,
            ProcessState::Blocked,
            "Waiting for " + waitObject,
            false
        );

        process.pendingIO = waitObject;
        blockedQueues_[waitObject].insert(pid);

        currentPid_.reset();

        logEvent(
            pid,
            "BLOCK",
            "Process cannot continue until " + waitObject
        );
    }

    void completeIO(
        const std::string& waitObject
    ) {
        auto iterator = blockedQueues_.find(waitObject);

        if (iterator == blockedQueues_.end()) {
            return;
        }

        /*
         * Copy the IDs before changing the wait queue. This prevents iterator
         * invalidation and keeps wake-up behavior deterministic.
         */
        const std::set<int> waitingProcesses = iterator->second;

        for (int pid : waitingProcesses) {
            auto& process = pcb(pid);

            if (process.state != ProcessState::Blocked) {
                continue;
            }

            process.pendingIO.reset();

            changeState(
                pid,
                ProcessState::Ready,
                "I/O completed for " + waitObject,
                true
            );

            logEvent(
                pid,
                "WAKE",
                "Process returned to ready queue"
            );
        }

        blockedQueues_.erase(iterator);
    }

    void waitForChild(
        int parentPid,
        std::optional<int> childPid
    ) {
        auto& parent = pcb(parentPid);

        if (parent.state == ProcessState::Terminated) {
            throw std::runtime_error(
                "Terminated process cannot wait."
            );
        }

        if (childPid.has_value()) {
            if (!parent.children.contains(*childPid)) {
                throw std::runtime_error(
                    "Specified PID is not a child."
                );
            }

            const auto& child = pcb(*childPid);

            if (child.state == ProcessState::Terminated) {
                return;
            }
        }

        parent.waitingForChild = childPid;

        if (
            currentPid_.has_value() &&
            *currentPid_ == parentPid
        ) {
            changeState(
                parentPid,
                ProcessState::Blocked,
                "Parent waiting for child termination",
                false
            );

            currentPid_.reset();
        }

        logEvent(
            parentPid,
            "WAIT",
            childPid.has_value()
                ? "Waiting for child " +
                      std::to_string(*childPid)
                : "Waiting for any child"
        );
    }

    void terminate(
        int pid,
        int exitCode
    ) {
        auto& process = pcb(pid);

        if (process.state == ProcessState::Terminated) {
            return;
        }

        if (
            currentPid_.has_value() &&
            *currentPid_ == pid
        ) {
            currentPid_.reset();
        }

        readyQueue_.erase(
            std::remove(
                readyQueue_.begin(),
                readyQueue_.end(),
                pid
            ),
            readyQueue_.end()
        );

        for (auto& [_, waiting] : blockedQueues_) {
            waiting.erase(pid);
        }

        /*
         * A process must not leave owned resources behind when it terminates.
         * The cleanup models the resource-accounting responsibility of the
         * process manager.
         */
        const auto ownedResources = process.ownedResources;

        for (const auto& resourceId : ownedResources) {
            releaseResource(pid, resourceId);
        }

        process.exitCode = exitCode;

        changeState(
            pid,
            ProcessState::Terminated,
            "Process exited",
            false
        );

        process.terminatedAt = tick_;

        logEvent(
            pid,
            "EXIT",
            "Exit code " + std::to_string(exitCode)
        );

        if (process.parentPid.has_value()) {
            const int parentPid = *process.parentPid;

            if (pcbs_.contains(parentPid)) {
                auto& parent = pcb(parentPid);

                const bool waitingForThisChild =
                    parent.waitingForChild.has_value() &&
                    *parent.waitingForChild == pid;

                const bool waitingForAnyChild =
                    !parent.waitingForChild.has_value();

                if (
                    parent.state == ProcessState::Blocked &&
                    (waitingForThisChild || waitingForAnyChild)
                ) {
                    parent.waitingForChild.reset();

                    changeState(
                        parentPid,
                        ProcessState::Ready,
                        "Child termination satisfied wait",
                        true
                    );

                    logEvent(
                        parentPid,
                        "WAKE",
                        "Parent awakened after child exit"
                    );
                }
            }
        }
    }

    void cpuTick() {
        if (!currentPid_.has_value()) {
            dispatch();
        }

        if (!currentPid_.has_value()) {
            tick_++;
            return;
        }

        const int pid = *currentPid_;
        auto& process = pcb(pid);

        process.cpuTicks++;
        process.remainingBurst--;

        /*
         * The program counter and register state belong to the PCB. When the
         * process is preempted, these values remain associated with it and
         * become the starting point when it is dispatched again.
         */
        process.context.programCounter += 4;
        process.context.registers["R0"]++;

        tick_++;

        if (process.remainingBurst <= 0) {
            terminate(pid, 0);
            return;
        }

        /*
         * Build workers periodically perform simulated disk access. The
         * important lifecycle behavior is RUNNING -> BLOCKED, followed later
         * by BLOCKED -> READY when the device completes.
         */
        if (
            process.name.find("build") != std::string::npos &&
            process.cpuTicks % 4 == 0
        ) {
            blockCurrent("artifact-disk");
            return;
        }

        if (
            process.cpuTicks % process.timeSlice == 0
        ) {
            preempt();
        }
    }

    void run(int maxTicks) {
        if (maxTicks <= 0) {
            throw std::invalid_argument(
                "Maximum tick count must be positive."
            );
        }

        for (int i = 0; i < maxTicks; ++i) {
            bool active = false;

            for (const auto& [_, process] : pcbs_) {
                if (process.state != ProcessState::Terminated) {
                    active = true;
                    break;
                }
            }

            if (!active) {
                break;
            }

            cpuTick();

            /*
             * The disk completes every third simulation tick. This gives the
             * blocked queue an observable lifecycle rather than making I/O
             * behave like instantaneous CPU execution.
             */
            if (tick_ % 3 == 0) {
                completeIO("artifact-disk");
            }
        }
    }

    void validateInvariants() const {
        int runningCount = 0;

        for (const auto& [pid, process] : pcbs_) {
            if (process.state == ProcessState::Running) {
                runningCount++;

                if (
                    !currentPid_.has_value() ||
                    *currentPid_ != pid
                ) {
                    throw std::runtime_error(
                        "RUNNING PCB disagrees with current PID."
                    );
                }
            }

            const bool inReadyQueue =
                std::find(
                    readyQueue_.begin(),
                    readyQueue_.end(),
                    pid
                ) != readyQueue_.end();

            if (
                process.state == ProcessState::Ready &&
                !inReadyQueue
            ) {
                throw std::runtime_error(
                    "READY process missing from ready queue."
                );
            }

            if (
                process.state != ProcessState::Ready &&
                inReadyQueue
            ) {
                throw std::runtime_error(
                    "Non-READY process appears in ready queue."
                );
            }
        }

        if (runningCount > 1) {
            throw std::runtime_error(
                "Single CPU cannot run multiple processes."
            );
        }

        for (const auto& [resourceId, resource] : resources_) {
            if (resource.ownerPid.has_value()) {
                const auto& owner = pcb(*resource.ownerPid);

                if (
                    !owner.ownedResources.contains(resourceId)
                ) {
                    throw std::runtime_error(
                        "Resource ownership invariant violated."
                    );
                }
            }
        }
    }

    void printPCB(int pid) const {
        const auto& process = pcb(pid);

        std::cout
            << "PID: " << process.pid << '\n'
            << "Name: " << process.name << '\n'
            << "Parent: ";

        if (process.parentPid.has_value()) {
            std::cout << *process.parentPid;
        } else {
            std::cout << "none";
        }

        std::cout
            << '\n'
            << "State: " << stateName(process.state) << '\n'
            << "Priority: " << process.priority << '\n'
            << "Remaining CPU burst: "
            << process.remainingBurst << '\n'
            << "CPU ticks: " << process.cpuTicks << '\n'
            << "Ready ticks: " << process.readyTicks << '\n'
            << "Blocked ticks: " << process.blockedTicks << '\n'
            << "Context switches: "
            << process.contextSwitches << '\n'
            << "Program counter: "
            << process.context.programCounter << '\n'
            << "R0: "
            << process.context.registers.at("R0") << '\n';

        std::cout << "Children: ";

        for (int child : process.children) {
            std::cout << child << ' ';
        }

        std::cout << '\n';

        std::cout << "Resources: ";

        for (const auto& resource : process.ownedResources) {
            std::cout << resource << ' ';
        }

        std::cout << "\n";
    }

    void printProcessTree(
        int pid,
        int depth = 0
    ) const {
        const auto& process = pcb(pid);

        std::cout
            << std::string(depth * 2, ' ')
            << process.pid
            << " "
            << process.name
            << " ["
            << stateName(process.state)
            << "]\n";

        for (int child : process.children) {
            printProcessTree(child, depth + 1);
        }
    }

    void printEvents() const {
        std::cout << "\nLifecycle event log:\n";

        for (const auto& event : events_) {
            std::cout
                << "t="
                << std::setw(2)
                << event.tick
                << " PID="
                << std::setw(2)
                << event.pid
                << " "
                << std::setw(8)
                << event.event
                << " "
                << event.detail
                << '\n';
        }
    }

    void printLifecycle(int pid) const {
        const auto& process = pcb(pid);

        std::cout
            << "PID "
            << pid
            << ": ";

        for (
            std::size_t index = 0;
            index < process.history.size();
            ++index
        ) {
            const auto& record = process.history[index];

            if (index != 0) {
                std::cout << " -> ";
            }

            std::cout
                << stateName(record.state)
                << "@"
                << record.tick;
        }

        std::cout << '\n';
    }

    int contextSwitchCount() const {
        return contextSwitchCount_;
    }

    const ProcessControlBlock& getPCB(int pid) const {
        return pcb(pid);
    }
};

int main() {
    try {
        std::cout
            << "PROCESS MANAGEMENT CASE STUDY\n"
            << "=============================\n";

        ProcessManager manager;

        manager.addResource(
            "compiler-slot",
            "exclusive build compiler"
        );

        manager.addResource(
            "artifact-disk",
            "build artifact storage"
        );

        /*
         * The service process represents a long-running parent process.
         * Build workers are children with independent PCBs and lifecycles.
         */
        const int service = manager.createProcess(
            "build-service",
            std::nullopt,
            2,
            8
        );

        const int buildA = manager.createProcess(
            "build-worker-A",
            service,
            4,
            9
        );

        const int buildB = manager.createProcess(
            "build-worker-B",
            service,
            5,
            7
        );

        const int monitor = manager.createProcess(
            "monitor",
            service,
            3,
            5
        );

        std::cout << "\nInitial process hierarchy:\n";
        manager.printProcessTree(service);

        std::cout << "\nInitial PCB for build worker A:\n";
        manager.printPCB(buildA);

        std::cout << "\nResource ownership:\n";

        std::cout
            << "build-worker-A compiler slot: "
            << std::boolalpha
            << manager.acquireResource(
                buildA,
                "compiler-slot"
            )
            << '\n';

        /*
         * The second worker cannot acquire an exclusive resource while the
         * first worker owns it. The example demonstrates why ownership belongs
         * in process-management metadata rather than being inferred from the
         * process name.
         */
        std::cout
            << "build-worker-B compiler slot: "
            << manager.acquireResource(
                buildB,
                "compiler-slot"
            )
            << '\n';

        /*
         * The service process is dispatched and waits for build-worker-A.
         * This creates a parent lifecycle dependency.
         */
        manager.dispatch();

        manager.waitForChild(
            service,
            buildA
        );

        std::cout
            << "\nService state after waiting: "
            << stateName(
                manager.getPCB(service).state
            )
            << '\n';

        std::cout
            << "\nRunning lifecycle simulation...\n";

        manager.run(35);

        /*
         * Release of the compiler slot is explicit in this scenario. In
         * production kernel resource management, termination cleanup would
         * normally ensure resources do not remain permanently owned.
         */
        if (
            manager.getPCB(buildA).state ==
                ProcessState::Terminated
        ) {
            try {
                manager.releaseResource(
                    buildA,
                    "compiler-slot"
                );
            } catch (const std::exception&) {
                /*
                 * The manager already releases owned resources during
                 * termination. This branch documents that ownership cleanup
                 * has already occurred.
                 */
            }
        }

        manager.validateInvariants();

        std::cout << "\nFinal process hierarchy:\n";
        manager.printProcessTree(service);

        std::cout << "\nFinal PCBs:\n";
        manager.printPCB(service);
        manager.printPCB(buildA);
        manager.printPCB(buildB);
        manager.printPCB(monitor);

        std::cout << "\nLifecycle paths:\n";
        manager.printLifecycle(service);
        manager.printLifecycle(buildA);
        manager.printLifecycle(buildB);
        manager.printLifecycle(monitor);

        manager.printEvents();

        std::cout
            << "\nContext switches: "
            << manager.contextSwitchCount()
            << '\n';

        std::cout
            << "\nCase study invariants validated successfully.\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr
            << "Simulation failure: "
            << error.what()
            << '\n';

        return 1;
    }
}
