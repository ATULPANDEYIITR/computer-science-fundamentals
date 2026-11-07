import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.TreeMap;

public class SearchingAlgorithms {

    enum Algorithm {
        LINEAR,
        BINARY,
        INTERPOLATION
    }

    enum SearchStatus {
        FOUND,
        NOT_FOUND
    }

    record SearchResult(
        Algorithm algorithm,
        int target,
        Integer index,
        long comparisons,
        double elapsedMicroseconds,
        SearchStatus status
    ) {
        SearchResult {
            Objects.requireNonNull(algorithm);
            Objects.requireNonNull(status);

            if (comparisons < 0 || elapsedMicroseconds < 0) {
                throw new IllegalArgumentException(
                    "Invalid search metrics."
                );
            }
        }

        void display() {
            System.out.println("\nAlgorithm: " + algorithm);
            System.out.println("Target: " + target);
            System.out.println("Status: " + status);
            System.out.println("Index: " + index);
            System.out.println("Comparisons: " + comparisons);
            System.out.printf(
                "Execution time: %.3f microseconds%n",
                elapsedMicroseconds
            );
        }
    }

    static class SearchValidationException extends RuntimeException {
        SearchValidationException(String message) {
            super(message);
        }
    }

    interface SearchStrategy {
        SearchResult search(List<Integer> data, int target);
    }

    static void validateData(List<Integer> data) {
        Objects.requireNonNull(data, "Data cannot be null.");

        if (data.stream().anyMatch(Objects::isNull)) {
            throw new SearchValidationException(
                "Null elements are not supported."
            );
        }
    }

    static void validateSorted(List<Integer> data) {
        for (int i = 1; i < data.size(); i++) {
            if (data.get(i) < data.get(i - 1)) {
                throw new SearchValidationException(
                    "Data must be sorted in ascending order."
                );
            }
        }
    }

    static class LinearSearch implements SearchStrategy {

        @Override
        public SearchResult search(List<Integer> data, int target) {
            validateData(data);

            long start = System.nanoTime();
            long comparisons = 0;
            Integer index = null;

            for (int i = 0; i < data.size(); i++) {
                comparisons++;

                if (data.get(i) == target) {
                    index = i;
                    break;
                }
            }

            return createResult(
                Algorithm.LINEAR,
                target,
                index,
                comparisons,
                start
            );
        }
    }

    static class BinarySearch implements SearchStrategy {

        @Override
        public SearchResult search(List<Integer> data, int target) {
            validateData(data);
            validateSorted(data);

            long start = System.nanoTime();
            long comparisons = 0;

            int left = 0;
            int right = data.size() - 1;
            Integer index = null;

            // Lower-bound behavior ensures the first duplicate is returned.
            while (left <= right) {
                int middle = left + (right - left) / 2;
                comparisons++;

                int value = data.get(middle);

                if (value == target) {
                    index = middle;
                    right = middle - 1;
                } else if (value < target) {
                    left = middle + 1;
                } else {
                    right = middle - 1;
                }
            }

            return createResult(
                Algorithm.BINARY,
                target,
                index,
                comparisons,
                start
            );
        }
    }

    static class InterpolationSearch implements SearchStrategy {

        @Override
        public SearchResult search(List<Integer> data, int target) {
            validateData(data);
            validateSorted(data);

            long start = System.nanoTime();
            long comparisons = 0;

            int low = 0;
            int high = data.size() - 1;
            Integer index = null;

            while (low <= high) {
                comparisons++;

                int lowValue = data.get(low);
                int highValue = data.get(high);

                if (target < lowValue || target > highValue) {
                    break;
                }

                if (lowValue == highValue) {
                    if (lowValue == target) {
                        index = low;
                    }
                    break;
                }

                // Long arithmetic avoids intermediate integer overflow.
                long numerator =
                    ((long) target - lowValue) * (high - low);

                long denominator = (long) highValue - lowValue;

                long estimated = low + numerator / denominator;

                int position = (int) Math.max(
                    low,
                    Math.min(estimated, high)
                );

                comparisons++;

                int value = data.get(position);

                if (value == target) {
                    index = position;
                    high = position - 1;
                } else if (value < target) {
                    low = position + 1;
                } else {
                    high = position - 1;
                }
            }

            return createResult(
                Algorithm.INTERPOLATION,
                target,
                index,
                comparisons,
                start
            );
        }
    }

    static SearchResult createResult(
        Algorithm algorithm,
        int target,
        Integer index,
        long comparisons,
        long start
    ) {
        double elapsed =
            (System.nanoTime() - start) / 1000.0;

        return new SearchResult(
            algorithm,
            target,
            index,
            comparisons,
            elapsed,
            index == null
                ? SearchStatus.NOT_FOUND
                : SearchStatus.FOUND
        );
    }

    static class SearchService {

        private final Map<Algorithm, SearchStrategy> strategies =
            new TreeMap<>();

        SearchService() {
            strategies.put(Algorithm.LINEAR, new LinearSearch());
            strategies.put(Algorithm.BINARY, new BinarySearch());
            strategies.put(
                Algorithm.INTERPOLATION,
                new InterpolationSearch()
            );
        }

        SearchResult execute(
            Algorithm algorithm,
            List<Integer> data,
            int target
        ) {
            SearchStrategy strategy = strategies.get(algorithm);

            if (strategy == null) {
                throw new SearchValidationException(
                    "Unsupported search algorithm."
                );
            }

            return strategy.search(data, target);
        }

        List<SearchResult> compare(
            List<Integer> data,
            int target
        ) {
            List<SearchResult> results = new ArrayList<>();

            for (Algorithm algorithm : Algorithm.values()) {
                results.add(execute(algorithm, data, target));
            }

            return List.copyOf(results);
        }
    }

    static class ProductCatalog {

        private final List<Integer> productIds = new ArrayList<>();
        private final SearchService searchService = new SearchService();

        ProductCatalog(List<Integer> initialIds) {
            validateData(initialIds);
            productIds.addAll(initialIds);
            Collections.sort(productIds);
        }

        SearchResult find(int productId) {
            return searchService.execute(
                Algorithm.BINARY,
                productIds,
                productId
            );
        }

        void add(int productId) {
            int index = Collections.binarySearch(
                productIds,
                productId
            );

            if (index < 0) {
                index = -index - 1;
            } else {
                // Place new duplicates after existing duplicates.
                while (
                    index < productIds.size()
                    && productIds.get(index) == productId
                ) {
                    index++;
                }
            }

            productIds.add(index, productId);
        }

        boolean remove(int productId) {
            SearchResult result = find(productId);

            if (!result.index().isPresent()) {
                return false;
            }

            productIds.remove(result.index());
            return true;
        }

        List<Integer> getProductIds() {
            return List.copyOf(productIds);
        }
    }

    static void runTests() {
        SearchService service = new SearchService();

        List<Integer> data = List.of(10, 20, 30, 40, 50, 60);

        assert service.execute(
            Algorithm.LINEAR, data, 40
        ).index() == 3;

        assert service.execute(
            Algorithm.BINARY, data, 40
        ).index() == 3;

        assert service.execute(
            Algorithm.INTERPOLATION, data, 40
        ).index() == 3;

        List<Integer> duplicates = List.of(5, 5, 5, 10, 10, 20);

        assert service.execute(
            Algorithm.BINARY, duplicates, 10
        ).index() == 3;

        assert service.execute(
            Algorithm.INTERPOLATION, duplicates, 10
        ).index() == 3;

        assert service.execute(
            Algorithm.INTERPOLATION, List.of(7, 7, 7), 7
        ).index() == 0;

        assert service.execute(
            Algorithm.BINARY, List.of(), 10
        ).status() == SearchStatus.NOT_FOUND;

        boolean rejected = false;

        try {
            service.execute(
                Algorithm.BINARY,
                List.of(30, 10, 20),
                20
            );
        } catch (SearchValidationException exception) {
            rejected = true;
        }

        assert rejected;

        ProductCatalog catalog = new ProductCatalog(
            List.of(5004, 5001, 5003)
        );

        assert catalog.find(5003).index() == 1;

        catalog.add(5002);

        assert catalog.getProductIds().equals(
            List.of(5001, 5002, 5003, 5004)
        );

        assert catalog.remove(5002);
        assert !catalog.remove(9999);

        System.out.println("All Java 17 tests passed.");
    }

    public static void main(String[] args) {
        try {
            System.out.println("ENTERPRISE PRODUCT SEARCH");
            System.out.println("=========================");

            List<Integer> productIds = List.of(
                1205, 1010, 1150, 1300, 1100, 1250, 1050
            );

            List<Integer> sortedIds = new ArrayList<>(productIds);
            Collections.sort(sortedIds);

            SearchService service = new SearchService();

            System.out.println("Product IDs: " + sortedIds);
            System.out.println("Target: 1205");

            for (SearchResult result :
                    service.compare(sortedIds, 1205)) {
                result.display();
            }

            System.out.println("\nMissing product:");

            service.execute(
                Algorithm.BINARY,
                sortedIds,
                9999
            ).display();

            System.out.println("\nProduct catalog management:");

            ProductCatalog catalog = new ProductCatalog(productIds);

            catalog.add(1400);
            catalog.remove(1010);

            System.out.println("Updated catalog: " +
                catalog.getProductIds());

            System.out.println("\nRunning tests:");
            runTests();

        } catch (SearchValidationException exception) {
            System.err.println(
                "Validation failure: " + exception.getMessage()
            );
            System.exit(1);
        } catch (Exception exception) {
            System.err.println(
                "Application failure: " + exception.getMessage()
            );
            System.exit(1);
        }
    }
}
