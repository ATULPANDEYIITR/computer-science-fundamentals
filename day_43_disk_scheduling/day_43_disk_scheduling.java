import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;

/*
 * Enterprise-oriented disk scheduling model.
 *
 * The domain separates:
 *   - disk requests,
 *   - scheduling algorithms,
 *   - reviewable scheduling policies,
 *   - physical movement,
 *   - merge-like eligibility of a scheduling decision.
 *
 * Java enums and records make the policy vocabulary explicit, while
 * exceptions prevent invalid disk states from silently entering the model.
 */

public class DiskSchedulingGovernance {

    enum Direction {
        LEFT,
        RIGHT
    }

    enum Algorithm {
        FCFS,
        SSTF,
        SCAN,
        C_SCAN,
        LOOK,
        C_LOOK
    }

    record DiskRequest(String requestId, int cylinder, String workloadClass) {
        public DiskRequest {
            if (requestId == null || requestId.isBlank()) {
                throw new IllegalArgumentException("requestId is required");
            }
            if (workloadClass == null || workloadClass.isBlank()) {
                throw new IllegalArgumentException("workloadClass is required");
            }
        }
    }

    record ScheduleResult(
        Algorithm algorithm,
        List<Integer> serviceOrder,
        List<Integer> physicalPath,
        int movement,
        double averageSeek
    ) {
        public ScheduleResult {
            serviceOrder = List.copyOf(serviceOrder);
            physicalPath = List.copyOf(physicalPath);
        }
    }

    record SchedulingPolicy(
        String policyName,
        int maximumAllowedMovement,
        boolean requireDeterministicTieBreaking
    ) {
        public SchedulingPolicy {
            if (policyName == null || policyName.isBlank()) {
                throw new IllegalArgumentException("Policy name is required");
            }
            if (maximumAllowedMovement < 0) {
                throw new IllegalArgumentException(
                    "Maximum movement cannot be negative"
                );
            }
        }
    }

    static final class DiskController {
        private final int diskSize;
        private final int initialHead;

        DiskController(int diskSize, int initialHead) {
            if (diskSize < 2) {
                throw new IllegalArgumentException(
                    "Disk must contain at least two cylinders"
                );
            }
            if (initialHead < 0 || initialHead >= diskSize) {
                throw new IllegalArgumentException(
                    "Initial head is outside disk boundaries"
                );
            }
            this.diskSize = diskSize;
            this.initialHead = initialHead;
        }

        private List<Integer> cylinders(
            List<DiskRequest> requests
        ) {
            if (requests.isEmpty()) {
                throw new IllegalArgumentException(
                    "A scheduling workload cannot be empty"
                );
            }

            List<Integer> cylinders = new ArrayList<>();

            for (DiskRequest request : requests) {
                if (request.cylinder() < 0 ||
                    request.cylinder() >= diskSize) {
                    throw new IllegalArgumentException(
                        "Request " + request.requestId() +
                        " targets cylinder " + request.cylinder()
                    );
                }
                cylinders.add(request.cylinder());
            }

            return cylinders;
        }

        private int movement(List<Integer> path) {
            int current = initialHead;
            int total = 0;

            for (int cylinder : path) {
                total += Math.abs(cylinder - current);
                current = cylinder;
            }

            return total;
        }

        private ScheduleResult result(
            Algorithm algorithm,
            List<Integer> serviceOrder,
            List<Integer> physicalPath
        ) {
            int movement = movement(physicalPath);
            double average = serviceOrder.isEmpty()
                ? 0.0
                : (double) movement / serviceOrder.size();

            return new ScheduleResult(
                algorithm,
                serviceOrder,
                physicalPath,
                movement,
                average
            );
        }

        ScheduleResult fcfs(List<DiskRequest> requests) {
            return result(
                Algorithm.FCFS,
                cylinders(requests),
                cylinders(requests)
            );
        }

        ScheduleResult sstf(List<DiskRequest> requests) {
            List<Integer> pending = new ArrayList<>(cylinders(requests));
            List<Integer> order = new ArrayList<>();
            int current = initialHead;

            while (!pending.isEmpty()) {
                int selectedIndex = 0;

                for (int i = 1; i < pending.size(); i++) {
                    int selectedDistance =
                        Math.abs(pending.get(selectedIndex) - current);
                    int candidateDistance =
                        Math.abs(pending.get(i) - current);

                    if (candidateDistance < selectedDistance ||
                        (candidateDistance == selectedDistance &&
                         pending.get(i) < pending.get(selectedIndex))) {
                        selectedIndex = i;
                    }
                }

                current = pending.remove(selectedIndex);
                order.add(current);
            }

            return result(Algorithm.SSTF, order, order);
        }

        ScheduleResult scan(
            List<DiskRequest> requests,
            Direction direction
        ) {
            List<Integer> all = cylinders(requests);

            List<Integer> left = all.stream()
                .filter(c -> c < initialHead)
                .sorted(Comparator.reverseOrder())
                .toList();

            List<Integer> right = all.stream()
                .filter(c -> c >= initialHead)
                .sorted()
                .toList();

            List<Integer> service = new ArrayList<>();
            List<Integer> path = new ArrayList<>();

            if (direction == Direction.RIGHT) {
                service.addAll(right);
                path.addAll(right);

                if (!left.isEmpty()) {
                    path.add(diskSize - 1);
                    path.addAll(left);
                    service.addAll(left);
                }
            } else {
                service.addAll(left);
                path.addAll(left);

                if (!right.isEmpty()) {
                    path.add(0);
                    path.addAll(right);
                    service.addAll(right);
                }
            }

            return result(Algorithm.SCAN, service, path);
        }

        ScheduleResult cScan(
            List<DiskRequest> requests,
            Direction direction
        ) {
            List<Integer> all = cylinders(requests);

            List<Integer> left = all.stream()
                .filter(c -> c < initialHead)
                .sorted()
                .toList();

            List<Integer> right = all.stream()
                .filter(c -> c >= initialHead)
                .sorted()
                .toList();

            List<Integer> service = new ArrayList<>();
            List<Integer> path = new ArrayList<>();

            if (direction == Direction.RIGHT) {
                service.addAll(right);
                path.addAll(right);

                if (!left.isEmpty()) {
                    path.add(diskSize - 1);
                    path.add(0);
                    path.addAll(left);
                    service.addAll(left);
                }
            } else {
                List<Integer> leftDesc = new ArrayList<>(left);
                List<Integer> rightDesc = new ArrayList<>(right);
                leftDesc.reversed();
                rightDesc.reversed();

                service.addAll(leftDesc);
                path.addAll(leftDesc);

                if (!rightDesc.isEmpty()) {
                    path.add(0);
                    path.add(diskSize - 1);
                    path.addAll(rightDesc);
                    service.addAll(rightDesc);
                }
            }

            return result(Algorithm.C_SCAN, service, path);
        }

        ScheduleResult look(
            List<DiskRequest> requests,
            Direction direction
        ) {
            List<Integer> all = cylinders(requests);

            List<Integer> left = all.stream()
                .filter(c -> c < initialHead)
                .sorted(Comparator.reverseOrder())
                .toList();

            List<Integer> right = all.stream()
                .filter(c -> c >= initialHead)
                .sorted()
                .toList();

            List<Integer> order = new ArrayList<>();

            if (direction == Direction.RIGHT) {
                order.addAll(right);
                order.addAll(left);
            } else {
                order.addAll(left);
                order.addAll(right);
            }

            return result(Algorithm.LOOK, order, order);
        }

        ScheduleResult cLook(
            List<DiskRequest> requests,
            Direction direction
        ) {
            List<Integer> all = cylinders(requests);

            List<Integer> left = all.stream()
                .filter(c -> c < initialHead)
                .sorted()
                .toList();

            List<Integer> right = all.stream()
                .filter(c -> c >= initialHead)
                .sorted()
                .toList();

            List<Integer> order = new ArrayList<>();

            if (direction == Direction.RIGHT) {
                order.addAll(right);
                order.addAll(left);
            } else {
                List<Integer> leftDesc = new ArrayList<>(left);
                List<Integer> rightDesc = new ArrayList<>(right);
                java.util.Collections.reverse(leftDesc);
                java.util.Collections.reverse(rightDesc);
                order.addAll(leftDesc);
                order.addAll(rightDesc);
            }

            return result(Algorithm.C_LOOK, order, order);
        }

        Map<Algorithm, ScheduleResult> evaluate(
            List<DiskRequest> requests,
            Direction direction
        ) {
            Map<Algorithm, ScheduleResult> results =
                new EnumMap<>(Algorithm.class);

            results.put(Algorithm.FCFS, fcfs(requests));
            results.put(Algorithm.SSTF, sstf(requests));
            results.put(Algorithm.SCAN, scan(requests, direction));
            results.put(Algorithm.C_SCAN, cScan(requests, direction));
            results.put(Algorithm.LOOK, look(requests, direction));
            results.put(Algorithm.C_LOOK, cLook(requests, direction));

            return results;
        }
    }

    static final class MergeEligibilityService {

        boolean eligible(
            ScheduleResult result,
            SchedulingPolicy policy
        ) {
            return result.movement() <= policy.maximumAllowedMovement();
        }

        ScheduleResult select(
            Map<Algorithm, ScheduleResult> results,
            SchedulingPolicy policy
        ) {
            return results.values().stream()
                .filter(result -> eligible(result, policy))
                .min(Comparator.comparingInt(ScheduleResult::movement))
                .orElseThrow(() -> new IllegalStateException(
                    "No scheduling strategy satisfies the movement policy"
                ));
        }
    }

    private static void print(
        ScheduleResult result,
        boolean eligible
    ) {
        System.out.printf(
            "%-8s movement=%4d average=%7.2f eligible=%s order=%s%n",
            result.algorithm(),
            result.movement(),
            result.averageSeek(),
            eligible,
            result.serviceOrder()
        );
    }

    public static void main(String[] args) {
        DiskController controller = new DiskController(200, 53);

        List<DiskRequest> requests = List.of(
            new DiskRequest("REQ-001", 98, "interactive"),
            new DiskRequest("REQ-002", 183, "batch"),
            new DiskRequest("REQ-003", 37, "interactive"),
            new DiskRequest("REQ-004", 122, "batch"),
            new DiskRequest("REQ-005", 14, "archive"),
            new DiskRequest("REQ-006", 124, "interactive"),
            new DiskRequest("REQ-007", 65, "interactive"),
            new DiskRequest("REQ-008", 67, "batch")
        );

        SchedulingPolicy policy = new SchedulingPolicy(
            "storage-efficiency-policy",
            300,
            true
        );

        Map<Algorithm, ScheduleResult> results =
            controller.evaluate(requests, Direction.RIGHT);

        MergeEligibilityService eligibilityService =
            new MergeEligibilityService();

        System.out.println("Enterprise Disk Scheduling Governance");
        System.out.println("=====================================");

        results.values().stream()
            .sorted(Comparator.comparingInt(ScheduleResult::movement))
            .forEach(result ->
                print(
                    result,
                    eligibilityService.eligible(result, policy)
                )
            );

        ScheduleResult selected =
            eligibilityService.select(results, policy);

        System.out.println();
        System.out.println(
            "Selected scheduling policy: " +
            selected.algorithm()
        );
        System.out.println(
            "Movement accepted under policy: " +
            selected.movement()
        );

        try {
            controller.fcfs(List.of(
                new DiskRequest("BAD-001", 999, "invalid")
            ));
        } catch (IllegalArgumentException exception) {
            System.out.println();
            System.out.println(
                "Invalid request rejected: " +
                exception.getMessage()
            );
        }
    }
}
