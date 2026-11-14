import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.function.Consumer;
import java.util.stream.Collectors;

/**
 * BACKTRACKING: ENTERPRISE CONSTRAINT SEARCH
 *
 * Java 17
 * No external dependencies.
 *
 * Domain-oriented implementation:
 * - Immutable search requests.
 * - Explicit constraint policies.
 * - Search service abstraction.
 * - Search lifecycle management.
 * - Reviewable solution records.
 * - Resource limits.
 * - N-Queens constraint evaluation.
 * - Permutation and combination enumeration.
 */

public class Main {

    enum SearchType {
        PERMUTATION,
        COMBINATION,
        N_QUEENS
    }

    enum SearchStatus {
        CREATED,
        RUNNING,
        COMPLETED,
        FAILED,
        LIMIT_EXCEEDED
    }

    record SearchRequest(
        SearchType type,
        List<Integer> input,
        int selectionSize,
        int boardSize,
        long maximumNodes,
        long maximumSolutions
    ) {
        SearchRequest {
            Objects.requireNonNull(type);
            input = List.copyOf(input);

            if (maximumNodes < 1 || maximumSolutions < 1) {
                throw new IllegalArgumentException(
                    "Search limits must be positive"
                );
            }

            if (input.size() > 20) {
                throw new IllegalArgumentException(
                    "Input cannot exceed 20 elements"
                );
            }

            if (type == SearchType.COMBINATION &&
                (selectionSize < 0 ||
                 selectionSize > input.size())) {
                throw new IllegalArgumentException(
                    "Invalid selection size"
                );
            }

            if (type == SearchType.N_QUEENS &&
                (boardSize < 1 || boardSize > 15)) {
                throw new IllegalArgumentException(
                    "Board size must be between 1 and 15"
                );
            }
        }
    }

    record SearchSolution(
        int sequence,
        List<Integer> values
    ) {
        SearchSolution {
            values = List.copyOf(values);
        }
    }

    record SearchReport(
        SearchType type,
        SearchStatus status,
        long nodesVisited,
        long solutionsFound,
        long prunedBranches,
        int maximumDepth,
        Duration elapsed
    ) {}

    static class SearchException extends RuntimeException {
        SearchException(String message) {
            super(message);
        }
    }

    static class SearchLimitException extends SearchException {
        SearchLimitException(String message) {
            super(message);
        }
    }

    interface SearchPolicy {
        boolean allowNode(long nodeCount);

        boolean allowSolution(long solutionCount);
    }

    static final class BoundedSearchPolicy implements SearchPolicy {
        private final long maximumNodes;
        private final long maximumSolutions;

        BoundedSearchPolicy(long maximumNodes, long maximumSolutions) {
            if (maximumNodes < 1 || maximumSolutions < 1) {
                throw new IllegalArgumentException(
                    "Invalid search policy"
                );
            }

            this.maximumNodes = maximumNodes;
            this.maximumSolutions = maximumSolutions;
        }

        @Override
        public boolean allowNode(long nodeCount) {
            return nodeCount <= maximumNodes;
        }

        @Override
        public boolean allowSolution(long solutionCount) {
            return solutionCount <= maximumSolutions;
        }
    }

    static final class SearchContext {
        private final SearchPolicy policy;
        private long nodes;
        private long solutions;
        private long pruned;
        private int maximumDepth;

        SearchContext(SearchPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        void visit(int depth) {
            nodes++;
            maximumDepth = Math.max(maximumDepth, depth);

            if (!policy.allowNode(nodes)) {
                throw new SearchLimitException(
                    "Maximum node count exceeded"
                );
            }
        }

        void recordSolution() {
            solutions++;

            if (!policy.allowSolution(solutions)) {
                throw new SearchLimitException(
                    "Maximum solution count exceeded"
                );
            }
        }

        void prune() {
            pruned++;
        }

        long nodes() {
            return nodes;
        }

        long solutions() {
            return solutions;
        }

        long pruned() {
            return pruned;
        }

        int maximumDepth() {
            return maximumDepth;
        }
    }

    interface SearchService {
        List<SearchSolution> execute(
            SearchRequest request,
            SearchContext context
        );
    }

    static final class PermutationService implements SearchService {

        @Override
        public List<SearchSolution> execute(
            SearchRequest request,
            SearchContext context
        ) {
            List<Integer> values = request.input().stream()
                .sorted()
                .collect(Collectors.toCollection(ArrayList::new));

            boolean[] used = new boolean[values.size()];
            List<Integer> path = new ArrayList<>();
            List<SearchSolution> results = new ArrayList<>();

            search(values, used, path, results, context);

            return List.copyOf(results);
        }

        private void search(
            List<Integer> values,
            boolean[] used,
            List<Integer> path,
            List<SearchSolution> results,
            SearchContext context
        ) {
            context.visit(path.size());

            if (path.size() == values.size()) {
                context.recordSolution();

                results.add(
                    new SearchSolution(
                        results.size() + 1,
                        path
                    )
                );

                return;
            }

            for (int i = 0; i < values.size(); i++) {
                if (used[i]) continue;

                if (
                    i > 0 &&
                    values.get(i).equals(values.get(i - 1)) &&
                    !used[i - 1]
                ) {
                    context.prune();
                    continue;
                }

                used[i] = true;
                path.add(values.get(i));

                search(values, used, path, results, context);

                path.remove(path.size() - 1);
                used[i] = false;
            }
        }
    }

    static final class CombinationService implements SearchService {

        @Override
        public List<SearchSolution> execute(
            SearchRequest request,
            SearchContext context
        ) {
            List<Integer> values = request.input().stream()
                .sorted()
                .collect(Collectors.toCollection(ArrayList::new));

            List<Integer> path = new ArrayList<>();
            List<SearchSolution> results = new ArrayList<>();

            search(
                values,
                request.selectionSize(),
                0,
                path,
                results,
                context
            );

            return List.copyOf(results);
        }

        private void search(
            List<Integer> values,
            int k,
            int start,
            List<Integer> path,
            List<SearchSolution> results,
            SearchContext context
        ) {
            context.visit(path.size());

            if (path.size() == k) {
                context.recordSolution();

                results.add(
                    new SearchSolution(
                        results.size() + 1,
                        path
                    )
                );

                return;
            }

            int remaining = k - path.size();
            int last = values.size() - remaining;

            for (int i = start; i <= last; i++) {
                if (
                    i > start &&
                    values.get(i).equals(values.get(i - 1))
                ) {
                    context.prune();
                    continue;
                }

                path.add(values.get(i));

                search(
                    values,
                    k,
                    i + 1,
                    path,
                    results,
                    context
                );

                path.remove(path.size() - 1);
            }
        }
    }

    static final class NQueensService implements SearchService {

        @Override
        public List<SearchSolution> execute(
            SearchRequest request,
            SearchContext context
        ) {
            int n = request.boardSize();

            List<Integer> positions = new ArrayList<>(
                java.util.Collections.nCopies(n, -1)
            );

            List<SearchSolution> results = new ArrayList<>();

            search(
                n,
                0,
                new HashSet<>(),
                new HashSet<>(),
                new HashSet<>(),
                positions,
                results,
                context
            );

            return List.copyOf(results);
        }

        private void search(
            int n,
            int row,
            Set<Integer> columns,
            Set<Integer> descending,
            Set<Integer> ascending,
            List<Integer> positions,
            List<SearchSolution> results,
            SearchContext context
        ) {
            context.visit(row);

            if (row == n) {
                context.recordSolution();

                results.add(
                    new SearchSolution(
                        results.size() + 1,
                        positions
                    )
                );

                return;
            }

            for (int column = 0; column < n; column++) {
                int d1 = row - column;
                int d2 = row + column;

                if (
                    columns.contains(column) ||
                    descending.contains(d1) ||
                    ascending.contains(d2)
                ) {
                    context.prune();
                    continue;
                }

                positions.set(row, column);

                columns.add(column);
                descending.add(d1);
                ascending.add(d2);

                search(
                    n,
                    row + 1,
                    columns,
                    descending,
                    ascending,
                    positions,
                    results,
                    context
                );

                // Undo all state mutations.
                positions.set(row, -1);

                columns.remove(column);
                descending.remove(d1);
                ascending.remove(d2);
            }
        }
    }

    static final class SearchOrchestrator {
        private SearchStatus status = SearchStatus.CREATED;

        private final SearchPolicy policy;

        SearchOrchestrator(SearchPolicy policy) {
            this.policy = policy;
        }

        SearchReport execute(SearchRequest request) {
            if (status == SearchStatus.RUNNING) {
                throw new SearchException(
                    "Search is already running"
                );
            }

            status = SearchStatus.RUNNING;

            Instant start = Instant.now();
            SearchContext context = new SearchContext(policy);

            try {
                SearchService service = switch (request.type()) {
                    case PERMUTATION -> new PermutationService();
                    case COMBINATION -> new CombinationService();
                    case N_QUEENS -> new NQueensService();
                };

                List<SearchSolution> results =
                    service.execute(request, context);

                status = SearchStatus.COMPLETED;

                System.out.println(
                    "\n" + request.type() + " RESULTS"
                );

                results.forEach(solution ->
                    System.out.println(
                        solution.sequence() + ": " +
                        solution.values()
                    )
                );

            } catch (SearchLimitException exception) {
                status = SearchStatus.LIMIT_EXCEEDED;
                throw exception;

            } catch (RuntimeException exception) {
                status = SearchStatus.FAILED;
                throw exception;

            } finally {
                Duration elapsed = Duration.between(
                    start,
                    Instant.now()
                );

                System.out.println(
                    "Status: " + status +
                    ", Nodes: " + context.nodes() +
                    ", Solutions: " + context.solutions() +
                    ", Pruned: " + context.pruned() +
                    ", Maximum depth: " + context.maximumDepth() +
                    ", Elapsed: " + elapsed.toMillis() + " ms"
                );
            }

            return new SearchReport(
                request.type(),
                status,
                context.nodes(),
                context.solutions(),
                context.pruned(),
                context.maximumDepth(),
                Duration.between(start, Instant.now())
            );
        }
    }

    static SearchRequest permutationRequest() {
        return new SearchRequest(
            SearchType.PERMUTATION,
            List.of(1, 2, 2),
            0,
            0,
            100_000,
            1000
        );
    }

    static SearchRequest combinationRequest() {
        return new SearchRequest(
            SearchType.COMBINATION,
            List.of(1, 2, 3, 4),
            2,
            0,
            100_000,
            1000
        );
    }

    static SearchRequest queensRequest(int n) {
        return new SearchRequest(
            SearchType.N_QUEENS,
            List.of(),
            0,
            n,
            100_000,
            1000
        );
    }

    static void validateResults() {
        SearchPolicy policy = new BoundedSearchPolicy(
            100_000,
            1000
        );

        SearchOrchestrator permutations =
            new SearchOrchestrator(policy);

        SearchReport p = permutations.execute(
            permutationRequest()
        );

        if (p.solutionsFound() != 3) {
            throw new AssertionError("Permutation count incorrect");
        }

        SearchOrchestrator combinations =
            new SearchOrchestrator(policy);

        SearchReport c = combinations.execute(
            combinationRequest()
        );

        if (c.solutionsFound() != 6) {
            throw new AssertionError("Combination count incorrect");
        }

        SearchOrchestrator queens =
            new SearchOrchestrator(policy);

        SearchReport q = queens.execute(
            queensRequest(4)
        );

        if (q.solutionsFound() != 2) {
            throw new AssertionError("N-Queens count incorrect");
        }

        if (
            new SearchOrchestrator(policy)
                .execute(queensRequest(2))
                .solutionsFound() != 0
        ) {
            throw new AssertionError("N-Queens edge case incorrect");
        }

        if (
            new SearchOrchestrator(policy)
                .execute(queensRequest(5))
                .solutionsFound() != 10
        ) {
            throw new AssertionError("N-Queens count incorrect");
        }
    }

    public static void main(String[] args) {
        try {
            System.out.println(
                "BACKTRACKING ENTERPRISE SEARCH ENGINE"
            );

            validateResults();

            System.out.println(
                "\nAll validation checks passed."
            );

        } catch (RuntimeException | AssertionError exception) {
            System.err.println(
                "Execution failed: " + exception.getMessage()
            );

            System.exit(1);
        }
    }
}
