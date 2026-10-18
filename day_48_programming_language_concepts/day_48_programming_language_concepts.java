import java.util.ArrayList;
import java.util.EnumSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.function.Predicate;
import java.util.stream.Collectors;

/*
 * Enterprise-oriented model for scope, binding, lifetime, and type systems.
 *
 * Java provides static compile-time typing, lexical scope, deterministic
 * initialization/finalization rules for ordinary objects, and garbage
 * collection for memory management. External resources still require
 * explicit lifecycle management.
 */
public class ProgrammingLanguageConcepts {

    enum PullRequestState {
        DRAFT,
        OPEN,
        CLOSED,
        MERGED
    }

    enum ReviewState {
        PENDING,
        APPROVED,
        CHANGES_REQUESTED
    }

    enum CheckState {
        PENDING,
        PASSED,
        FAILED
    }

    record StatusCheck(String name, CheckState state) {
        StatusCheck {
            Objects.requireNonNull(name, "name");
            Objects.requireNonNull(state, "state");

            if (name.isBlank()) {
                throw new IllegalArgumentException("Check name cannot be blank");
            }
        }
    }

    record Review(
        String reviewer,
        ReviewState state,
        String comment
    ) {
        Review {
            Objects.requireNonNull(reviewer, "reviewer");
            Objects.requireNonNull(state, "state");
            Objects.requireNonNull(comment, "comment");

            if (reviewer.isBlank()) {
                throw new IllegalArgumentException("Reviewer is required");
            }
        }
    }

    record PullRequest(
        int number,
        String author,
        String sourceBranch,
        String targetBranch,
        PullRequestState state,
        List<Review> reviews,
        List<StatusCheck> checks
    ) {
        PullRequest {
            if (number <= 0) {
                throw new IllegalArgumentException("PR number must be positive");
            }

            Objects.requireNonNull(author, "author");
            Objects.requireNonNull(sourceBranch, "sourceBranch");
            Objects.requireNonNull(targetBranch, "targetBranch");
            Objects.requireNonNull(state, "state");

            if (sourceBranch.equals(targetBranch)) {
                throw new IllegalArgumentException(
                    "Source and target branches must differ"
                );
            }

            reviews = List.copyOf(reviews);
            checks = List.copyOf(checks);
        }
    }

    record BranchProtection(
        String branchName,
        int requiredApprovals,
        boolean requirePassingChecks,
        boolean allowDirectPush,
        boolean allowForcePush
    ) {
        BranchProtection {
            Objects.requireNonNull(branchName, "branchName");

            if (branchName.isBlank()) {
                throw new IllegalArgumentException("Branch name is required");
            }

            if (requiredApprovals < 0) {
                throw new IllegalArgumentException(
                    "Approval requirement cannot be negative"
                );
            }

            if (!allowDirectPush && allowForcePush) {
                throw new IllegalArgumentException(
                    "A protected branch cannot enable force-push while " +
                    "direct pushes are disabled in this policy model"
                );
            }
        }
    }

    static final class MergeDecision {
        private final boolean eligible;
        private final List<String> reasons;

        MergeDecision(boolean eligible, List<String> reasons) {
            this.eligible = eligible;
            this.reasons = List.copyOf(reasons);
        }

        boolean eligible() {
            return eligible;
        }

        List<String> reasons() {
            return reasons;
        }

        @Override
        public String toString() {
            return "MergeDecision{" +
                "eligible=" + eligible +
                ", reasons=" + reasons +
                '}';
        }
    }

    interface ReviewRule {
        boolean accepts(PullRequest pullRequest, Review review);
        String failureReason();
    }

    static final class NoSelfApprovalRule implements ReviewRule {
        @Override
        public boolean accepts(PullRequest pullRequest, Review review) {
            return !pullRequest.author().equals(review.reviewer());
        }

        @Override
        public String failureReason() {
            return "Author cannot satisfy an approval requirement with self-review";
        }
    }

    static final class ReviewEligibilityService {
        private final List<ReviewRule> rules;

        ReviewEligibilityService(List<ReviewRule> rules) {
            this.rules = List.copyOf(rules);
        }

        boolean isEligible(PullRequest pr, Review review) {
            return rules.stream().allMatch(rule -> rule.accepts(pr, review));
        }

        List<String> failures(PullRequest pr, Review review) {
            return rules.stream()
                .filter(rule -> !rule.accepts(pr, review))
                .map(ReviewRule::failureReason)
                .toList();
        }
    }

    static final class MergeEligibilityService {

        MergeDecision evaluate(
            PullRequest pullRequest,
            BranchProtection protection,
            ReviewEligibilityService reviewService
        ) {
            List<String> failures = new ArrayList<>();

            if (pullRequest.state() != PullRequestState.OPEN) {
                failures.add("Pull Request must be open");
            }

            if (!pullRequest.targetBranch().equals(protection.branchName())) {
                failures.add("Pull Request does not target the protected branch");
            }

            if (protection.requirePassingChecks()
                    && pullRequest.checks().stream()
                        .anyMatch(check -> check.state() != CheckState.PASSED)) {
                failures.add("At least one required status check is not passed");
            }

            long validApprovals = pullRequest.reviews().stream()
                .filter(review -> review.state() == ReviewState.APPROVED)
                .filter(review -> reviewService.isEligible(pullRequest, review))
                .map(Review::reviewer)
                .distinct()
                .count();

            if (validApprovals < protection.requiredApprovals()) {
                failures.add(
                    "Required approvals: " +
                    protection.requiredApprovals() +
                    ", valid approvals: " +
                    validApprovals
                );
            }

            /*
             * A review that requested changes is retained in the history but
             * does not count as an approval. This separates participation
             * from the specific state needed by the merge policy.
             */
            if (pullRequest.reviews().stream()
                    .anyMatch(review ->
                        review.state() == ReviewState.CHANGES_REQUESTED)) {
                failures.add("A reviewer currently requests changes");
            }

            return new MergeDecision(failures.isEmpty(), failures);
        }
    }

    static final class ResourceSession implements AutoCloseable {
        private final String resourceName;
        private boolean closed;

        ResourceSession(String resourceName) {
            this.resourceName = Objects.requireNonNull(resourceName);
            this.closed = false;
            System.out.println("Opened resource: " + resourceName);
        }

        void execute(String operation) {
            if (closed) {
                throw new IllegalStateException(
                    "Resource has already been closed"
                );
            }

            System.out.println(
                "Executing " + operation + " on " + resourceName
            );
        }

        @Override
        public void close() {
            if (!closed) {
                closed = true;
                System.out.println("Closed resource: " + resourceName);
            }
        }
    }

    private static void scopeAndBindingDemo() {
        String repository = "identity-service";

        {
            String branch = "main";
            System.out.println("Inner lexical binding: " + branch);
            System.out.println("Outer binding remains visible: " + repository);
        }

        // branch is no longer in scope here.
        System.out.println("Outer binding after block: " + repository);
    }

    private static void staticTypingDemo() {
        int approvalRequirement = 2;
        String branchName = "main";

        System.out.println(
            "Statically typed values: " +
            approvalRequirement + " approvals for " + branchName
        );

        /*
         * Java rejects incompatible assignments at compile time.
         * For example, assigning a String directly to approvalRequirement
         * would not compile. The compiler therefore participates in the
         * type-safety boundary before execution.
         */
    }

    private static void streamBasedTypeFiltering() {
        List<Object> values = List.of(
            "main",
            42,
            "release",
            17
        );

        List<String> branchNames = values.stream()
            .filter(String.class::isInstance)
            .map(String.class::cast)
            .collect(Collectors.toList());

        System.out.println("Strings selected by runtime type:");
        branchNames.forEach(System.out::println);
    }

    private static PullRequest createPullRequest() {
        return new PullRequest(
            418,
            "atul",
            "feature/auth-policy",
            "main",
            PullRequestState.OPEN,
            List.of(
                new Review(
                    "reviewer-a",
                    ReviewState.APPROVED,
                    "Authorization rules verified"
                ),
                new Review(
                    "reviewer-b",
                    ReviewState.APPROVED,
                    "Failure paths are covered"
                ),
                new Review(
                    "security-reviewer",
                    ReviewState.CHANGES_REQUESTED,
                    "Threat model needs clarification"
                )
            ),
            List.of(
                new StatusCheck("unit-tests", CheckState.PASSED),
                new StatusCheck("integration-tests", CheckState.PASSED),
                new StatusCheck("security-scan", CheckState.PASSED)
            )
        );
    }

    private static void enterpriseGovernanceDemo() {
        PullRequest pullRequest = createPullRequest();

        BranchProtection protection = new BranchProtection(
            "main",
            2,
            true,
            false,
            false
        );

        ReviewEligibilityService reviewService =
            new ReviewEligibilityService(
                List.of(new NoSelfApprovalRule())
            );

        MergeEligibilityService mergeService =
            new MergeEligibilityService();

        MergeDecision decision = mergeService.evaluate(
            pullRequest,
            protection,
            reviewService
        );

        System.out.println("\nEnterprise merge decision");
        System.out.println(decision);

        Review selfApproval = new Review(
            "atul",
            ReviewState.APPROVED,
            "Self-approved"
        );

        System.out.println(
            "Self-approval valid: " +
            reviewService.isEligible(pullRequest, selfApproval)
        );

        System.out.println(
            "Self-approval failures: " +
            reviewService.failures(pullRequest, selfApproval)
        );
    }

    private static void lifetimeDemo() {
        /*
         * try-with-resources binds resource lifetime to the lexical scope.
         * close() executes even when the body completes through an exception.
         */
        try (ResourceSession session =
                 new ResourceSession("repository-policy-store")) {
            session.execute("load branch policy");
        }

        try {
            ResourceSession session =
                new ResourceSession("temporary-store");
            session.close();
            session.execute("invalid operation");
        } catch (IllegalStateException exception) {
            System.out.println(
                "Lifecycle failure: " + exception.getMessage()
            );
        }
    }

    public static void main(String[] args) {
        scopeAndBindingDemo();
        staticTypingDemo();
        streamBasedTypeFiltering();
        lifetimeDemo();
        enterpriseGovernanceDemo();

        System.out.println("\nProgram completed.");
    }
}
