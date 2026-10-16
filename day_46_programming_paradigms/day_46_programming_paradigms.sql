-- PostgreSQL 15+.
-- Relational model of repository changes, reviews, approvals, and governance.
-- The four paradigms are separate concepts in the companion implementations;
-- this database enforces data integrity and stores the evidence used by policy.

BEGIN;

DROP VIEW IF EXISTS merge_eligibility;
DROP FUNCTION IF EXISTS evaluate_pull_request(BIGINT);
DROP FUNCTION IF EXISTS enforce_review_commit();
DROP TABLE IF EXISTS review_comments CASCADE;
DROP TABLE IF EXISTS reviews CASCADE;
DROP TABLE IF EXISTS status_checks CASCADE;
DROP TABLE IF EXISTS pull_request_commits CASCADE;
DROP TABLE IF EXISTS commits CASCADE;
DROP TABLE IF EXISTS pull_requests CASCADE;
DROP TABLE IF EXISTS branch_protection CASCADE;
DROP TABLE IF EXISTS branches CASCADE;
DROP TABLE IF EXISTS reviewers CASCADE;
DROP TABLE IF EXISTS repositories CASCADE;

CREATE TABLE repositories (
    repository_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    default_branch TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (length(trim(name)) > 0),
    CHECK (length(trim(default_branch)) > 0)
);

CREATE TABLE branches (
    branch_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id) ON DELETE CASCADE,
    branch_name TEXT NOT NULL,
    head_revision BIGINT NOT NULL DEFAULT 0,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (repository_id, branch_name),
    CHECK (length(trim(branch_name)) > 0),
    CHECK (head_revision >= 0)
);

CREATE TABLE reviewers (
    reviewer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    can_bypass_protection BOOLEAN NOT NULL DEFAULT FALSE,
    CHECK (length(trim(username)) > 0)
);

CREATE TABLE branch_protection (
    protection_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    branch_id BIGINT NOT NULL UNIQUE
        REFERENCES branches(branch_id) ON DELETE CASCADE,
    required_approvals INTEGER NOT NULL DEFAULT 2,
    required_checks TEXT[] NOT NULL
        DEFAULT ARRAY['unit-tests', 'security-scan']::TEXT[],
    prohibit_direct_push BOOLEAN NOT NULL DEFAULT TRUE,
    prohibit_force_push BOOLEAN NOT NULL DEFAULT TRUE,
    prohibit_deletion BOOLEAN NOT NULL DEFAULT TRUE,
    require_resolved_conversations BOOLEAN NOT NULL DEFAULT TRUE,
    require_linear_history BOOLEAN NOT NULL DEFAULT TRUE,
    allow_admin_bypass BOOLEAN NOT NULL DEFAULT FALSE,
    CHECK (required_approvals >= 0),
    CHECK (array_position(required_checks, NULL) IS NULL)
);

CREATE TABLE pull_requests (
    pull_request_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id) ON DELETE CASCADE,
    pull_request_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    source_branch_id BIGINT NOT NULL REFERENCES branches(branch_id),
    target_branch_id BIGINT NOT NULL REFERENCES branches(branch_id),
    state TEXT NOT NULL DEFAULT 'open'
        CHECK (state IN ('draft', 'open', 'closed', 'merged')),
    merge_strategy TEXT
        CHECK (merge_strategy IN ('merge_commit', 'squash', 'rebase')),
    base_revision_at_review BIGINT NOT NULL DEFAULT 0,
    current_base_revision BIGINT NOT NULL DEFAULT 0,
    conversations_resolved BOOLEAN NOT NULL DEFAULT TRUE,
    proposed_history_is_linear BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    merged_at TIMESTAMPTZ,
    UNIQUE (repository_id, pull_request_number),
    CHECK (pull_request_number > 0),
    CHECK (length(trim(title)) > 0),
    CHECK (source_branch_id <> target_branch_id),
    CHECK (base_revision_at_review >= 0),
    CHECK (current_base_revision >= 0),
    CHECK (
        state <> 'merged'
        OR (merged_at IS NOT NULL AND merge_strategy IS NOT NULL)
    )
);

CREATE TABLE commits (
    commit_id TEXT PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id) ON DELETE CASCADE,
    author_id BIGINT NOT NULL REFERENCES reviewers(reviewer_id),
    message TEXT NOT NULL,
    change_kind TEXT NOT NULL
        CHECK (change_kind IN ('feature', 'bugfix', 'security', 'documentation')),
    additions INTEGER NOT NULL DEFAULT 0,
    deletions INTEGER NOT NULL DEFAULT 0,
    committed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (length(trim(commit_id)) > 0),
    CHECK (length(trim(message)) > 0),
    CHECK (additions >= 0 AND deletions >= 0)
);

CREATE TABLE pull_request_commits (
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id) ON DELETE CASCADE,
    commit_id TEXT NOT NULL REFERENCES commits(commit_id),
    position INTEGER NOT NULL,
    PRIMARY KEY (pull_request_id, commit_id),
    UNIQUE (pull_request_id, position),
    CHECK (position > 0)
);

CREATE TABLE status_checks (
    status_check_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id) ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    passed BOOLEAN NOT NULL,
    checked_revision BIGINT NOT NULL,
    completed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (pull_request_id, check_name, checked_revision),
    CHECK (length(trim(check_name)) > 0),
    CHECK (checked_revision >= 0)
);

CREATE TABLE reviews (
    review_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id) ON DELETE CASCADE,
    reviewer_id BIGINT NOT NULL REFERENCES reviewers(reviewer_id),
    reviewed_commit_id TEXT NOT NULL REFERENCES commits(commit_id),
    state TEXT NOT NULL
        CHECK (state IN ('commented', 'approved', 'changes_requested')),
    dismissed BOOLEAN NOT NULL DEFAULT FALSE,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dismissed_at TIMESTAMPTZ,
    dismissal_reason TEXT,
    CHECK (
        (dismissed = FALSE AND dismissed_at IS NULL)
        OR
        (dismissed = TRUE AND dismissed_at IS NOT NULL)
    ),
    CHECK (
        dismissal_reason IS NULL OR length(trim(dismissal_reason)) > 0
    )
);

CREATE TABLE review_comments (
    comment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id BIGINT NOT NULL
        REFERENCES reviews(review_id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    line_number INTEGER NOT NULL,
    body TEXT NOT NULL,
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (length(trim(file_path)) > 0),
    CHECK (line_number > 0),
    CHECK (length(trim(body)) > 0)
);

CREATE INDEX idx_pull_requests_target_state
    ON pull_requests(target_branch_id, state);

CREATE INDEX idx_pull_request_commits_commit
    ON pull_request_commits(commit_id);

CREATE INDEX idx_reviews_latest
    ON reviews(pull_request_id, reviewer_id, submitted_at DESC);

CREATE INDEX idx_status_checks_latest
    ON status_checks(pull_request_id, check_name, checked_revision DESC);

CREATE INDEX idx_unresolved_comments
    ON review_comments(review_id)
    WHERE resolved = FALSE;

-- Prevent a review from referring to a commit unrelated to its pull request.
CREATE FUNCTION enforce_review_commit()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pull_request_commits prc
        WHERE prc.pull_request_id = NEW.pull_request_id
          AND prc.commit_id = NEW.reviewed_commit_id
    ) THEN
        RAISE EXCEPTION
            'Reviewed commit % is not part of pull request %',
            NEW.reviewed_commit_id, NEW.pull_request_id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER reviews_must_reference_pr_commit
BEFORE INSERT OR UPDATE OF pull_request_id, reviewed_commit_id
ON reviews
FOR EACH ROW
EXECUTE FUNCTION enforce_review_commit();

-- Seed a repository and its branch topology.
INSERT INTO repositories (name, default_branch)
VALUES ('identity-platform', 'main');

INSERT INTO branches (repository_id, branch_name, head_revision)
SELECT repository_id, branch_name, revision
FROM repositories
CROSS JOIN (
    VALUES
        ('main', 18::BIGINT),
        ('feature/token-expiry', 7::BIGINT),
        ('release', 15::BIGINT)
) AS seeded(branch_name, revision)
WHERE repositories.name = 'identity-platform';

INSERT INTO reviewers (username, active, can_bypass_protection)
VALUES
    ('maya', TRUE, FALSE),
    ('liam', TRUE, FALSE),
    ('olivia', TRUE, FALSE),
    ('ethan', TRUE, FALSE),
    ('nora', TRUE, FALSE),
    ('admin-release', TRUE, TRUE);

INSERT INTO branch_protection (
    branch_id,
    required_approvals,
    required_checks,
    prohibit_direct_push,
    prohibit_force_push,
    prohibit_deletion,
    require_resolved_conversations,
    require_linear_history,
    allow_admin_bypass
)
SELECT branch_id, 2,
       ARRAY['unit-tests', 'security-scan', 'integration-tests']::TEXT[],
       TRUE, TRUE, TRUE, TRUE, TRUE, FALSE
FROM branches
WHERE branch_name IN ('main', 'release');

INSERT INTO pull_requests (
    repository_id,
    pull_request_number,
    title,
    source_branch_id,
    target_branch_id,
    state,
    base_revision_at_review,
    current_base_revision,
    conversations_resolved,
    proposed_history_is_linear
)
SELECT r.repository_id, 248,
       'Strengthen token expiry validation',
       source.branch_id, target.branch_id,
       'open', 18, 18, TRUE, TRUE
FROM repositories r
JOIN branches source
  ON source.repository_id = r.repository_id
 AND source.branch_name = 'feature/token-expiry'
JOIN branches target
  ON target.repository_id = r.repository_id
 AND target.branch_name = 'main'
WHERE r.name = 'identity-platform';

INSERT INTO commits (
    commit_id, repository_id, author_id, message, change_kind, additions, deletions
)
SELECT seed.commit_id, r.repository_id, reviewer.reviewer_id,
       seed.message, seed.change_kind, seed.additions, seed.deletions
FROM (
    VALUES
        ('c100', 'maya', 'Validate token expiry before session lookup',
         'security', 65, 14),
        ('c101', 'liam', 'Add regression coverage for expired tokens',
         'bugfix', 42, 6),
        ('c102', 'maya', 'Document session validation rules',
         'documentation', 18, 3)
) AS seed(commit_id, author, message, change_kind, additions, deletions)
JOIN repositories r ON r.name = 'identity-platform'
JOIN reviewers reviewer ON reviewer.username = seed.author;

INSERT INTO pull_request_commits (pull_request_id, commit_id, position)
SELECT pr.pull_request_id, seed.commit_id, seed.position
FROM pull_requests pr
JOIN (
    VALUES ('c100', 1), ('c101', 2), ('c102', 3)
) AS seed(commit_id, position) ON TRUE
WHERE pr.pull_request_number = 248;

INSERT INTO status_checks (
    pull_request_id, check_name, passed, checked_revision
)
SELECT pr.pull_request_id, seed.check_name, seed.passed, 18
FROM pull_requests pr
CROSS JOIN (
    VALUES
        ('unit-tests', TRUE),
        ('security-scan', TRUE),
        ('integration-tests', TRUE)
) AS seed(check_name, passed)
WHERE pr.pull_request_number = 248;

INSERT INTO reviews (
    pull_request_id, reviewer_id, reviewed_commit_id, state
)
SELECT pr.pull_request_id, reviewer.reviewer_id, 'c102', seed.state
FROM pull_requests pr
CROSS JOIN (
    VALUES ('olivia', 'approved'),
           ('ethan', 'approved'),
           ('maya', 'approved')
) AS seed(username, state)
JOIN reviewers reviewer ON reviewer.username = seed.username
WHERE pr.pull_request_number = 248;

INSERT INTO review_comments (
    review_id, file_path, line_number, body, resolved
)
SELECT review.review_id,
       'src/session.py',
       48,
       'Confirm expiry is checked before retrieving the session.',
       TRUE
FROM reviews review
JOIN reviewers reviewer ON reviewer.reviewer_id = review.reviewer_id
WHERE reviewer.username = 'olivia'
  AND review.pull_request_id = (
      SELECT pull_request_id
      FROM pull_requests
      WHERE pull_request_number = 248
  );

-- A policy query uses current review state per reviewer, not the raw count
-- of all historical approvals. Dismissed decisions cannot count as approvals.
CREATE VIEW merge_eligibility AS
WITH latest_reviews AS (
    SELECT DISTINCT ON (review.pull_request_id, review.reviewer_id)
           review.pull_request_id,
           review.reviewer_id,
           review.state,
           review.dismissed,
           reviewer.username,
           reviewer.active
    FROM reviews review
    JOIN reviewers ON reviewers.reviewer_id = review.reviewer_id
    ORDER BY review.pull_request_id,
             review.reviewer_id,
             review.submitted_at DESC,
             review.review_id DESC
),
approval_counts AS (
    SELECT pr.pull_request_id,
           COUNT(DISTINCT lr.reviewer_id) FILTER (
               WHERE lr.state = 'approved'
                 AND NOT lr.dismissed
                 AND lr.active
                 AND NOT EXISTS (
                     SELECT 1
                     FROM pull_request_commits prc
                     JOIN commits commit ON commit.commit_id = prc.commit_id
                     WHERE prc.pull_request_id = pr.pull_request_id
                       AND commit.author_id = lr.reviewer_id
                 )
           ) AS valid_approvals,
           COUNT(*) FILTER (
               WHERE lr.state = 'changes_requested'
                 AND NOT lr.dismissed
                 AND lr.active
           ) AS active_change_requests
    FROM pull_requests pr
    LEFT JOIN latest_reviews lr
      ON lr.pull_request_id = pr.pull_request_id
    GROUP BY pr.pull_request_id
),
check_results AS (
    SELECT pr.pull_request_id,
           COALESCE(
               bool_and(latest_check.passed),
               FALSE
           ) AS all_required_checks_passed
    FROM pull_requests pr
    JOIN branch_protection bp ON bp.branch_id = pr.target_branch_id
    LEFT JOIN LATERAL unnest(bp.required_checks) AS required(name) ON TRUE
    LEFT JOIN LATERAL (
        SELECT sc.passed
        FROM status_checks sc
        WHERE sc.pull_request_id = pr.pull_request_id
          AND sc.check_name = required.name
          AND sc.checked_revision = pr.current_base_revision
        ORDER BY sc.completed_at DESC, sc.status_check_id DESC
        LIMIT 1
    ) latest_check ON TRUE
    GROUP BY pr.pull_request_id
)
SELECT pr.pull_request_id,
       pr.pull_request_number,
       pr.title,
       source.branch_name AS source_branch,
       target.branch_name AS target_branch,
       pr.state,
       ac.valid_approvals,
       bp.required_approvals,
       ac.active_change_requests,
       cr.all_required_checks_passed,
       pr.conversations_resolved,
       pr.proposed_history_is_linear,
       (pr.base_revision_at_review = pr.current_base_revision)
           AS base_is_synchronized,
       ARRAY_REMOVE(ARRAY[
           CASE WHEN pr.state <> 'open'
                THEN 'Pull request is not open' END,
           CASE WHEN ac.valid_approvals < bp.required_approvals
                THEN 'Insufficient valid approvals' END,
           CASE WHEN ac.active_change_requests > 0
                THEN 'Active change requests remain' END,
           CASE WHEN NOT cr.all_required_checks_passed
                THEN 'Required checks are missing or failing' END,
           CASE WHEN bp.require_resolved_conversations
                     AND NOT pr.conversations_resolved
                THEN 'Review conversations are unresolved' END,
           CASE WHEN bp.require_linear_history
                     AND NOT pr.proposed_history_is_linear
                THEN 'Linear history is required' END,
           CASE WHEN pr.base_revision_at_review <> pr.current_base_revision
                THEN 'Pull request must be synchronized with base branch' END
       ]::TEXT[], NULL) AS blocking_reasons
FROM pull_requests pr
JOIN branches source ON source.branch_id = pr.source_branch_id
JOIN branches target ON target.branch_id = pr.target_branch_id
JOIN branch_protection bp ON bp.branch_id = pr.target_branch_id
JOIN approval_counts ac ON ac.pull_request_id = pr.pull_request_id
JOIN check_results cr ON cr.pull_request_id = pr.pull_request_id;

-- Inspect merge eligibility.
SELECT pull_request_number,
       source_branch,
       target_branch,
       valid_approvals,
       required_approvals,
       all_required_checks_passed,
       base_is_synchronized,
       blocking_reasons,
       cardinality(blocking_reasons) = 0 AS eligible
FROM merge_eligibility
ORDER BY pull_request_number;

-- Procedural and aggregate analysis inside SQL.
SELECT pr.pull_request_number,
       COUNT(DISTINCT prc.commit_id) AS commit_count,
       COUNT(DISTINCT commit.author_id) AS distinct_authors,
       COUNT(DISTINCT path.file_path) AS distinct_files,
       SUM(commit.additions) AS total_additions,
       SUM(commit.deletions) AS total_deletions,
       SUM(commit.additions - commit.deletions) AS net_line_change
FROM pull_requests pr
JOIN pull_request_commits prc ON prc.pull_request_id = pr.pull_request_id
JOIN commits commit ON commit.commit_id = prc.commit_id
JOIN LATERAL (
    SELECT unnest(ARRAY[
        CASE WHEN commit.commit_id = 'c100' THEN 'src/session.py' END,
        CASE WHEN commit.commit_id = 'c101' THEN 'tests/session_test.py' END,
        CASE WHEN commit.commit_id = 'c102' THEN 'docs/session.md' END
    ]) AS file_path
) path ON path.file_path IS NOT NULL
GROUP BY pr.pull_request_number;

-- A failed check for the current base revision makes eligibility false.
INSERT INTO status_checks (
    pull_request_id, check_name, passed, checked_revision
)
SELECT pull_request_id, 'integration-tests', FALSE, 19
FROM pull_requests
WHERE pull_request_number = 248;

UPDATE pull_requests
SET current_base_revision = 19
WHERE pull_request_number = 248;

SELECT pull_request_number, all_required_checks_passed, blocking_reasons
FROM merge_eligibility
WHERE pull_request_number = 248;

-- Protected branch governance is represented as data that can be inspected
-- independently of individual review decisions.
SELECT branch.branch_name,
       protection.required_approvals,
       protection.required_checks,
       protection.prohibit_direct_push,
       protection.prohibit_force_push,
       protection.prohibit_deletion,
       protection.require_resolved_conversations,
       protection.require_linear_history,
       protection.allow_admin_bypass
FROM branch_protection protection
JOIN branches branch ON branch.branch_id = protection.branch_id
ORDER BY branch.branch_name;

COMMIT;
