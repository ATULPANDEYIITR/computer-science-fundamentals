import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

public class ObjectOrientedBanking {

    enum AccountStatus {
        ACTIVE,
        FROZEN,
        CLOSED
    }

    record Customer(String id, String name) {
        Customer {
            if (id == null || id.isBlank()) {
                throw new IllegalArgumentException("Customer ID is required.");
            }
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("Customer name is required.");
            }
        }
    }

    interface InterestBearing {
        void applyInterest();
    }

    static abstract class BankAccount {
        private final String accountNumber;
        private final Customer owner;
        private double balance;
        private AccountStatus status;

        protected BankAccount(String accountNumber, Customer owner, double openingBalance) {
            if (accountNumber == null || accountNumber.isBlank()) {
                throw new IllegalArgumentException("Account number is required.");
            }
            if (openingBalance < 0) {
                throw new IllegalArgumentException("Opening balance cannot be negative.");
            }

            this.accountNumber = accountNumber;
            this.owner = Objects.requireNonNull(owner, "Owner is required.");
            this.balance = openingBalance;
            this.status = AccountStatus.ACTIVE;
        }

        public final String accountNumber() {
            return accountNumber;
        }

        public final Customer owner() {
            return owner;
        }

        public final double balance() {
            return balance;
        }

        public final AccountStatus status() {
            return status;
        }

        protected final void changeBalance(double amount) {
            balance += amount;

            if (balance < 0) {
                throw new IllegalStateException("Account balance invariant violated.");
            }
        }

        public final void deposit(double amount) {
            requireActive();

            if (amount <= 0) {
                throw new IllegalArgumentException("Deposit must be positive.");
            }

            changeBalance(amount);
        }

        public abstract void withdraw(double amount);

        public final void freeze() {
            if (status == AccountStatus.CLOSED) {
                throw new IllegalStateException("Closed accounts cannot be frozen.");
            }
            status = AccountStatus.FROZEN;
        }

        public final void activate() {
            if (status == AccountStatus.CLOSED) {
                throw new IllegalStateException("Closed accounts cannot be activated.");
            }
            status = AccountStatus.ACTIVE;
        }

        public final void close() {
            if (balance != 0) {
                throw new IllegalStateException("Account must have zero balance before closure.");
            }
            status = AccountStatus.CLOSED;
        }

        protected final void requireActive() {
            if (status != AccountStatus.ACTIVE) {
                throw new IllegalStateException(
                    "Account operation rejected while status is " + status
                );
            }
        }

        public String description() {
            return accountNumber + " | " + owner.name() + " | " + balance;
        }
    }

    static final class SavingsAccount extends BankAccount implements InterestBearing {
        private final double annualInterestRate;

        SavingsAccount(
            String accountNumber,
            Customer owner,
            double openingBalance,
            double annualInterestRate
        ) {
            super(accountNumber, owner, openingBalance);

            if (annualInterestRate < 0 || annualInterestRate > 1) {
                throw new IllegalArgumentException("Interest rate must be between 0 and 1.");
            }

            this.annualInterestRate = annualInterestRate;
        }

        @Override
        public void withdraw(double amount) {
            requireActive();

            if (amount <= 0) {
                throw new IllegalArgumentException("Withdrawal must be positive.");
            }

            if (amount > balance()) {
                throw new IllegalStateException("Insufficient savings balance.");
            }

            changeBalance(-amount);
        }

        @Override
        public void applyInterest() {
            requireActive();
            changeBalance(balance() * annualInterestRate);
        }
    }

    static final class BusinessAccount extends BankAccount {
        private final double creditLimit;

        BusinessAccount(
            String accountNumber,
            Customer owner,
            double openingBalance,
            double creditLimit
        ) {
            super(accountNumber, owner, openingBalance);

            if (creditLimit < 0) {
                throw new IllegalArgumentException("Credit limit cannot be negative.");
            }

            this.creditLimit = creditLimit;
        }

        @Override
        public void withdraw(double amount) {
            requireActive();

            if (amount <= 0) {
                throw new IllegalArgumentException("Withdrawal must be positive.");
            }

            if (amount > balance() + creditLimit) {
                throw new IllegalStateException("Credit limit exceeded.");
            }

            changeBalance(-amount);
        }
    }

    static final class BankingService {
        private final List<BankAccount> accounts = new ArrayList<>();

        public void register(BankAccount account) {
            Objects.requireNonNull(account, "Account is required.");

            boolean duplicate = accounts.stream()
                .anyMatch(existing ->
                    existing.accountNumber().equals(account.accountNumber()));

            if (duplicate) {
                throw new IllegalArgumentException("Duplicate account number.");
            }

            accounts.add(account);
        }

        public List<BankAccount> activeAccounts() {
            return accounts.stream()
                .filter(account -> account.status() == AccountStatus.ACTIVE)
                .toList();
        }

        public double totalBalance() {
            return accounts.stream()
                .mapToDouble(BankAccount::balance)
                .sum();
        }

        public List<BankAccount> accountsView() {
            return Collections.unmodifiableList(accounts);
        }
    }

    public static void main(String[] args) {
        Customer alice = new Customer("C001", "Alice");
        Customer company = new Customer("C002", "Acme Systems");

        SavingsAccount savings =
            new SavingsAccount("S-1001", alice, 5000, 0.04);

        BusinessAccount business =
            new BusinessAccount("B-2001", company, 10000, 5000);

        BankingService service = new BankingService();
        service.register(savings);
        service.register(business);

        savings.deposit(1000);
        savings.applyInterest();

        business.withdraw(12000);

        System.out.println("Active accounts:");
        service.activeAccounts()
            .forEach(account -> System.out.println(account.description()));

        System.out.printf("Total balance: %.2f%n", service.totalBalance());

        savings.freeze();

        try {
            savings.deposit(100);
        } catch (IllegalStateException error) {
            System.out.println("Blocked frozen-account operation: " + error.getMessage());
        }

        savings.activate();
        savings.withdraw(savings.balance());

        savings.close();

        try {
            service.register(
                new SavingsAccount("S-1001", alice, 100, 0.03)
            );
        } catch (IllegalArgumentException error) {
            System.out.println("Registration rejected: " + error.getMessage());
        }

        /*
         * BankAccount defines the stable domain contract.
         * SavingsAccount and BusinessAccount specialize withdrawal behavior.
         * BankingService operates on the BankAccount abstraction, so new
         * account types can be introduced without rewriting its collection logic.
         */
    }
}
