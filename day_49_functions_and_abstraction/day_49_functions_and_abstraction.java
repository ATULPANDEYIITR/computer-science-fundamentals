import java.util.ArrayList;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

/*
 * Enterprise-oriented demonstration of Functions and Abstraction.
 *
 * The domain is a repository governance service. The abstractions are
 * deliberately separated: pull-request state belongs to PullRequest,
 * review decisions belong to Review, repository rules belong to
 * BranchProtectionPolicy, and merge evaluation belongs to GovernanceService.
 */
public class FunctionsAndAbstraction {

    enum PullRequestState {
        DRAFT,
        OPEN,
        CLOSED,
        MERGED
    }

    enum ReviewState {
        COMMENTED,
        APPROVED,
        CHANGES_REQUESTED
    }

    record Review(String reviewer, ReviewState state, String comment) {
        public Review {
            if (reviewer == null || reviewer.isBlank()) {
                throw new IllegalArgumentException("reviewer is required");
            }

            if (comment == null) {
                throw new IllegalArgumentException("comment cannot be null");
            }
        }
    }

    record StatusCheck(String name, boolean passed) {
        public StatusCheck {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("status check name is required");
            }
        }
    }

    record BranchProtectionPolicy(
            String branch,
            int requiredApprovals,
            boolean requirePassingChecks,
            boolean requireResolvedConversations,
            boolean allowForcePush,
            boolean allowDirectPush
    ) {
        public BranchProtectionPolicy {
            if (branch == null || branch.isBlank()) {
                throw new IllegalArgumentException("protected branch is required");
            }

            if (requiredApprovals < 0) {
                throw new IllegalArgumentException(
                        "required approvals cannot be negative"
                );
            }
        }
    }

    static final class PullRequest {
        private final int number;
        private final String author;
        private final String sourceBranch;
        private final String targetBranch;
        private PullRequestState state = PullRequestState.DRAFT;
        private final List<String> commits = new ArrayList<>();
        private final List<Review> reviews = new ArrayList<>();
        private final Map<String, StatusCheck> checks = new HashMap<>();
        private int unresolvedConversations;
        private boolean mergeConflict;

        PullRequest(
                int number,
                String author,
                String sourceBranch,
                String targetBranch
        ) {
            if (number <= 0) {
                throw new IllegalArgumentException("number must be positive");
            }

            this.number = number;
            this.author = requireText(author, "author");
            this.sourceBranch = requireText(sourceBranch, "source branch");
            this.targetBranch = requireText(targetBranch, "target branch");
        }

        void addCommit(String sha) {
            if (state == PullRequestState.CLOSED ||
                    state == PullRequestState.MERGED) {
                throw new IllegalStateException(
                        "cannot add commits after closure"
                );
            }

            if (sha == null || !sha.matches("[0-9a-f]{7,40}")) {
                throw new IllegalArgumentException("invalid commit identifier");
            }

            commits.add(sha);
        }

        void open() {
            if (state != PullRequestState.DRAFT) {
                throw new IllegalStateException(
                        "only a draft pull request can become open"
                );
            }

            if (commits.isEmpty()) {
                throw new IllegalStateException(
                        "pull request requires at least one commit"
                );
            }

            state = PullRequestState.OPEN;
        }

        void addReview(Review review) {
            requireOpen();
            reviews.add(review);
        }

        void recordStatusCheck(StatusCheck check) {
            checks.put(check.name(), check);
        }

        void setUnresolvedConversations(int count) {
            if (count < 0) {
                throw new IllegalArgumentException(
                        "conversation count cannot be negative"
                );
            }

            unresolvedConversations = count;
        }

        void setMergeConflict(boolean conflict) {
            mergeConflict = conflict;
        }

        void markMerged() {
            if (state != PullRequestState.OPEN) {
                throw new IllegalStateException(
                        "only an open pull request can be merged"
                );
            }

            state = PullRequestState.MERGED;
        }

        private void requireOpen() {
            if (state != PullRequestState.OPEN) {
                throw new IllegalStateException(
                        "operation requires an open pull request"
                );
            }
        }

        private static String requireText(String value, String field) {
            if (value == null || value.isBlank()) {
                throw new IllegalArgumentException(field + " is required");
            }

            return value;
        }

        int number() {
            return number;
        }

        String author() {
            return author;
        }

        String sourceBranch() {
            return sourceBranch;
        }

        String targetBranch() {
            return targetBranch;
        }

        PullRequestState state() {
            return state;
        }

        List<String> commits() {
            return List.copyOf(commits);
        }

        List<Review> reviews() {
            return List.copyOf(reviews);
        }

        Map<String, StatusCheck> checks() {
            return Map.copyOf(checks);
        }

        int unresolvedConversations() {
            return unresolvedConversations;
        }

        boolean hasMergeConflict() {
            return mergeConflict;
        }
    }

    record MergeDecision(boolean eligible, List<String> reasons) {
        MergeDecision {
            reasons = List.copyOf(reasons);
        }
    }

    static final class GovernanceService {
        private final BranchProtectionPolicy policy;

        GovernanceService(BranchProtectionPolicy policy) {
            this.policy = policy;
        }

        MergeDecision evaluate(PullRequest pullRequest) {
            List<String> failures = new ArrayList<>();

            if (!pullRequest.targetBranch().equals(policy.branch())) {
                failures.add("target branch is not protected by this policy");
            }

            if (pullRequest.state() != PullRequestState.OPEN) {
                failures.add("pull request is not open");
            }

            if (pullRequest.commits().isEmpty()) {
                failures.add("pull request contains no commits");
            }

            if (pullRequest.hasMergeConflict()) {
                failures.add("merge conflict must be resolved");
            }

            Set<String> approvedReviewers = pullRequest.reviews()
                    .stream()
                    .filter(review -> review.state() == ReviewState.APPROVED)
                    .map(Review::reviewer)
                    .collect(Collectors.toSet());

            boolean changesRequested = pullRequest.reviews()
                    .stream()
                    .anyMatch(
                            review ->
                                    review.state() == ReviewState.CHANGES_REQUESTED
                    );

            if (changesRequested) {
                failures.add("a reviewer has requested changes");
            }

            if (approvedReviewers.size() < policy.requiredApprovals()) {
                failures.add("required approval count has not been reached");
            }

            if (policy.requirePassingChecks()) {
                boolean checksPass = !pullRequest.checks().isEmpty() &&
                        pullRequest.checks()
                                .values()
                                .stream()
                                .allMatch(StatusCheck::passed);

                if (!checksPass) {
                    failures.add("required status checks are not passing");
                }
            }

            if (policy.requireResolvedConversations() &&
                    pullRequest.unresolvedConversations() > 0) {
                failures.add("review conversations remain unresolved");
            }

            return new MergeDecision(failures.isEmpty(), failures);
        }

        void merge(PullRequest pullRequest) {
            MergeDecision decision = evaluate(pullRequest);

            if (!decision.eligible()) {
                throw new IllegalStateException(
                        "merge rejected: " +
                                String.join("; ", decision.reasons())
                );
            }

            pullRequest.markMerged();
        }
    }

    // A generic function abstraction keeps aggregation logic reusable while
    // preserving compile-time type safety.
    static <T> long countMatching(
            List<T> values,
            java.util.function.Predicate<T> predicate
    ) {
        return values.stream().filter(predicate).count();
    }

    static String formatDecision(
            PullRequest pullRequest,
            MergeDecision decision
    ) {
        if (decision.eligible()) {
            return "PR #" + pullRequest.number() + " is mergeable";
        }

        return "PR #" + pullRequest.number() +
                " is blocked: " +
                String.join(", ", decision.reasons());
    }

    static void printHeader(String title) {
        System.out.println("\n" + "=".repeat(72));
        System.out.println(title);
        System.out.println("=".repeat(72));
    }

    public static void main(String[] args) {
        printHeader("Enterprise Repository Governance");

        BranchProtectionPolicy policy = new BranchProtectionPolicy(
                "main",
                2,
                true,
                true,
                false,
                false
        );

        GovernanceService governance = new GovernanceService(policy);

        PullRequest approvedRequest = new PullRequest(
                801,
                "alice",
                "feature/auth-policy",
                "main"
        );

        approvedRequest.addCommit("abc1234");
        approvedRequest.addCommit("def5678");
        approvedRequest.open();

        approvedRequest.addReview(
                new Review(
                        "security-reviewer",
                        ReviewState.APPROVED,
                        "Authorization boundaries are explicit."
                )
        );

        approvedRequest.addReview(
                new Review(
                        "platform-reviewer",
                        ReviewState.APPROVED,
                        "Failure handling is consistent."
                )
        );

        approvedRequest.recordStatusCheck(
                new StatusCheck("unit-tests", true)
        );

        approvedRequest.recordStatusCheck(
                new StatusCheck("security-scan", true)
        );

        approvedRequest.setUnresolvedConversations(0);

        MergeDecision approvedDecision =
                governance.evaluate(approvedRequest);

        System.out.println(formatDecision(
                approvedRequest,
                approvedDecision
        ));

        if (approvedDecision.eligible()) {
            governance.merge(approvedRequest);
        }

        System.out.println(
                "Post-merge state: " + approvedRequest.state()
        );

        printHeader("Blocked Request");

        PullRequest blockedRequest = new PullRequest(
                802,
                "bob",
                "feature/payment-policy",
                "main"
        );

        blockedRequest.addCommit("123abcd");
        blockedRequest.open();

        blockedRequest.addReview(
                new Review(
                        "platform-reviewer",
                        ReviewState.APPROVED,
                        "Partial approval."
                )
        );

        blockedRequest.addReview(
                new Review(
                        "security-reviewer",
                        ReviewState.CHANGES_REQUESTED,
                        "Input authorization requires revision."
                )
        );

        blockedRequest.recordStatusCheck(
                new StatusCheck("unit-tests", true)
        );

        blockedRequest.recordStatusCheck(
                new StatusCheck("security-scan", false)
        );

        blockedRequest.setUnresolvedConversations(2);

        MergeDecision blockedDecision =
                governance.evaluate(blockedRequest);

        System.out.println(formatDecision(
                blockedRequest,
                blockedDecision
        ));

        System.out.println("\nBlocking reasons:");
        blockedDecision.reasons()
                .forEach(reason -> System.out.println("- " + reason));

        printHeader("Functional Analysis");

        List<Review> reviews = List.of(
                new Review("alice", ReviewState.APPROVED, "Approved"),
                new Review("bob", ReviewState.COMMENTED, "Question"),
                new Review("carol", ReviewState.APPROVED, "Approved")
        );

        long approvals = countMatching(
                reviews,
                review -> review.state() == ReviewState.APPROVED
        );

        System.out.println("Approval records: " + approvals);

        Set<ReviewState> activeReviewStates =
                EnumSet.of(
                        ReviewState.APPROVED,
                        ReviewState.CHANGES_REQUESTED
                );

        System.out.println(
                "Decision-bearing states: " + activeReviewStates
        );

        printHeader("Abstraction Boundary");

        System.out.println(
                "PullRequest controls lifecycle state and domain data."
        );
        System.out.println(
                "Review records represent independent reviewer decisions."
        );
        System.out.println(
                "BranchProtectionPolicy expresses repository governance."
        );
        System.out.println(
                "GovernanceService converts those facts into a merge decision."
        );

        printHeader("Validation Failure");

        try {
            PullRequest invalid = new PullRequest(
                    803,
                    "carol",
                    "feature/test",
                    "main"
            );

            invalid.open();
        } catch (IllegalStateException exception) {
            System.out.println(
                    "Expected failure: " + exception.getMessage()
            );
        }
    }
}
