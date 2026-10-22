#include <algorithm>
#include <exception>
#include <iostream>
#include <map>
#include <optional>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

/*
 * Repository deployment validation engine.
 *
 * The program demonstrates:
 * - exception hierarchy
 * - RAII cleanup
 * - exception propagation
 * - strong validation boundaries
 * - transaction-like rollback
 * - selective recovery
 * - noexcept destruction
 * - preservation of the original exception through nested operations
 */

class ValidationError : public std::runtime_error {
public:
    explicit ValidationError(const std::string& message)
        : std::runtime_error(message) {}
};

class ConfigurationError : public std::runtime_error {
public:
    explicit ConfigurationError(const std::string& message)
        : std::runtime_error(message) {}
};

class RepositoryError : public std::runtime_error {
public:
    explicit RepositoryError(const std::string& message)
        : std::runtime_error(message) {}
};

class RepositoryNotFound : public RepositoryError {
public:
    explicit RepositoryNotFound(const std::string& message)
        : RepositoryError(message) {}
};

class TransientStorageError : public RepositoryError {
public:
    explicit TransientStorageError(const std::string& message)
        : RepositoryError(message) {}
};

struct Repository {
    std::string name;
    std::string owner;
    std::string defaultBranch;
};

void validateRepository(const Repository& repository) {
    if (repository.name.empty()) {
        throw ValidationError("Repository name cannot be empty.");
    }

    if (repository.owner.empty()) {
        throw ValidationError("Repository owner cannot be empty.");
    }

    if (repository.defaultBranch.empty()) {
        throw ValidationError("Default branch cannot be empty.");
    }

    if (repository.name.find(' ') != std::string::npos) {
        throw ValidationError("Repository name cannot contain spaces.");
    }
}

class AuditScope {
public:
    explicit AuditScope(std::string operation)
        : operation_(std::move(operation)) {
        std::cout << "audit: begin " << operation_ << '\n';
    }

    ~AuditScope() noexcept {
        std::cout << "audit: end " << operation_ << '\n';
    }

    AuditScope(const AuditScope&) = delete;
    AuditScope& operator=(const AuditScope&) = delete;

private:
    std::string operation_;
};

class RepositoryCatalog {
public:
    void insert(Repository repository) {
        validateRepository(repository);

        if (repositories_.contains(repository.name)) {
            throw RepositoryError(
                "Repository already exists: " + repository.name
            );
        }

        repositories_.emplace(repository.name, std::move(repository));
    }

    const Repository& find(const std::string& name) const {
        auto iterator = repositories_.find(name);

        if (iterator == repositories_.end()) {
            throw RepositoryNotFound("Repository not found: " + name);
        }

        return iterator->second;
    }

    void remove(const std::string& name) {
        if (repositories_.erase(name) == 0) {
            throw RepositoryNotFound("Repository not found: " + name);
        }
    }

    std::size_t size() const noexcept {
        return repositories_.size();
    }

private:
    std::map<std::string, Repository> repositories_;
};

class DeploymentTransaction {
public:
    explicit DeploymentTransaction(RepositoryCatalog& catalog)
        : catalog_(catalog) {}

    void stage(Repository repository) {
        validateRepository(repository);
        staged_.push_back(std::move(repository));
    }

    void commit() {
        AuditScope audit("deployment-commit");

        const std::size_t originalSize = catalog_.size();

        try {
            for (const auto& repository : staged_) {
                catalog_.insert(repository);
            }

            committed_ = true;
        } catch (...) {
            /*
             * Roll back only entries inserted by this transaction.
             * The catalog's previous state is restored before rethrowing.
             */
            while (catalog_.size() > originalSize) {
                rollbackLastInserted();
            }

            throw;
        }
    }

    ~DeploymentTransaction() noexcept {
        staged_.clear();
    }

private:
    void rollbackLastInserted() {
        // This simplified transaction knows the last staged name.
        // A production implementation would track inserted identifiers.
        if (!staged_.empty()) {
            try {
                catalog_.remove(staged_.back().name);
            } catch (...) {
                // Destructors must not allow rollback failures to escape.
            }
            staged_.pop_back();
        }
    }

    RepositoryCatalog& catalog_;
    std::vector<Repository> staged_;
    bool committed_{false};
};

void validateConfiguration(const std::map<std::string, std::string>& config) {
    auto iterator = config.find("DEPLOYMENT_ENV");

    if (iterator == config.end() || iterator->second.empty()) {
        throw ConfigurationError("DEPLOYMENT_ENV is missing.");
    }

    if (iterator->second != "development" &&
        iterator->second != "staging" &&
        iterator->second != "production") {
        throw ConfigurationError("DEPLOYMENT_ENV is invalid.");
    }
}

std::string performStorageOperation(int& attempts) {
    ++attempts;

    if (attempts < 3) {
        throw TransientStorageError("Temporary storage failure.");
    }

    return "storage operation succeeded";
}

std::string retryStorageOperation(int maxAttempts) {
    if (maxAttempts <= 0) {
        throw ValidationError("Maximum attempts must be positive.");
    }

    for (int attempt = 1; attempt <= maxAttempts; ++attempt) {
        try {
            int attempts = attempt;
            return performStorageOperation(attempts);
        } catch (const TransientStorageError&) {
            if (attempt == maxAttempts) {
                throw;
            }
        }
    }

    throw RepositoryError("Unreachable retry state.");
}

void nestedOperation(const RepositoryCatalog& catalog) {
    const Repository& repository = catalog.find("missing-service");
    std::cout << repository.name << '\n';
}

int main() {
    RepositoryCatalog catalog;

    std::cout << "Validation failure:\n";

    try {
        catalog.insert({"", "platform", "main"});
    } catch (const ValidationError& error) {
        std::cout << "  rejected: " << error.what() << '\n';
    }

    std::cout << "\nSuccessful insertion:\n";

    try {
        catalog.insert({"billing-service", "platform", "main"});
        std::cout << "  repositories: " << catalog.size() << '\n';
    } catch (const RepositoryError& error) {
        std::cout << "  repository failure: " << error.what() << '\n';
    }

    std::cout << "\nException propagation:\n";

    try {
        nestedOperation(catalog);
    } catch (const RepositoryNotFound& error) {
        std::cout << "  handled at application boundary: "
                  << error.what() << '\n';
    }

    std::cout << "\nConfiguration validation:\n";

    try {
        validateConfiguration({{"DEPLOYMENT_ENV", "unknown"}});
    } catch (const ConfigurationError& error) {
        std::cout << "  configuration rejected: "
                  << error.what() << '\n';
    }

    std::cout << "\nTransactional workflow:\n";

    try {
        DeploymentTransaction transaction(catalog);

        transaction.stage({"analytics-service", "data-team", "main"});
        transaction.stage({"billing-service", "platform", "main"});

        transaction.commit();
    } catch (const RepositoryError& error) {
        std::cout << "  transaction failed: " << error.what() << '\n';
        std::cout << "  repository count after rollback: "
                  << catalog.size() << '\n';
    }

    std::cout << "\nTransient failure recovery:\n";

    try {
        std::cout << "  " << retryStorageOperation(3) << '\n';
    } catch (const RepositoryError& error) {
        std::cout << "  unrecoverable storage failure: "
                  << error.what() << '\n';
    }

    return 0;
}
