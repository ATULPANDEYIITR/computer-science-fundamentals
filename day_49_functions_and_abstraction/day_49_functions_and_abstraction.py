"""
Functions and Abstraction
Demonstrates parameters, return values, recursion, modular design,
validation, higher-order functions, closures, decorators, memoization,
and a small functional repository-style data-processing system.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache, wraps
from typing import Callable, Iterable, Iterator, TypeVar


T = TypeVar("T")
R = TypeVar("R")


def print_title(title: str) -> None:
    print(f"\n{'=' * 72}\n{title}\n{'=' * 72}")


# Functions encapsulate one well-defined operation and expose a clear
# input/output contract through parameters and a return value.
def calculate_discount(price: float, percentage: float) -> float:
    if price < 0:
        raise ValueError("price cannot be negative")
    if not 0 <= percentage <= 100:
        raise ValueError("percentage must be between 0 and 100")
    return price * percentage / 100


def final_price(price: float, percentage: float) -> float:
    return price - calculate_discount(price, percentage)


def normalize_username(username: str) -> str:
    if not isinstance(username, str):
        raise TypeError("username must be a string")

    normalized = username.strip().lower()

    if not normalized:
        raise ValueError("username cannot be empty")

    if any(character.isspace() for character in normalized):
        raise ValueError("username cannot contain spaces")

    return normalized


# Default parameters let callers omit values while preserving a useful
# contract for the common case.
def build_greeting(name: str, prefix: str = "Hello") -> str:
    clean_name = name.strip()

    if not clean_name:
        raise ValueError("name cannot be empty")

    return f"{prefix}, {clean_name}!"


def divide(dividend: float, divisor: float) -> float:
    if divisor == 0:
        raise ZeroDivisionError("divisor cannot be zero")
    return dividend / divisor


# Returning multiple values is naturally represented by a tuple.
def analyze_numbers(values: Iterable[float]) -> tuple[float, float, float]:
    numbers = list(values)

    if not numbers:
        raise ValueError("at least one number is required")

    return min(numbers), max(numbers), sum(numbers) / len(numbers)


# Recursion reduces a problem into a smaller instance of the same problem.
# The explicit base case prevents infinite recursion.
def factorial(n: int) -> int:
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("factorial requires an integer")

    if n < 0:
        raise ValueError("factorial is undefined for negative integers")

    if n in (0, 1):
        return 1

    return n * factorial(n - 1)


def recursive_sum(values: list[int]) -> int:
    if not values:
        return 0
    return values[0] + recursive_sum(values[1:])


def binary_search(values: list[int], target: int, low: int = 0, high: int | None = None) -> int:
    if high is None:
        high = len(values) - 1

    if low > high:
        return -1

    midpoint = (low + high) // 2

    if values[midpoint] == target:
        return midpoint

    if target < values[midpoint]:
        return binary_search(values, target, low, midpoint - 1)

    return binary_search(values, target, midpoint + 1, high)


# A class groups related state and behavior. Methods are functions whose
# first parameter conventionally represents the object receiving the call.
@dataclass
class Repository:
    name: str
    default_branch: str = "main"
    open_pull_requests: int = 0

    def create_pull_request(self) -> None:
        self.open_pull_requests += 1

    def close_pull_request(self) -> None:
        if self.open_pull_requests == 0:
            raise ValueError("there are no open pull requests")
        self.open_pull_requests -= 1

    def status(self) -> str:
        return (
            f"{self.name}: branch={self.default_branch}, "
            f"open_prs={self.open_pull_requests}"
        )


# Higher-order functions accept functions as parameters. This creates
# reusable behavior without duplicating the surrounding control flow.
def transform(values: Iterable[T], operation: Callable[[T], R]) -> list[R]:
    return [operation(value) for value in values]


def filter_values(
    values: Iterable[T],
    predicate: Callable[[T], bool],
) -> list[T]:
    return [value for value in values if predicate(value)]


def compose(
    first: Callable[[T], R],
    second: Callable[[R], T],
) -> Callable[[T], T]:
    def composed(value: T) -> T:
        return second(first(value))

    return composed


# Closures preserve values from their defining scope. The returned function
# behaves like a specialized function factory.
def make_multiplier(factor: float) -> Callable[[float], float]:
    if not isinstance(factor, (int, float)):
        raise TypeError("factor must be numeric")

    def multiply(value: float) -> float:
        return value * factor

    return multiply


# A decorator adds behavior around an existing function without modifying
# its core calculation.
def trace_calls(function: Callable[..., R]) -> Callable[..., R]:
    @wraps(function)
    def wrapper(*args, **kwargs) -> R:
        print(f"CALL {function.__name__}(args={args}, kwargs={kwargs})")
        result = function(*args, **kwargs)
        print(f"RETURN {result!r}")
        return result

    return wrapper


@trace_calls
def calculate_total(prices: Iterable[float], tax_rate: float = 0.0) -> float:
    if not 0 <= tax_rate <= 1:
        raise ValueError("tax_rate must be between 0 and 1")

    subtotal = sum(prices)

    if subtotal < 0:
        raise ValueError("subtotal cannot be negative")

    return subtotal * (1 + tax_rate)


# Memoization avoids recomputing expensive recursive subproblems.
@lru_cache(maxsize=None)
def fibonacci(n: int) -> int:
    if n < 0:
        raise ValueError("n must be non-negative")

    if n < 2:
        return n

    return fibonacci(n - 1) + fibonacci(n - 2)


def walk_directory_tree(tree: dict[str, dict | None], prefix: str = "") -> Iterator[str]:
    """
    Recursively traverse a nested dictionary representing directories.

    A value of None represents a leaf file. The generator yields paths
    lazily, so callers do not need to build a complete result list.
    """
    for name, children in tree.items():
        path = f"{prefix}/{name}" if prefix else name

        if children is None:
            yield path
        else:
            yield from walk_directory_tree(children, path)


@dataclass(frozen=True)
class PullRequest:
    number: int
    author: str
    changed_files: int
    approvals: int
    tests_passed: bool

    def is_mergeable(self, required_approvals: int = 2) -> bool:
        if required_approvals < 1:
            raise ValueError("required_approvals must be positive")

        return (
            self.changed_files > 0
            and self.approvals >= required_approvals
            and self.tests_passed
        )


def summarize_pull_requests(
    pull_requests: Iterable[PullRequest],
    eligibility_rule: Callable[[PullRequest], bool],
) -> dict[str, int]:
    total = 0
    eligible = 0

    for pull_request in pull_requests:
        total += 1
        if eligibility_rule(pull_request):
            eligible += 1

    return {
        "total": total,
        "eligible": eligible,
        "blocked": total - eligible,
    }


def safe_execute(
    operation: Callable[[], R],
    fallback: R,
) -> R:
    try:
        return operation()
    except (ValueError, TypeError, ZeroDivisionError):
        return fallback


def demonstrate_basics() -> None:
    print_title("Parameters and Return Values")

    print("Discount:", calculate_discount(2500, 15))
    print("Final price:", final_price(2500, 15))
    print("Username:", normalize_username("  DevUser  "))
    print(build_greeting("Atul"))
    print(build_greeting("Repository Team", prefix="Welcome"))

    minimum, maximum, average = analyze_numbers([12, 18, 21, 30])
    print(f"min={minimum}, max={maximum}, average={average:.2f}")

    print_title("Failure Conditions")
    print("Invalid division:", safe_execute(lambda: divide(10, 0), fallback=float("nan")))
    print(
        "Invalid discount:",
        safe_execute(lambda: calculate_discount(100, 120), fallback=0.0),
    )


def demonstrate_recursion() -> None:
    print_title("Recursion")

    print("factorial(6):", factorial(6))
    print("recursive sum:", recursive_sum([4, 7, 11, 18]))

    sorted_values = [3, 8, 14, 21, 29, 35, 42]
    print("binary search index:", binary_search(sorted_values, 29))
    print("missing value:", binary_search(sorted_values, 31))

    print_title("Memoized Recursion")
    print("fibonacci(40):", fibonacci(40))
    print("cache statistics:", fibonacci.cache_info())


def demonstrate_modularity() -> None:
    print_title("Classes and Modular Behavior")

    repository = Repository("governance-engine")
    repository.create_pull_request()
    repository.create_pull_request()

    print(repository.status())

    repository.close_pull_request()
    print(repository.status())

    print_title("Higher-Order Functions")

    numbers = [1, 2, 3, 4, 5]
    print("squared:", transform(numbers, lambda value: value * value))
    print("even:", filter_values(numbers, lambda value: value % 2 == 0))

    double = make_multiplier(2)
    triple = make_multiplier(3)

    print("double:", transform(numbers, double))
    print("triple:", transform(numbers, triple))

    print_title("Composition and Decorators")

    strip_text = lambda value: value.strip()
    to_lower = lambda value: value.lower()

    clean_username = compose(strip_text, to_lower)
    print(clean_username("  DEV-TEAM  "))

    calculate_total([100, 250, 50], tax_rate=0.18)


def demonstrate_recursive_data_processing() -> None:
    print_title("Recursive Data Processing")

    repository_tree = {
        "src": {
            "auth": {
                "policy.py": None,
                "review.py": None,
            },
            "workflow.py": None,
        },
        "tests": {
            "test_policy.py": None,
            "test_workflow.py": None,
        },
        "README.md": None,
    }

    for path in walk_directory_tree(repository_tree):
        print(path)


def demonstrate_domain_abstraction() -> None:
    print_title("Domain-Level Abstraction")

    pull_requests = [
        PullRequest(101, "alice", 4, 3, True),
        PullRequest(102, "bob", 8, 1, True),
        PullRequest(103, "carol", 2, 2, False),
        PullRequest(104, "david", 6, 4, True),
    ]

    # The workflow owns the decision while the domain object owns the
    # rule describing whether one pull request satisfies its requirements.
    summary = summarize_pull_requests(
        pull_requests,
        lambda pull_request: pull_request.is_mergeable(required_approvals=2),
    )

    print(summary)

    print_title("Immutable Domain Data")

    for pull_request in pull_requests:
        state = "mergeable" if pull_request.is_mergeable() else "blocked"
        print(
            f"PR #{pull_request.number} by {pull_request.author}: "
            f"{state}"
        )


def demonstrate_generators_and_pipeline() -> None:
    print_title("Lazy Modular Pipeline")

    events = [
        {"type": "push", "branch": "feature/auth", "files": 3},
        {"type": "pull_request", "branch": "feature/auth", "files": 7},
        {"type": "pull_request", "branch": "feature/payments", "files": 4},
        {"type": "issue", "branch": "main", "files": 0},
    ]

    def pull_request_events(
        records: Iterable[dict],
    ) -> Iterator[dict]:
        for record in records:
            if record["type"] == "pull_request":
                yield record

    def significant_changes(
        records: Iterable[dict],
        threshold: int,
    ) -> Iterator[dict]:
        for record in records:
            if record["files"] >= threshold:
                yield record

    pipeline = significant_changes(
        pull_request_events(events),
        threshold=5,
    )

    for event in pipeline:
        print(event)


def main() -> None:
    demonstrate_basics()
    demonstrate_recursion()
    demonstrate_modularity()
    demonstrate_recursive_data_processing()
    demonstrate_domain_abstraction()
    demonstrate_generators_and_pipeline()

    print_title("Design Boundary")
    print(
        "Small functions expose narrow contracts; classes encapsulate related "
        "state; recursion handles self-similar structures; higher-order "
        "functions make behavior configurable; and composition allows these "
        "units to form larger workflows without duplicating logic."
    )


if __name__ == "__main__":
    main()
