from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


class ValidationError(ValueError):
    """Raised when domain data violates an OOP invariant."""


@dataclass
class Account:
    """Encapsulated bank account state and behavior."""

    account_number: str
    owner: str
    _balance: float = field(default=0.0, repr=False)

    def __post_init__(self) -> None:
        if not self.account_number.strip():
            raise ValidationError("Account number cannot be empty.")
        if not self.owner.strip():
            raise ValidationError("Owner cannot be empty.")
        if self._balance < 0:
            raise ValidationError("Initial balance cannot be negative.")

    @property
    def balance(self) -> float:
        return self._balance

    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValidationError("Deposit must be positive.")
        self._balance += amount

    def withdraw(self, amount: float) -> None:
        if amount <= 0:
            raise ValidationError("Withdrawal must be positive.")
        if amount > self._balance:
            raise ValidationError("Insufficient funds.")
        self._balance -= amount


class SavingsAccount(Account):
    """Specialized account demonstrating inheritance."""

    def __init__(
        self,
        account_number: str,
        owner: str,
        balance: float = 0.0,
        interest_rate: float = 0.02,
    ) -> None:
        super().__init__(account_number, owner, balance)
        if not 0 <= interest_rate <= 1:
            raise ValidationError("Interest rate must be between 0 and 1.")
        self.interest_rate = interest_rate

    def apply_interest(self) -> None:
        self.deposit(self.balance * self.interest_rate)


class CurrentAccount(Account):
    """Account whose withdrawals may use an approved overdraft."""

    def __init__(
        self,
        account_number: str,
        owner: str,
        balance: float = 0.0,
        overdraft_limit: float = 0.0,
    ) -> None:
        super().__init__(account_number, owner, balance)
        if overdraft_limit < 0:
            raise ValidationError("Overdraft limit cannot be negative.")
        self.overdraft_limit = overdraft_limit

    def withdraw(self, amount: float) -> None:
        if amount <= 0:
            raise ValidationError("Withdrawal must be positive.")
        if amount > self.balance + self.overdraft_limit:
            raise ValidationError("Withdrawal exceeds available funds and overdraft.")
        self._balance -= amount


class Reportable(ABC):
    """Abstract interface used to demonstrate polymorphism."""

    @abstractmethod
    def summary(self) -> str:
        raise NotImplementedError


class AccountReport(Account, Reportable):
    """Combines inherited account behavior with a reporting contract."""

    def summary(self) -> str:
        return (
            f"{self.__class__.__name__} | "
            f"account={self.account_number} | "
            f"owner={self.owner} | "
            f"balance={self.balance:.2f}"
        )


def calculate_total_balance(accounts: Iterable[Account]) -> float:
    """Works with Account subclasses through polymorphic behavior."""
    return sum(account.balance for account in accounts)


def save_report(accounts: Iterable[Reportable], path: Path) -> None:
    """Persist report data using standard-library file handling."""
    try:
        path.write_text(
            "\n".join(account.summary() for account in accounts) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise RuntimeError(f"Unable to write report: {exc}") from exc


def demonstrate_polymorphism(accounts: Iterable[Account]) -> None:
    """
    The same method call can have different behavior depending on
    the concrete subclass. This is runtime polymorphism.
    """
    for account in accounts:
        try:
            account.withdraw(100)
        except ValidationError as exc:
            print(f"Withdrawal rejected for {account.account_number}: {exc}")


def main() -> None:
    savings = SavingsAccount(
        "SAV-1001",
        "Anika",
        balance=1500,
        interest_rate=0.05,
    )

    current = CurrentAccount(
        "CUR-2001",
        "Rohan",
        balance=500,
        overdraft_limit=300,
    )

    savings.deposit(250)
    savings.apply_interest()
    current.withdraw(700)

    accounts = [savings, current]

    print("Account summaries:")
    for account in accounts:
        print(
            f"{account.__class__.__name__}: "
            f"{account.account_number}, "
            f"balance={account.balance:.2f}"
        )

    print(f"Total balance: {calculate_total_balance(accounts):.2f}")

    demonstrate_polymorphism(accounts)

    # Encapsulation prevents direct mutation through the public API.
    try:
        savings.withdraw(-50)
    except ValidationError as exc:
        print(f"Invalid operation: {exc}")

    report_accounts = [
        AccountReport("REP-3001", "Meera", 2200),
        AccountReport("REP-3002", "Vikram", 3100),
    ]

    report_path = Path("account_report.txt")
    save_report(report_accounts, report_path)
    print(f"Report written to: {report_path.resolve()}")

    # A mutable object can still be shared by reference.
    shared = AccountReport("REP-4001", "Shared Owner", 1000)
    alias = shared
    alias.deposit(500)
    print(f"Shared object balance: {shared.balance:.2f}")


if __name__ == "__main__":
    main()
