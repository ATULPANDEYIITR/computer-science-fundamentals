#include <algorithm>
#include <cassert>
#include <cstddef>
#include <exception>
#include <functional>
#include <iostream>
#include <optional>
#include <queue>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

class QueueError : public std::runtime_error {
public:
    explicit QueueError(const std::string& message)
        : std::runtime_error(message) {}
};

class QueueEmptyError : public QueueError {
public:
    explicit QueueEmptyError(const std::string& message = "queue is empty")
        : QueueError(message) {}
};

class QueueFullError : public QueueError {
public:
    explicit QueueFullError(const std::string& message = "queue is full")
        : QueueError(message) {}
};

template <typename T>
class FIFOQueue {
private:
    std::queue<T> data_;

public:
    void enqueue(const T& value) {
        data_.push(value);
    }

    T dequeue() {
        if (data_.empty()) {
            throw QueueEmptyError();
        }

        T value = data_.front();
        data_.pop();
        return value;
    }

    const T& peek() const {
        if (data_.empty()) {
            throw QueueEmptyError();
        }
        return data_.front();
    }

    bool empty() const {
        return data_.empty();
    }

    std::size_t size() const {
        return data_.size();
    }
};

template <typename T>
class CircularQueue {
private:
    std::vector<std::optional<T>> buffer_;
    std::size_t head_ = 0;
    std::size_t tail_ = 0;
    std::size_t size_ = 0;

public:
    explicit CircularQueue(std::size_t capacity)
        : buffer_(capacity) {
        if (capacity == 0) {
            throw std::invalid_argument("capacity must be positive");
        }
    }

    void enqueue(const T& value) {
        if (full()) {
            throw QueueFullError();
        }

        buffer_[tail_] = value;
        tail_ = (tail_ + 1) % buffer_.size();
        ++size_;
    }

    T dequeue() {
        if (empty()) {
            throw QueueEmptyError();
        }

        T value = *buffer_[head_];
        buffer_[head_].reset();
        head_ = (head_ + 1) % buffer_.size();
        --size_;
        return value;
    }

    const T& peek() const {
        if (empty()) {
            throw QueueEmptyError();
        }
        return *buffer_[head_];
    }

    bool empty() const {
        return size_ == 0;
    }

    bool full() const {
        return size_ == buffer_.size();
    }

    std::size_t size() const {
        return size_;
    }

    std::vector<T> snapshot() const {
        std::vector<T> result;
        result.reserve(size_);

        for (std::size_t i = 0; i < size_; ++i) {
            result.push_back(*buffer_[(head_ + i) % buffer_.size()]);
        }

        return result;
    }
};

template <typename T>
class DequeModel {
private:
    std::deque<T> data_;

public:
    void push_front(const T& value) {
        data_.push_front(value);
    }

    void push_back(const T& value) {
        data_.push_back(value);
    }

    T pop_front() {
        if (data_.empty()) {
            throw QueueEmptyError("deque is empty");
        }

        T value = data_.front();
        data_.pop_front();
        return value;
    }

    T pop_back() {
        if (data_.empty()) {
            throw QueueEmptyError("deque is empty");
        }

        T value = data_.back();
        data_.pop_back();
        return value;
    }

    const T& front() const {
        if (data_.empty()) {
            throw QueueEmptyError("deque is empty");
        }
        return data_.front();
    }

    const T& back() const {
        if (data_.empty()) {
            throw QueueEmptyError("deque is empty");
        }
        return data_.back();
    }

    bool empty() const {
        return data_.empty();
    }
};

enum class JobState {
    Queued,
    Running,
    Completed,
    Failed
};

struct Job {
    int id;
    std::string name;
    int priority;
    JobState state = JobState::Queued;
};

struct PriorityCompare {
    bool operator()(const Job& left, const Job& right) const {
        // std::priority_queue is a max-heap by default. Reversing the
        // comparison makes smaller numeric priorities execute first.
        if (left.priority != right.priority) {
            return left.priority > right.priority;
        }
        return left.id > right.id;
    }
};

class GovernanceEngine {
private:
    CircularQueue<Job> intake_;
    std::priority_queue<Job, std::vector<Job>, PriorityCompare> ready_;
    std::unordered_set<int> known_ids_;
    std::unordered_map<int, JobState> states_;

public:
    explicit GovernanceEngine(std::size_t intake_capacity)
        : intake_(intake_capacity) {}

    void submit(Job job) {
        if (job.id <= 0) {
            throw std::invalid_argument("job id must be positive");
        }

        if (job.name.empty()) {
            throw std::invalid_argument("job name cannot be empty");
        }

        if (job.priority < 0) {
            throw std::invalid_argument("priority cannot be negative");
        }

        if (!known_ids_.insert(job.id).second) {
            throw std::invalid_argument("duplicate job id");
        }

        intake_.enqueue(job);
        states_[job.id] = JobState::Queued;
    }

    void stage() {
        while (!intake_.empty()) {
            Job job = intake_.dequeue();
            ready_.push(job);
        }
    }

    std::optional<Job> dispatch() {
        if (ready_.empty()) {
            return std::nullopt;
        }

        Job job = ready_.top();
        ready_.pop();

        job.state = JobState::Running;
        states_[job.id] = JobState::Running;
        return job;
    }

    void complete(int id) {
        auto it = states_.find(id);
        if (it == states_.end()) {
            throw std::out_of_range("unknown job id");
        }

        if (it->second != JobState::Running) {
            throw std::logic_error("only running jobs can be completed");
        }

        it->second = JobState::Completed;
    }

    void fail(int id) {
        auto it = states_.find(id);
        if (it == states_.end()) {
            throw std::out_of_range("unknown job id");
        }

        if (it->second != JobState::Running) {
            throw std::logic_error("only running jobs can fail");
        }

        it->second = JobState::Failed;
    }

    JobState state(int id) const {
        auto it = states_.find(id);
        if (it == states_.end()) {
            throw std::out_of_range("unknown job id");
        }
        return it->second;
    }
};

std::string stateName(JobState state) {
    switch (state) {
    case JobState::Queued:
        return "queued";
    case JobState::Running:
        return "running";
    case JobState::Completed:
        return "completed";
    case JobState::Failed:
        return "failed";
    }
    return "unknown";
}

int main() {
    try {
        std::cout << "=== FIFO Queue ===\n";

        FIFOQueue<std::string> fifo;
        fifo.enqueue("request-1");
        fifo.enqueue("request-2");
        fifo.enqueue("request-3");

        std::cout << fifo.dequeue() << '\n';
        std::cout << fifo.peek() << '\n';

        std::cout << "\n=== Circular Queue ===\n";

        CircularQueue<int> circular(3);
        circular.enqueue(10);
        circular.enqueue(20);
        circular.enqueue(30);

        circular.dequeue();
        circular.enqueue(40);

        for (int value : circular.snapshot()) {
            std::cout << value << ' ';
        }
        std::cout << '\n';

        try {
            circular.enqueue(50);
            circular.enqueue(60);
        } catch (const QueueFullError& error) {
            std::cout << "expected failure: " << error.what() << '\n';
        }

        std::cout << "\n=== Deque ===\n";

        DequeModel<std::string> deque;
        deque.push_front("security");
        deque.push_back("build");
        deque.push_front("validation");
        deque.push_back("deployment");

        std::cout << deque.pop_front() << '\n';
        std::cout << deque.pop_back() << '\n';
        std::cout << deque.front() << '\n';

        std::cout << "\n=== Repository Job Governance Engine ===\n";

        GovernanceEngine engine(4);

        engine.submit({101, "documentation", 30});
        engine.submit({102, "security-scan", 5});
        engine.submit({103, "release-build", 10});
        engine.submit({104, "unit-tests", 20});

        engine.stage();

        while (true) {
            auto job = engine.dispatch();

            if (!job.has_value()) {
                break;
            }

            std::cout
                << "dispatch "
                << job->id
                << " "
                << job->name
                << " priority="
                << job->priority
                << '\n';

            if (job->id == 102) {
                engine.fail(job->id);
            } else {
                engine.complete(job->id);
            }

            std::cout
                << "state="
                << stateName(engine.state(job->id))
                << '\n';
        }

        std::cout << "\n=== Invariant Tests ===\n";

        FIFOQueue<int> q;
        q.enqueue(1);
        q.enqueue(2);
        assert(q.dequeue() == 1);
        assert(q.dequeue() == 2);

        CircularQueue<int> cq(2);
        cq.enqueue(1);
        cq.enqueue(2);
        assert(cq.dequeue() == 1);
        cq.enqueue(3);
        assert(cq.snapshot() == std::vector<int>({2, 3}));

        DequeModel<int> dq;
        dq.push_back(2);
        dq.push_front(1);
        dq.push_back(3);
        assert(dq.pop_front() == 1);
        assert(dq.pop_back() == 3);

        GovernanceEngine validationEngine(2);
        validationEngine.submit({1, "urgent", 1});
        validationEngine.stage();

        auto urgent = validationEngine.dispatch();
        assert(urgent.has_value());
        assert(urgent->id == 1);

        validationEngine.complete(1);
        assert(validationEngine.state(1) == JobState::Completed);

        try {
            CircularQueue<int> invalid(0);
            (void)invalid;
            assert(false);
        } catch (const std::invalid_argument&) {
        }

        try {
            FIFOQueue<int> empty;
            empty.dequeue();
            assert(false);
        } catch (const QueueEmptyError&) {
        }

        std::cout << "all invariants passed\n";
    } catch (const std::exception& error) {
        std::cerr << "fatal error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
