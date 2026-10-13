#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

/*
 * Repository-style technical case study:
 *
 * A storage service receives logical block requests that map to disk
 * cylinders. A governance component chooses a scheduling policy and
 * evaluates its seek cost before dispatching the requests.
 *
 * The program focuses on the mechanics of six classical disk scheduling
 * algorithms while using C++ data structures and policy objects to model
 * a realistic storage controller.
 */

enum class Direction {
    Left,
    Right
};

struct ScheduleResult {
    string algorithm;
    vector<int> serviceOrder;
    vector<int> physicalPath;
    int movement{};
    double averageSeek{};
};

class DiskDevice {
private:
    int cylinderCount_;
    int initialHead_;

public:
    DiskDevice(int cylinderCount, int initialHead)
        : cylinderCount_(cylinderCount), initialHead_(initialHead) {
        if (cylinderCount < 2) {
            throw invalid_argument("Cylinder count must be at least 2");
        }
        if (initialHead < 0 || initialHead >= cylinderCount) {
            throw invalid_argument("Initial head is outside the disk");
        }
    }

    int cylinders() const {
        return cylinderCount_;
    }

    int head() const {
        return initialHead_;
    }

    void validate(const vector<int>& requests) const {
        if (requests.empty()) {
            throw invalid_argument("Request queue cannot be empty");
        }

        for (int request : requests) {
            if (request < 0 || request >= cylinderCount_) {
                throw invalid_argument(
                    "A request lies outside the valid cylinder range"
                );
            }
        }
    }

    int movement(const vector<int>& path) const {
        int current = initialHead_;
        int total = 0;

        for (int cylinder : path) {
            total += abs(cylinder - current);
            current = cylinder;
        }

        return total;
    }

    ScheduleResult createResult(
        const string& algorithm,
        const vector<int>& serviceOrder,
        const vector<int>& physicalPath
    ) const {
        int total = movement(physicalPath);
        double average = serviceOrder.empty()
            ? 0.0
            : static_cast<double>(total) / serviceOrder.size();

        return {
            algorithm,
            serviceOrder,
            physicalPath,
            total,
            average
        };
    }

    ScheduleResult fcfs(const vector<int>& requests) const {
        validate(requests);
        return createResult("FCFS", requests, requests);
    }

    ScheduleResult sstf(const vector<int>& requests) const {
        validate(requests);

        vector<int> pending = requests;
        vector<int> order;
        int current = initialHead_;

        while (!pending.empty()) {
            auto best = pending.begin();

            for (auto it = pending.begin(); it != pending.end(); ++it) {
                int candidateDistance = abs(*it - current);
                int bestDistance = abs(*best - current);

                if (candidateDistance < bestDistance ||
                    (candidateDistance == bestDistance && *it < *best)) {
                    best = it;
                }
            }

            current = *best;
            order.push_back(*best);
            pending.erase(best);
        }

        return createResult("SSTF", order, order);
    }

    ScheduleResult scan(
        const vector<int>& requests,
        Direction direction
    ) const {
        validate(requests);

        vector<int> left;
        vector<int> right;

        for (int request : requests) {
            if (request < initialHead_) {
                left.push_back(request);
            } else {
                right.push_back(request);
            }
        }

        sort(left.begin(), left.end(), greater<int>());
        sort(right.begin(), right.end());

        vector<int> path;
        vector<int> serviceOrder;

        if (direction == Direction::Right) {
            serviceOrder.insert(
                serviceOrder.end(), right.begin(), right.end()
            );
            path = serviceOrder;

            if (!left.empty()) {
                // SCAN reaches the physical end before reversing.
                path.push_back(cylinderCount_ - 1);
                path.insert(path.end(), left.begin(), left.end());
                serviceOrder.insert(
                    serviceOrder.end(), left.begin(), left.end()
                );
            }
        } else {
            serviceOrder.insert(
                serviceOrder.end(), left.begin(), left.end()
            );
            path = serviceOrder;

            if (!right.empty()) {
                path.push_back(0);
                path.insert(path.end(), right.begin(), right.end());
                serviceOrder.insert(
                    serviceOrder.end(), right.begin(), right.end()
                );
            }
        }

        return createResult("SCAN", serviceOrder, path);
    }

    ScheduleResult cscan(
        const vector<int>& requests,
        Direction direction
    ) const {
        validate(requests);

        vector<int> left;
        vector<int> right;

        for (int request : requests) {
            if (request < initialHead_) {
                left.push_back(request);
            } else {
                right.push_back(request);
            }
        }

        sort(left.begin(), left.end());
        sort(right.begin(), right.end());

        vector<int> path;
        vector<int> serviceOrder;

        if (direction == Direction::Right) {
            serviceOrder.insert(
                serviceOrder.end(), right.begin(), right.end()
            );
            path = serviceOrder;

            if (!left.empty()) {
                path.push_back(cylinderCount_ - 1);
                path.push_back(0);
                path.insert(path.end(), left.begin(), left.end());

                serviceOrder.insert(
                    serviceOrder.end(), left.begin(), left.end()
                );
            }
        } else {
            reverse(left.begin(), left.end());
            reverse(right.begin(), right.end());

            serviceOrder.insert(
                serviceOrder.end(), left.begin(), left.end()
            );
            path = serviceOrder;

            if (!right.empty()) {
                path.push_back(0);
                path.push_back(cylinderCount_ - 1);
                path.insert(path.end(), right.begin(), right.end());

                serviceOrder.insert(
                    serviceOrder.end(), right.begin(), right.end()
                );
            }
        }

        return createResult("C-SCAN", serviceOrder, path);
    }

    ScheduleResult look(
        const vector<int>& requests,
        Direction direction
    ) const {
        validate(requests);

        vector<int> left;
        vector<int> right;

        for (int request : requests) {
            if (request < initialHead_) {
                left.push_back(request);
            } else {
                right.push_back(request);
            }
        }

        sort(left.begin(), left.end(), greater<int>());
        sort(right.begin(), right.end());

        vector<int> order;

        if (direction == Direction::Right) {
            order.insert(order.end(), right.begin(), right.end());
            order.insert(order.end(), left.begin(), left.end());
        } else {
            order.insert(order.end(), left.begin(), left.end());
            order.insert(order.end(), right.begin(), right.end());
        }

        return createResult("LOOK", order, order);
    }

    ScheduleResult clook(
        const vector<int>& requests,
        Direction direction
    ) const {
        validate(requests);

        vector<int> left;
        vector<int> right;

        for (int request : requests) {
            if (request < initialHead_) {
                left.push_back(request);
            } else {
                right.push_back(request);
            }
        }

        sort(left.begin(), left.end());
        sort(right.begin(), right.end());

        vector<int> order;

        if (direction == Direction::Right) {
            order.insert(order.end(), right.begin(), right.end());
            order.insert(order.end(), left.begin(), left.end());
        } else {
            reverse(left.begin(), left.end());
            reverse(right.begin(), right.end());

            order.insert(order.end(), left.begin(), left.end());
            order.insert(order.end(), right.begin(), right.end());
        }

        /*
         * C-LOOK does not travel to cylinders 0 or N-1 merely because
         * they are disk boundaries. Its circular jump connects request
         * extremes. The movement from one extreme to the other is still
         * counted because the disk head physically relocates.
         */
        return createResult("C-LOOK", order, order);
    }

    map<string, ScheduleResult> evaluate(
        const vector<int>& requests,
        Direction direction
    ) const {
        return {
            {"FCFS", fcfs(requests)},
            {"SSTF", sstf(requests)},
            {"SCAN", scan(requests, direction)},
            {"C-SCAN", cscan(requests, direction)},
            {"LOOK", look(requests, direction)},
            {"C-LOOK", clook(requests, direction)}
        };
    }
};

class StoragePolicyEngine {
public:
    static const ScheduleResult& chooseLowestMovement(
        const map<string, ScheduleResult>& results
    ) {
        if (results.empty()) {
            throw runtime_error("No scheduling results available");
        }

        auto best = results.begin();

        for (auto it = next(results.begin()); it != results.end(); ++it) {
            if (it->second.movement < best->second.movement) {
                best = it;
            }
        }

        return best->second;
    }
};

void printResult(const ScheduleResult& result) {
    cout << left << setw(10) << result.algorithm
         << " movement=" << setw(4) << result.movement
         << " average=" << fixed << setprecision(2)
         << result.averageSeek
         << " order=";

    for (size_t i = 0; i < result.serviceOrder.size(); ++i) {
        if (i > 0) {
            cout << " -> ";
        }
        cout << result.serviceOrder[i];
    }

    cout << '\n';
}

int main() {
    try {
        DiskDevice disk(200, 53);

        // This workload is intentionally asymmetric so that algorithms
        // that reach or avoid physical boundaries produce different costs.
        vector<int> requests{
            98, 183, 37, 122, 14, 124, 65, 67
        };

        cout << "Storage Controller Scheduling Case Study\n";
        cout << "========================================\n";
        cout << "Disk cylinders : 0..199\n";
        cout << "Initial head   : 53\n";
        cout << "Initial sweep  : right\n";
        cout << "Requests       : ";

        for (size_t i = 0; i < requests.size(); ++i) {
            if (i > 0) cout << ", ";
            cout << requests[i];
        }
        cout << "\n\n";

        auto results = disk.evaluate(requests, Direction::Right);

        vector<ScheduleResult> ordered;
        for (const auto& [name, result] : results) {
            ordered.push_back(result);
        }

        sort(
            ordered.begin(),
            ordered.end(),
            [](const ScheduleResult& a, const ScheduleResult& b) {
                return a.movement < b.movement;
            }
        );

        for (const auto& result : ordered) {
            printResult(result);
        }

        const auto& best = StoragePolicyEngine::chooseLowestMovement(results);

        cout << "\nSelected policy\n";
        cout << "---------------\n";
        cout << best.algorithm
             << " has the lowest calculated head movement: "
             << best.movement << " cylinders.\n";

        cout << "\nImportant distinction\n";
        cout << "---------------------\n";
        cout << "SCAN reaches a physical disk boundary before reversing.\n";
        cout << "LOOK reverses at the last pending request instead.\n";
        cout << "C-SCAN wraps at the disk boundaries.\n";
        cout << "C-LOOK wraps between request extremes.\n";

        cout << "\nValidation test\n";
        cout << "---------------\n";

        try {
            disk.fcfs({10, 500});
        } catch (const exception& ex) {
            cout << "Rejected invalid request: " << ex.what() << '\n';
        }
    } catch (const exception& ex) {
        cerr << "Fatal scheduling error: " << ex.what() << '\n';
        return 1;
    }

    return 0;
}
