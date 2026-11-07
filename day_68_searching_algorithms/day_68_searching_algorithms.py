from dataclasses import dataclass
from typing import Sequence, Optional
from enum import Enum
import random
import time


class SearchAlgorithm(Enum):
    LINEAR = "Linear Search"
    BINARY = "Binary Search"
    INTERPOLATION = "Interpolation Search"


@dataclass
class SearchResult:
    algorithm: str
    target: int
    index: Optional[int]
    comparisons: int
    elapsed_microseconds: float

    @property
    def found(self) -> bool:
        return self.index is not None

    def display(self) -> None:
        status = f"Found at index {self.index}" if self.found else "Not found"
        print(
            f"{self.algorithm}: {status} | "
            f"Comparisons: {self.comparisons} | "
            f"Time: {self.elapsed_microseconds:.3f} µs"
        )


class SearchEngine:
    """Implements three searching algorithms with consistent result reporting."""

    @staticmethod
    def validate_input(data: Sequence[int]) -> None:
        if not isinstance(data, (list, tuple)):
            raise TypeError("Data must be a list or tuple.")

        if any(type(value) is not int for value in data):
            raise TypeError("All elements must be integers.")

    @staticmethod
    def validate_target(target: int) -> None:
        if type(target) is not int:
            raise TypeError("Target must be an integer.")

    @staticmethod
    def validate_sorted(data: Sequence[int]) -> None:
        if any(data[i] > data[i + 1] for i in range(len(data) - 1)):
            raise ValueError("Binary and interpolation search require sorted data.")

    @staticmethod
    def linear_search(data: Sequence[int], target: int) -> SearchResult:
        SearchEngine.validate_input(data)
        SearchEngine.validate_target(target)

        comparisons = 0
        start = time.perf_counter_ns()

        for index, value in enumerate(data):
            comparisons += 1
            if value == target:
                elapsed = (time.perf_counter_ns() - start) / 1000
                return SearchResult(
                    SearchAlgorithm.LINEAR.value,
                    target, index, comparisons, elapsed
                )

        elapsed = (time.perf_counter_ns() - start) / 1000
        return SearchResult(
            SearchAlgorithm.LINEAR.value,
            target, None, comparisons, elapsed
        )

    @staticmethod
    def binary_search(data: Sequence[int], target: int) -> SearchResult:
        SearchEngine.validate_input(data)
        SearchEngine.validate_target(target)
        SearchEngine.validate_sorted(data)

        start = time.perf_counter_ns()
        left, right = 0, len(data) - 1
        comparisons = 0
        result = None

        # Continue left after finding a match to return the first occurrence.
        while left <= right:
            middle = left + (right - left) // 2
            comparisons += 1

            if data[middle] == target:
                result = middle
                right = middle - 1
            elif data[middle] < target:
                left = middle + 1
            else:
                right = middle - 1

        elapsed = (time.perf_counter_ns() - start) / 1000
        return SearchResult(
            SearchAlgorithm.BINARY.value,
            target, result, comparisons, elapsed
        )

    @staticmethod
    def interpolation_search(
        data: Sequence[int], target: int
    ) -> SearchResult:
        SearchEngine.validate_input(data)
        SearchEngine.validate_target(target)
        SearchEngine.validate_sorted(data)

        start = time.perf_counter_ns()
        low, high = 0, len(data) - 1
        comparisons = 0
        result = None

        while low <= high:
            comparisons += 1

            if target < data[low] or target > data[high]:
                break

            # Avoid division by zero when all remaining values are equal.
            if data[low] == data[high]:
                if data[low] == target:
                    result = low
                break

            position = low + (
                (target - data[low]) * (high - low)
                // (data[high] - data[low])
            )

            # Guard against invalid estimates.
            position = max(low, min(position, high))

            comparisons += 1

            if data[position] == target:
                result = position
                high = position - 1
            elif data[position] < target:
                low = position + 1
            else:
                high = position - 1

        elapsed = (time.perf_counter_ns() - start) / 1000
        return SearchResult(
            SearchAlgorithm.INTERPOLATION.value,
            target, result, comparisons, elapsed
        )

    @staticmethod
    def compare(data: Sequence[int], target: int) -> list[SearchResult]:
        return [
            SearchEngine.linear_search(data, target),
            SearchEngine.binary_search(data, target),
            SearchEngine.interpolation_search(data, target),
        ]


class InventorySearch:
    """Searches product identifiers in an inventory."""

    def __init__(self, product_ids: Sequence[int]):
        SearchEngine.validate_input(product_ids)
        self.product_ids = sorted(product_ids)

    def find_product(self, product_id: int) -> SearchResult:
        return SearchEngine.binary_search(self.product_ids, product_id)

    def add_product(self, product_id: int) -> None:
        SearchEngine.validate_target(product_id)

        # Maintain sorted order for future binary and interpolation searches.
        import bisect
        bisect.insort(self.product_ids, product_id)

    def remove_product(self, product_id: int) -> bool:
        import bisect

        index = bisect.bisect_left(self.product_ids, product_id)

        if index < len(self.product_ids) and self.product_ids[index] == product_id:
            self.product_ids.pop(index)
            return True

        return False


def benchmark_search(size: int = 100_000) -> None:
    if type(size) is not int or size <= 0:
        raise ValueError("Benchmark size must be a positive integer.")

    # Uniformly distributed unique integers.
    data = sorted(random.sample(range(size * 10), size))
    target = data[size // 2]

    print(f"\nBenchmark: {size:,} elements")
    for result in SearchEngine.compare(data, target):
        result.display()


def run_tests() -> None:
    # Ordinary searching.
    data = [10, 20, 30, 40, 50, 60, 70]

    assert SearchEngine.linear_search(data, 40).index == 3
    assert SearchEngine.binary_search(data, 40).index == 3
    assert SearchEngine.interpolation_search(data, 40).index == 3

    # Duplicate values: all algorithms return the first occurrence.
    duplicates = [5, 5, 5, 10, 10, 20]
    assert SearchEngine.linear_search(duplicates, 10).index == 3
    assert SearchEngine.binary_search(duplicates, 10).index == 3
    assert SearchEngine.interpolation_search(duplicates, 10).index == 3

    # Missing elements.
    assert SearchEngine.binary_search(data, 99).index is None
    assert SearchEngine.interpolation_search(data, 5).index is None

    # Empty collections.
    assert SearchEngine.linear_search([], 10).index is None
    assert SearchEngine.binary_search([], 10).index is None
    assert SearchEngine.interpolation_search([], 10).index is None

    # Single element and identical elements.
    assert SearchEngine.interpolation_search([7], 7).index == 0
    assert SearchEngine.interpolation_search([7, 7, 7], 7).index == 0

    # Unsorted input is supported only by linear search.
    unsorted = [40, 10, 30, 20]
    assert SearchEngine.linear_search(unsorted, 30).index == 2

    try:
        SearchEngine.binary_search(unsorted, 30)
        raise AssertionError("Unsorted input should be rejected.")
    except ValueError:
        pass

    # Type validation.
    try:
        SearchEngine.binary_search([1, "2", 3], 2)
        raise AssertionError("Invalid data should be rejected.")
    except TypeError:
        pass

    inventory = InventorySearch([1005, 1001, 1003])
    assert inventory.find_product(1003).index == 1
    inventory.add_product(1002)
    assert inventory.product_ids == [1001, 1002, 1003, 1005]
    assert inventory.remove_product(1002)
    assert not inventory.remove_product(9999)

    print("All tests passed.")


def main() -> None:
    print("=" * 60)
    print("SEARCHING ALGORITHMS")
    print("=" * 60)

    data = [12, 24, 36, 48, 60, 72, 84, 96]
    target = 60

    print(f"\nDataset: {data}")
    print(f"Target: {target}\n")

    for result in SearchEngine.compare(data, target):
        result.display()

    print("\nDuplicate-value example:")
    duplicate_data = [10, 20, 20, 20, 30, 40]
    for result in SearchEngine.compare(duplicate_data, 20):
        result.display()

    print("\nInventory example:")
    inventory = InventorySearch([5004, 5001, 5003, 5002])
    inventory.find_product(5003).display()

    print("\nRunning validation tests:")
    run_tests()

    # Optional benchmark with a larger dataset.
    benchmark_search(100_000)


if __name__ == "__main__":
    main()
