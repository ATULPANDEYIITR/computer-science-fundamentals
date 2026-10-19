DROP SCHEMA IF EXISTS repository_governance CASCADE;
CREATE SCHEMA repository_governance;

SET search_path TO repository_governance;

-- PostgreSQL enums make important workflow states explicit instead of
-- allowing arbitrary strings to represent domain state.
CREATE TYPE pull_request_state AS ENUM (
    'draft',
    'open',
    'closed',
    'merged'
);

CREATE TYPE review_state AS ENUM (
    'commented',
    'approved',
    'changes_requested'
);

CREATE TYPE merge_strategy AS ENUM (
    'merge_commit',
    'squash',
    'rebase'
);

CREATE TABLE repositories (
    repository_id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    owner TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE branches (
    branch_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    branch_name TEXT NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (repository_id, branch_name)
);

CREATE TABLE users (
    user_id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL
);

CREATE TABLE commits (
    commit_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    sha CHAR(40) NOT NULL UNIQUE,
    author_id BIGINT NOT NULL
        REFERENCES users(user_id),
    message TEXT NOT NULL,
    committed_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE pull_requests (
    pull_request_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    number INTEGER NOT NULL,
    author_id BIGINT NOT NULL
        REFERENCES users(user_id),
    source_branch_id BIGINT NOT NULL
        REFERENCES branches(branch_id),
    target_branch_id BIGINT NOT NULL
        REFERENCES branches(branch_id),
    state pull_request_state NOT NULL DEFAULT 'draft',
    is_draft BOOLEAN NOT NULL DEFAULT TRUE,
    merge_conflict BOOLEAN NOT NULL DEFAULT FALSE,
    unresolved_conversations INTEGER NOT NULL DEFAULT 0,
    merged_at TIMESTAMPTZ,
    merge_strategy merge_strategy,
    UNIQUE (repository_id, number),
    CHECK (unresolved_conversations >= 0),
    CHECK (
        state <> 'merged'
        OR merged_at IS NOT NULL
    )
);

CREATE TABLE pull_request_commits (
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    commit_id BIGINT NOT NULL
        REFERENCES commits(commit_id)
        ON DELETE RESTRICT,
    commit_position INTEGER NOT NULL,
    PRIMARY KEY (pull_request_id, commit_id),
    UNIQUE (pull_request_id, commit_position),
    CHECK (commit_position > 0)
);

CREATE TABLE review_requests (
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    reviewer_id BIGINT NOT NULL
        REFERENCES users(user_id),
    requested_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (pull_request_id, reviewer_id)
);

CREATE TABLE reviews (
    review_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    reviewer_id BIGINT NOT NULL
        REFERENCES users(user_id),
    state review_state NOT NULL,
    body TEXT NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE review_comments (
    comment_id BIGSERIAL PRIMARY KEY,
    review_id BIGINT NOT NULL
        REFERENCES reviews(review_id)
        ON DELETE CASCADE,
    commit_id BIGINT
        REFERENCES commits(commit_id),
    file_path TEXT,
    line_number INTEGER,
    body TEXT NOT NULL,
    is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (line_number IS NULL OR line_number > 0)
);

CREATE TABLE status_checks (
    status_check_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    passed BOOLEAN NOT NULL,
    completed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (pull_request_id, check_name)
);

CREATE TABLE branch_protection_policies (
    policy_id BIGSERIAL PRIMARY KEY,
    branch_id BIGINT NOT NULL UNIQUE
        REFERENCES branches(branch_id)
        ON DELETE CASCADE,
    required_approvals INTEGER NOT NULL DEFAULT 0,
    require_passing_checks BOOLEAN NOT NULL DEFAULT TRUE,
    require_resolved_conversations BOOLEAN NOT NULL DEFAULT TRUE,
    allow_direct_push BOOLEAN NOT NULL DEFAULT FALSE,
    allow_force_push BOOLEAN NOT NULL DEFAULT FALSE,
    allow_branch_deletion BOOLEAN NOT NULL DEFAULT FALSE,
    require_linear_history BOOLEAN NOT NULL DEFAULT FALSE,
    require_conversation_resolution BOOLEAN NOT NULL DEFAULT TRUE,
    CHECK (required_approvals >= 0)
);

CREATE TABLE merge_events (
    merge_event_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL UNIQUE
        REFERENCES pull_requests(pull_request_id)
        ON DELETE RESTRICT,
    merged_by BIGINT NOT NULL
        REFERENCES users(user_id),
    strategy merge_strategy NOT NULL,
    merged_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pull_requests_repository_state
    ON pull_requests(repository_id, state);

CREATE INDEX idx_pull_requests_target_branch
    ON pull_requests(target_branch_id, state);

CREATE INDEX idx_reviews_pull_request_state
    ON reviews(pull_request_id, state);

CREATE INDEX idx_status_checks_pull_request
    ON status_checks(pull_request_id, passed);

CREATE INDEX idx_review_comments_unresolved
    ON review_comments(review_id, is_resolved)
    WHERE is_resolved = FALSE;

INSERT INTO repositories (name, owner)
VALUES
    ('governance-engine', 'platform-team'),
    ('payment-service', 'payments-team');

INSERT INTO users (username, display_name)
VALUES
    ('alice', 'Alice Sharma'),
    ('bob', 'Bob Singh'),
    ('carol', 'Carol Verma'),
    ('david', 'David Rao'),
    ('security-reviewer', 'Security Reviewer'),
    ('platform-reviewer', 'Platform Reviewer');

INSERT INTO branches (repository_id, branch_name, is_default)
SELECT repository_id, 'main', TRUE
FROM repositories
WHERE name = 'governance-engine';

INSERT INTO branches (repository_id, branch_name)
SELECT repository_id, branch_name
FROM repositories
CROSS JOIN (
    VALUES
        ('feature/review-policy'),
        ('feature/payment-policy')
) AS branch_data(branch_name)
WHERE repositories.name = 'governance-engine';

INSERT INTO commits (
    repository_id,
    sha,
    author_id,
    message
)
SELECT
    r.repository_id,
    c.sha,
    u.user_id,
    c.message
FROM repositories r
CROSS JOIN (
    VALUES
        (
            'abc1234567890123456789012345678901234567',
            'alice',
            'Define review policy'
        ),
        (
            'def1234567890123456789012345678901234567',
            'alice',
            'Add policy validation'
        ),
        (
            '1111234567890123456789012345678901234567',
            'bob',
            'Change payment authorization'
        )
) AS c(sha, username, message)
JOIN users u ON u.username = c.username
WHERE r.name = 'governance-engine';

INSERT INTO pull_requests (
    repository_id,
    number,
    author_id,
    source_branch_id,
    target_branch_id,
    state,
    is_draft,
    merge_conflict
)
SELECT
    r.repository_id,
    101,
    alice.user_id,
    source_branch.branch_id,
    target_branch.branch_id,
    'open',
    FALSE,
    FALSE
FROM repositories r
JOIN users alice ON alice.username = 'alice'
JOIN branches source_branch
    ON source_branch.repository_id = r.repository_id
   AND source_branch.branch_name = 'feature/review-policy'
JOIN branches target_branch
    ON target_branch.repository_id = r.repository_id
   AND target_branch.branch_name = 'main'
WHERE r.name = 'governance-engine';

INSERT INTO pull_requests (
    repository_id,
    number,
    author_id,
    source_branch_id,
    target_branch_id,
    state,
    is_draft,
    merge_conflict,
    unresolved_conversations
)
SELECT
    r.repository_id,
    102,
    bob.user_id,
    source_branch.branch_id,
    target_branch.branch_id,
    'open',
    FALSE,
    FALSE,
    2
FROM repositories r
JOIN users bob ON bob.username = 'bob'
JOIN branches source_branch
    ON source_branch.repository_id = r.repository_id
   AND source_branch.branch_name = 'feature/payment-policy'
JOIN branches target_branch
    ON target_branch.repository_id = r.repository_id
   AND target_branch.branch_name = 'main'
WHERE r.name = 'governance-engine';

INSERT INTO pull_request_commits (
    pull_request_id,
    commit_id,
    commit_position
)
SELECT
    pr.pull_request_id,
    c.commit_id,
    1
FROM pull_requests pr
JOIN commits c
    ON c.sha = 'abc1234567890123456789012345678901234567'
WHERE pr.number = 101;

INSERT INTO pull_request_commits (
    pull_request_id,
    commit_id,
    commit_position
)
SELECT
    pr.pull_request_id,
    c.commit_id,
    2
FROM pull_requests pr
JOIN commits c
    ON c.sha = 'def1234567890123456789012345678901234567'
WHERE pr.number = 101;

INSERT INTO pull_request_commits (
    pull_request_id,
    commit_id,
    commit_position
)
SELECT
    pr.pull_request_id,
    c.commit_id,
    1
FROM pull_requests pr
JOIN commits c
    ON c.sha = '1111234567890123456789012345678901234567'
WHERE pr.number = 102;

INSERT INTO review_requests (pull_request_id, reviewer_id)
SELECT pr.pull_request_id, u.user_id
FROM pull_requests pr
JOIN users u ON u.username IN ('security-reviewer', 'platform-reviewer')
WHERE pr.number = 101;

INSERT INTO review_requests (pull_request_id, reviewer_id)
SELECT pr.pull_request_id, u.user_id
FROM pull_requests pr
JOIN users u ON u.username IN ('security-reviewer', 'platform-reviewer')
WHERE pr.number = 102;

INSERT INTO reviews (
    pull_request_id,
    reviewer_id,
    state,
    body
)
SELECT
    pr.pull_request_id,
    reviewer.user_id,
    'approved',
    'The repository policy is explicit and testable.'
FROM pull_requests pr
JOIN users reviewer ON reviewer.username = 'security-reviewer'
WHERE pr.number = 101;

INSERT INTO reviews (
    pull_request_id,
    reviewer_id,
    state,
    body
)
SELECT
    pr.pull_request_id,
    reviewer.user_id,
    'approved',
    'The workflow has sufficient validation.'
FROM pull_requests pr
JOIN users reviewer ON reviewer.username = 'platform-reviewer'
WHERE pr.number = 101;

INSERT INTO reviews (
    pull_request_id,
    reviewer_id,
    state,
    body
)
SELECT
    pr.pull_request_id,
    reviewer.user_id,
    'approved',
    'Initial review completed.'
FROM pull_requests pr
JOIN users reviewer ON reviewer.username = 'platform-reviewer'
WHERE pr.number = 102;

INSERT INTO reviews (
    pull_request_id,
    reviewer_id,
    state,
    body
)
SELECT
    pr.pull_request_id,
    reviewer.user_id,
    'changes_requested',
    'Authorization rule needs revision.'
FROM pull_requests pr
JOIN users reviewer ON reviewer.username = 'security-reviewer'
WHERE pr.number = 102;

INSERT INTO status_checks (
    pull_request_id,
    check_name,
    passed
)
SELECT pr.pull_request_id, checks.check_name, checks.passed
FROM pull_requests pr
CROSS JOIN (
    VALUES
        ('unit-tests', TRUE),
        ('static-analysis', TRUE),
        ('security-scan', TRUE)
) AS checks(check_name, passed)
WHERE pr.number = 101;

INSERT INTO status_checks (
    pull_request_id,
    check_name,
    passed
)
SELECT pr.pull_request_id, checks.check_name, checks.passed
FROM pull_requests pr
CROSS JOIN (
    VALUES
        ('unit-tests', TRUE),
        ('static-analysis', TRUE),
        ('security-scan', FALSE)
) AS checks(check_name, passed)
WHERE pr.number = 102;

INSERT INTO review_comments (
    review_id,
    commit_id,
    file_path,
    line_number,
    body,
    is_resolved
)
SELECT
    review.review_id,
    commit.commit_id,
    'src/policy.py',
    42,
    'Clarify the approval threshold validation.',
    FALSE
FROM reviews review
JOIN pull_requests pr
    ON pr.pull_request_id = review.pull_request_id
JOIN commits commit
    ON commit.sha = 'abc1234567890123456789012345678901234567'
WHERE pr.number = 101
  AND review.state = 'approved'
LIMIT 1;

INSERT INTO branch_protection_policies (
    branch_id,
    required_approvals,
    require_passing_checks,
    require_resolved_conversations,
    allow_direct_push,
    allow_force_push,
    allow_branch_deletion,
    require_linear_history,
    require_conversation_resolution
)
SELECT
    branch_id,
    2,
    TRUE,
    TRUE,
    FALSE,
    FALSE,
    FALSE,
    TRUE,
    TRUE
FROM branches
WHERE branch_name = 'main';

-- This view separates raw review records from the derived approval count.
-- A reviewer can submit multiple approvals, but the governance decision
-- counts distinct approving reviewers.
CREATE VIEW pull_request_approval_summary AS
SELECT
    pr.pull_request_id,
    pr.number,
    COUNT(DISTINCT r.reviewer_id)
        FILTER (WHERE r.state = 'approved') AS approval_count,
    COUNT(DISTINCT r.reviewer_id)
        FILTER (WHERE r.state = 'changes_requested') AS change_request_count
FROM pull_requests pr
LEFT JOIN reviews r
    ON r.pull_request_id = pr.pull_request_id
GROUP BY pr.pull_request_id, pr.number;

-- Evaluate required status checks for each pull request.
CREATE VIEW pull_request_check_summary AS
SELECT
    pr.pull_request_id,
    pr.number,
    COUNT(sc.status_check_id) AS check_count,
    COUNT(sc.status_check_id)
        FILTER (WHERE sc.passed) AS passed_check_count,
    COUNT(sc.status_check_id)
        FILTER (WHERE NOT sc.passed) AS failed_check_count
FROM pull_requests pr
LEFT JOIN status_checks sc
    ON sc.pull_request_id = pr.pull_request_id
GROUP BY pr.pull_request_id, pr.number;

-- This query exposes the complete governance evidence for each request.
SELECT
    pr.number,
    pr.state,
    pr.is_draft,
    pr.merge_conflict,
    pr.unresolved_conversations,
    COALESCE(a.approval_count, 0) AS approvals,
    COALESCE(a.change_request_count, 0) AS change_requests,
    COALESCE(c.check_count, 0) AS checks,
    COALESCE(c.failed_check_count, 0) AS failed_checks,
    bp.required_approvals,
    bp.require_passing_checks,
    bp.require_conversation_resolution
FROM pull_requests pr
JOIN branch_protection_policies bp
    ON bp.branch_id = pr.target_branch_id
LEFT JOIN pull_request_approval_summary a
    ON a.pull_request_id = pr.pull_request_id
LEFT JOIN pull_request_check_summary c
    ON c.pull_request_id = pr.pull_request_id
ORDER BY pr.number;

-- Merge eligibility is derived from all policy dimensions rather than
-- from the approval count alone.
WITH evidence AS (
    SELECT
        pr.pull_request_id,
        pr.number,
        pr.state,
        pr.is_draft,
        pr.merge_conflict,
        pr.unresolved_conversations,
        COALESCE(a.approval_count, 0) AS approvals,
        COALESCE(a.change_request_count, 0) AS change_requests,
        COALESCE(c.failed_check_count, 0) AS failed_checks,
        bp.required_approvals,
        bp.require_passing_checks,
        bp.require_conversation_resolution
    FROM pull_requests pr
    JOIN branch_protection_policies bp
        ON bp.branch_id = pr.target_branch_id
    LEFT JOIN pull_request_approval_summary a
        ON a.pull_request_id = pr.pull_request_id
    LEFT JOIN pull_request_check_summary c
        ON c.pull_request_id = pr.pull_request_id
)
SELECT
    number,
    CASE
        WHEN state <> 'open' THEN FALSE
        WHEN is_draft THEN FALSE
        WHEN merge_conflict THEN FALSE
        WHEN approvals < required_approvals THEN FALSE
        WHEN change_requests > 0 THEN FALSE
        WHEN require_passing_checks AND failed_checks > 0 THEN FALSE
        WHEN require_conversation_resolution
             AND unresolved_conversations > 0 THEN FALSE
        ELSE TRUE
    END AS merge_eligible
FROM evidence
ORDER BY number;

-- A transaction demonstrates database-level state change. The update and
-- audit record are committed together, preventing a merge record from
-- existing without the corresponding pull-request state.
BEGIN;

UPDATE pull_requests
SET
    state = 'merged',
    is_draft = FALSE,
    merged_at = CURRENT_TIMESTAMP,
    merge_strategy = 'squash'
WHERE number = 101
  AND state = 'open'
  AND is_draft = FALSE
  AND merge_conflict = FALSE
  AND unresolved_conversations = 0
  AND NOT EXISTS (
      SELECT 1
      FROM reviews r
      WHERE r.pull_request_id = pull_requests.pull_request_id
        AND r.state = 'changes_requested'
  )
  AND (
      SELECT COUNT(DISTINCT r.reviewer_id)
      FROM reviews r
      WHERE r.pull_request_id = pull_requests.pull_request_id
        AND r.state = 'approved'
  ) >= 2
  AND NOT EXISTS (
      SELECT 1
      FROM status_checks sc
      WHERE sc.pull_request_id = pull_requests.pull_request_id
        AND NOT sc.passed
  );

INSERT INTO merge_events (
    pull_request_id,
    merged_by,
    strategy
)
SELECT
    pr.pull_request_id,
    u.user_id,
    'squash'
FROM pull_requests pr
JOIN users u ON u.username = 'alice'
WHERE pr.number = 101
  AND pr.state = 'merged';

COMMIT;

-- This query shows why a request remains blocked even when one approval
-- exists: the database evaluates the complete policy evidence.
SELECT
    pr.number,
    a.approval_count,
    a.change_request_count,
    c.failed_check_count,
    pr.unresolved_conversations,
    CASE
        WHEN a.approval_count >= bp.required_approvals
         AND a.change_request_count = 0
         AND c.failed_check_count = 0
         AND pr.unresolved_conversations = 0
         AND NOT pr.merge_conflict
         AND pr.state = 'open'
         AND NOT pr.is_draft
        THEN 'eligible'
        ELSE 'blocked'
    END AS governance_result
FROM pull_requests pr
JOIN branch_protection_policies bp
    ON bp.branch_id = pr.target_branch_id
JOIN pull_request_approval_summary a
    ON a.pull_request_id = pr.pull_request_id
JOIN pull_request_check_summary c
    ON c.pull_request_id = pr.pull_request_id
ORDER BY pr.number;
