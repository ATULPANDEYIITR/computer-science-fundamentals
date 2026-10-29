DROP SCHEMA IF EXISTS tree_learning CASCADE;
CREATE SCHEMA tree_learning;

SET search_path TO tree_learning, public;

CREATE TYPE node_kind AS ENUM ('ROOT', 'INTERNAL', 'LEAF');
CREATE TYPE traversal_kind AS ENUM ('PREORDER', 'INORDER', 'POSTORDER', 'LEVEL_ORDER');

CREATE TABLE trees (
    tree_id BIGSERIAL PRIMARY KEY,
    tree_name TEXT NOT NULL UNIQUE,
    tree_type TEXT NOT NULL CHECK (tree_type IN ('BINARY', 'BINARY_SEARCH')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tree_nodes (
    node_id BIGSERIAL PRIMARY KEY,
    tree_id BIGINT NOT NULL REFERENCES trees(tree_id) ON DELETE CASCADE,
    value INTEGER NOT NULL,
    parent_node_id BIGINT,
    left_node_id BIGINT,
    right_node_id BIGINT,
    kind node_kind NOT NULL,
    depth INTEGER NOT NULL DEFAULT 0 CHECK (depth >= 0),
    CONSTRAINT tree_node_parent_fk
        FOREIGN KEY (tree_id, parent_node_id)
        REFERENCES tree_nodes(tree_id, node_id)
        DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT tree_node_left_fk
        FOREIGN KEY (tree_id, left_node_id)
        REFERENCES tree_nodes(tree_id, node_id)
        DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT tree_node_right_fk
        FOREIGN KEY (tree_id, right_node_id)
        REFERENCES tree_nodes(tree_id, node_id)
        DEFERRABLE INITIALLY DEFERRED
);

CREATE UNIQUE INDEX one_root_per_tree
    ON tree_nodes(tree_id)
    WHERE parent_node_id IS NULL;

CREATE UNIQUE INDEX unique_bst_value_per_tree
    ON tree_nodes(tree_id, value);

CREATE INDEX tree_nodes_parent_idx
    ON tree_nodes(tree_id, parent_node_id);

CREATE INDEX tree_nodes_value_idx
    ON tree_nodes(tree_id, value);

CREATE TABLE traversal_runs (
    traversal_id BIGSERIAL PRIMARY KEY,
    tree_id BIGINT NOT NULL REFERENCES trees(tree_id) ON DELETE CASCADE,
    traversal traversal_kind NOT NULL,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    duration_ms NUMERIC(12,3) CHECK (duration_ms >= 0)
);

CREATE TABLE traversal_results (
    traversal_id BIGINT NOT NULL REFERENCES traversal_runs(traversal_id) ON DELETE CASCADE,
    sequence_no INTEGER NOT NULL CHECK (sequence_no > 0),
    node_id BIGINT NOT NULL REFERENCES tree_nodes(node_id) ON DELETE CASCADE,
    value INTEGER NOT NULL,
    PRIMARY KEY (traversal_id, sequence_no)
);

CREATE OR REPLACE FUNCTION validate_node_relationships()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    parent_value INTEGER;
    left_value INTEGER;
    right_value INTEGER;
BEGIN
    IF NEW.parent_node_id IS NOT NULL THEN
        SELECT value
        INTO parent_value
        FROM tree_nodes
        WHERE tree_id = NEW.tree_id
          AND node_id = NEW.parent_node_id;

        IF parent_value IS NULL THEN
            RAISE EXCEPTION 'Parent node % does not exist in tree %',
                NEW.parent_node_id, NEW.tree_id;
        END IF;
    END IF;

    IF NEW.left_node_id IS NOT NULL THEN
        SELECT value
        INTO left_value
        FROM tree_nodes
        WHERE tree_id = NEW.tree_id
          AND node_id = NEW.left_node_id;

        IF left_value IS NULL OR left_value >= NEW.value THEN
            RAISE EXCEPTION
                'Left child must have a smaller value than parent node %',
                NEW.node_id;
        END IF;
    END IF;

    IF NEW.right_node_id IS NOT NULL THEN
        SELECT value
        INTO right_value
        FROM tree_nodes
        WHERE tree_id = NEW.tree_id
          AND node_id = NEW.right_node_id;

        IF right_value IS NULL OR right_value <= NEW.value THEN
            RAISE EXCEPTION
                'Right child must have a larger value than parent node %',
                NEW.node_id;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE CONSTRAINT TRIGGER validate_tree_node_relationships
AFTER INSERT OR UPDATE ON tree_nodes
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION validate_node_relationships();

CREATE OR REPLACE FUNCTION refresh_node_kind()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE tree_nodes
    SET kind = CASE
        WHEN parent_node_id IS NULL THEN 'ROOT'::node_kind
        WHEN left_node_id IS NULL AND right_node_id IS NULL
            THEN 'LEAF'::node_kind
        ELSE 'INTERNAL'::node_kind
    END
    WHERE node_id = NEW.node_id;

    RETURN NEW;
END;
$$;

CREATE TRIGGER refresh_tree_node_kind
AFTER INSERT OR UPDATE OF parent_node_id, left_node_id, right_node_id
ON tree_nodes
FOR EACH ROW
EXECUTE FUNCTION refresh_node_kind();

CREATE OR REPLACE FUNCTION bst_insert(
    p_tree_id BIGINT,
    p_value INTEGER
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    current_id BIGINT;
    current_value INTEGER;
    new_id BIGINT;
    current_depth INTEGER;
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM trees
        WHERE tree_id = p_tree_id
          AND tree_type = 'BINARY_SEARCH'
    ) THEN
        RAISE EXCEPTION 'Tree % is not a BINARY_SEARCH tree', p_tree_id;
    END IF;

    SELECT node_id
    INTO current_id
    FROM tree_nodes
    WHERE tree_id = p_tree_id
      AND parent_node_id IS NULL;

    IF current_id IS NULL THEN
        INSERT INTO tree_nodes (
            tree_id, value, kind, depth
        )
        VALUES (
            p_tree_id, p_value, 'ROOT', 0
        )
        RETURNING node_id INTO new_id;

        RETURN new_id;
    END IF;

    LOOP
        SELECT value, depth
        INTO current_value, current_depth
        FROM tree_nodes
        WHERE node_id = current_id
        FOR UPDATE;

        IF p_value = current_value THEN
            RAISE EXCEPTION 'Duplicate value % in tree %',
                p_value, p_tree_id;
        END IF;

        IF p_value < current_value THEN
            SELECT left_node_id
            INTO new_id
            FROM tree_nodes
            WHERE node_id = current_id
            FOR UPDATE;

            IF new_id IS NULL THEN
                INSERT INTO tree_nodes (
                    tree_id,
                    value,
                    parent_node_id,
                    kind,
                    depth
                )
                VALUES (
                    p_tree_id,
                    p_value,
                    current_id,
                    'LEAF',
                    current_depth + 1
                )
                RETURNING node_id INTO new_id;

                UPDATE tree_nodes
                SET left_node_id = new_id
                WHERE node_id = current_id;

                RETURN new_id;
            END IF;

            current_id := new_id;
        ELSE
            SELECT right_node_id
            INTO new_id
            FROM tree_nodes
            WHERE node_id = current_id
            FOR UPDATE;

            IF new_id IS NULL THEN
                INSERT INTO tree_nodes (
                    tree_id,
                    value,
                    parent_node_id,
                    kind,
                    depth
                )
                VALUES (
                    p_tree_id,
                    p_value,
                    current_id,
                    'LEAF',
                    current_depth + 1
                )
                RETURNING node_id INTO new_id;

                UPDATE tree_nodes
                SET right_node_id = new_id
                WHERE node_id = current_id;

                RETURN new_id;
            END IF;

            current_id := new_id;
        END IF;
    END LOOP;
END;
$$;

CREATE OR REPLACE FUNCTION tree_height(p_tree_id BIGINT)
RETURNS INTEGER
LANGUAGE sql
STABLE
AS $$
    SELECT COALESCE(MAX(depth) + 1, 0)::INTEGER
    FROM tree_nodes
    WHERE tree_id = p_tree_id;
$$;

CREATE OR REPLACE VIEW tree_structure AS
SELECT
    n.tree_id,
    t.tree_name,
    n.node_id,
    n.value,
    n.kind,
    n.parent_node_id,
    n.left_node_id,
    n.right_node_id,
    n.depth
FROM tree_nodes n
JOIN trees t ON t.tree_id = n.tree_id;

CREATE OR REPLACE VIEW tree_leaf_report AS
SELECT
    t.tree_id,
    t.tree_name,
    COUNT(n.node_id) FILTER (
        WHERE n.left_node_id IS NULL
          AND n.right_node_id IS NULL
    ) AS leaf_count,
    tree_height(t.tree_id) AS height
FROM trees t
LEFT JOIN tree_nodes n
    ON n.tree_id = t.tree_id
GROUP BY t.tree_id, t.tree_name;

INSERT INTO trees (tree_name, tree_type)
VALUES
    ('employee_hierarchy_demo', 'BINARY'),
    ('commit_index_demo', 'BINARY_SEARCH');

-- A normal binary tree can contain arbitrary child values.
INSERT INTO tree_nodes (
    tree_id, value, kind, depth
)
SELECT tree_id, 10, 'ROOT', 0
FROM trees
WHERE tree_name = 'employee_hierarchy_demo';

INSERT INTO tree_nodes (
    tree_id, value, parent_node_id, kind, depth
)
SELECT
    t.tree_id,
    v.value,
    root.node_id,
    'LEAF',
    v.depth
FROM trees t
JOIN tree_nodes root
    ON root.tree_id = t.tree_id
   AND root.parent_node_id IS NULL
CROSS JOIN (
    VALUES
        (5, 1),
        (20, 1)
) AS v(value, depth)
WHERE t.tree_name = 'employee_hierarchy_demo';

UPDATE tree_nodes root
SET
    left_node_id = (
        SELECT node_id
        FROM tree_nodes
        WHERE tree_id = root.tree_id
          AND value = 5
    ),
    right_node_id = (
        SELECT node_id
        FROM tree_nodes
        WHERE tree_id = root.tree_id
          AND value = 20
    )
WHERE root.tree_id = (
    SELECT tree_id
    FROM trees
    WHERE tree_name = 'employee_hierarchy_demo'
);

-- The BST is populated through the transactional insertion function.
BEGIN;

SELECT bst_insert(
    (SELECT tree_id FROM trees WHERE tree_name = 'commit_index_demo'),
    value
)
FROM unnest(ARRAY[50, 30, 70, 20, 40, 60, 80, 65]) AS value;

COMMIT;

-- Retrieval and structural inspection.
SELECT *
FROM tree_structure
ORDER BY tree_id, depth, node_id;

-- Height and leaf reporting.
SELECT *
FROM tree_leaf_report
ORDER BY tree_id;

-- Recursive traversal. This CTE produces a root-to-node path.
WITH RECURSIVE paths AS (
    SELECT
        node_id,
        tree_id,
        value,
        parent_node_id,
        1 AS level,
        ARRAY[node_id] AS path
    FROM tree_nodes
    WHERE parent_node_id IS NULL

    UNION ALL

    SELECT
        child.node_id,
        child.tree_id,
        child.value,
        child.parent_node_id,
        parent.level + 1,
        parent.path || child.node_id
    FROM tree_nodes child
    JOIN paths parent
      ON child.parent_node_id = parent.node_id
     AND child.tree_id = parent.tree_id
)
SELECT
    tree_id,
    node_id,
    value,
    level,
    path
FROM paths
ORDER BY tree_id, path;

-- In-order sequence for the BST.
WITH RECURSIVE inorder AS (
    SELECT
        node_id,
        tree_id,
        value,
        left_node_id,
        right_node_id,
        1 AS emitted
    FROM tree_nodes
    WHERE tree_id = (
        SELECT tree_id
        FROM trees
        WHERE tree_name = 'commit_index_demo'
    )
      AND parent_node_id IS NULL

    UNION ALL

    SELECT
        child.node_id,
        child.tree_id,
        child.value,
        child.left_node_id,
        child.right_node_id,
        inorder.emitted + 1
    FROM tree_nodes child
    JOIN inorder
      ON child.node_id = inorder.left_node_id
      OR child.node_id = inorder.right_node_id
)
SELECT
    tree_id,
    value,
    depth
FROM tree_nodes
WHERE tree_id = (
    SELECT tree_id
    FROM trees
    WHERE tree_name = 'commit_index_demo'
)
ORDER BY value;

-- Aggregate distribution by depth.
SELECT
    t.tree_name,
    n.depth,
    COUNT(*) AS nodes_at_depth,
    MIN(n.value) AS minimum_value,
    MAX(n.value) AS maximum_value
FROM tree_nodes n
JOIN trees t ON t.tree_id = n.tree_id
GROUP BY t.tree_name, n.depth
ORDER BY t.tree_name, n.depth;

-- Transactional failure example. The duplicate value is rejected and
-- the transaction is rolled back without changing the existing tree.
BEGIN;

DO $$
BEGIN
    PERFORM bst_insert(
        (SELECT tree_id
         FROM trees
         WHERE tree_name = 'commit_index_demo'),
        50
    );
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Expected duplicate-key failure: %', SQLERRM;
        ROLLBACK;
        RETURN;
END;
$$;

-- Explicit validation query for BST ordering.
WITH violations AS (
    SELECT child.node_id, child.value, parent.value AS parent_value
    FROM tree_nodes child
    JOIN tree_nodes parent
      ON parent.node_id = child.parent_node_id
    WHERE child.tree_id = (
        SELECT tree_id
        FROM trees
        WHERE tree_name = 'commit_index_demo'
    )
    AND (
        (child.node_id = parent.left_node_id AND child.value >= parent.value)
        OR
        (child.node_id = parent.right_node_id AND child.value <= parent.value)
    )
)
SELECT *
FROM violations;

-- Eligibility-style query: nodes that satisfy the structural condition
-- for being leaves.
SELECT
    t.tree_name,
    n.node_id,
    n.value,
    n.depth
FROM tree_nodes n
JOIN trees t ON t.tree_id = n.tree_id
WHERE n.left_node_id IS NULL
  AND n.right_node_id IS NULL
ORDER BY t.tree_name, n.value;

-- Performance inspection for the indexed value lookup.
EXPLAIN (ANALYZE, BUFFERS)
SELECT node_id, value
FROM tree_nodes
WHERE tree_id = (
    SELECT tree_id
    FROM trees
    WHERE tree_name = 'commit_index_demo'
)
AND value = 65;
