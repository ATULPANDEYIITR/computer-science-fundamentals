import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/*
 * Enterprise repository deployment service.
 *
 * The model separates:
 * - validation failures
 * - configuration failures
 * - persistence failures
 * - missing resources
 * - transient failures
 *
 * Checked exceptions represent recoverable service-boundary failures.
 * Domain state transitions are validated before mutation.
 */

public class ErrorHandlingEnterpriseDemo {

    public enum RepositoryState {
        ACTIVE,
        ARCHIVED
    }

    public record Repository(
            String name,
            String owner,
            String defaultBranch,
            RepositoryState state) {

        public Repository {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("Repository name is required.");
            }
            if (owner == null || owner.isBlank()) {
                throw new IllegalArgumentException("Repository owner is required.");
            }
            if (defaultBranch == null || defaultBranch.isBlank()) {
                throw new IllegalArgumentException(
                        "Default branch is required.");
            }
            Objects.requireNonNull(state, "Repository state is required.");
        }

        public Repository archive() throws DomainValidationException {
            if (state == RepositoryState.ARCHIVED) {
                throw new DomainValidationException(
                        "Repository is already archived.");
            }

            return new Repository(
                    name,
                    owner,
                    defaultBranch,
                    RepositoryState.ARCHIVED);
        }
    }

    public static class DomainValidationException extends Exception {
        public DomainValidationException(String message) {
            super(message);
        }
    }

    public static class RepositoryNotFoundException extends Exception {
        public RepositoryNotFoundException(String message) {
            super(message);
        }
    }

    public static class PersistenceException extends Exception {
        public PersistenceException(String message, Throwable cause) {
            super(message, cause);
        }

        public PersistenceException(String message) {
            super(message);
        }
    }

    public static class TransientPersistenceException
            extends PersistenceException {

        public TransientPersistenceException(String message) {
            super(message);
        }
    }

    public interface RepositoryRepository {
        void save(Repository repository) throws PersistenceException;

        Repository find(String name) throws RepositoryNotFoundException;
    }

    public static final class InMemoryRepositoryRepository
            implements RepositoryRepository {

        private final Map<String, Repository> data = new HashMap<>();
        private int transientFailuresRemaining;

        public InMemoryRepositoryRepository(int transientFailuresRemaining) {
            if (transientFailuresRemaining < 0) {
                throw new IllegalArgumentException(
                        "Failure count cannot be negative.");
            }
            this.transientFailuresRemaining = transientFailuresRemaining;
        }

        @Override
        public void save(Repository repository) throws PersistenceException {
            Objects.requireNonNull(repository, "repository");

            if (transientFailuresRemaining > 0) {
                transientFailuresRemaining--;
                throw new TransientPersistenceException(
                        "Temporary repository storage failure.");
            }

            if (data.containsKey(repository.name())) {
                throw new PersistenceException(
                        "Repository already exists: " + repository.name());
            }

            data.put(repository.name(), repository);
        }

        @Override
        public Repository find(String name)
                throws RepositoryNotFoundException {

            Repository repository = data.get(name);

            if (repository == null) {
                throw new RepositoryNotFoundException(
                        "Repository not found: " + name);
            }

            return repository;
        }
    }

    public static final class RepositoryService {

        private final RepositoryRepository repositoryRepository;

        public RepositoryService(RepositoryRepository repositoryRepository) {
            this.repositoryRepository =
                    Objects.requireNonNull(repositoryRepository);
        }

        public void register(Repository repository)
                throws DomainValidationException, PersistenceException {

            if (repository.state() != RepositoryState.ACTIVE) {
                throw new DomainValidationException(
                        "Only active repositories can be registered.");
            }

            saveWithRetry(repository, 3);
        }

        public Repository archive(String name)
                throws RepositoryNotFoundException,
                DomainValidationException {

            Repository existing = repositoryRepository.find(name);
            Repository archived = existing.archive();

            try {
                repositoryRepository.save(archived);
            } catch (PersistenceException exception) {
                throw new DomainValidationException(
                        "Repository could not be archived: "
                                + exception.getMessage());
            }

            return archived;
        }

        private void saveWithRetry(
                Repository repository,
                int maximumAttempts)
                throws PersistenceException {

            PersistenceException lastFailure = null;

            for (int attempt = 1;
                 attempt <= maximumAttempts;
                 attempt++) {

                try {
                    repositoryRepository.save(repository);
                    return;
                } catch (TransientPersistenceException exception) {
                    lastFailure = exception;

                    if (attempt == maximumAttempts) {
                        throw exception;
                    }
                }
            }

            throw new PersistenceException(
                    "Persistence failed.",
                    lastFailure);
        }
    }

    public static Map<String, String> loadConfiguration(
            Map<String, String> environment) {

        String deploymentEnvironment =
                environment.get("DEPLOYMENT_ENV");

        if (deploymentEnvironment == null ||
                deploymentEnvironment.isBlank()) {
            throw new IllegalStateException(
                    "DEPLOYMENT_ENV is not configured.");
        }

        return Collections.unmodifiableMap(
                Map.of("DEPLOYMENT_ENV", deploymentEnvironment));
    }

    public static void main(String[] args) {
        System.out.println("Configuration validation:");

        try {
            loadConfiguration(Map.of());
        } catch (IllegalStateException exception) {
            System.out.println("  rejected: " + exception.getMessage());
        }

        System.out.println("\nRepository registration:");

        InMemoryRepositoryRepository repositoryRepository =
                new InMemoryRepositoryRepository(2);

        RepositoryService service =
                new RepositoryService(repositoryRepository);

        Repository repository = new Repository(
                "billing-service",
                "platform-team",
                "main",
                RepositoryState.ACTIVE);

        try {
            service.register(repository);
            System.out.println("  repository registered.");
        } catch (PersistenceException | DomainValidationException exception) {
            System.out.println(
                    "  registration failed: " + exception.getMessage());
        }

        System.out.println("\nException propagation:");

        try {
            repositoryRepository.find("missing-service");
        } catch (RepositoryNotFoundException exception) {
            System.out.println(
                    "  handled at service boundary: "
                            + exception.getMessage());
        }

        System.out.println("\nInvalid state transition:");

        try {
            Repository archived = repository.archive();
            service.register(archived);
        } catch (DomainValidationException exception) {
            System.out.println(
                    "  policy rejected: " + exception.getMessage());
        } catch (PersistenceException exception) {
            System.out.println(
                    "  persistence failed: " + exception.getMessage());
        }

        System.out.println("\nCollection-based validation:");

        List<Repository> repositories = new ArrayList<>();
        repositories.add(repository);
        repositories.add(new Repository(
                "analytics-service",
                "data-team",
                "main",
                RepositoryState.ACTIVE));

        repositories.stream()
                .filter(item -> item.state() == RepositoryState.ACTIVE)
                .map(Repository::name)
                .sorted()
                .forEach(name ->
                        System.out.println("  active: " + name));
    }
}
