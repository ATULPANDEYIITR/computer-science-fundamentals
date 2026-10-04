#include <algorithm>
#include <atomic>
#include <cerrno>
#include <chrono>
#include <cstring>
#include <fcntl.h>
#include <future>
#include <iostream>
#include <mutex>
#include <optional>
#include <queue>
#include <stdexcept>
#include <string>
#include <string_view>
#include <sys/socket.h>
#include <sys/wait.h>
#include <sys/mman.h>
#include <sys/un.h>
#include <thread>
#include <unistd.h>
#include <vector>

/*
 * C++17 IPC case study: telemetry processing service
 *
 * Scenario:
 * A local telemetry collector receives sensor records from producer
 * processes, distributes work to a processor, maintains a shared aggregate,
 * and exposes a Unix-domain socket for administrative queries.
 *
 * The implementation deliberately separates IPC mechanisms:
 *
 *   pipe       -> private producer/processor command stream
 *   message queue abstraction -> application-level work queue in this
 *                                single executable
 *   shared memory -> process-shared aggregate counters
 *   socket      -> request/response administrative interface
 *
 * The message-queue portion is represented with a bounded condition-variable
 * queue because POSIX/System V message queues differ significantly between
 * platforms. The queue still demonstrates message-oriented IPC semantics:
 * complete work items, bounded capacity, producer/consumer coordination, and
 * shutdown messages.
 *
 * Build on Linux:
 *   g++ -std=c++17 -pthread ipc_case_study.cpp -o ipc_case_study
 */

namespace ipc {

struct SensorRecord {
    int sensor_id;
    double value;
    std::string unit;
};

struct WorkMessage {
    enum class Type {
        Process,
        Shutdown
    };

    Type type;
    SensorRecord record{};
};

struct SharedMetrics {
    std::atomic<long long> records_processed;
    std::atomic<long long> anomalies_detected;
    std::atomic<long long> scaled_sum_milli;
};

/*
 * The queue is intentionally bounded. An unbounded producer queue can turn a
 * downstream slowdown into uncontrolled memory growth. Condition variables
 * provide blocking backpressure while preserving whole-message semantics.
 */
class MessageQueue {
public:
    explicit MessageQueue(std::size_t capacity)
        : capacity_(capacity) {}

    void push(WorkMessage message) {
        std::unique_lock<std::mutex> lock(mutex_);
        not_full_.wait(lock, [&] {
            return queue_.size() < capacity_ || closed_;
        });

        if (closed_) {
            throw std::runtime_error("message queue is closed");
        }

        queue_.push(std::move(message));
        not_empty_.notify_one();
    }

    std::optional<WorkMessage> pop() {
        std::unique_lock<std::mutex> lock(mutex_);
        not_empty_.wait(lock, [&] {
            return !queue_.empty() || closed_;
        });

        if (queue_.empty()) {
            return std::nullopt;
        }

        WorkMessage message = std::move(queue_.front());
        queue_.pop();
        not_full_.notify_one();
        return message;
    }

    void close() {
        std::lock_guard<std::mutex> lock(mutex_);
        closed_ = true;
        not_empty_.notify_all();
        not_full_.notify_all();
    }

private:
    std::size_t capacity_;
    std::queue<WorkMessage> queue_;
    bool closed_ = false;
    std::mutex mutex_;
    std::condition_variable not_empty_;
    std::condition_variable not_full_;
};

class Pipe {
public:
    Pipe() {
        if (::pipe(file_descriptors_) == -1) {
            throw std::runtime_error(
                std::string("pipe failed: ") + std::strerror(errno));
        }
    }

    Pipe(const Pipe&) = delete;
    Pipe& operator=(const Pipe&) = delete;

    ~Pipe() {
        close_read();
        close_write();
    }

    int read_fd() const { return file_descriptors_[0]; }
    int write_fd() const { return file_descriptors_[1]; }

    void close_read() {
        if (file_descriptors_[0] != -1) {
            ::close(file_descriptors_[0]);
            file_descriptors_[0] = -1;
        }
    }

    void close_write() {
        if (file_descriptors_[1] != -1) {
            ::close(file_descriptors_[1]);
            file_descriptors_[1] = -1;
        }
    }

private:
    int file_descriptors_[2]{-1, -1};
};

bool write_all(int fd, const void* data, std::size_t size) {
    const auto* bytes = static_cast<const char*>(data);
    std::size_t written = 0;

    while (written < size) {
        ssize_t result = ::write(fd, bytes + written, size - written);

        if (result == -1) {
            if (errno == EINTR) {
                continue;
            }
            return false;
        }

        if (result == 0) {
            return false;
        }

        written += static_cast<std::size_t>(result);
    }

    return true;
}

bool read_all(int fd, void* data, std::size_t size) {
    auto* bytes = static_cast<char*>(data);
    std::size_t received = 0;

    while (received < size) {
        ssize_t result = ::read(fd, bytes + received, size - received);

        if (result == -1) {
            if (errno == EINTR) {
                continue;
            }
            return false;
        }

        if (result == 0) {
            return false;
        }

        received += static_cast<std::size_t>(result);
    }

    return true;
}

/*
 * Fixed-size records make this pipe protocol simple. For a production
 * variable-length protocol, explicit framing would be required because a
 * pipe is a byte stream and write/read boundaries should not be confused with
 * application message boundaries.
 */
struct PipeRecord {
    int sensor_id;
    double value;
};

void pipe_producer(int write_fd) {
    const std::vector<PipeRecord> records = {
        {101, 21.5},
        {102, 87.2},
        {103, 42.8},
        {104, 99.7}
    };

    for (const auto& record : records) {
        if (!write_all(write_fd, &record, sizeof(record))) {
            _exit(2);
        }
    }

    ::close(write_fd);
    _exit(0);
}

void demonstrate_pipe() {
    std::cout << "\n=== PIPE: producer process to parent ===\n";

    Pipe channel;

    pid_t child = ::fork();

    if (child == -1) {
        throw std::runtime_error("fork failed");
    }

    if (child == 0) {
        channel.close_read();
        pipe_producer(channel.write_fd());
    }

    channel.close_write();

    PipeRecord record{};

    while (read_all(channel.read_fd(), &record, sizeof(record))) {
        std::cout
            << "sensor=" << record.sensor_id
            << " value=" << record.value << '\n';
    }

    channel.close_read();

    int status = 0;
    if (::waitpid(child, &status, 0) == -1) {
        throw std::runtime_error("waitpid failed");
    }

    if (WIFEXITED(status)) {
        std::cout << "producer exit status=" << WEXITSTATUS(status) << '\n';
    }
}

/*
 * Shared-memory creation with mmap().
 *
 * MAP_SHARED means modifications made by one process are visible to another
 * process mapping the same pages. Atomics provide synchronization for the
 * counters. The shared object contains only trivially constructible atomics,
 * which keeps lifetime handling straightforward for this demonstration.
 */
SharedMetrics* create_shared_metrics() {
    void* memory = ::mmap(
        nullptr,
        sizeof(SharedMetrics),
        PROT_READ | PROT_WRITE,
        MAP_SHARED | MAP_ANONYMOUS,
        -1,
        0
    );

    if (memory == MAP_FAILED) {
        throw std::runtime_error("mmap failed");
    }

    auto* metrics = static_cast<SharedMetrics*>(memory);

    new (&metrics->records_processed) std::atomic<long long>(0);
    new (&metrics->anomalies_detected) std::atomic<long long>(0);
    new (&metrics->scaled_sum_milli) std::atomic<long long>(0);

    return metrics;
}

void destroy_shared_metrics(SharedMetrics* metrics) {
    metrics->records_processed.~atomic<long long>();
    metrics->anomalies_detected.~atomic<long long>();
    metrics->scaled_sum_milli.~atomic<long long>();

    ::munmap(metrics, sizeof(SharedMetrics));
}

void shared_metrics_worker(SharedMetrics* metrics, int base) {
    for (int i = 0; i < 1000; ++i) {
        metrics->records_processed.fetch_add(1, std::memory_order_relaxed);

        if ((i + base) % 37 == 0) {
            metrics->anomalies_detected.fetch_add(1, std::memory_order_relaxed);
        }

        metrics->scaled_sum_milli.fetch_add(
            static_cast<long long>((base + i) * 1000),
            std::memory_order_relaxed
        );
    }

    _exit(0);
}

void demonstrate_shared_memory() {
    std::cout << "\n=== SHARED MEMORY: process-shared counters ===\n";

    SharedMetrics* metrics = create_shared_metrics();

    constexpr int workers = 3;

    for (int i = 0; i < workers; ++i) {
        pid_t child = ::fork();

        if (child == -1) {
            destroy_shared_metrics(metrics);
            throw std::runtime_error("fork failed");
        }

        if (child == 0) {
            shared_metrics_worker(metrics, (i + 1) * 10);
        }
    }

    for (int i = 0; i < workers; ++i) {
        int status = 0;
        ::wait(&status);
    }

    std::cout
        << "records processed="
        << metrics->records_processed.load() << '\n'
        << "anomalies="
        << metrics->anomalies_detected.load() << '\n'
        << "scaled sum="
        << metrics->scaled_sum_milli.load() << '\n';

    destroy_shared_metrics(metrics);
}

void processor(MessageQueue& queue, SharedMetrics* metrics) {
    while (true) {
        auto message = queue.pop();

        if (!message.has_value()) {
            return;
        }

        if (message->type == WorkMessage::Type::Shutdown) {
            return;
        }

        const SensorRecord& record = message->record;

        if (record.unit != "C" && record.unit != "F") {
            metrics->anomalies_detected.fetch_add(1);
            continue;
        }

        double celsius = record.unit == "F"
            ? (record.value - 32.0) * 5.0 / 9.0
            : record.value;

        if (celsius < -80.0 || celsius > 80.0) {
            metrics->anomalies_detected.fetch_add(1);
        }

        metrics->records_processed.fetch_add(1);
        metrics->scaled_sum_milli.fetch_add(
            static_cast<long long>(celsius * 1000.0)
        );
    }
}

void demonstrate_message_queue(SharedMetrics* metrics) {
    std::cout << "\n=== MESSAGE QUEUE: bounded work distribution ===\n";

    MessageQueue queue(3);

    std::thread consumer([&] {
        processor(queue, metrics);
    });

    const std::vector<SensorRecord> records = {
        {201, 22.5, "C"},
        {202, 72.0, "F"},
        {203, 110.0, "F"},
        {204, 15.0, "C"},
        {205, 500.0, "K"}
    };

    for (const auto& record : records) {
        queue.push({WorkMessage::Type::Process, record});
        std::cout
            << "queued sensor " << record.sensor_id
            << " (" << record.value << ' ' << record.unit << ")\n";
    }

    queue.push({WorkMessage::Type::Shutdown, {}});
    consumer.join();

    std::cout
        << "aggregate records="
        << metrics->records_processed.load() << '\n'
        << "aggregate anomalies="
        << metrics->anomalies_detected.load() << '\n';
}

/*
 * Unix domain socket server.
 *
 * SOCK_STREAM deliberately mirrors TCP stream behavior. The protocol uses
 * newline-delimited commands for readability. A binary production protocol
 * would normally use explicit length-prefix framing, versioning, and
 * authentication/authorization rules.
 */
std::string handle_request(const std::string& request,
                           const SharedMetrics* metrics) {
    if (request == "GET_METRICS") {
        return
            "records=" +
            std::to_string(metrics->records_processed.load()) +
            " anomalies=" +
            std::to_string(metrics->anomalies_detected.load()) +
            "\n";
    }

    if (request == "GET_PID") {
        return "pid=" + std::to_string(::getpid()) + "\n";
    }

    return "ERROR unsupported_command\n";
}

void socket_server(const std::string& path, SharedMetrics* metrics) {
    int server_fd = ::socket(AF_UNIX, SOCK_STREAM, 0);

    if (server_fd == -1) {
        _exit(3);
    }

    ::unlink(path.c_str());

    sockaddr_un address{};
    address.sun_family = AF_UNIX;

    if (path.size() >= sizeof(address.sun_path)) {
        ::close(server_fd);
        _exit(4);
    }

    std::strncpy(
        address.sun_path,
        path.c_str(),
        sizeof(address.sun_path) - 1
    );

    if (::bind(
            server_fd,
            reinterpret_cast<sockaddr*>(&address),
            sizeof(address)) == -1) {
        ::close(server_fd);
        _exit(5);
    }

    // A local socket is a security boundary only if its filesystem
    // permissions are controlled. Restrict access to the owning user.
    ::chmod(path.c_str(), 0600);

    if (::listen(server_fd, 8) == -1) {
        ::close(server_fd);
        ::unlink(path.c_str());
        _exit(6);
    }

    int client_fd = ::accept(server_fd, nullptr, nullptr);

    if (client_fd != -1) {
        char buffer[256]{};
        ssize_t count = ::read(client_fd, buffer, sizeof(buffer) - 1);

        if (count > 0) {
            std::string request(buffer, static_cast<std::size_t>(count));
            std::string response = handle_request(
                request,
                metrics
            );

            write_all(client_fd, response.data(), response.size());
        }

        ::close(client_fd);
    }

    ::close(server_fd);
    ::unlink(path.c_str());
    _exit(0);
}

void demonstrate_socket(SharedMetrics* metrics) {
    std::cout << "\n=== SOCKET: local administrative API ===\n";

    std::string socket_path =
        "/tmp/ipc_case_" + std::to_string(::getpid()) + ".sock";

    pid_t server = ::fork();

    if (server == -1) {
        throw std::runtime_error("fork failed");
    }

    if (server == 0) {
        socket_server(socket_path, metrics);
    }

    for (int attempt = 0; attempt < 100; ++attempt) {
        if (::access(socket_path.c_str(), F_OK) == 0) {
            break;
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }

    int client_fd = ::socket(AF_UNIX, SOCK_STREAM, 0);

    if (client_fd == -1) {
        ::waitpid(server, nullptr, 0);
        throw std::runtime_error("client socket failed");
    }

    sockaddr_un address{};
    address.sun_family = AF_UNIX;
    std::strncpy(
        address.sun_path,
        socket_path.c_str(),
        sizeof(address.sun_path) - 1
    );

    if (::connect(
            client_fd,
            reinterpret_cast<sockaddr*>(&address),
            sizeof(address)) == -1) {
        ::close(client_fd);
        ::waitpid(server, nullptr, 0);
        ::unlink(socket_path.c_str());
        throw std::runtime_error("socket connect failed");
    }

    const std::string request = "GET_METRICS";
    write_all(client_fd, request.data(), request.size());

    char response[512]{};
    ssize_t count = ::read(client_fd, response, sizeof(response) - 1);

    if (count > 0) {
        std::cout
            << "administrative response: "
            << std::string(response, static_cast<std::size_t>(count));
    }

    ::close(client_fd);

    ::waitpid(server, nullptr, 0);
}

} // namespace ipc

int main() {
    try {
        std::cout << "C++17 Interprocess Communication case study\n";

        ipc::demonstrate_pipe();

        ipc::SharedMetrics* metrics = ipc::create_shared_metrics();

        ipc::demonstrate_message_queue(metrics);
        ipc::demonstrate_socket(metrics);

        ipc::destroy_shared_metrics(metrics);

        ipc::demonstrate_shared_memory();

        std::cout << "\nCase study completed successfully.\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Fatal IPC error: " << error.what() << '\n';
        return 1;
    }
}
