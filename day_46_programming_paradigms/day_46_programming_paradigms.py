"""
Programming Paradigms: Procedural, Object-Oriented, Functional, and Declarative.

This executable case study implements a repository-quality analysis system.
Each paradigm solves a distinct part of the same engineering problem:
procedural code orchestrates processing, objects preserve domain invariants,
functional transformations calculate metrics, and declarative rules determine
whether a proposed repository change satisfies quality requirements.

Run with Python 3.10 or later:
    python programming_paradigms.py
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from functools import reduce
from statistics import mean
from typing import Callable, Iterable, Sequence


class ParadigmError(ValueError):
    """Raised when input violates a repository-analysis invariant."""


class ChangeType(str, Enum):
    FEATURE = "feature"
    BUGFIX = "bugfix"
    SECURITY = "security"
    DOCUMENTATION = "documentation"


@dataclass(frozen=True)
class Commit:
    """An immutable record of a proposed repository change."""

    commit_id: str
    author: str
    changed_files: tuple[str, ...]
    additions: int
    deletions: int
    change_type: ChangeType

    def __post_init__(self) -> None:
        if not self.commit_id.strip():
            raise ParadigmError("Commit ID cannot be empty.")
        if not self.author.strip():
            raise ParadigmError("Commit author cannot be empty.")
        if not self.changed_files:
            raise ParadigmError("A commit must change at least one file.")
        if len(set(self.changed_files)) != len(self.changed_files):
            raise ParadigmError("Duplicate file paths are not allowed.")
        if any(not path.strip() for path in self.changed_files):
            raise ParadigmError("File paths cannot be empty.")
        if any(path.startswith("/") or ".." in path.split("/")
               for path in self.changed_files):
            raise ParadigmError("File paths must remain inside the repository.")
        if self.additions < 0 or self.deletions < 0:
            raise ParadigmError("Line counts cannot be negative.")

    @property
    def net_change(self) -> int:
        return self.additions - self.deletions

    @property
    def total_changed_lines(self) -> int:
        return self.additions + self.deletions


@dataclass(frozen=True)
class PullRequest:
    """A proposed change containing commits and review metadata."""

    number: int
    title: str
    source_branch: str
    target_branch: str
    commits: tuple[Commit, ...]
    draft: bool = False
    conversations_resolved: bool = True
    status_checks: tuple[tuple[str, bool], ...] = ()

    def __post_init__(self) -> None:
        if self.number <= 0:
            raise ParadigmError("Pull request number must be positive.")
        if not self.title.strip():
            raise ParadigmError("Pull request title cannot be empty.")
        if not self.source_branch.strip() or not self.target_branch.strip():
            raise ParadigmError("Source and target branches are required.")
        if self.source_branch == self.target_branch:
            raise ParadigmError("Source and target branches must differ.")
        if not self.commits:
            raise ParadigmError("A pull request must contain at least one commit.")
        check_names = [name for name, _ in self.status_checks]
        if len(check_names) != len(set(check_names)):
            raise ParadigmError("Status-check names must be unique.")

    @property
    def changed_files(self) -> frozenset[str]:
        return frozenset(
            path for commit in self.commits for path in commit.changed_files
        )

    @property
    def additions(self) -> int:
        return sum(commit.additions for commit in self.commits)

    @property
    def deletions(self) -> int:
        return sum(commit.deletions for commit in self.commits)


class ReviewState(str, Enum):
    COMMENTED = "commented"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"


@dataclass(frozen=True)
class Review:
    """A review decision, separate from the comments attached to it."""

    reviewer: str
    state: ReviewState
    commit_id: str
    dismissed: bool = False
    comments: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.reviewer.strip() or not self.commit_id.strip():
            raise ParadigmError("Reviewer and reviewed commit are required.")
        if any(not comment.strip() for comment in self.comments):
            raise ParadigmError("Review comments cannot be empty.")


@dataclass(frozen=True)
class ReviewPolicy:
    """Declarative conditions governing merge eligibility."""

    required_approvals: int = 2
    required_checks: frozenset[str] = frozenset(
        {"unit-tests", "security-scan"}
    )
    require_resolved_conversations: bool = True
    require_linear_history: bool = True
    prohibit_self_approval: bool = True

    def __post_init__(self) -> None:
        if self.required_approvals < 0:
            raise ParadigmError("Required approvals cannot be negative.")
        if any(not check.strip() for check in self.required_checks):
            raise ParadigmError("Required check names cannot be empty.")


@dataclass(frozen=True)
class MergeDecision:
    eligible: bool
    reasons: tuple[str, ...]


def procedural_line_audit(commits: Sequence[Commit]) -> dict[str, int]:
    """
    Procedural paradigm: explicitly control the sequence of calculations.
    Local mutable accumulators make the processing order visible.
    """
    additions = 0
    deletions = 0
    changed_files: set[str] = set()
    security_commits = 0

    for commit in commits:
        additions += commit.additions
        deletions += commit.deletions
        changed_files.update(commit.changed_files)

        if commit.change_type is ChangeType.SECURITY:
            security_commits += 1

    return {
        "commits": len(commits),
        "additions": additions,
        "deletions": deletions,
        "net_change": additions - deletions,
        "unique_files": len(changed_files),
        "security_commits": security_commits,
    }


class RepositoryQualityService:
    """
    Object-oriented paradigm: encapsulate repository state and operations.
    The repository owns its policy and exposes a consistent evaluation method.
    """

    def __init__(
        self,
        repository_name: str,
        protected_branches: Iterable[str],
        policy: ReviewPolicy,
    ) -> None:
        if not repository_name.strip():
            raise ParadigmError("Repository name cannot be empty.")
        self.repository_name = repository_name
        self.protected_branches = frozenset(protected_branches)
        self.policy = policy

    def evaluate(
        self,
        pull_request: PullRequest,
        reviews: Sequence[Review],
        merge_commit_is_linear: bool = True,
    ) -> MergeDecision:
        reasons: list[str] = []
        policy = self.policy

        if pull_request.draft:
            reasons.append("Draft pull requests cannot be merged.")

        if pull_request.target_branch in self.protected_branches:
            if not pull_request.target_branch:
                reasons.append("Protected target branch is invalid.")

        latest_review_by_reviewer: dict[str, Review] = {}

        # A later non-dismissed review supersedes an earlier decision.
        # In production, ordering must use an authoritative timestamp or ID.
        for review in reviews:
            if not review.dismissed:
                latest_review_by_reviewer[review.reviewer] = review

        if policy.prohibit_self_approval:
            authors = {commit.author for commit in pull_request.commits}
            for reviewer, review in latest_review_by_reviewer.items():
                if reviewer in authors and review.state is ReviewState.APPROVED:
                    reasons.append(
                        f"Author {reviewer} cannot approve their own change."
                    )

        valid_approvals = {
            reviewer
            for reviewer, review in latest_review_by_reviewer.items()
            if review.state is ReviewState.APPROVED
            and reviewer not in {
                commit.author for commit in pull_request.commits
            }
        }

        # Approval count is evaluated independently from unresolved requests.
        if len(valid_approvals) < policy.required_approvals:
            reasons.append(
                f"Requires {policy.required_approvals} distinct valid "
                f"approvals; found {len(valid_approvals)}."
            )

        blocking_reviewers = [
            reviewer
            for reviewer, review in latest_review_by_reviewer.items()
            if review.state is ReviewState.CHANGES_REQUESTED
        ]
        if blocking_reviewers:
            reasons.append(
                "Changes remain requested by: "
                + ", ".join(sorted(blocking_reviewers))
            )

        check_results = dict(pull_request.status_checks)
        for required_check in sorted(policy.required_checks):
            if check_results.get(required_check) is not True:
                reasons.append(
                    f"Required status check is missing or failing: "
                    f"{required_check}."
                )

        if (
            policy.require_resolved_conversations
            and not pull_request.conversations_resolved
        ):
            reasons.append("Review conversations remain unresolved.")

        if policy.require_linear_history and not merge_commit_is_linear:
            reasons.append("The selected merge result violates linear history.")

        return MergeDecision(eligible=not reasons, reasons=tuple(reasons))


def functional_metrics(commits: Sequence[Commit]) -> dict[str, object]:
    """
    Functional paradigm: derive new values from immutable commit records.
    map, filter, and reduce make each transformation explicit.
    """
    additions = tuple(map(lambda commit: commit.additions, commits))
    deletions = tuple(map(lambda commit: commit.deletions, commits))
    security_changes = tuple(
        filter(
            lambda commit: commit.change_type is ChangeType.SECURITY,
            commits,
        )
    )

    total_additions = reduce(lambda left, right: left + right, additions, 0)
    total_deletions = reduce(lambda left, right: left + right, deletions, 0)

    file_frequency = Counter(
        path for commit in commits for path in commit.changed_files
    )

    return {
        "average_additions_per_commit": mean(additions) if additions else 0.0,
        "average_deletions_per_commit": mean(deletions) if deletions else 0.0,
        "total_net_change": total_additions - total_deletions,
        "security_commit_ids": tuple(
            commit.commit_id for commit in security_changes
        ),
        "frequently_changed_files": tuple(
            sorted(
                path for path, count in file_frequency.items()
                if count > 1
            )
        ),
    }


@dataclass(frozen=True)
class Rule:
    """A named declarative predicate used by the policy engine."""

    name: str
    predicate: Callable[[PullRequest], bool]
    failure_message: str


def evaluate_declarative_rules(
    pull_request: PullRequest,
    rules: Sequence[Rule],
) -> tuple[str, ...]:
    """
    Declarative paradigm: specify conditions rather than procedural steps.
    Each rule states what must be true, while the evaluator applies the rules.
    """
    return tuple(
        rule.failure_message
        for rule in rules
        if not rule.predicate(pull_request)
    )


def build_declarative_rules() -> tuple[Rule, ...]:
    return (
        Rule(
            "has-commits",
            lambda pr: len(pr.commits) > 0,
            "At least one commit is required.",
        ),
        Rule(
            "not-draft",
            lambda pr: not pr.draft,
            "The pull request is still a draft.",
        ),
        Rule(
            "has-title",
            lambda pr: bool(pr.title.strip()),
            "A descriptive title is required.",
        ),
        Rule(
            "different-branches",
            lambda pr: pr.source_branch != pr.target_branch,
            "Source and target branches must differ.",
        ),
    )


def demonstrate_paradigms() -> None:
    commits = (
        Commit(
            "a12bc34",
            "maya",
            ("src/auth.py", "tests/test_auth.py"),
            85,
            12,
            ChangeType.FEATURE,
        ),
        Commit(
            "d56ef78",
            "liam",
            ("src/auth.py", "docs/security.md"),
            32,
            9,
            ChangeType.SECURITY,
        ),
        Commit(
            "9012abc",
            "nora",
            ("tests/test_auth.py",),
            41,
            3,
            ChangeType.BUGFIX,
        ),
    )

    pull_request = PullRequest(
        number=248,
        title="Strengthen token validation and regression coverage",
        source_branch="feature/token-validation",
        target_branch="main",
        commits=commits,
        status_checks=(
            ("unit-tests", True),
            ("security-scan", True),
            ("integration-tests", False),
        ),
        conversations_resolved=True,
    )

    reviews = (
        Review(
            "olivia",
            ReviewState.APPROVED,
            "9012abc",
            comments=("Token expiry handling is clear.",),
        ),
        Review(
            "ethan",
            ReviewState.APPROVED,
            "9012abc",
        ),
        Review(
            "maya",
            ReviewState.APPROVED,
            "9012abc",
        ),
    )

    print("\nPROCEDURAL PROCESSING")
    for metric, value in procedural_line_audit(commits).items():
        print(f"{metric}: {value}")

    print("\nOBJECT-ORIENTED GOVERNANCE")
    service = RepositoryQualityService(
        "identity-platform",
        {"main", "release"},
        ReviewPolicy(
            required_approvals=2,
            required_checks=frozenset(
                {"unit-tests", "security-scan", "integration-tests"}
            ),
        ),
    )
    decision = service.evaluate(pull_request, reviews)
    print(f"Merge eligible: {decision.eligible}")
    for reason in decision.reasons:
        print(f"Blocked: {reason}")

    print("\nFUNCTIONAL ANALYSIS")
    for metric, value in functional_metrics(commits).items():
        print(f"{metric}: {value}")

    print("\nDECLARATIVE VALIDATION")
    for message in evaluate_declarative_rules(
        pull_request, build_declarative_rules()
    ):
        print(f"Rule violation: {message}")
    print("No structural rule violations found.")

    print("\nEDGE CASES")
    try:
        Commit(
            "bad0001",
            "developer",
            ("../secrets.env",),
            4,
            0,
            ChangeType.FEATURE,
        )
    except ParadigmError as error:
        print(f"Rejected unsafe path: {error}")

    dismissed_approval = Review(
        "olivia",
        ReviewState.APPROVED,
        "9012abc",
        dismissed=True,
    )
    reduced_decision = service.evaluate(
        pull_request,
        (dismissed_approval, reviews[1], reviews[2]),
    )
    print(f"After approval dismissal, eligible: {reduced_decision.eligible}")
    for reason in reduced_decision.reasons:
        print(f"Blocked: {reason}")


if __name__ == "__main__":
    demonstrate_paradigms()
