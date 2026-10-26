import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Deque;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

public class Main {

    enum ReviewState {
        DRAFT,
        OPEN,
        APPROVED,
        CHANGES_REQUESTED,
        MERGED,
        CLOSED
    }

    enum CheckState {
        PENDING,
        PASSED,
        FAILED
    }

    record Commit(String id, String message) {
        Commit {
            Objects.requireNonNull(id);
            Objects.requireNonNull(message);
            if (id.isBlank() || message.isBlank()) {
                throw new IllegalArgumentException("commit fields cannot be blank");
            }
        }
    }

    record Review(String reviewer, ReviewState state, String comment) {
        Review {
            Objects.requireNonNull(reviewer);
            Objects.requireNonNull(state);
            Objects.requireNonNull(comment);
            if (reviewer.isBlank()) {
                throw new IllegalArgumentException("reviewer cannot be blank");
            }
        }
    }

    record StatusCheck(String name, CheckState state) {
        StatusCheck {
            Objects.requireNonNull(name);
            Objects.requireNonNull(state);
        }
    }

    record BranchProtectionPolicy(
            int requiredApprovals,
            boolean requirePassingChecks,
            boolean requireResolvedConversations,
            boolean requireLinearHistory,
            boolean allowForcePush,
            boolean allowDirectPush) {

        BranchProtectionPolicy {
            if (requiredApprovals < 0) {
                throw new IllegalArgumentException("approval count cannot be negative");
            }
        }
    }

    static final class Stack<T> {
        private final Deque<T> values = new ArrayDeque<>();
        private final int capacity;

        Stack() {
            this(0);
        }

        Stack(int capacity) {
            if (capacity < 0) {
                throw new IllegalArgumentException("capacity cannot be negative");
            }
            this.capacity = capacity;
        }

        void push(T value) {
            if (capacity > 0 && values.size() >= capacity) {
                throw new StackOverflowException("stack capacity reached");
            }
            values.push(Objects.requireNonNull(value));
        }

        T pop() {
            if (values.isEmpty()) {
                throw new StackUnderflowException("stack is empty");
            }
            return values.pop();
        }

        T peek() {
            if (values.isEmpty()) {
                throw new StackUnderflowException("stack is empty");
            }
            return values.peek();
        }

        boolean isEmpty() {
            return values.isEmpty();
        }

        int size() {
            return values.size();
        }

        void clear() {
            values.clear();
        }
    }

    static class StackException extends RuntimeException {
        StackException(String message) {
            super(message);
        }
    }

    static final class StackUnderflowException extends StackException {
        StackUnderflowException(String message) {
            super(message);
        }
    }

    static final class StackOverflowException extends StackException {
        StackOverflowException(String message) {
            super(message);
        }
    }

    static final class InvalidExpressionException extends StackException {
        InvalidExpressionException(String message) {
            super(message);
        }
    }

    static final class PullRequest {
        private final int number;
        private final String sourceBranch;
        private final String targetBranch;
        private final List<Commit> commits;
        private final List<Review> reviews;
        private final List<StatusCheck> checks;

        private boolean draft;
        private boolean conversationsResolved;
        private boolean conflicts;
        private boolean branchUpToDate;
        private boolean linearHistory;
        private ReviewState state;

        PullRequest(
                int number,
                String sourceBranch,
                String targetBranch,
                List<Commit> commits,
                List<Review> reviews,
                List<StatusCheck> checks) {

            if (number <= 0) {
                throw new IllegalArgumentException("PR number must be positive");
            }

            this.number = number;
            this.sourceBranch = Objects.requireNonNull(sourceBranch);
            this.targetBranch = Objects.requireNonNull(targetBranch);
            this.commits = new ArrayList<>(commits);
            this.reviews = new ArrayList<>(reviews);
            this.checks = new ArrayList<>(checks);

            this.draft = true;
            this.conversationsResolved = false;
            this.conflicts = false;
            this.branchUpToDate = false;
            this.linearHistory = false;
            this.state = ReviewState.DRAFT;
        }

        void setDraft(boolean draft) {
            this.draft = draft;
            if (!draft && state == ReviewState.DRAFT) {
                state = ReviewState.OPEN;
            }
        }

        void setConversationsResolved(boolean value) {
            conversationsResolved = value;
        }

        void setConflicts(boolean value) {
            conflicts = value;
        }

        void setBranchUpToDate(boolean value) {
            branchUpToDate = value;
        }

        void setLinearHistory(boolean value) {
            linearHistory = value;
        }

        void setState(ReviewState state) {
            this.state = Objects.requireNonNull(state);
        }

        int number() {
            return number;
        }

        String sourceBranch() {
            return sourceBranch;
        }

        String targetBranch() {
            return targetBranch;
        }

        List<Commit> commits() {
            return List.copyOf(commits);
        }

        List<Review> reviews() {
            return List.copyOf(reviews);
        }

        List<StatusCheck> checks() {
            return List.copyOf(checks);
        }

        boolean isDraft() {
            return draft;
        }

        boolean conversationsResolved() {
            return conversationsResolved;
        }

        boolean hasConflicts() {
            return conflicts;
        }

        boolean branchUpToDate() {
            return branchUpToDate;
        }

        boolean hasLinearHistory() {
            return linearHistory;
        }

        ReviewState state() {
            return state;
        }
    }

    interface MergePolicy {
        List<String> violations(PullRequest pullRequest);
    }

    static final class EnterpriseMergePolicy implements MergePolicy {
        private final BranchProtectionPolicy policy;

        EnterpriseMergePolicy(BranchProtectionPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        @Override
        public List<String> violations(PullRequest pr) {
            List<String> failures = new ArrayList<>();

            if (pr.isDraft()) {
                failures.add("pull request is still a draft");
            }

            if (pr.sourceBranch().isBlank() || pr.targetBranch().isBlank()) {
                failures.add("source and target branches are required");
            }

            if (pr.sourceBranch().equals(pr.targetBranch())) {
                failures.add("source and target branches must differ");
            }

            if (pr.commits().isEmpty()) {
                failures.add("pull request contains no commits");
            }

            if (pr.hasConflicts()) {
                failures.add("merge conflicts are unresolved");
            }

            if (!pr.branchUpToDate()) {
                failures.add("source branch is not synchronized with target");
            }

            if (policy.requireLinearHistory() && !pr.hasLinearHistory()) {
                failures.add("linear history is required");
            }

            if (policy.requireResolvedConversations()
                    && !pr.conversationsResolved()) {
                failures.add("review conversations are unresolved");
            }

            if (policy.requirePassingChecks()) {
                if (pr.checks().isEmpty()) {
                    failures.add("required status checks are missing");
                }

                for (StatusCheck check : pr.checks()) {
                    if (check.state() != CheckState.PASSED) {
                        failures.add("status check failed or is pending: "
                                + check.name());
                    }
                }
            }

            if (countCurrentApprovals(pr) < policy.requiredApprovals()) {
                failures.add(
                        "insufficient current approvals: "
                                + countCurrentApprovals(pr)
                                + "/"
                                + policy.requiredApprovals());
            }

            return List.copyOf(failures);
        }

        private int countCurrentApprovals(PullRequest pr) {
            Map<String, ReviewState> latest = new HashMap<>();

            for (Review review : pr.reviews()) {
                latest.put(review.reviewer(), review.state());
            }

            return (int) latest.values().stream()
                    .filter(state -> state == ReviewState.APPROVED)
                    .count();
        }
    }

    static final class MergeService {
        private final MergePolicy policy;

        MergeService(MergePolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        void merge(PullRequest pr) {
            List<String> failures = policy.violations(pr);

            if (!failures.isEmpty()) {
                throw new IllegalStateException(
                        "merge rejected:\n - " + String.join("\n - ", failures));
            }

            pr.setState(ReviewState.MERGED);
        }
    }

    static boolean balancedDelimiters(String input) {
        Stack<Character> stack = new Stack<>();
        Map<Character, Character> pairs = Map.of(
                ')', '(',
                ']', '[',
                '}', '{'
        );

        for (char character : input.toCharArray()) {
            if ("([{".indexOf(character) >= 0) {
                stack.push(character);
            } else if (pairs.containsKey(character)) {
                if (stack.isEmpty() || stack.pop() != pairs.get(character)) {
                    return false;
                }
            }
        }

        return stack.isEmpty();
    }

    static int[] nextGreaterElements(int[] values) {
        int[] result = new int[values.length];
        Arrays.fill(result, -1);

        Stack<Integer> indices = new Stack<>();

        for (int i = 0; i < values.length; i++) {
            while (!indices.isEmpty()
                    && values[indices.peek()] < values[i]) {
                result[indices.pop()] = values[i];
            }
            indices.push(i);
        }

        return result;
    }

    static double evaluatePostfix(List<String> tokens) {
        Stack<Double> operands = new Stack<>();

        for (String token : tokens) {
            if (isNumber(token)) {
                operands.push(Double.parseDouble(token));
                continue;
            }

            if ("u-".equals(token)) {
                operands.push(-operands.pop());
                continue;
            }

            if (operands.size() < 2) {
                throw new InvalidExpressionException("insufficient operands");
            }

            double right = operands.pop();
            double left = operands.pop();

            if ((token.equals("/") || token.equals("%")) && right == 0.0) {
                throw new InvalidExpressionException("division by zero");
            }

            double result = switch (token) {
                case "+" -> left + right;
                case "-" -> left - right;
                case "*" -> left * right;
                case "/" -> left / right;
                case "%" -> left % right;
                case "^" -> Math.pow(left, right);
                default -> throw new InvalidExpressionException(
                        "unknown operator: " + token);
            };

            if (!Double.isFinite(result)) {
                throw new InvalidExpressionException("non-finite result");
            }

            operands.push(result);
        }

        if (operands.size() != 1) {
            throw new InvalidExpressionException("malformed postfix expression");
        }

        return operands.pop();
    }

    private static boolean isNumber(String token) {
        try {
            Double.parseDouble(token);
            return true;
        } catch (NumberFormatException error) {
            return false;
        }
    }

    static void require(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }

    static void runTests() {
        Stack<Integer> stack = new Stack<>(2);
        stack.push(10);
        stack.push(20);

        try {
            stack.push(30);
            throw new AssertionError("overflow was not detected");
        } catch (StackOverflowException expected) {
        }

        require(stack.pop() == 20, "LIFO operation");
        require(stack.peek() == 10, "peek operation");

        require(balancedDelimiters("{[()]}"), "valid delimiters");
        require(!balancedDelimiters("{[(])}"), "invalid delimiters");

        require(
                Arrays.equals(
                        nextGreaterElements(new int[]{4, 5, 2, 10, 8}),
                        new int[]{5, 10, 10, -1, -1}),
                "next greater elements");

        double value = evaluatePostfix(
                List.of("3", "4", "2", "*", "1", "5", "-", "2", "^", "/", "+"));

        require(Math.abs(value - 3.5) < 0.000001, "postfix evaluation");
    }

    public static void main(String[] args) {
        try {
            runTests();

            System.out.println("STACK OPERATIONS");
            Stack<String> stack = new Stack<>();
            stack.push("parse");
            stack.push("validate");
            stack.push("execute");
            System.out.println("top: " + stack.peek());
            System.out.println("pop: " + stack.pop());

            System.out.println("\nDELIMITER VALIDATION");
            System.out.println("{[()]} -> " + balancedDelimiters("{[()]}"));
            System.out.println("{[(])} -> " + balancedDelimiters("{[(])}"));

            System.out.println("\nMONOTONIC STACK");
            int[] values = {4, 5, 2, 10, 8};
            System.out.println("values: " + Arrays.toString(values));
            System.out.println(
                    "next greater: "
                            + Arrays.toString(nextGreaterElements(values)));

            System.out.println("\nPOSTFIX EVALUATION");
            List<String> postfix = List.of(
                    "3", "4", "2", "*", "1", "5", "-", "2", "^", "/", "+");
            System.out.println(
                    String.join(" ", postfix)
                            + " = "
                            + evaluatePostfix(postfix));

            System.out.println("\nENTERPRISE MERGE POLICY");

            BranchProtectionPolicy policy = new BranchProtectionPolicy(
                    2,
                    true,
                    true,
                    true,
                    false,
                    false);

            PullRequest pullRequest = new PullRequest(
                    1042,
                    "feature/stack-parser",
                    "main",
                    List.of(
                            new Commit("a1b2c3", "Implement stack parser"),
                            new Commit("d4e5f6", "Add expression tests")),
                    List.of(
                            new Review(
                                    "reviewer-a",
                                    ReviewState.APPROVED,
                                    "Stack invariants are correct."),
                            new Review(
                                    "reviewer-b",
                                    ReviewState.APPROVED,
                                    "Parser tests are sufficient.")),
                    List.of(
                            new StatusCheck("unit-tests", CheckState.PASSED),
                            new StatusCheck("static-analysis", CheckState.PASSED)));

            pullRequest.setDraft(false);
            pullRequest.setConversationsResolved(true);
            pullRequest.setBranchUpToDate(true);
            pullRequest.setLinearHistory(true);

            MergeService mergeService =
                    new MergeService(new EnterpriseMergePolicy(policy));

            mergeService.merge(pullRequest);

            System.out.println(
                    "PR #" + pullRequest.number()
                            + " state: "
                            + pullRequest.state());

            pullRequest.setState(ReviewState.OPEN);
            pullRequest.setConflicts(true);

            try {
                mergeService.merge(pullRequest);
            } catch (IllegalStateException error) {
                System.out.println("Expected rejection:");
                System.out.println(error.getMessage());
            }

            System.out.println("\nComplexity:");
            System.out.println("- Stack operations: O(1) amortized.");
            System.out.println("- Delimiter validation: O(n).");
            System.out.println("- Monotonic stack: O(n).");
            System.out.println("- Postfix evaluation: O(n).");
            System.out.println("- Policy evaluation: O(R + C).");

        } catch (Exception error) {
            System.err.println("Fatal error: " + error.getMessage());
            System.exit(1);
        }
    }
}
