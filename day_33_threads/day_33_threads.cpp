#include <algorithm>
#include <atomic>
#include <chrono>
#include <condition_variable>
#include <exception>
#include <functional>
#include <future>
#include <iomanip>
#include <iostream>
#include <map>
#include <mutex>
#include <optional>
#include <queue>
#include <stdexcept>
#include <string>
#include <thread>
#include <utility>
#include <vector>

/*
 * C++17 case study: repository-independent server workload scheduler.
 *
 * The system models a service that receives CPU and I/O-like jobs and chooses
 * an execution strategy. C++ provides direct access to std::thread, futures,
 * mutexes, condition variables, atomics, and a thread pool implemented here.
 *
 * The case study focuses on:
 *   - process versus thread isolation
 *   - thread lifecycle
 *   - worker-thread scheduling
 *   - producer-consumer coordination
 *   - synchronization and race prevention
 *   - thread-pool design
 *   - failure propagation
 *   - cancellation
 *   - performance and scalability trade-offs
 *
 * Build:
 *   g++ -std=c++17 -O2 -pthread threads_case_study.cpp -o threads_case_study
 */

using namespace std::chrono_literals;


// -----------------------------------------------------------------------------
// Thread lifecycle model
// -----------------------------------------------------------------------------

enum class ThreadLifecycle {
    New,
    Runnable,
    Running,
    Waiting,
    Terminated
};


std::string lifecycleName(ThreadLifecycle state) {
    switch (state) {
        case ThreadLifecycle::New:
            return "NEW";
        case ThreadLifecycle::Runnable:
            return "RUNNABLE";
        case ThreadLifecycle::Running:
            return "RUNNING";
        case ThreadLifecycle::Waiting:
            return "WAITING";
        case ThreadLifecycle::Terminated:
            return "TERMINATED";
    }

    return "UNKNOWN";
}


class LifecycleTracker {
private:
    std::mutex mutex_;
    std::vector<std::string> events_;

public:
    void record(const std::string& threadName,
                ThreadLifecycle state,
                const std::string& detail) {
        std::lock_guard<std::mutex> lock(mutex_);

        events_.push_back(
            threadName + " -> " +
            lifecycleName(state) + " -> " +
            detail
        );
    }

    void print() const {
        for (const auto& event : events_) {
            std::cout << "  " << event << '\n';
        }
    }
};


// -----------------------------------------------------------------------------
// Process versus thread representation
// -----------------------------------------------------------------------------

struct ExecutionContext {
    std::thread::id threadId;
    std::string role;
};


void demonstrateProcessVsThreads() {
    std::cout << "\n=== Process versus threads ===\n";

    /*
     * A C++ thread is created inside the current process. All these threads
     * share the process address space, file descriptors, and most process-level
     * resources. A real process boundary requires OS facilities such as fork()
     * on POSIX or CreateProcess() on Windows.
     *
     * The program therefore represents the process boundary conceptually rather
     * than embedding platform-specific process APIs into this C++17 example.
     */

    ExecutionContext mainContext{
        std::this_thread::get_id(),
        "main process thread"
    };

    ExecutionContext childContext;

    std::thread worker([&childContext]() {
        childContext = {
            std::this_thread::get_id(),
            "worker thread"
        };
    });

    worker.join();

    std::cout << "Main thread ID:   " << mainContext.threadId << '\n';
    std::cout << "Worker thread ID: " << childContext.threadId << '\n';

    std::cout
        << "Both thread IDs belong to the same process and therefore share "
           "the process address space.\n";

    std::cout
        << "A separate process would have an independent virtual address space "
           "and a stronger failure-isolation boundary.\n";
}


// -----------------------------------------------------------------------------
// Lifecycle demonstration
// -----------------------------------------------------------------------------

void demonstrateThreadLifecycle() {
    std::cout << "\n=== Thread lifecycle ===\n";

    LifecycleTracker tracker;

    tracker.record(
        "lifecycle-worker",
        ThreadLifecycle::New,
        "std::thread object constructed"
    );

    std::thread worker([&tracker]() {
        tracker.record(
            "lifecycle-worker",
            ThreadLifecycle::Runnable,
            "thread has entered the scheduler"
        );

        tracker.record(
            "lifecycle-worker",
            ThreadLifecycle::Running,
            "thread is executing application code"
        );

        tracker.record(
            "lifecycle-worker",
            ThreadLifecycle::Waiting,
            "thread waits for a timed event"
        );

        std::this_thread::sleep_for(20ms);

        tracker.record(
            "lifecycle-worker",
            ThreadLifecycle::Running,
            "thread resumed after wait"
        );

        tracker.record(
            "lifecycle-worker",
            ThreadLifecycle::Terminated,
            "thread function returned"
        );
    });

    tracker.record(
        "lifecycle-worker",
        ThreadLifecycle::Runnable,
        "std::thread::start equivalent is represented by construction"
    );

    worker.join();

    tracker.print();

    /*
     * The enum is an application-level model. The C++ standard library does not
     * expose the operating system's complete scheduler state machine.
     */
}


// -----------------------------------------------------------------------------
// Thread-safe bounded queue
// -----------------------------------------------------------------------------

template <typename T>
class BoundedQueue {
private:
    std::queue<T> queue_;
    const std::size_t capacity_;

    mutable std::mutex mutex_;
    std::condition_variable notEmpty_;
    std::condition_variable notFull_;

    bool closed_ = false;

public:
    explicit BoundedQueue(std::size_t capacity)
        : capacity_(capacity) {
        if (capacity == 0) {
            throw std::invalid_argument("Queue capacity must be positive");
        }
    }

    bool push(T item) {
        std::unique_lock<std::mutex> lock(mutex_);

        notFull_.wait(lock, [this]() {
            return queue_.size() < capacity_ || closed_;
        });

        if (closed_) {
            return false;
        }

        queue_.push(std::move(item));
        notEmpty_.notify_one();
        return true;
    }

    bool pop(T& output) {
        std::unique_lock<std::mutex> lock(mutex_);

        notEmpty_.wait(lock, [this]() {
            return !queue_.empty() || closed_;
        });

        if (queue_.empty()) {
            return false;
        }

        output = std::move(queue_.front());
        queue_.pop();

        notFull_.notify_one();
        return true;
    }

    void close() {
        {
            std::lock_guard<std::mutex> lock(mutex_);
            closed_ = true;
        }

        notEmpty_.notify_all();
        notFull_.notify_all();
    }
};


// -----------------------------------------------------------------------------
// Work model
// -----------------------------------------------------------------------------

enum class WorkKind {
    CpuBound,
    IoBound
};


struct WorkItem {
    int id;
    WorkKind kind;
    int amount;
    std::string description;
};


struct WorkResult {
    int id;
    bool success;
    long long value;
    std::string message;
};


// -----------------------------------------------------------------------------
// Computation
// -----------------------------------------------------------------------------

bool isPrime(int value) {
    if (value < 2) {
        return false;
    }

    for (int divisor = 2; divisor * divisor <= value; ++divisor) {
        if (value % divisor == 0) {
            return false;
        }
    }

    return true;
}


int countPrimes(int limit) {
    int count = 0;

    for (int value = 2; value <= limit; ++value) {
        if (isPrime(value)) {
            ++count;
        }
    }

    return count;
}


// -----------------------------------------------------------------------------
// Governance-style scheduler
// -----------------------------------------------------------------------------

class WorkScheduler {
private:
    BoundedQueue<WorkItem> queue_;

    std::vector<std::thread> workers_;

    std::mutex resultMutex_;
    std::vector<WorkResult> results_;

    std::atomic<bool> cancellationRequested_{false};

public:
    explicit WorkScheduler(std::size_t workerCount,
                           std::size_t queueCapacity)
        : queue_(queueCapacity) {
        if (workerCount == 0) {
            throw std::invalid_argument(
                "At least one worker is required"
            );
        }

        workers_.reserve(workerCount);

        for (std::size_t index = 0; index < workerCount; ++index) {
            workers_.emplace_back(
                [this, index]() {
                    workerLoop(index);
                }
            );
        }
    }

    ~WorkScheduler() {
        stop();
    }

    bool submit(WorkItem item) {
        if (cancellationRequested_.load()) {
            return false;
        }

        if (item.id < 0) {
            throw std::invalid_argument("Work item ID cannot be negative");
        }

        if (item.amount <= 0) {
            throw std::invalid_argument(
                "Work item amount must be positive"
            );
        }

        return queue_.push(std::move(item));
    }

    void requestCancellation() {
        cancellationRequested_.store(true);
    }

    void stop() {
        if (workers_.empty()) {
            return;
        }

        queue_.close();

        for (auto& worker : workers_) {
            if (worker.joinable()) {
                worker.join();
            }
        }

        workers_.clear();
    }

    std::vector<WorkResult> results() const {
        std::lock_guard<std::mutex> lock(resultMutex_);
        return results_;
    }

private:
    void workerLoop(std::size_t workerIndex) {
        WorkItem item;

        while (queue_.pop(item)) {
            if (cancellationRequested_.load()) {
                recordResult({
                    item.id,
                    false,
                    0,
                    "cancelled before execution by worker " +
                    std::to_string(workerIndex)
                });

                continue;
            }

            try {
                WorkResult result;

                if (item.kind == WorkKind::CpuBound) {
                    /*
                     * CPU-bound work is intentionally performed directly on
                     * worker threads. This provides parallel execution on
                     * systems where multiple OS threads can run concurrently.
                     */
                    const int primeCount = countPrimes(item.amount);

                    result = {
                        item.id,
                        true,
                        primeCount,
                        "CPU work completed by worker " +
                        std::to_string(workerIndex)
                    };
                } else {
                    /*
                     * Waiting-heavy work does not consume CPU continuously.
                     * A real application could replace this sleep with socket,
                     * file, database, or other blocking I/O.
                     */
                    std::this_thread::sleep_for(
                        std::chrono::milliseconds(item.amount)
                    );

                    result = {
                        item.id,
                        true,
                        item.amount,
                        "I/O-like wait completed by worker " +
                        std::to_string(workerIndex)
                    };
                }

                recordResult(std::move(result));
            } catch (const std::exception& error) {
                recordResult({
                    item.id,
                    false,
                    0,
                    "worker failure: " + std::string(error.what())
                });
            }
        }
    }

    void recordResult(WorkResult result) {
        std::lock_guard<std::mutex> lock(resultMutex_);
        results_.push_back(std::move(result));
    }
};


// -----------------------------------------------------------------------------
// Race condition demonstration
// -----------------------------------------------------------------------------

class UnsafeCounter {
private:
    int value_ = 0;

public:
    void increment() {
        /*
         * This intentionally performs a non-atomic read-modify-write operation.
         * Concurrent calls create a data race, which is undefined behavior in
         * C++. It is shown only to explain why synchronization is necessary.
         */
        const int current = value_;
        std::this_thread::yield();
        value_ = current + 1;
    }

    int value() const {
        return value_;
    }
};


class AtomicCounter {
private:
    std::atomic<int> value_{0};

public:
    void increment() {
        value_.fetch_add(1, std::memory_order_relaxed);
    }

    int value() const {
        return value_.load(std::memory_order_relaxed);
    }
};


void demonstrateSynchronization() {
    std::cout << "\n=== Synchronization and race conditions ===\n";

    /*
     * The unsafe implementation is not executed because intentionally creating
     * a C++ data race invokes undefined behavior. The design itself is shown
     * through the class so the unsafe mechanism is visible without relying on
     * undefined program behavior for the case study.
     */

    std::cout
        << "UnsafeCounter demonstrates why an unsynchronized read-modify-write "
           "operation cannot safely be shared between threads.\n";

    AtomicCounter counter;

    constexpr int threadCount = 8;
    constexpr int incrementsPerThread = 5000;

    std::vector<std::thread> threads;
    threads.reserve(threadCount);

    for (int index = 0; index < threadCount; ++index) {
        threads.emplace_back([&counter]() {
            for (int iteration = 0;
                 iteration < incrementsPerThread;
                 ++iteration) {
                counter.increment();
            }
        });
    }

    for (auto& thread : threads) {
        thread.join();
    }

    const int expected = threadCount * incrementsPerThread;

    std::cout << "Atomic result:  " << counter.value() << '\n';
    std::cout << "Expected result: " << expected << '\n';

    std::cout
        << "std::atomic provides synchronization for this independent counter "
           "without requiring a mutex around each increment.\n";
}


// -----------------------------------------------------------------------------
// Futures and asynchronous result propagation
// -----------------------------------------------------------------------------

WorkResult asynchronousTask(int id) {
    std::this_thread::sleep_for(30ms);

    if (id == 3) {
        throw std::runtime_error(
            "simulated failure in asynchronous task"
        );
    }

    return {
        id,
        true,
        id * id,
        "future task completed"
    };
}


void demonstrateFutures() {
    std::cout << "\n=== Futures and failure propagation ===\n";

    std::vector<std::future<WorkResult>> futures;

    for (int id = 0; id < 6; ++id) {
        futures.push_back(
            std::async(
                std::launch::async,
                asynchronousTask,
                id
            )
        );
    }

    for (auto& future : futures) {
        try {
            WorkResult result = future.get();

            std::cout
                << "Task " << result.id
                << " result=" << result.value << '\n';
        } catch (const std::exception& error) {
            /*
             * Exceptions raised inside the asynchronous function are stored
             * inside the future and rethrown by get().
             */
            std::cout
                << "Task failed: " << error.what() << '\n';
        }
    }
}


// -----------------------------------------------------------------------------
// Thread-model explanation
// -----------------------------------------------------------------------------

void explainThreadModels() {
    std::cout << "\n=== Thread models ===\n";

    std::cout
        << "Many-to-one: many user-level threads are multiplexed onto one "
           "kernel thread; a blocking kernel operation can stall the group.\n";

    std::cout
        << "One-to-one: each user-level thread maps to a kernel-schedulable "
           "thread, allowing independent OS scheduling and CPU parallelism.\n";

    std::cout
        << "Many-to-many: many user-level execution contexts are multiplexed "
           "over a pool of kernel threads.\n";

    std::cout
        << "Modern C++ std::thread represents an OS-supported execution thread "
           "but does not expose a portable API for selecting one of these "
           "historical mapping policies.\n";
}


// -----------------------------------------------------------------------------
// Practical scheduler case study
// -----------------------------------------------------------------------------

void demonstrateScheduler() {
    std::cout << "\n=== Practical workload scheduler ===\n";

    const auto workerCount = std::max(
        std::size_t{2},
        std::thread::hardware_concurrency() == 0
            ? std::size_t{2}
            : static_cast<std::size_t>(
                  std::thread::hardware_concurrency()
              )
    );

    WorkScheduler scheduler(
        std::min(workerCount, std::size_t{4}),
        4
    );

    std::vector<WorkItem> work = {
        {1, WorkKind::CpuBound, 7000, "prime analysis"},
        {2, WorkKind::IoBound, 40, "remote configuration read"},
        {3, WorkKind::CpuBound, 7200, "prime analysis"},
        {4, WorkKind::IoBound, 25, "database wait"},
        {5, WorkKind::CpuBound, 7100, "prime analysis"},
        {6, WorkKind::IoBound, 30, "object-store wait"}
    };

    for (const auto& item : work) {
        if (!scheduler.submit(item)) {
            std::cout
                << "Work item " << item.id
                << " was rejected.\n";
        }
    }

    scheduler.stop();

    auto results = scheduler.results();

    std::sort(
        results.begin(),
        results.end(),
        [](const WorkResult& left, const WorkResult& right) {
            return left.id < right.id;
        }
    );

    for (const auto& result : results) {
        std::cout
            << "Work " << result.id
            << ": "
            << (result.success ? "success" : "failure")
            << ", value=" << result.value
            << ", " << result.message
            << '\n';
    }

    std::cout
        << "The bounded queue prevents producers from creating unlimited "
           "pending work, while worker reuse limits thread creation overhead.\n";
}


// -----------------------------------------------------------------------------
// Performance and design trade-offs
// -----------------------------------------------------------------------------

void explainPerformance() {
    std::cout << "\n=== Performance characteristics ===\n";

    std::cout
        << "Thread creation has scheduling and stack-allocation costs, so a "
           "thread pool is preferable for many short-lived tasks.\n";

    std::cout
        << "Too many threads can increase context switching, memory consumption, "
           "scheduler contention, and cache disruption.\n";

    std::cout
        << "A CPU-bound workload can benefit from multiple worker threads when "
           "the OS schedules them on multiple cores, but scalability is bounded "
           "by available cores and shared resources.\n";

    std::cout
        << "I/O-bound workloads can tolerate more concurrent operations because "
           "workers spend significant time waiting rather than consuming CPU.\n";

    std::cout
        << "Locks protect invariants but can reduce scalability when contention "
           "is high. Atomics are useful for narrowly defined independent state, "
           "not as a replacement for every higher-level synchronization design.\n";
}


// -----------------------------------------------------------------------------
// Security and reliability
// -----------------------------------------------------------------------------

void explainReliability() {
    std::cout << "\n=== Reliability and security ===\n";

    std::cout
        << "Shared mutable state increases the attack and failure surface because "
           "incorrect synchronization can corrupt application invariants.\n";

    std::cout
        << "Bounded queues provide backpressure and reduce the risk of unbounded "
           "memory growth when producers outpace workers.\n";

    std::cout
        << "Worker failures should be isolated, reported, and prevented from "
           "silently corrupting shared state.\n";

    std::cout
        << "A separate process is a stronger isolation boundary than a thread. "
           "Untrusted workloads should not be treated as safe merely because "
           "they execute on a separate thread.\n";

    std::cout
        << "Deadlocks are avoided by consistent lock ordering, short critical "
           "sections, condition-variable predicates, and careful ownership "
           "of shared resources.\n";
}


// -----------------------------------------------------------------------------
// Main
// -----------------------------------------------------------------------------

int main() {
    try {
        std::cout << "THREADS CASE STUDY\n";
        std::cout << "==================\n";

        demonstrateProcessVsThreads();
        demonstrateThreadLifecycle();
        explainThreadModels();
        demonstrateSynchronization();
        demonstrateFutures();
        demonstrateScheduler();
        explainPerformance();
        explainReliability();

        std::cout << "\nCase study completed.\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << '\n';

        return 1;
    }
}
