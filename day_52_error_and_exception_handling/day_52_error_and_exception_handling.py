from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import logging
import tempfile


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)


class ValidationError(ValueError):
    """Raised when supplied data violates domain validation rules."""


class ConfigurationError(RuntimeError):
    """Raised when required application configuration is invalid."""


class RepositoryError(RuntimeError):
    """Base exception for repository persistence failures."""


class RepositoryNotFoundError(RepositoryError):
    """Raised when a requested repository does not exist."""


class RepositoryStorageError(RepositoryError):
    """Raised when repository data cannot be persisted safely."""


@dataclass(frozen=True)
class Repository:
    name: str
    owner: str
    default_branch: str = "main"

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValidationError("Repository name cannot be empty.")
        if not self.owner.strip():
            raise ValidationError("Repository owner cannot be empty.")
        if not self.default_branch.strip():
            raise ValidationError("Default branch cannot be empty.")


class RepositoryStore:
    """Small persistence layer demonstrating exception translation and recovery."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def save(self, repository: Repository) -> None:
        payload = {
            "name": repository.name,
            "owner": repository.owner,
            "default_branch": repository.default_branch,
        }

        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(".tmp")
            temporary.write_text(
                json.dumps(payload, indent=2),
                encoding="utf-8",
            )
            temporary.replace(self.path)
        except OSError as exc:
            # Low-level filesystem details are translated into a domain exception.
            raise RepositoryStorageError(
                f"Unable to save repository to {self.path}"
            ) from exc

    def load(self) -> Repository:
        try:
            raw = self.path.read_text(encoding="utf-8")
            data: Any = json.loads(raw)

            if not isinstance(data, dict):
                raise ValidationError("Repository document must be a JSON object.")

            return Repository(
                name=str(data["name"]),
                owner=str(data["owner"]),
                default_branch=str(data["default_branch"]),
            )
        except FileNotFoundError as exc:
            raise RepositoryNotFoundError(
                f"Repository file does not exist: {self.path}"
            ) from exc
        except json.JSONDecodeError as exc:
            raise RepositoryStorageError(
                f"Repository file contains invalid JSON: {self.path}"
            ) from exc
        except KeyError as exc:
            raise RepositoryStorageError(
                f"Repository document is missing field: {exc.args[0]}"
            ) from exc
        except OSError as exc:
            raise RepositoryStorageError(
                f"Unable to read repository from {self.path}"
            ) from exc


def parse_positive_integer(value: str) -> int:
    """Validate external text before converting it into an integer."""
    try:
        number = int(value)
    except ValueError as exc:
        raise ValidationError(f"Expected an integer, received {value!r}.") from exc

    if number <= 0:
        raise ValidationError("Value must be greater than zero.")

    return number


def retry_operation(operation, attempts: int = 3) -> Any:
    """
    Retry only transient repository failures.

    Validation and not-found failures are not retried because repeating them
    cannot make the underlying condition valid.
    """
    if attempts <= 0:
        raise ValidationError("Retry attempts must be positive.")

    last_error: RepositoryStorageError | None = None

    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except RepositoryStorageError as exc:
            last_error = exc
            logging.warning(
                "Transient storage failure on attempt %d/%d",
                attempt,
                attempts,
            )

    assert last_error is not None
    raise last_error


def demonstrate_propagation() -> None:
    """Show how an exception moves through nested functions until handled."""
    def read_required_configuration() -> str:
        raise ConfigurationError("DATABASE_URL is missing.")

    def initialize_application() -> str:
        # The exception propagates because this layer cannot recover from it.
        return read_required_configuration()

    try:
        initialize_application()
    except ConfigurationError as exc:
        logging.error("Application initialization failed: %s", exc)


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "repository.json"
        store = RepositoryStore(path)

        print("Defensive validation:")
        for value in ("42", "0", "abc"):
            try:
                print(f"  {value!r} -> {parse_positive_integer(value)}")
            except ValidationError as exc:
                print(f"  {value!r} -> rejected: {exc}")

        print("\nNormal persistence:")
        repository = Repository(
            name="payment-service",
            owner="platform-team",
            default_branch="main",
        )

        try:
            store.save(repository)
            loaded = store.load()
            print(f"  loaded: {loaded}")
        except RepositoryError as exc:
            print(f"  repository operation failed: {exc}")

        print("\nException propagation:")
        demonstrate_propagation()

        print("\nNot-found handling:")
        missing = RepositoryStore(Path(directory) / "missing.json")
        try:
            missing.load()
        except RepositoryNotFoundError as exc:
            print(f"  recoverable domain failure: {exc}")

        print("\nException chaining:")
        corrupt = Path(directory) / "corrupt.json"
        corrupt.write_text("{invalid", encoding="utf-8")

        try:
            RepositoryStore(corrupt).load()
        except RepositoryStorageError as exc:
            print(f"  translated failure: {exc}")
            if exc.__cause__ is not None:
                print(f"  original cause: {type(exc.__cause__).__name__}")

        print("\nRetry policy:")
        state = {"attempts": 0}

        def flaky_operation() -> str:
            state["attempts"] += 1
            if state["attempts"] < 3:
                raise RepositoryStorageError("Temporary storage outage.")
            return "operation succeeded"

        try:
            print(f"  {retry_operation(flaky_operation)}")
        except RepositoryStorageError as exc:
            print(f"  retry exhausted: {exc}")


if __name__ == "__main__":
    main()
