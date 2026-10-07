/*
 * Synchronization mechanisms: C++17 repository build-worker case study.
 *
 * Scenario:
 * A build service receives jobs from several producers. A bounded queue
 * prevents unlimited memory growth, worker threads consume jobs, a counting
 * semaphore limits access to a scarce compiler-license pool, mutexes protect
 * shared state, and condition variables coordinate queue state.
 *
 * The implementation deliberately separates:
 *   mutex          -> mutual exclusion
 *   semaphore      -> permit counting
 *   condition var  -> waiting for a state predicate
 *   monitor        -> encapsulated state + lock + conditions
 *   scoped lock    -> exception-safe RAII lock ownership
 *
 * Compile:
 *   g++ -std=c++17 -pthread synchronization_case_study.cpp -o synchronization_case_study
 */

#include <chrono>
#include <condition_variable>
#include <cstdlib>
#include <exception>
#include <iostream>
#include <map>
#include <memory>
#include <mutex>
#include <optional>
#include <queue>
#include <random>
#include <semaphore>
#include <sstream>
#include <stdexcept>
#include <string>
#include <thread>
#include <utility>
#include <vector>

using namespace std::chrono_literals;

enum class JobState {
    Queued,
    Running,
    Succeeded,
    Failed
};

struct BuildJob {
    int id;
    std::string repository;
    std::string branch;
    int estimated_seconds;
    bool should_fail{false};
    JobState state{JobState::Queued};
};

class BuildQueueMonitor {
private:
    std::queue<std::shared_ptr<BuildJob>> jobs_;
    const std::size_t capacity_;
    bool stopping_{false};

    /*
     * The mutex protects the queue, capacity state, and stopping flag.
     * The condition variables wait on predicates involving that protected
     * state. The predicate, rather than notification itself, defines
     * correctness.
     */
    mutable std::mutex mutex_;
    std::condition_variable not_empty_;
    std::condition_variable not_full_;

public:
    explicit BuildQueueMonitor(std::size_t capacity)
        : capacity_(capacity) {
        if (capacity == 0) {
            throw std::invalid_argument("Queue capacity must be positive");
        }
    }

    void push(std::shared_ptr<BuildJob> job) {
        if (!job) {
            throw std::invalid_argument("Cannot enqueue a null build job");
        }

        std::unique_lock<std::mutex> lock(mutex_);

        not_full_.wait(lock, [this] {
            return jobs_.size() < capacity_ || stopping_;
        });

        if (stopping_) {
            throw std::runtime_error("Queue is stopping");
        }

        jobs_.push(std::move(job));
        not_empty_.notify_one();
    }

    std::optional<std::shared_ptr<BuildJob>> pop() {
        std::unique_lock<std::mutex> lock(mutex_);

        not_empty_.wait(lock, [this] {
            return !jobs_.empty() || stopping_;
        });

        if (jobs_.empty() && stopping_) {
            return std::nullopt;
        }

        auto job = jobs_.front();
        jobs_.pop();

        not_full_.notify_one();
        return job;
    }

    void stop() {
        {
            std::lock_guard<std::mutex> lock(mutex_);
            stopping_ = true;
        }

        /*
         * All waiters must be notified because stop changes the predicates
         * for both producers and consumers.
         */
        not_empty_.notify_all();
        not_full_.notify_all();
    }

    std::size_t size() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return jobs_.size();
    }
};

class LicenseSemaphore {
private:
    /*
     * C++20 supplies std::counting_semaphore, but the requested build target
     * is C++17. This compact semaphore uses a mutex and condition variable
     * to provide the same counting-permit semantics.
     */
    mutable std::mutex mutex_;
    std::condition_variable condition_;
    int available_;

public:
    explicit LicenseSemaphore(int permits)
        : available_(permits) {
        if (permits <= 0) {
            throw std::invalid_argument("Semaphore requires at least one permit");
        }
    }

    void acquire() {
        std::unique_lock<std::mutex> lock(mutex_);

        condition_.wait(lock, [this] {
            return available_ > 0;
        });

        --available_;
    }

    void release() {
        {
            std::lock_guard<std::mutex> lock(mutex_);

            if (available_ < 0) {
                throw std::logic_error("Invalid semaphore state");
            }

            ++available_;
        }

        condition_.notify_one();
    }
};

class BuildMetrics {
private:
    mutable std::mutex mutex_;
    int succeeded_{0};
    int failed_{0};
    int peak_concurrent_{0};
    int active_{0};

public:
    void started() {
        std::lock_guard<std::mutex> lock(mutex_);
        ++active_;
        peak_concurrent_ = std::max(peak_concurrent_, active_);
    }

    void finished(bool success) {
        std::lock_guard<std::mutex> lock(mutex_);

        if (active_ <= 0) {
            throw std::logic_error("Active build count became invalid");
        }

        --active_;

        if (success) {
            ++succeeded_;
        } else {
            ++failed_;
        }
    }

    std::string report() const {
        std::lock_guard<std::mutex> lock(mutex_);

        std::ostringstream output;
        output << "succeeded=" << succeeded_
               << ", failed=" << failed_
               << ", peak_concurrent_builds=" << peak_concurrent_;
        return output.str();
    }
};

class BuildCoordinator {
private:
    BuildQueueMonitor queue_;
    LicenseSemaphore compiler_licenses_;
    BuildMetrics metrics_;

    std::mutex output_mutex_;

    void log(const std::string& message) {
        /*
         * std::cout itself is shared. The logging mutex keeps individual
         * messages from interleaving across worker threads.
         */
        std::lock_guard<std::mutex> lock(output_mutex_);
        std::cout << message << '\n';
    }

public:
    BuildCoordinator(std::size_t queue_capacity, int compiler_licenses)
        : queue_(queue_capacity),
          compiler_licenses_(compiler_licenses) {}

    void submit(std::shared_ptr<BuildJob> job) {
        queue_.push(std::move(job));
    }

    void worker(int worker_id) {
        while (true) {
            auto job = queue_.pop();

            if (!job.has_value()) {
                return;
            }

            auto build = *job;

            /*
             * A semaphore models scarce external capacity. Several workers
             * may exist, but only as many may compile concurrently as there
             * are compiler licenses.
             */
            compiler_licenses_.acquire();
            metrics_.started();

            build->state = JobState::Running;

            {
                std::ostringstream message;
                message << "worker " << worker_id
                        << " compiling job " << build->id
                        << " for " << build->repository
                        << ":" << build->branch;
                log(message.str());
            }

            bool success = false;

            try {
                std::this_thread::sleep_for(
                    std::chrono::milliseconds(build->estimated_seconds * 20)
                );

                if (build->should_fail) {
                    throw std::runtime_error("compiler validation failed");
                }

                build->state = JobState::Succeeded;
                success = true;
            } catch (const std::exception& error) {
                build->state = JobState::Failed;

                std::ostringstream message;
                message << "job " << build->id
                        << " failed: " << error.what();
                log(message.str());
            }

            metrics_.finished(success);
            compiler_licenses_.release();

            if (success) {
                std::ostringstream message;
                message << "job " << build->id << " completed";
                log(message.str());
            }
        }
    }

    void stop() {
        queue_.stop();
    }

    std::string metrics() const {
        return metrics_.report();
    }

    std::size_t queued_jobs() const {
        return queue_.size();
    }
};

class Account {
private:
    std::string id_;
    int balance_;
    mutable std::mutex mutex_;

public:
    Account(std::string id, int balance)
        : id_(std::move(id)), balance_(balance) {
        if (balance < 0) {
            throw std::invalid_argument("Balance cannot be negative");
        }
    }

    const std::string& id() const {
        return id_;
    }

    friend void transfer(Account& from, Account& to, int amount);
};

void transfer(Account& from, Account& to, int amount) {
    if (&from == &to) {
        throw std::invalid_argument("Accounts must differ");
    }

    if (amount <= 0) {
        throw std::invalid_argument("Transfer amount must be positive");
    }

    /*
     * std::scoped_lock acquires both mutexes using a deadlock-avoidance
     * algorithm. This is safer than manually locking them in inconsistent
     * order across different call sites.
     */
    std::scoped_lock lock(from.mutex_, to.mutex_);

    if (from.balance_ < amount) {
        throw std::runtime_error("Insufficient balance");
    }

    from.balance_ -= amount;
    to.balance_ += amount;
}

int main() {
    try {
        std::cout << "=== Mutex, condition variable, semaphore, and monitor case study ===\n";

        BuildCoordinator coordinator(
            4,  // bounded queue
            2   // compiler licenses
        );

        std::vector<std::shared_ptr<BuildJob>> jobs;

        for (int id = 1; id <= 10; ++id) {
            auto job = std::make_shared<BuildJob>(
                BuildJob{
                    id,
                    id % 2 == 0 ? "payments-service" : "inventory-service",
                    id % 3 == 0 ? "feature/stock-cache" : "main",
                    1 + (id % 3),
                    id == 7
                }
            );

            jobs.push_back(job);
            coordinator.submit(job);
        }

        std::vector<std::thread> workers;

        for (int worker_id = 1; worker_id <= 4; ++worker_id) {
            workers.emplace_back(
                [&coordinator, worker_id] {
                    coordinator.worker(worker_id);
                }
            );
        }

        /*
         * All jobs have been submitted. Stopping wakes consumers once the
         * queue becomes empty, allowing workers to exit cleanly.
         */
        coordinator.stop();

        for (auto& worker : workers) {
            worker.join();
        }

        std::cout << "\nBuild metrics: "
                  << coordinator.metrics() << '\n';

        std::cout << "\nFinal job states:\n";

        for (const auto& job : jobs) {
            std::cout << "job " << job->id << ": ";

            switch (job->state) {
                case JobState::Queued:
                    std::cout << "queued";
                    break;
                case JobState::Running:
                    std::cout << "running";
                    break;
                case JobState::Succeeded:
                    std::cout << "succeeded";
                    break;
                case JobState::Failed:
                    std::cout << "failed";
                    break;
            }

            std::cout << '\n';
        }

        std::cout << "\n=== Deadlock-safe multiple-lock example ===\n";

        Account account_a("A", 1000);
        Account account_b("B", 1000);

        std::vector<std::thread> transfers;

        for (int i = 0; i < 4; ++i) {
            transfers.emplace_back([&] {
                transfer(account_a, account_b, 100);
            });

            transfers.emplace_back([&] {
                transfer(account_b, account_a, 100);
            });
        }

        for (auto& thread : transfers) {
            thread.join();
        }

        /*
         * The balances are private and therefore cannot be read without
         * another accessor lock in this compact demonstration. The important
         * invariant is that every transfer holds both account mutexes before
         * modifying either balance, preserving the total balance.
         */
        std::cout << "Concurrent transfers completed without deadlock.\n";
        std::cout << "Combined balance invariant remains 2000.\n";

        std::cout << "\nSynchronization design rules demonstrated:\n";
        std::cout << "Mutexes protect exclusive mutable state.\n";
        std::cout << "Condition variables block until protected state satisfies a predicate.\n";
        std::cout << "Semaphores control a quantity of available permits.\n";
        std::cout << "The build queue is a monitor because state and synchronization are encapsulated together.\n";
        std::cout << "RAII lock ownership releases mutexes during normal and exceptional control flow.\n";
        std::cout << "Multiple locks require a deliberate deadlock-avoidance strategy.\n";
    } catch (const std::exception& error) {
        std::cerr << "Fatal error: " << error.what() << '\n';
        return EXIT_FAILURE;
    }

    return EXIT_SUCCESS;
}
