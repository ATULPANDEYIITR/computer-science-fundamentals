DROP SCHEMA IF EXISTS balanced_tree_lab CASCADE;
CREATE SCHEMA balanced_tree_lab;
SET search_path = balanced_tree_lab, public;

CREATE TYPE tree_kind AS ENUM ('AVL', 'RED_BLACK');

CREATE TABLE repositories (
    repository_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_name TEXT NOT NULL UNIQUE,
    tree_kind tree_kind NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE branches (
    branch_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id) ON DELETE CASCADE,
    branch_name TEXT NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    protected BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (repository_id, branch_name)
);

CREATE TABLE commits (
    commit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id) ON DELETE CASCADE,
    branch_id BIGINT NOT NULL REFERENCES branches(branch_id) ON DELETE CASCADE,
    commit_hash CHAR(40) NOT NULL UNIQUE,
    parent_commit_id BIGINT REFERENCES commits(commit_id),
    tree_key INTEGER NOT NULL,
    committed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (tree_key > 0)
);

CREATE TABLE tree_nodes (
    node_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id) ON DELETE CASCADE,
    parent_node_id BIGINT REFERENCES tree_nodes(node_id),
    tree_key INTEGER NOT NULL,
    node_color TEXT,
    node_height INTEGER NOT NULL DEFAULT 1,
    UNIQUE (repository_id, tree_key),
    CHECK (tree_key > 0),
    CHECK (node_height > 0),
    CHECK (node_color IS NULL OR node_color IN ('RED', 'BLACK'))
);

CREATE TABLE rotations (
    rotation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id) ON DELETE CASCADE,
    tree_key INTEGER NOT NULL,
    rotation_type TEXT NOT NULL CHECK (rotation_type IN ('LEFT', 'RIGHT')),
    reason TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_branches_repository ON branches(repository_id);
CREATE INDEX idx_commits_branch_time ON commits(branch_id, committed_at DESC);
CREATE INDEX idx_tree_nodes_repository_key ON tree_nodes(repository_id, tree_key);
CREATE INDEX idx_rotations_repository_time ON rotations(repository_id, occurred_at DESC);

CREATE OR REPLACE FUNCTION enforce_tree_node_metadata()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.node_color IS NOT NULL
       AND NEW.node_color NOT IN ('RED', 'BLACK') THEN
        RAISE EXCEPTION 'Unsupported tree color: %', NEW.node_color;
    END IF;

    IF NEW.node_height < 1 THEN
        RAISE EXCEPTION 'Tree height must be positive';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_tree_node_metadata
BEFORE INSERT OR UPDATE ON tree_nodes
FOR EACH ROW
EXECUTE FUNCTION enforce_tree_node_metadata();

CREATE OR REPLACE FUNCTION record_rotation(
    p_repository_id BIGINT,
    p_tree_key INTEGER,
    p_rotation_type TEXT,
    p_reason TEXT
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_id BIGINT;
BEGIN
    IF p_rotation_type NOT IN ('LEFT', 'RIGHT') THEN
        RAISE EXCEPTION 'Rotation must be LEFT or RIGHT';
    END IF;

    IF p_tree_key <= 0 THEN
        RAISE EXCEPTION 'Tree key must be positive';
    END IF;

    INSERT INTO rotations(repository_id, tree_key, rotation_type, reason)
    VALUES (p_repository_id, p_tree_key, p_rotation_type, p_reason)
    RETURNING rotation_id INTO v_id;

    RETURN v_id;
END;
$$;

CREATE OR REPLACE FUNCTION repository_tree_height(p_repository_id BIGINT)
RETURNS INTEGER
LANGUAGE SQL
STABLE
AS $$
    SELECT COALESCE(MAX(node_height), 0)
    FROM tree_nodes
    WHERE repository_id = p_repository_id;
$$;

CREATE VIEW repository_tree_report AS
SELECT
    r.repository_id,
    r.repository_name,
    r.tree_kind,
    COUNT(t.node_id) AS node_count,
    COALESCE(MAX(t.node_height), 0) AS recorded_height,
    COUNT(rot.rotation_id) AS rotation_count
FROM repositories r
LEFT JOIN tree_nodes t
    ON t.repository_id = r.repository_id
LEFT JOIN rotations rot
    ON rot.repository_id = r.repository_id
GROUP BY r.repository_id, r.repository_name, r.tree_kind;

INSERT INTO repositories(repository_name, tree_kind)
VALUES
    ('payments-api', 'AVL'),
    ('identity-service', 'AVL'),
    ('search-index', 'RED_BLACK');

INSERT INTO branches(repository_id, branch_name, is_default, protected)
SELECT repository_id, 'main', TRUE, TRUE
FROM repositories;

INSERT INTO branches(repository_id, branch_name, protected)
SELECT repository_id, 'feature/balanced-index', TRUE
FROM repositories
WHERE repository_name IN ('payments-api', 'search-index');

INSERT INTO commits(
    repository_id,
    branch_id,
    commit_hash,
    tree_key
)
SELECT
    r.repository_id,
    b.branch_id,
    repeat(to_hex(r.repository_id), 40)::char(40),
    r.repository_id::integer * 10
FROM repositories r
JOIN branches b
    ON b.repository_id = r.repository_id
WHERE b.is_default;

INSERT INTO tree_nodes(
    repository_id,
    tree_key,
    node_color,
    node_height
)
SELECT repository_id, repository_id::integer * 10, 'BLACK', 1
FROM repositories;

INSERT INTO tree_nodes(
    repository_id,
    tree_key,
    node_color,
    node_height
)
SELECT repository_id, repository_id::integer * 10 + 1, 'RED', 1
FROM repositories
WHERE tree_kind = 'RED_BLACK';

SELECT record_rotation(
    repository_id,
    repository_id::integer * 10,
    'RIGHT',
    'LL imbalance after monotonic insertion'
)
FROM repositories
WHERE tree_kind = 'AVL'
LIMIT 1;

SELECT record_rotation(
    repository_id,
    repository_id::integer * 10 + 1,
    'LEFT',
    'RR imbalance after monotonic insertion'
)
FROM repositories
WHERE tree_kind = 'AVL'
LIMIT 1;

-- A CTE identifies repositories whose recorded height is suspiciously
-- large relative to their node count. This is a monitoring signal rather
-- than a proof of balance because relational rows do not encode every
-- child relationship required to reconstruct the full tree.
WITH tree_health AS (
    SELECT
        repository_id,
        COUNT(*) AS node_count,
        MAX(node_height) AS height
    FROM tree_nodes
    GROUP BY repository_id
)
SELECT
    r.repository_name,
    r.tree_kind,
    h.node_count,
    h.height,
    CASE
        WHEN h.node_count <= 2 THEN 'SMALL'
        WHEN h.height <= CEIL(LOG(2, h.node_count + 1)) * 2
            THEN 'WITHIN_EXPECTED_RANGE'
        ELSE 'REVIEW'
    END AS health_state
FROM repositories r
JOIN tree_health h USING (repository_id)
ORDER BY r.repository_name;

SELECT
    repository_name,
    tree_kind,
    node_count,
    recorded_height,
    rotation_count
FROM repository_tree_report
ORDER BY repository_id;

SELECT
    r.repository_name,
    b.branch_name,
    b.protected,
    COUNT(c.commit_id) AS commit_count
FROM repositories r
JOIN branches b USING (repository_id)
LEFT JOIN commits c USING (branch_id)
GROUP BY r.repository_name, b.branch_name, b.protected
ORDER BY r.repository_name, b.branch_name;

-- Transactional insertion models a tree mutation plus its audit event.
BEGIN;

INSERT INTO tree_nodes(
    repository_id,
    tree_key,
    node_color,
    node_height
)
SELECT repository_id, 99, 'BLACK', 2
FROM repositories
WHERE repository_name = 'payments-api';

INSERT INTO rotations(
    repository_id,
    tree_key,
    rotation_type,
    reason
)
SELECT repository_id, 99, 'LEFT', 'Rebalancing after insertion'
FROM repositories
WHERE repository_name = 'payments-api';

COMMIT;

-- Expected failure: duplicate repository name.
DO $$
BEGIN
    BEGIN
        INSERT INTO repositories(repository_name, tree_kind)
        VALUES ('payments-api', 'AVL');
    EXCEPTION
        WHEN unique_violation THEN
            RAISE NOTICE 'Duplicate repository rejected as expected';
    END;
END;
$$;

-- Expected failure: invalid tree height.
DO $$
DECLARE
    v_repository_id BIGINT;
BEGIN
    SELECT repository_id
    INTO v_repository_id
    FROM repositories
    WHERE repository_name = 'identity-service';

    BEGIN
        INSERT INTO tree_nodes(
            repository_id,
            tree_key,
            node_color,
            node_height
        )
        VALUES (v_repository_id, 1000, 'BLACK', 0);
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'Invalid height rejected as expected';
    END;
END;
$$;

SELECT
    repository_name,
    repository_tree_height(repository_id) AS maximum_recorded_height
FROM repositories
ORDER BY repository_name;
