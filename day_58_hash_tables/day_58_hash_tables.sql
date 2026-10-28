DROP SCHEMA IF EXISTS hash_tables_demo CASCADE;
CREATE SCHEMA hash_tables_demo;

SET search_path = hash_tables_demo, public;

CREATE TYPE repository_state AS ENUM ('ACTIVE', 'ARCHIVED');

CREATE TYPE pull_request_state AS ENUM (
    'DRAFT',
    'OPEN',
    'CLOSED',
    'MERGED'
);

CREATE TYPE review_state AS ENUM (
    'COMMENTED',
    'CHANGES_REQUESTED',
    'APPROVED',
    'DISMISSED'
);

CREATE TYPE check_state AS ENUM (
    'PENDING',
    'PASSED',
    'FAILED'
);

CREATE TABLE repositories (
    repository_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization TEXT NOT NULL,
    repository_name TEXT NOT NULL,
    state repository_state NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (organization, repository_name),
    CHECK (length(trim(organization)) > 0),
    CHECK (length(trim(repository_name)) > 0)
);

CREATE TABLE branches (
    branch_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    branch_name TEXT NOT NULL,
    protected BOOLEAN NOT NULL DEFAULT FALSE,
    allows_direct_push BOOLEAN NOT NULL DEFAULT TRUE,
    allows_force_push BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (repository_id, branch_name),
    CHECK (length(trim(branch_name)) > 0),
    CHECK (NOT protected OR NOT allows_force_push)
);

CREATE TABLE commits (
    commit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    commit_hash CHAR(40) NOT NULL,
    author_name TEXT NOT NULL,
    message TEXT NOT NULL,
    committed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (repository_id, commit_hash),
    CHECK (commit_hash ~ '^[0-9a-fA-F]{40}$'),
    CHECK (length(trim(author_name)) > 0),
    CHECK (length(trim(message)) > 0)
);

CREATE TABLE pull_requests (
    pull_request_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    source_branch_id BIGINT NOT NULL
        REFERENCES branches(branch_id),
    target_branch_id BIGINT NOT NULL
        REFERENCES branches(branch_id),
    title TEXT NOT NULL,
    state pull_request_state NOT NULL DEFAULT 'DRAFT',
    is_draft BOOLEAN NOT NULL DEFAULT TRUE,
    has_merge_conflicts BOOLEAN NOT NULL DEFAULT FALSE,
    conversations_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    merged_at TIMESTAMPTZ,
    CHECK (source_branch_id <> target_branch_id),
    CHECK (NOT is_draft OR state = 'DRAFT'),
    CHECK (state <> 'MERGED' OR merged_at IS NOT NULL),
    CHECK (length(trim(title)) > 0)
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

CREATE TABLE reviewers (
    reviewer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    reviewer_role TEXT NOT NULL,
    CHECK (length(trim(username)) > 0)
);

CREATE TABLE reviews (
    review_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    reviewer_id BIGINT NOT NULL
        REFERENCES reviewers(reviewer_id),
    state review_state NOT NULL,
    stale BOOLEAN NOT NULL DEFAULT FALSE,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (pull_request_id, reviewer_id, submitted_at)
);

CREATE TABLE review_comments (
    comment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id BIGINT NOT NULL
        REFERENCES reviews(review_id)
        ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    line_number INTEGER,
    body TEXT NOT NULL,
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (line_number IS NULL OR line_number > 0),
    CHECK (length(trim(file_path)) > 0),
    CHECK (length(trim(body)) > 0)
);

CREATE TABLE status_checks (
    status_check_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    state check_state NOT NULL DEFAULT 'PENDING',
    completed_at TIMESTAMPTZ,
    UNIQUE (pull_request_id, check_name),
    CHECK (
        (state = 'PASSED' AND completed_at IS NOT NULL)
        OR
        (state <> 'PASSED')
    )
);

CREATE TABLE branch_protection_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    branch_id BIGINT NOT NULL
        REFERENCES branches(branch_id)
        ON DELETE CASCADE,
    required_approvals INTEGER NOT NULL DEFAULT 0,
    require_passing_checks BOOLEAN NOT NULL DEFAULT TRUE,
    require_resolved_conversations BOOLEAN NOT NULL DEFAULT TRUE,
    restrict_direct_push BOOLEAN NOT NULL DEFAULT TRUE,
    restrict_force_push BOOLEAN NOT NULL DEFAULT TRUE,
    restrict_deletion BOOLEAN NOT NULL DEFAULT TRUE,
    require_linear_history BOOLEAN NOT NULL DEFAULT FALSE,
    allow_administrator_bypass BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (branch_id),
    CHECK (required_approvals >= 0),
    CHECK (NOT restrict_force_push OR branch_id IS NOT NULL)
);

CREATE INDEX idx_branches_repository
    ON branches(repository_id);

CREATE INDEX idx_commits_repository_time
    ON commits(repository_id, committed_at DESC);

CREATE INDEX idx_pull_requests_repository_state
    ON pull_requests(repository_id, state);

CREATE INDEX idx_reviews_pull_request_state
    ON reviews(pull_request_id, state, stale);

CREATE INDEX idx_comments_review_resolution
    ON review_comments(review_id, resolved);

CREATE INDEX idx_checks_pull_request_state
    ON status_checks(pull_request_id, state);

CREATE TABLE hash_table_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT
        REFERENCES repositories(repository_id)
        ON DELETE SET NULL,
    pull_request_id BIGINT
        REFERENCES pull_requests(pull_request_id)
        ON DELETE SET NULL,
    event_type TEXT NOT NULL,
    event_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION prevent_invalid_protection()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    branch_record branches%ROWTYPE;
BEGIN
    SELECT *
    INTO branch_record
    FROM branches
    WHERE branch_id = NEW.branch_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'branch % does not exist', NEW.branch_id;
    END IF;

    IF branch_record.repository_id <> NEW.repository_id THEN
        RAISE EXCEPTION
            'branch % does not belong to repository %',
            NEW.branch_id,
            NEW.repository_id;
    END IF;

    IF NOT branch_record.protected
       AND (
            NEW.required_approvals > 0
            OR NEW.require_passing_checks
            OR NEW.restrict_direct_push
            OR NEW.restrict_force_push
       ) THEN
        RAISE EXCEPTION
            'non-protected branch cannot receive restrictive governance policy';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_protection
BEFORE INSERT OR UPDATE ON branch_protection_policies
FOR EACH ROW
EXECUTE FUNCTION prevent_invalid_protection();

CREATE OR REPLACE FUNCTION audit_pull_request_changes()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO hash_table_audit (
        repository_id,
        pull_request_id,
        event_type,
        event_data
    )
    VALUES (
        NEW.repository_id,
        NEW.pull_request_id,
        'PULL_REQUEST_STATE_CHANGE',
        jsonb_build_object(
            'state', NEW.state,
            'is_draft', NEW.is_draft,
            'has_merge_conflicts', NEW.has_merge_conflicts
        )
    );

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_audit_pull_request
AFTER INSERT OR UPDATE OF state, is_draft, has_merge_conflicts
ON pull_requests
FOR EACH ROW
EXECUTE FUNCTION audit_pull_request_changes();

CREATE OR REPLACE FUNCTION merge_eligibility(
    p_pull_request_id BIGINT
)
RETURNS TABLE (
    eligible BOOLEAN,
    approval_count BIGINT,
    required_approvals INTEGER,
    all_checks_pass BOOLEAN,
    unresolved_comments BIGINT,
    failure_reason TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    pr RECORD;
    policy RECORD;
    approvals BIGINT;
    checks_ok BOOLEAN;
    unresolved BIGINT;
BEGIN
    SELECT
        pr.*,
        b.branch_id AS target_branch_id
    INTO pr
    FROM pull_requests pr
    JOIN branches b
      ON b.branch_id = pr.target_branch_id
    WHERE pr.pull_request_id = p_pull_request_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'pull request % does not exist',
            p_pull_request_id;
    END IF;

    SELECT *
    INTO policy
    FROM branch_protection_policies
    WHERE branch_id = pr.target_branch_id;

    IF NOT FOUND THEN
        RETURN QUERY
        SELECT
            FALSE,
            0::BIGINT,
            0,
            FALSE,
            0::BIGINT,
            'target branch has no protection policy';
        RETURN;
    END IF;

    SELECT count(*)
    INTO approvals
    FROM reviews r
    JOIN reviewers rv
      ON rv.reviewer_id = r.reviewer_id
    WHERE r.pull_request_id = p_pull_request_id
      AND r.state = 'APPROVED'
      AND NOT r.stale
      AND rv.active
      AND rv.reviewer_role IN ('reviewer', 'maintainer');

    SELECT COALESCE(bool_and(state = 'PASSED'), FALSE)
    INTO checks_ok
    FROM status_checks
    WHERE pull_request_id = p_pull_request_id;

    SELECT count(*)
    INTO unresolved
    FROM review_comments rc
    JOIN reviews r
      ON r.review_id = rc.review_id
    WHERE r.pull_request_id = p_pull_request_id
      AND NOT rc.resolved;

    IF pr.state <> 'OPEN' THEN
        RETURN QUERY
        SELECT
            FALSE,
            approvals,
            policy.required_approvals,
            checks_ok,
            unresolved,
            'pull request is not open';
        RETURN;
    END IF;

    IF pr.has_merge_conflicts THEN
        RETURN QUERY
        SELECT
            FALSE,
            approvals,
            policy.required_approvals,
            checks_ok,
            unresolved,
            'merge conflicts exist';
        RETURN;
    END IF;

    IF approvals < policy.required_approvals THEN
        RETURN QUERY
        SELECT
            FALSE,
            approvals,
            policy.required_approvals,
            checks_ok,
            unresolved,
            'required approvals are missing';
        RETURN;
    END IF;

    IF policy.require_passing_checks AND NOT checks_ok THEN
        RETURN QUERY
        SELECT
            FALSE,
            approvals,
            policy.required_approvals,
            checks_ok,
            unresolved,
            'one or more status checks have not passed';
        RETURN;
    END IF;

    IF policy.require_resolved_conversations
       AND unresolved > 0 THEN
        RETURN QUERY
        SELECT
            FALSE,
            approvals,
            policy.required_approvals,
            checks_ok,
            unresolved,
            'review conversations remain unresolved';
        RETURN;
    END IF;

    RETURN QUERY
    SELECT
        TRUE,
        approvals,
        policy.required_approvals,
        checks_ok,
        unresolved,
        'all merge conditions satisfied';
END;
$$;


INSERT INTO repositories (
    organization,
    repository_name
)
VALUES
    ('security-platform', 'gateway'),
    ('research-platform', 'gateway'),
    ('data-platform', 'analytics');

INSERT INTO branches (
    repository_id,
    branch_name,
    protected,
    allows_direct_push,
    allows_force_push
)
SELECT repository_id, 'main', TRUE, FALSE, FALSE
FROM repositories
WHERE repository_name = 'gateway';

INSERT INTO branches (
    repository_id,
    branch_name,
    protected,
    allows_direct_push,
    allows_force_push
)
SELECT repository_id, 'develop', FALSE, TRUE, TRUE
FROM repositories
WHERE repository_name = 'gateway';

INSERT INTO branches (
    repository_id,
    branch_name,
    protected,
    allows_direct_push,
    allows_force_push
)
SELECT repository_id, 'main', TRUE, FALSE, FALSE
FROM repositories
WHERE organization = 'data-platform';

INSERT INTO commits (
    repository_id,
    commit_hash,
    author_name,
    message
)
SELECT
    r.repository_id,
    repeat('a', 40),
    'asha',
    'Implement chained hash table';

INSERT INTO commits (
    repository_id,
    commit_hash,
    author_name,
    message
)
SELECT
    r.repository_id,
    repeat('b', 40),
    'ravi',
    'Add collision metrics'
FROM repositories r
WHERE r.organization = 'security-platform'
  AND r.repository_name = 'gateway';

INSERT INTO commits (
    repository_id,
    commit_hash,
    author_name,
    message
)
SELECT
    r.repository_id,
    repeat('c', 40),
    'meera',
    'Add open addressing benchmark'
FROM repositories r
WHERE r.organization = 'security-platform'
  AND r.repository_name = 'gateway';

INSERT INTO pull_requests (
    repository_id,
    source_branch_id,
    target_branch_id,
    title,
    state,
    is_draft,
    conversations_resolved
)
SELECT
    r.repository_id,
    source.branch_id,
    target.branch_id,
    'Improve hash table collision handling',
    'OPEN',
    FALSE,
    TRUE
FROM repositories r
JOIN branches source
  ON source.repository_id = r.repository_id
 AND source.branch_name = 'develop'
JOIN branches target
  ON target.repository_id = r.repository_id
 AND target.branch_name = 'main'
WHERE r.organization = 'security-platform'
  AND r.repository_name = 'gateway';

INSERT INTO pull_requests (
    repository_id,
    source_branch_id,
    target_branch_id,
    title,
    state,
    is_draft,
    conversations_resolved,
    has_merge_conflicts
)
SELECT
    r.repository_id,
    source.branch_id,
    target.branch_id,
    'Demonstrate failed merge eligibility',
    'OPEN',
    FALSE,
    TRUE,
    TRUE
FROM repositories r
JOIN branches source
  ON source.repository_id = r.repository_id
 AND source.branch_name = 'develop'
JOIN branches target
  ON target.repository_id = r.repository_id
 AND target.branch_name = 'main'
WHERE r.organization = 'data-platform';

INSERT INTO reviewers (username, reviewer_role)
VALUES
    ('asha', 'reviewer'),
    ('ravi', 'maintainer'),
    ('meera', 'reviewer'),
    ('external-user', 'guest');

INSERT INTO branch_protection_policies (
    repository_id,
    branch_id,
    required_approvals,
    require_passing_checks,
    require_resolved_conversations,
    restrict_direct_push,
    restrict_force_push,
    restrict_deletion,
    require_linear_history,
    allow_administrator_bypass
)
SELECT
    r.repository_id,
    b.branch_id,
    2,
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    FALSE
FROM repositories r
JOIN branches b
  ON b.repository_id = r.repository_id
 AND b.branch_name = 'main'
WHERE r.organization = 'security-platform';

INSERT INTO branch_protection_policies (
    repository_id,
    branch_id,
    required_approvals,
    require_passing_checks,
    require_resolved_conversations,
    restrict_direct_push,
    restrict_force_push,
    restrict_deletion,
    require_linear_history,
    allow_administrator_bypass
)
SELECT
    r.repository_id,
    b.branch_id,
    1,
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    FALSE,
    TRUE
FROM repositories r
JOIN branches b
  ON b.repository_id = r.repository_id
 AND b.branch_name = 'main'
WHERE r.organization = 'data-platform';

INSERT INTO pull_request_commits (
    pull_request_id,
    commit_id,
    commit_position
)
SELECT
    pr.pull_request_id,
    c.commit_id,
    row_number() OVER (
        PARTITION BY pr.pull_request_id
        ORDER BY c.commit_id
    )
FROM pull_requests pr
JOIN commits c
  ON c.repository_id = pr.repository_id
WHERE pr.title = 'Improve hash table collision handling';

INSERT INTO reviews (
    pull_request_id,
    reviewer_id,
    state,
    stale
)
SELECT
    pr.pull_request_id,
    rv.reviewer_id,
    CASE rv.username
        WHEN 'asha' THEN 'APPROVED'::review_state
        WHEN 'ravi' THEN 'APPROVED'::review_state
        ELSE 'COMMENTED'::review_state
    END,
    FALSE
FROM pull_requests pr
CROSS JOIN reviewers rv
WHERE pr.title = 'Improve hash table collision handling';

INSERT INTO review_comments (
    review_id,
    file_path,
    line_number,
    body,
    resolved
)
SELECT
    r.review_id,
    'hash_table.cpp',
    42,
    'Please verify the resize threshold under high collision load.',
    TRUE
FROM reviews r
JOIN pull_requests pr
  ON pr.pull_request_id = r.pull_request_id
JOIN reviewers rv
  ON rv.reviewer_id = r.reviewer_id
WHERE pr.title = 'Improve hash table collision handling'
  AND rv.username = 'asha';

INSERT INTO status_checks (
    pull_request_id,
    check_name,
    state,
    completed_at
)
SELECT
    pr.pull_request_id,
    check_name,
    'PASSED',
    now()
FROM pull_requests pr
CROSS JOIN (
    VALUES
        ('unit-tests'),
        ('static-analysis'),
        ('security-scan')
) AS checks(check_name)
WHERE pr.title = 'Improve hash table collision handling';

-- Main merge-eligibility report.
SELECT
    pr.pull_request_id,
    r.organization,
    r.repository_name,
    pr.title,
    eligibility.*
FROM pull_requests pr
JOIN repositories r
  ON r.repository_id = pr.repository_id
CROSS JOIN LATERAL merge_eligibility(pr.pull_request_id) eligibility
ORDER BY pr.pull_request_id;

-- Approval aggregation demonstrates that only eligible,
-- active, non-stale approvals count.
SELECT
    pr.pull_request_id,
    count(*) FILTER (
        WHERE rv.active
          AND rv.reviewer_role IN ('reviewer', 'maintainer')
          AND rev.state = 'APPROVED'
          AND NOT rev.stale
    ) AS valid_approvals,
    count(*) FILTER (
        WHERE rev.state = 'APPROVED'
    ) AS all_approval_decisions
FROM pull_requests pr
LEFT JOIN reviews rev
  ON rev.pull_request_id = pr.pull_request_id
LEFT JOIN reviewers rv
  ON rv.reviewer_id = rev.reviewer_id
GROUP BY pr.pull_request_id
ORDER BY pr.pull_request_id;

-- Status-check evaluation.
SELECT
    pr.pull_request_id,
    pr.title,
    bool_and(sc.state = 'PASSED') AS all_checks_pass,
    count(*) AS check_count
FROM pull_requests pr
LEFT JOIN status_checks sc
  ON sc.pull_request_id = pr.pull_request_id
GROUP BY pr.pull_request_id, pr.title
ORDER BY pr.pull_request_id;

-- Review-conversation report.
SELECT
    pr.pull_request_id,
    pr.title,
    count(rc.comment_id) AS comments,
    count(rc.comment_id) FILTER (WHERE NOT rc.resolved)
        AS unresolved_comments
FROM pull_requests pr
LEFT JOIN reviews r
  ON r.pull_request_id = pr.pull_request_id
LEFT JOIN review_comments rc
  ON rc.review_id = r.review_id
GROUP BY pr.pull_request_id, pr.title
ORDER BY pr.pull_request_id;

-- Branch-governance report.
SELECT
    r.organization,
    r.repository_name,
    b.branch_name,
    b.protected,
    p.required_approvals,
    p.require_passing_checks,
    p.require_resolved_conversations,
    p.restrict_direct_push,
    p.restrict_force_push,
    p.restrict_deletion,
    p.require_linear_history,
    p.allow_administrator_bypass
FROM repositories r
JOIN branches b
  ON b.repository_id = r.repository_id
LEFT JOIN branch_protection_policies p
  ON p.branch_id = b.branch_id
ORDER BY r.organization, r.repository_name, b.branch_name;

-- Demonstrate transactional integrity for a policy change.
BEGIN;

UPDATE branch_protection_policies
SET required_approvals = required_approvals + 1
WHERE branch_id = (
    SELECT b.branch_id
    FROM branches b
    JOIN repositories r
      ON r.repository_id = b.repository_id
    WHERE r.organization = 'security-platform'
      AND r.repository_name = 'gateway'
      AND b.branch_name = 'main'
);

-- The transaction can be inspected before the decision is committed.
SELECT
    branch_id,
    required_approvals
FROM branch_protection_policies
WHERE branch_id = (
    SELECT b.branch_id
    FROM branches b
    JOIN repositories r
      ON r.repository_id = b.repository_id
    WHERE r.organization = 'security-platform'
      AND r.repository_name = 'gateway'
      AND b.branch_name = 'main'
);

ROLLBACK;

-- Hash-index-style lookup demonstration:
-- equality on a unique composite key is supported by the unique index.
SELECT
    repository_id,
    organization,
    repository_name,
    state
FROM repositories
WHERE organization = 'security-platform'
  AND repository_name = 'gateway';

-- EXPLAIN verifies the planner's access path without modifying data.
EXPLAIN (COSTS OFF)
SELECT repository_id
FROM repositories
WHERE organization = 'security-platform'
  AND repository_name = 'gateway';

-- Audit records capture governance state changes without storing
-- sensitive authentication material.
SELECT
    audit_id,
    event_type,
    event_data,
    created_at
FROM hash_table_audit
ORDER BY audit_id;
