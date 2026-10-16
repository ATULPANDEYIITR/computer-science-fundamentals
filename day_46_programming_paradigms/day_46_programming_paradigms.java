import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeSet;
import java.util.stream.Collectors;

/*
 * Enterprise repository governance.
 *
 * Java 17 implementation using explicit domain types, immutable records,
 * validated state transitions, and a policy evaluation service.
 *
 * Run:
 *   javac ProgrammingParadigms.java
 *   java ProgrammingParadigms
 */

public class ProgrammingParadigms {

    enum ChangeKind {
        FEATURE, BUGFIX, SECURITY, DOCUMENTATION
    }

    enum ReviewState {
        COMMENTED, APPROVED, CHANGES_REQUESTED
    }

    enum PullRequestState {
        DRAFT, OPEN, CLOSED, MERGED
    }

    enum MergeStrategy {
        MERGE_COMMIT, SQUASH, REBASE
    }

    static final class DomainException extends RuntimeException {
        DomainException(String message) {
            super(message);
        }
    }

    record Commit(
            String id,
            String author,
            Set<String> changedFiles,
            int additions,
            int deletions,
            ChangeKind kind
    ) {
        Commit {
            requireText(id, "Commit ID");
            requireText(author, "Author");
            Objects.requireNonNull(kind, "Change kind is required");

            if (changedFiles == null || changedFiles.isEmpty()) {
                throw new DomainException("A commit must change at least one file.");
            }

            changedFiles = Collections.unmodifiableSet(
                    new TreeSet<>(changedFiles)
            );

            for (String file : changedFiles) {
                requireText(file, "File path");
                if (file.startsWith("/") ||
                        List.of(file.split("/")).contains("..")) {
                    throw new DomainException(
                            "Changed file path escapes the repository."
                    );
                }
            }

            if (additions < 0 || deletions < 0) {
                throw new DomainException(
                        "Commit line counts cannot be negative."
                );
            }
        }

        int netChange() {
            return additions - deletions;
        }
    }

    record ReviewComment(
            String id,
            String filePath,
            int line,
            String body,
            boolean resolved
    ) {
        ReviewComment {
            requireText(id, "Comment ID");
            requireText(filePath, "Comment file path");
            requireText(body, "Comment body");
            if (line < 1) {
                throw new DomainException("Comment line must be positive.");
            }
        }
    }

    record Review(
            String reviewer,
            String commitId,
            ReviewState state,
            boolean dismissed,
            Instant submittedAt,
            List<ReviewComment> comments
    ) {
        Review {
            requireText(reviewer, "Reviewer");
            requireText(commitId, "Reviewed commit");
            Objects.requireNonNull(state, "Review state is required");
            Objects.requireNonNull(submittedAt, "Submission time is required");
            comments = List.copyOf(comments);
        }
    }

    record BranchProtection(
            String branchName,
            int requiredApprovals,
            Set<String> requiredChecks,
            boolean prohibitDirectPush,
            boolean prohibitForcePush,
            boolean prohibitDeletion,
            boolean requireResolvedConversations,
            boolean requireLinearHistory,
            boolean allowAdministratorBypass,
            Set<String> eligibleReviewers
    ) {
        BranchProtection {
            requireText(branchName, "Protected branch");
            if (requiredApprovals < 0) {
                throw new DomainException(
                        "Required approvals cannot be negative."
                );
            }
            requiredChecks = Set.copyOf(requiredChecks);
            eligibleReviewers = Set.copyOf(eligibleReviewers);
        }
    }

    record MergeDecision(
            boolean eligible,
            List<String> reasons,
            int eligibleApprovals,
            Set<String> failedChecks
    ) {
        MergeDecision {
            reasons = List.copyOf(reasons);
            failedChecks = Set.copyOf(failedChecks);
        }
    }

    static final class PullRequest {
        private final int number;
        private final String title;
        private final String sourceBranch;
        private final String targetBranch;
        private final List<Commit> commits;
        private final List<Review> reviews = new ArrayList<>();
        private final Map<String, Boolean> statusChecks = new LinkedHashMap<>();
        private final Set<String> resolvedConversationIds = new HashSet<>();
        private final Set<String> unresolvedConversationIds = new HashSet<>();
        private PullRequestState state;
        private long baseRevision;

        PullRequest(
                int number,
                String title,
                String sourceBranch,
                String targetBranch,
                List<Commit> commits,
                PullRequestState initialState
        ) {
            if (number <= 0) {
                throw new DomainException("Pull request number must be positive.");
            }
            this.number = number;
            this.title = requireText(title, "Pull request title");
            this.sourceBranch = requireText(sourceBranch, "Source branch");
            this.targetBranch = requireText(targetBranch, "Target branch");

            if (sourceBranch.equals(targetBranch)) {
                throw new DomainException(
                        "Source and target branches must differ."
                );
            }

            if (commits == null || commits.isEmpty()) {
                throw new DomainException(
                        "A pull request requires at least one commit."
                );
            }

            this.commits = List.copyOf(commits);
            this.state = Objects.requireNonNull(initialState);
        }

        void addReview(Review review) {
            ensureOpen();
            Set<String> commitIds = commits.stream()
                    .map(Commit::id)
                    .collect(Collectors.toSet());

            if (!commitIds.contains(review.commitId())) {
                throw new DomainException(
                        "Review references an unknown commit."
                );
            }
            reviews.add(review);
        }

        void recordCheck(String name, boolean passed) {
            ensureOpen();
            statusChecks.put(requireText(name, "Check name"), passed);
        }

        void openConversation(String id) {
            ensureOpen();
            requireText(id, "Conversation ID");
            if (resolvedConversationIds.contains(id) ||
                    !unresolvedConversationIds.add(id)) {
                throw new DomainException(
                        "Conversation already exists."
                );
            }
        }

        void resolveConversation(String id) {
            ensureOpen();
            if (!unresolvedConversationIds.remove(id)) {
                throw new DomainException(
                        "No unresolved conversation exists with that ID."
                );
            }
            resolvedConversationIds.add(id);
        }

        void synchronizeBase(long revision) {
            ensureOpen();
            if (revision <= baseRevision) {
                throw new DomainException(
                        "Base revision must move forward."
                );
            }
            baseRevision = revision;
        }

        void markReady() {
            if (state != PullRequestState.DRAFT) {
                throw new DomainException(
                        "Only a draft can transition to open."
                );
            }
            state = PullRequestState.OPEN;
        }

        void close() {
            ensureOpen();
            state = PullRequestState.CLOSED;
        }

        void reopen() {
            if (state != PullRequestState.CLOSED) {
                throw new DomainException(
                        "Only a closed pull request can be reopened."
                );
            }
            state = PullRequestState.OPEN;
        }

        void merge(MergeDecision decision, MergeStrategy strategy) {
            ensureOpen();
            if (!decision.eligible()) {
                throw new DomainException(
                        "Merge blocked: " + String.join("; ", decision.reasons())
                );
            }
            Objects.requireNonNull(strategy);
            state = PullRequestState.MERGED;
        }

        private void ensureOpen() {
            if (state != PullRequestState.OPEN) {
                throw new DomainException(
                        "Operation requires an open pull request."
                );
            }
        }

        int number() {
            return number;
        }

        String title() {
            return title;
        }

        String targetBranch() {
            return targetBranch;
        }

        PullRequestState state() {
            return state;
        }

        List<Commit> commits() {
            return commits;
        }

        List<Review> reviews() {
            return List.copyOf(reviews);
        }

        Map<String, Boolean> statusChecks() {
            return Collections.unmodifiableMap(statusChecks);
        }

        Set<String> unresolvedConversations() {
            return Set.copyOf(unresolvedConversationIds);
        }

        long baseRevision() {
            return baseRevision;
        }
    }

    static final class MergeEligibilityService {
        MergeDecision evaluate(
                PullRequest pullRequest,
                BranchProtection policy,
                boolean administrator,
                boolean proposedHistoryIsLinear
        ) {
            List<String> reasons = new ArrayList<>();
            Set<String> failedChecks = new TreeSet<>();

            boolean protectedTarget =
                    policy.branchName().equals(pullRequest.targetBranch());

            if (pullRequest.state() != PullRequestState.OPEN) {
                reasons.add("Pull request is not open.");
            }

            if (!protectedTarget) {
                return new MergeDecision(
                        reasons.isEmpty(),
                        reasons,
                        0,
                        failedChecks
                );
            }

            boolean mayBypass =
                    administrator && policy.allowAdministratorBypass();

            if (mayBypass) {
                return new MergeDecision(true, List.of(), 0, Set.of());
            }

            Set<String> authors = pullRequest.commits().stream()
                    .map(Commit::author)
                    .collect(Collectors.toSet());

            // Reviewer eligibility and approval counting are separate rules.
            // An approval by a commit author or ineligible reviewer is excluded.
            Map<String, Review> latestByReviewer = new HashMap<>();

            pullRequest.reviews().stream()
                    .filter(review -> !review.dismissed())
                    .sorted((left, right) ->
                            left.submittedAt().compareTo(right.submittedAt()))
                    .forEach(review ->
                            latestByReviewer.put(review.reviewer(), review));

            Set<String> approvers = new HashSet<>();

            for (Review review : latestByReviewer.values()) {
                if (review.state() == ReviewState.CHANGES_REQUESTED) {
                    reasons.add(
                            "Changes requested by " + review.reviewer() + "."
                    );
                }

                if (review.state() == ReviewState.APPROVED()) {
                    if (authors.contains(review.reviewer())) {
                        reasons.add(
                                "Commit authors cannot approve their own changes."
                        );
                    } else if (!policy.eligibleReviewers().isEmpty() &&
                            !policy.eligibleReviewers().contains(review.reviewer())) {
                        reasons.add(
                                "Reviewer is not eligible: " + review.reviewer()
                        );
                    } else {
                        approvers.add(review.reviewer());
                    }
                }
            }

            if (approvers.size() < policy.requiredApprovals()) {
                reasons.add(
                        "Required approvals: " + policy.requiredApprovals() +
                        ", valid approvals: " + approvers.size() + "."
                );
            }

            for (String required : policy.requiredChecks()) {
                if (!Boolean.TRUE.equals(
                        pullRequest.statusChecks().get(required))) {
                    failedChecks.add(required);
                    reasons.add(
                            "Missing or failing status check: " + required
                    );
                }
            }

            if (policy.requireResolvedConversations() &&
                    !pullRequest.unresolvedConversations().isEmpty()) {
                reasons.add("Review conversations remain unresolved.");
            }

            if (policy.requireLinearHistory() && !proposedHistoryIsLinear) {
                reasons.add("Proposed merge violates linear history.");
            }

            return new MergeDecision(
                    reasons.isEmpty(),
                    reasons,
                    approvers.size(),
                    failedChecks
            );
        }
    }

    private static String requireText(String value, String label) {
        if (value == null || value.isBlank()) {
            throw new DomainException(label + " cannot be empty.");
        }
        return value.trim();
    }

    public static void main(String[] args) {
        Commit authentication = new Commit(
                "a501", "maya",
                Set.of("src/AuthService.java", "src/TokenValidator.java"),
                114, 23, ChangeKind.SECURITY
        );

        Commit tests = new Commit(
                "a502", "liam",
                Set.of("src/TokenValidator.java", "test/TokenValidatorTest.java"),
                63, 8, ChangeKind.BUGFIX
        );

        PullRequest pr = new PullRequest(
                731,
                "Reject expired session tokens",
                "feature/token-expiry",
                "main",
                List.of(authentication, tests),
                PullRequestState.DRAFT
        );

        pr.markReady();
        pr.synchronizeBase(12);
        pr.recordCheck("unit-tests", true);
        pr.recordCheck("security-scan", true);
        pr.recordCheck("integration-tests", true);
        pr.openConversation("discussion-token-expiry");

        pr.addReview(new Review(
                "olivia", "a502", ReviewState.APPROVED, false,
                Instant.parse("2026-10-16T04:00:00Z"),
                List.of(new ReviewComment(
                        "comment-1",
                        "src/TokenValidator.java",
                        48,
                        "Reject tokens at the expiry boundary.",
                        false
                ))
        ));

        pr.addReview(new Review(
                "ethan", "a502", ReviewState.APPROVED, false,
                Instant.parse("2026-10-16T04:05:00Z"),
                List.of()
        ));

        pr.addReview(new Review(
                "maya", "a502", ReviewState.APPROVED, false,
                Instant.parse("2026-10-16T04:06:00Z"),
                List.of()
        ));

        BranchProtection policy = new BranchProtection(
                "main",
                2,
                Set.of("unit-tests", "security-scan", "integration-tests"),
                true,
                true,
                true,
                true,
                true,
                false,
                Set.of("olivia", "ethan", "nora")
        );

        MergeEligibilityService service = new MergeEligibilityService();

        System.out.println("Pull request #" + pr.number() + ": " + pr.title());
        System.out.println("State: " + pr.state());
        System.out.println("Base revision: " + pr.baseRevision());

        MergeDecision blocked = service.evaluate(pr, policy, false, true);
        System.out.println("\nBefore resolving the discussion:");
        printDecision(blocked);

        pr.resolveConversation("discussion-token-expiry");

        MergeDecision ready = service.evaluate(pr, policy, false, true);
        System.out.println("\nAfter resolving the discussion:");
        printDecision(ready);

        if (ready.eligible()) {
            pr.merge(ready, MergeStrategy.SQUASH);
            System.out.println("Merged using " + MergeStrategy.SQUASH);
            System.out.println("State: " + pr.state());
        }

        System.out.println("\nAdministrator bypass policy:");
        System.out.println(
                service.evaluate(pr, policy, true, true).eligible()
        );

        System.out.println("\nFailure case:");
        PullRequest failing = new PullRequest(
                732, "Update authorization boundary",
                "feature/auth-boundary", "main",
                List.of(new Commit(
                        "b601", "nora", Set.of("src/AuthService.java"),
                        20, 5, ChangeKind.SECURITY
                )),
                PullRequestState.OPEN
        );

        failing.recordCheck("unit-tests", true);
        MergeDecision failure = service.evaluate(
                failing, policy, false, false
        );
        printDecision(failure);
    }

    private static void printDecision(MergeDecision decision) {
        System.out.println("Eligible: " + decision.eligible());
        System.out.println("Valid approvals: " + decision.eligibleApprovals());
        System.out.println("Failed checks: " + decision.failedChecks());
        for (String reason : decision.reasons()) {
            System.out.println("Blocked: " + reason);
        }
    }
}
