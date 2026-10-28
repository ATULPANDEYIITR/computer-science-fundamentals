import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;

public class HashTableGovernanceDemo {

    enum PullRequestState {
        DRAFT,
        OPEN,
        MERGED,
        CLOSED
    }

    enum ReviewState {
        COMMENTED,
        CHANGES_REQUESTED,
        APPROVED,
        DISMISSED
    }

    enum CheckState {
        PENDING,
        PASSED,
        FAILED
    }

    record RepositoryKey(String organization, String name) {
        RepositoryKey {
            if (organization == null || organization.isBlank()) {
                throw new IllegalArgumentException("organization is required");
            }
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("repository name is required");
            }
        }
    }

    record Branch(String name, boolean protectedBranch) {
        Branch {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("branch name is required");
            }
        }
    }

    record Commit(String id, String message) {
        Commit {
            if (id == null || id.isBlank()) {
                throw new IllegalArgumentException("commit id is required");
            }
            if (message == null || message.isBlank()) {
                throw new IllegalArgumentException("commit message is required");
            }
        }
    }

    record ReviewPolicy(
            int requiredApprovals,
            boolean requirePassingChecks,
            boolean requireResolvedConversations,
            boolean requireEligibleReviewers) {

        ReviewPolicy {
            if (requiredApprovals < 0) {
                throw new IllegalArgumentException(
                        "required approvals cannot be negative");
            }
        }
    }

    record Reviewer(String username, Set<String> repositoryRoles) {
        Reviewer {
            if (username == null || username.isBlank()) {
                throw new IllegalArgumentException("username is required");
            }

            repositoryRoles = Set.copyOf(repositoryRoles);
        }

        boolean eligible() {
            return repositoryRoles.contains("maintainer")
                    || repositoryRoles.contains("reviewer");
        }
    }

    record Review(
            String reviewer,
            ReviewState state,
            boolean stale,
            List<String> comments) {

        Review {
            if (reviewer == null || reviewer.isBlank()) {
                throw new IllegalArgumentException("reviewer is required");
            }

            comments = List.copyOf(comments);
        }
    }

    record StatusCheck(String name, CheckState state) {
        StatusCheck {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("check name is required");
            }
        }
    }

    static final class PullRequest {
        private final String id;
        private final RepositoryKey repository;
        private final Branch source;
        private final Branch target;
        private final List<Commit> commits;
        private PullRequestState state;
        private boolean mergeConflict;
        private boolean conversationsResolved;

        PullRequest(
                String id,
                RepositoryKey repository,
                Branch source,
                Branch target,
                List<Commit> commits) {

            if (id == null || id.isBlank()) {
                throw new IllegalArgumentException("pull request id is required");
            }

            if (source.name().equals(target.name())) {
                throw new IllegalArgumentException(
                        "source and target branches must differ");
            }

            this.id = id;
            this.repository = repository;
            this.source = source;
            this.target = target;
            this.commits = new ArrayList<>(commits);
            this.state = PullRequestState.DRAFT;
        }

        void markReadyForReview() {
            requireState(PullRequestState.DRAFT);
            if (commits.isEmpty()) {
                throw new IllegalStateException(
                        "a pull request needs at least one commit");
            }
            state = PullRequestState.OPEN;
        }

        void markConflict(boolean conflict) {
            requireState(PullRequestState.OPEN);
            mergeConflict = conflict;
        }

        void resolveConversations() {
            requireState(PullRequestState.OPEN);
            conversationsResolved = true;
        }

        void close() {
            if (state == PullRequestState.MERGED) {
                throw new IllegalStateException(
                        "merged pull request cannot be reopened");
            }
            state = PullRequestState.CLOSED;
        }

        void reopen() {
            if (state != PullRequestState.CLOSED) {
                throw new IllegalStateException(
                        "only closed pull requests can be reopened");
            }
            state = PullRequestState.OPEN;
        }

        void merge() {
            requireState(PullRequestState.OPEN);
            state = PullRequestState.MERGED;
        }

        private void requireState(PullRequestState expected) {
            if (state != expected) {
                throw new IllegalStateException(
                        "expected " + expected + " but found " + state);
            }
        }

        String id() {
            return id;
        }

        RepositoryKey repository() {
            return repository;
        }

        Branch target() {
            return target;
        }

        PullRequestState state() {
            return state;
        }

        boolean mergeConflict() {
            return mergeConflict;
        }

        boolean conversationsResolved() {
            return conversationsResolved;
        }
    }

    /*
     * Policy index backed by a standard Java hash table.
     *
     * Java's HashMap handles bucket management, collision handling,
     * resizing, and treeification internally. The application code
     * remains responsible for validating domain keys and policy values.
     */
    static final class PolicyIndex {
        private final java.util.Map<RepositoryKey, ReviewPolicy> policies =
                new java.util.HashMap<>();

        void put(RepositoryKey repository, ReviewPolicy policy) {
            Objects.requireNonNull(repository);
            Objects.requireNonNull(policy);
            policies.put(repository, policy);
        }

        ReviewPolicy require(RepositoryKey repository) {
            ReviewPolicy policy = policies.get(repository);

            if (policy == null) {
                throw new IllegalArgumentException(
                        "no policy configured for " + repository);
            }

            return policy;
        }

        int size() {
            return policies.size();
        }
    }

    static final class GovernanceService {
        private final PolicyIndex policyIndex;

        GovernanceService(PolicyIndex policyIndex) {
            this.policyIndex = policyIndex;
        }

        boolean eligibleForMerge(
                PullRequest pullRequest,
                List<Review> reviews,
                List<Reviewer> reviewers,
                List<StatusCheck> checks) {

            ReviewPolicy policy =
                    policyIndex.require(pullRequest.repository());

            if (pullRequest.state() != PullRequestState.OPEN) {
                return false;
            }

            if (pullRequest.mergeConflict()) {
                return false;
            }

            if (policy.requireResolvedConversations()
                    && !pullRequest.conversationsResolved()) {
                return false;
            }

            if (policy.requirePassingChecks()
                    && checks.stream()
                    .anyMatch(check -> check.state() != CheckState.PASSED)) {
                return false;
            }

            Set<String> eligibleUsers = new HashSet<>();

            reviewers.stream()
                    .filter(Reviewer::eligible)
                    .map(Reviewer::username)
                    .forEach(eligibleUsers::add);

            long validApprovals = reviews.stream()
                    .filter(review ->
                            review.state() == ReviewState.APPROVED)
                    .filter(review -> !review.stale())
                    .filter(review -> eligibleUsers.contains(review.reviewer()))
                    .count();

            return validApprovals >= policy.requiredApprovals();
        }
    }

    private static Reviewer reviewer(
            String username,
            String role) {
        return new Reviewer(username, Set.of(role));
    }

    public static void main(String[] args) {
        RepositoryKey repository =
                new RepositoryKey("security-platform", "gateway");

        Branch feature = new Branch("feature/hash-table", false);
        Branch main = new Branch("main", true);

        List<Commit> commits = List.of(
                new Commit("a1", "Add chained hash table"),
                new Commit("b2", "Add collision metrics"));

        PullRequest pullRequest =
                new PullRequest(
                        "PR-184",
                        repository,
                        feature,
                        main,
                        commits);

        PolicyIndex policyIndex = new PolicyIndex();

        policyIndex.put(
                repository,
                new ReviewPolicy(
                        2,
                        true,
                        true,
                        true));

        GovernanceService service =
                new GovernanceService(policyIndex);

        pullRequest.markReadyForReview();

        List<Reviewer> reviewers = List.of(
                reviewer("asha", "reviewer"),
                reviewer("ravi", "maintainer"),
                reviewer("external", "guest"));

        List<Review> reviews = List.of(
                new Review(
                        "asha",
                        ReviewState.APPROVED,
                        false,
                        List.of("Hash distribution looks sound.")),
                new Review(
                        "ravi",
                        ReviewState.APPROVED,
                        false,
                        List.of("Resize threshold is reasonable.")),
                new Review(
                        "external",
                        ReviewState.APPROVED,
                        false,
                        List.of("Not an eligible repository reviewer.")));

        List<StatusCheck> checks = List.of(
                new StatusCheck("unit-tests", CheckState.PASSED),
                new StatusCheck("static-analysis", CheckState.PASSED),
                new StatusCheck("security-scan", CheckState.PASSED));

        pullRequest.resolveConversations();

        boolean eligible = service.eligibleForMerge(
                pullRequest,
                reviews,
                reviewers,
                checks);

        System.out.println("Repository: " + repository);
        System.out.println("Pull request: " + pullRequest.id());
        System.out.println("Policy entries: " + policyIndex.size());
        System.out.println("Merge eligible: " + eligible);

        if (!eligible) {
            throw new IllegalStateException(
                    "initial scenario should be merge eligible");
        }

        List<Review> staleReviews = List.of(
                reviews.get(0),
                new Review(
                        "ravi",
                        ReviewState.APPROVED,
                        true,
                        List.of("Approval is stale after new commits.")));

        boolean rejectedForStaleApproval =
                service.eligibleForMerge(
                        pullRequest,
                        staleReviews,
                        reviewers,
                        checks);

        System.out.println(
                "Eligible with stale approval: "
                        + rejectedForStaleApproval);

        if (rejectedForStaleApproval) {
            throw new IllegalStateException(
                    "stale approval must not satisfy the policy");
        }

        pullRequest.markConflict(true);

        boolean rejectedForConflict =
                service.eligibleForMerge(
                        pullRequest,
                        reviews,
                        reviewers,
                        checks);

        System.out.println(
                "Eligible with merge conflict: "
                        + rejectedForConflict);

        if (rejectedForConflict) {
            throw new IllegalStateException(
                    "merge conflict must block eligibility");
        }

        pullRequest.markConflict(false);
        pullRequest.close();
        pullRequest.reopen();

        System.out.println(
                "State after close/reopen: "
                        + pullRequest.state());

        try {
            pullRequest.merge();
            System.out.println("Unexpected merge without rechecking policy.");
        } catch (IllegalStateException error) {
            System.out.println(
                    "State transition remains controlled: "
                            + error.getMessage());
        }

        boolean finalEligibility =
                service.eligibleForMerge(
                        pullRequest,
                        reviews,
                        reviewers,
                        checks);

        if (finalEligibility) {
            pullRequest.merge();
        }

        System.out.println(
                "Final state: " + pullRequest.state());
        System.out.println("Assertions passed.");
    }
}
