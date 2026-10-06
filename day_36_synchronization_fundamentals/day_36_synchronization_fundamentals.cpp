/*
 * Synchronization Fundamentals: Repository Job Scheduler
 *
 * C++17 case study demonstrating:
 *   - race conditions caused by unsynchronized shared state
 *   - critical sections
 *   - mutual exclusion with std::mutex
 *   - condition variables for coordinated access
 *   - lock_guard and unique_lock
 *   - atomic operations for simple counters
 *   - deadlock avoidance through consistent lock ordering
 *
 * Compile:
 *   g++ -std=c++17 -O2 -pthread synchronization_fundamentals.cpp -o synchronization_fundamentals
 */

#include <atomic>
#include <chrono>
#include <condition_variable>
#include <functional>
#include <iomanip>
#include <iostream>
#include <map>
#include <mutex>
#include <queue>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

using namespace std::chrono_literals;

class UnsafeCounter {
private:
    int value_ = 0;

public:
    void increment() {
        int observed = value_;

        // The delay makes the read-modify-write race easier to reproduce.
        std::this_thread::sleep_for(10us);

        value_ = observed + 1;
    }

    int value() const {
        return value_;
    }
};

class SafeCounter {
private:
    int value_ = 0;
    mutable std::mutex mutex_;

public:
    void increment() {
        std::lock_guard<std::mutex> guard(mutex_);

        // The entire read-modify-write operation is the critical section.
        ++value_;
    }

    int value() const {
        std::lock_guard<std::mutex> guard(mutex_);
        return value_;
    }
};

void demonstrateRaceCondition() {
    std::cout << "\n=== Race Condition ===\n";

    UnsafeCounter counter;

    constexpr int threadCount = 8;
    constexpr int incrementsPerThread = 1000;

    std::vector<std::thread> workers;

    for (int index = 0; index < threadCount; ++index) {
        workers.emplace_back([&counter]() {
            for (int i = 0; i < incrementsPerThread; ++i) {
                counter.increment();
            }
        });
    }

    for (auto& worker : workers) {
        worker.join();
    }

    const int expected = threadCount * incrementsPerThread;

    std::cout << "Expected: " << expected << '\n';
    std::cout << "Actual:   " << counter.value() << '\n';

    if (counter.value() != expected) {
        std::cout << "Lost updates occurred because the critical section was unprotected.\n";
    }
}

void demonstrateMutualExclusion() {
    std::cout << "\n=== Mutual Exclusion ===\n";

    SafeCounter counter;

    constexpr int threadCount = 8;
    constexpr int incrementsPerThread = 1000;

    std::vector<std::thread> workers;

    for (int index = 0; index < threadCount; ++index) {
        workers.emplace_back([&counter]() {
            for (int i = 0; i < incrementsPerThread; ++i) {
                counter.increment();
            }
        });
    }

    for (auto& worker : workers) {
        worker.join();
    }

    std::cout << "Expected: " << threadCount * incrementsPerThread << '\n';
    std::cout << "Actual:   " << counter.value() << '\n';
}

class JobQueue {
public:
    struct Job {
        int id;
        std::string payload;
    };

private:
    std::queue<Job> queue_;
    std::mutex mutex_;
    std::condition_variable condition_;
    bool shuttingDown_ = false;

public:
    void submit(Job job) {
        {
            std::lock_guard<std::mutex> guard(mutex_);

            if (shuttingDown_) {
                throw std::runtime_error("Cannot submit after scheduler shutdown.");
            }

            queue_.push(std::move(job));
        }

        // Notification happens after releasing the mutex, so the waiting
        // consumer can compete for the lock without unnecessary contention.
        condition_.notify_one();
    }

    bool take(Job& output) {
        std::unique_lock<std::mutex> lock(mutex_);

        /*
         * unique_lock is appropriate because condition_variable::wait may
         * temporarily release and reacquire the mutex.
         *
         * The predicate protects against spurious wakeups and handles shutdown
         * without leaving a consumer blocked forever.
         */
        condition_.wait(lock, [this]() {
            return !queue_.empty() || shuttingDown_;
        });

        if (queue_.empty() && shuttingDown_) {
            return false;
        }

        output = std::move(queue_.front());
        queue_.pop();

        return true;
    }

    void shutdown() {
        {
            std::lock_guard<std::mutex> guard(mutex_);
            shuttingDown_ = true;
        }

        condition_.notify_all();
    }
};

void demonstrateProducerConsumer() {
    std::cout << "\n=== Producer-Consumer Critical Section ===\n";

    JobQueue queue;

    constexpr int producerCount = 2;
    constexpr int jobsPerProducer = 20;

    std::atomic<int> processed{0};

    std::vector<std::thread> consumers;

    for (int consumerIndex = 0; consumerIndex < 2; ++consumerIndex) {
        consumers.emplace_back([&queue, &processed]() {
            JobQueue::Job job{};

            while (queue.take(job)) {
                std::this_thread::sleep_for(1ms);
                processed.fetch_add(1, std::memory_order_relaxed);
            }
        });
    }

    std::vector<std::thread> producers;

    for (int producerIndex = 0; producerIndex < producerCount; ++producerIndex) {
        producers.emplace_back([&queue, producerIndex]() {
            for (int jobIndex = 0; jobIndex < jobsPerProducer; ++jobIndex) {
                queue.submit({
                    producerIndex * 100 + jobIndex,
                    "repository-analysis-job",
                });
            }
        });
    }

    for (auto& producer : producers) {
        producer.join();
    }

    queue.shutdown();

    for (auto& consumer : consumers) {
        consumer.join();
    }

    std::cout << "Processed jobs: " << processed.load() << '\n';
}

class Account {
public:
    explicit Account(int id, int balance)
        : id_(id), balance_(balance) {
        if (balance < 0) {
            throw std::invalid_argument("Initial balance cannot be negative.");
        }
    }

    int id() const {
        return id_;
    }

    int balance() const {
        return balance_;
    }

private:
    friend class Bank;

    int id_;
    int balance_;
    std::mutex mutex_;
};

class Bank {
public:
    static bool transfer(Account& source, Account& target, int amount) {
        if (&source == &target) {
            throw std::invalid_argument("Source and target must differ.");
        }

        if (amount <= 0) {
            throw std::invalid_argument("Transfer amount must be positive.");
        }

        /*
         * std::scoped_lock locks both mutexes using a deadlock-avoidance
         * algorithm. This is safer than acquiring two mutexes manually in
         * inconsistent orders.
         */
        std::scoped_lock locks(source.mutex_, target.mutex_);

        if (source.balance_ < amount) {
            return false;
        }

        source.balance_ -= amount;
        target.balance_ += amount;

        return true;
    }

    static int total(Account& first, Account& second) {
        std::scoped_lock locks(first.mutex_, second.mutex_);
        return first.balance_ + second.balance_;
    }
};

void demonstrateMultiResourceSynchronization() {
    std::cout << "\n=== Multi-Resource Synchronization ===\n";

    Account accountA(1, 1000);
    Account accountB(2, 1000);

    std::vector<std::thread> workers;

    for (int index = 0; index < 100; ++index) {
        workers.emplace_back([&accountA, &accountB]() {
            Bank::transfer(accountA, accountB, 1);
        });

        workers.emplace_back([&accountA, &accountB]() {
            Bank::transfer(accountB, accountA, 1);
        });
    }

    for (auto& worker : workers) {
        worker.join();
    }

    std::cout << "Account A: " << accountA.balance() << '\n';
    std::cout << "Account B: " << accountB.balance() << '\n';
    std::cout << "Total:     " << Bank::total(accountA, accountB) << '\n';
}

void demonstrateAtomicCounter() {
    std::cout << "\n=== Atomic Operation ===\n";

    std::atomic<int> counter{0};

    constexpr int threadCount = 8;
    constexpr int incrementsPerThread = 10000;

    std::vector<std::thread> workers;

    for (int index = 0; index < threadCount; ++index) {
        workers.emplace_back([&counter]() {
            for (int i = 0; i < incrementsPerThread; ++i) {
                counter.fetch_add(1, std::memory_order_relaxed);
            }
        });
    }

    for (auto& worker : workers) {
        worker.join();
    }

    std::cout << "Expected: " << threadCount * incrementsPerThread << '\n';
    std::cout << "Actual:   " << counter.load() << '\n';
}

void demonstrateTimedLock() {
    std::cout << "\n=== Timed Lock ===\n";

    std::timed_mutex mutex;
    mutex.lock();

    std::thread worker([&mutex]() {
        if (mutex.try_lock_for(50ms)) {
            std::cout << "Worker acquired the mutex.\n";
            mutex.unlock();
        } else {
            std::cout << "Worker timed out instead of waiting indefinitely.\n";
        }
    });

    worker.join();
    mutex.unlock();
}

int main() {
    try {
        std::cout << "Synchronization Fundamentals\n";
        std::cout << "Race Conditions | Critical Sections | Mutual Exclusion\n";

        demonstrateRaceCondition();
        demonstrateMutualExclusion();
        demonstrateProducerConsumer();
        demonstrateMultiResourceSynchronization();
        demonstrateAtomicCounter();
        demonstrateTimedLock();

        std::cout << "\nCase study completed successfully.\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Fatal error: " << error.what() << '\n';
        return 1;
    }
}
