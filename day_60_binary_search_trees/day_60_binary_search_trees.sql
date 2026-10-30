BEGIN;

DROP SCHEMA IF EXISTS bst_lab CASCADE;
CREATE SCHEMA bst_lab;
SET search_path TO bst_lab, public;

CREATE TYPE tree_strategy AS ENUM (
    'BST',
    'REBUILT_BALANCED'
);

CREATE TYPE tree_event_type AS ENUM (
    'INSERT',
    'DELETE'
);

-- A catalog identifies a separate ordered index and its construction strategy.
CREATE TABLE tree_catalog (
    tree_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tree_name VARCHAR(100) NOT NULL UNIQUE,
    strategy tree_strategy NOT NULL,
    root_key INTEGER,
    node_count INTEGER NOT NULL DEFAULT 0 CHECK (node_count >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- This table is authoritative. Tree nodes are a derived search structure.
CREATE TABLE tree_item (
    tree_id BIGINT NOT NULL REFERENCES tree_catalog(tree_id)
        ON DELETE CASCADE,
    record_key INTEGER NOT NULL,
    payload VARCHAR(200) NOT NULL
        CHECK (length(btrim(payload)) > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (tree_id, record_key)
);

-- Adjacency representation: each row stores its parent and child keys.
-- Composite foreign keys prevent links from crossing separate trees.
CREATE TABLE tree_node (
    tree_id BIGINT NOT NULL,
    node_key INTEGER NOT NULL,
    parent_key INTEGER,
    left_key INTEGER,
    right_key INTEGER,
    PRIMARY KEY (tree_id, node_key),

    CONSTRAINT node_item_fk
        FOREIGN KEY (tree_id, node_key)
        REFERENCES tree_item(tree_id, record_key)
        ON DELETE CASCADE
        DEFERRABLE INITIALLY DEFERRED,

    CONSTRAINT node_parent_fk
        FOREIGN KEY (tree_id, parent_key)
        REFERENCES tree_node(tree_id, node_key)
        DEFERRABLE INITIALLY DEFERRED,

    CONSTRAINT node_left_fk
        FOREIGN KEY (tree_id, left_key)
        REFERENCES tree_node(tree_id, node_key)
        DEFERRABLE INITIALLY DEFERRED,

    CONSTRAINT node_right_fk
        FOREIGN KEY (tree_id, right_key)
        REFERENCES tree_node(tree_id, node_key)
        DEFERRABLE INITIALLY DEFERRED,

    CONSTRAINT node_not_own_parent
        CHECK (parent_key IS DISTINCT FROM node_key),

    CONSTRAINT node_not_own_child
        CHECK (
            left_key IS DISTINCT FROM node_key
            AND right_key IS DISTINCT FROM node_key
        ),

    CONSTRAINT node_distinct_children
        CHECK (left_key IS DISTINCT FROM right_key)
);

ALTER TABLE tree_catalog
ADD CONSTRAINT catalog_root_fk
FOREIGN KEY (tree_id, root_key)
REFERENCES tree_node(tree_id, node_key)
DEFERRABLE INITIALLY DEFERRED;

CREATE TABLE tree_event (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tree_id BIGINT NOT NULL,
    record_key INTEGER NOT NULL,
    event_type tree_event_type NOT NULL,
    event_time TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    database_user NAME NOT NULL DEFAULT CURRENT_USER
);

-- The composite primary keys already support tree-specific key lookups.
-- This index supports time-ordered audit retrieval for a particular tree.
CREATE INDEX tree_event_history_idx
    ON tree_event(tree_id, event_time DESC);

CREATE OR REPLACE FUNCTION log_tree_item_change()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO tree_event(tree_id, record_key, event_type)
        VALUES (NEW.tree_id, NEW.record_key, 'INSERT');

        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO tree_event(tree_id, record_key, event_type)
        VALUES (OLD.tree_id, OLD.record_key, 'DELETE');

        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$;

CREATE TRIGGER tree_item_audit_trigger
AFTER INSERT OR DELETE ON tree_item
FOR EACH ROW
EXECUTE FUNCTION log_tree_item_change();


-- Attach a newly inserted item to an ordinary, unbalanced BST.
CREATE OR REPLACE FUNCTION bst_attach(
    p_tree_id BIGINT,
    p_key INTEGER
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    current_key INTEGER;
    next_key INTEGER;
BEGIN
    SELECT root_key
    INTO current_key
    FROM tree_catalog
    WHERE tree_id = p_tree_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Unknown tree ID: %', p_tree_id;
    END IF;

    IF current_key IS NULL THEN
        INSERT INTO tree_node(tree_id, node_key)
        VALUES (p_tree_id, p_key);

        UPDATE tree_catalog
        SET root_key = p_key,
            node_count = node_count + 1
        WHERE tree_id = p_tree_id;

        RETURN;
    END IF;

    LOOP
        IF p_key = current_key THEN
            RAISE EXCEPTION 'Duplicate key in tree: %', p_key;
        END IF;

        IF p_key < current_key THEN
            SELECT left_key
            INTO next_key
            FROM tree_node
            WHERE tree_id = p_tree_id
              AND node_key = current_key;

            IF next_key IS NULL THEN
                INSERT INTO tree_node(tree_id, node_key, parent_key)
                VALUES (p_tree_id, p_key, current_key);

                UPDATE tree_node
                SET left_key = p_key
                WHERE tree_id = p_tree_id
                  AND node_key = current_key;

                EXIT;
            END IF;
        ELSE
            SELECT right_key
            INTO next_key
            FROM tree_node
            WHERE tree_id = p_tree_id
              AND node_key = current_key;

            IF next_key IS NULL THEN
                INSERT INTO tree_node(tree_id, node_key, parent_key)
                VALUES (p_tree_id, p_key, current_key);

                UPDATE tree_node
                SET right_key = p_key
                WHERE tree_id = p_tree_id
                  AND node_key = current_key;

                EXIT;
            END IF;
        END IF;

        current_key := next_key;
    END LOOP;

    UPDATE tree_catalog
    SET node_count = node_count + 1
    WHERE tree_id = p_tree_id;
END;
$$;


-- Rebuild a balanced binary search tree from the ordered authoritative keys.
-- This is deliberately a rebuild strategy, not an AVL rotation algorithm.
CREATE OR REPLACE FUNCTION build_balanced_subtree(
    p_tree_id BIGINT,
    p_keys INTEGER[],
    p_low INTEGER,
    p_high INTEGER,
    p_parent INTEGER
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    middle INTEGER;
    selected_key INTEGER;
    left_root INTEGER;
    right_root INTEGER;
BEGIN
    IF p_low > p_high THEN
        RETURN NULL;
    END IF;

    middle := (p_low + p_high) / 2;
    selected_key := p_keys[middle];

    INSERT INTO tree_node(tree_id, node_key, parent_key)
    VALUES (p_tree_id, selected_key, p_parent);

    left_root := build_balanced_subtree(
        p_tree_id,
        p_keys,
        p_low,
        middle - 1,
        selected_key
    );

    right_root := build_balanced_subtree(
        p_tree_id,
        p_keys,
        middle + 1,
        p_high,
        selected_key
    );

    UPDATE tree_node
    SET left_key = left_root,
        right_key = right_root
    WHERE tree_id = p_tree_id
      AND node_key = selected_key;

    RETURN selected_key;
END;
$$;

CREATE OR REPLACE FUNCTION rebuild_balanced_tree(
    p_tree_id BIGINT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    key_array INTEGER[];
    new_root INTEGER;
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM tree_catalog
        WHERE tree_id = p_tree_id
          AND strategy = 'REBUILT_BALANCED'
    ) THEN
        RAISE EXCEPTION 'Tree % is not configured for rebuilding', p_tree_id;
    END IF;

    SELECT array_agg(record_key ORDER BY record_key)
    INTO key_array
    FROM tree_item
    WHERE tree_id = p_tree_id;

    -- The deferred self-references allow the complete old shape to be
    -- replaced within this transaction.
    UPDATE tree_catalog
    SET root_key = NULL,
        node_count = 0
    WHERE tree_id = p_tree_id;

    DELETE FROM tree_node
    WHERE tree_id = p_tree_id;

    new_root := build_balanced_subtree(
        p_tree_id,
        key_array,
        1,
        COALESCE(array_length(key_array, 1), 0),
        NULL
    );

    UPDATE tree_catalog
    SET root_key = new_root,
        node_count = COALESCE(array_length(key_array, 1), 0)
    WHERE tree_id = p_tree_id;
END;
$$;


-- The transplant operation replaces one node with another while preserving
-- parent-to-child references. Foreign keys are checked at transaction end.
CREATE OR REPLACE FUNCTION bst_transplant(
    p_tree_id BIGINT,
    p_old_key INTEGER,
    p_new_key INTEGER
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    old_parent INTEGER;
    old_left INTEGER;
    old_right INTEGER;
BEGIN
    SELECT parent_key, left_key, right_key
    INTO old_parent, old_left, old_right
    FROM tree_node
    WHERE tree_id = p_tree_id
      AND node_key = p_old_key;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Node % does not exist in tree %',
            p_old_key, p_tree_id;
    END IF;

    IF old_parent IS NULL THEN
        UPDATE tree_catalog
        SET root_key = p_new_key
        WHERE tree_id = p_tree_id;
    ELSIF EXISTS (
        SELECT 1
        FROM tree_node
        WHERE tree_id = p_tree_id
          AND node_key = old_parent
          AND left_key = p_old_key
    ) THEN
        UPDATE tree_node
        SET left_key = p_new_key
        WHERE tree_id = p_tree_id
          AND node_key = old_parent;
    ELSE
        UPDATE tree_node
        SET right_key = p_new_key
        WHERE tree_id = p_tree_id
          AND node_key = old_parent
          AND right_key = p_old_key;
    END IF;

    IF p_new_key IS NOT NULL THEN
        UPDATE tree_node
        SET parent_key = old_parent
        WHERE tree_id = p_tree_id
          AND node_key = p_new_key;
    END IF;
END;
$$;


-- Remove a node from the unbalanced BST.
CREATE OR REPLACE FUNCTION bst_delete_node(
    p_tree_id BIGINT,
    p_key INTEGER
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    z_left INTEGER;
    z_right INTEGER;
    successor_key INTEGER;
    successor_parent INTEGER;
    successor_right INTEGER;
BEGIN
    SELECT left_key, right_key
    INTO z_left, z_right
    FROM tree_node
    WHERE tree_id = p_tree_id
      AND node_key = p_key;

    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;

    IF z_left IS NULL THEN
        PERFORM bst_transplant(p_tree_id, p_key, z_right);

    ELSIF z_right IS NULL THEN
        PERFORM bst_transplant(p_tree_id, p_key, z_left);

    ELSE
        -- The inorder successor is the minimum node in the right subtree.
        successor_key := z_right;

        LOOP
            SELECT left_key
            INTO successor_key
            FROM tree_node
            WHERE tree_id = p_tree_id
              AND node_key = successor_key
            AND left_key IS NOT NULL;

            IF NOT FOUND THEN
                EXIT;
            END IF;
        END LOOP;

        SELECT parent_key, right_key
        INTO successor_parent, successor_right
        FROM tree_node
        WHERE tree_id = p_tree_id
          AND node_key = successor_key;

        IF successor_parent <> p_key THEN
            PERFORM bst_transplant(
                p_tree_id,
                successor_key,
                successor_right
            );

            UPDATE tree_node
            SET right_key = z_right
            WHERE tree_id = p_tree_id
              AND node_key = successor_key;

            UPDATE tree_node
            SET parent_key = successor_key
            WHERE tree_id = p_tree_id
              AND node_key = z_right;
        END IF;

        PERFORM bst_transplant(
            p_tree_id,
            p_key,
            successor_key
        );

        UPDATE tree_node
        SET left_key = z_left
        WHERE tree_id = p_tree_id
          AND node_key = successor_key;

        UPDATE tree_node
        SET parent_key = successor_key
        WHERE tree_id = p_tree_id
          AND node_key = z_left;
    END IF;

    DELETE FROM tree_node
    WHERE tree_id = p_tree_id
      AND node_key = p_key;

    UPDATE tree_catalog
    SET node_count = node_count - 1
    WHERE tree_id = p_tree_id;

    RETURN TRUE;
END;
$$;


-- Insert a record and update the selected index in the same transaction.
CREATE OR REPLACE FUNCTION insert_item(
    p_tree_id BIGINT,
    p_key INTEGER,
    p_payload VARCHAR(200)
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    selected_strategy tree_strategy;
BEGIN
    SELECT strategy
    INTO selected_strategy
    FROM tree_catalog
    WHERE tree_id = p_tree_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Unknown tree ID: %', p_tree_id;
    END IF;

    IF p_payload IS NULL OR length(btrim(p_payload)) = 0 THEN
        RAISE EXCEPTION 'Payload cannot be empty';
    END IF;

    INSERT INTO tree_item(tree_id, record_key, payload)
    VALUES (p_tree_id, p_key, p_payload);

    IF selected_strategy = 'BST' THEN
        PERFORM bst_attach(p_tree_id, p_key);
    ELSE
        PERFORM rebuild_balanced_tree(p_tree_id);
    END IF;
END;
$$;


-- Delete an item and maintain the corresponding search structure.
CREATE OR REPLACE FUNCTION delete_item(
    p_tree_id BIGINT,
    p_key INTEGER
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    selected_strategy tree_strategy;
BEGIN
    SELECT strategy
    INTO selected_strategy
    FROM tree_catalog
    WHERE tree_id = p_tree_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Unknown tree ID: %', p_tree_id;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM tree_item
        WHERE tree_id = p_tree_id
          AND record_key = p_key
    ) THEN
        RETURN FALSE;
    END IF;

    IF selected_strategy = 'BST' THEN
        IF NOT bst_delete_node(p_tree_id, p_key) THEN
            RAISE EXCEPTION 'BST structure is missing key %', p_key;
        END IF;

        DELETE FROM tree_item
        WHERE tree_id = p_tree_id
          AND record_key = p_key;
    ELSE
        -- Rebuild strategy removes the previous shape and reconstructs it
        -- after the authoritative record has been deleted.
        UPDATE tree_catalog
        SET root_key = NULL,
            node_count = 0
        WHERE tree_id = p_tree_id;

        DELETE FROM tree_node
        WHERE tree_id = p_tree_id;

        DELETE FROM tree_item
        WHERE tree_id = p_tree_id
          AND record_key = p_key;

        PERFORM rebuild_balanced_tree(p_tree_id);
    END IF;

    RETURN TRUE;
END;
$$;


-- Search follows child links rather than scanning the authoritative table.
CREATE OR REPLACE FUNCTION search_item(
    p_tree_id BIGINT,
    p_key INTEGER
)
RETURNS VARCHAR(200)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    current_key INTEGER;
    next_key INTEGER;
    found_payload VARCHAR(200);
BEGIN
    SELECT root_key
    INTO current_key
    FROM tree_catalog
    WHERE tree_id = p_tree_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Unknown tree ID: %', p_tree_id;
    END IF;

    WHILE current_key IS NOT NULL LOOP
        IF p_key = current_key THEN
            SELECT payload
            INTO found_payload
            FROM tree_item
            WHERE tree_id = p_tree_id
              AND record_key = current_key;

            RETURN found_payload;
        END IF;

        SELECT CASE
            WHEN p_key < current_key THEN left_key
            ELSE right_key
        END
        INTO next_key
        FROM tree_node
        WHERE tree_id = p_tree_id
          AND node_key = current_key;

        current_key := next_key;
    END LOOP;

    RETURN NULL;
END;
$$;


-- The primary key on tree_item(tree_id, record_key) supports this range
-- retrieval efficiently. The tree traversal remains available through
-- search_item and the parent/child structure.
CREATE OR REPLACE FUNCTION range_items(
    p_tree_id BIGINT,
    p_lower INTEGER,
    p_upper INTEGER
)
RETURNS TABLE(record_key INTEGER, payload VARCHAR(200))
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    IF p_lower > p_upper THEN
        RAISE EXCEPTION 'Lower bound cannot exceed upper bound';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM tree_catalog WHERE tree_id = p_tree_id
    ) THEN
        RAISE EXCEPTION 'Unknown tree ID: %', p_tree_id;
    END IF;

    RETURN QUERY
    SELECT item.record_key, item.payload
    FROM tree_item AS item
    WHERE item.tree_id = p_tree_id
      AND item.record_key BETWEEN p_lower AND p_upper
    ORDER BY item.record_key;
END;
$$;


-- Reachability and ordering are checked independently from catalog metadata.
CREATE OR REPLACE VIEW tree_metrics AS
WITH RECURSIVE walk AS (
    SELECT
        catalog.tree_id,
        catalog.root_key AS node_key,
        1 AS depth,
        ARRAY[catalog.root_key] AS path,
        NULL::INTEGER AS lower_bound,
        NULL::INTEGER AS upper_bound
    FROM tree_catalog AS catalog
    WHERE catalog.root_key IS NOT NULL

    UNION ALL

    SELECT
        parent.tree_id,
        child.node_key,
        walk.depth + 1,
        walk.path || child.node_key,
        CASE
            WHEN child.side = 'L' THEN walk.lower_bound
            ELSE walk.node_key
        END,
        CASE
            WHEN child.side = 'L' THEN walk.node_key
            ELSE walk.upper_bound
        END
    FROM walk
    JOIN tree_node AS parent
      ON parent.tree_id = walk.tree_id
     AND parent.node_key = walk.node_key
    CROSS JOIN LATERAL (
        VALUES
            ('L'::TEXT, parent.left_key),
            ('R'::TEXT, parent.right_key)
    ) AS child(side, node_key)
    WHERE child.node_key IS NOT NULL
      AND NOT child.node_key = ANY(walk.path)
)
SELECT
    catalog.tree_id,
    catalog.tree_name,
    catalog.strategy,
    catalog.node_count,
    COUNT(walk.node_key)::INTEGER AS reachable_nodes,
    COALESCE(MAX(walk.depth), 0) AS tree_height,
    (
        COUNT(walk.node_key) = catalog.node_count
        AND COALESCE(
            bool_and(
                (walk.lower_bound IS NULL
                    OR walk.node_key > walk.lower_bound)
                AND
                (walk.upper_bound IS NULL
                    OR walk.node_key < walk.upper_bound)
            ),
            TRUE
        )
    ) AS structure_valid
FROM tree_catalog AS catalog
LEFT JOIN walk
  ON walk.tree_id = catalog.tree_id
GROUP BY
    catalog.tree_id,
    catalog.tree_name,
    catalog.strategy,
    catalog.node_count;


-- Create one ordinary BST and one balanced-by-rebuild index.
INSERT INTO tree_catalog(tree_name, strategy)
VALUES
    ('infrastructure-bst', 'BST'),
    ('infrastructure-balanced', 'REBUILT_BALANCED');

DO $$
DECLARE
    ordinary_tree BIGINT;
    balanced_tree BIGINT;
    sample_key INTEGER;
    sample_value VARCHAR(200);
BEGIN
    SELECT tree_id INTO ordinary_tree
    FROM tree_catalog
    WHERE tree_name = 'infrastructure-bst';

    SELECT tree_id INTO balanced_tree
    FROM tree_catalog
    WHERE tree_name = 'infrastructure-balanced';

    -- This order creates a valid but unbalanced BST.
    FOR sample_key, sample_value IN
        SELECT *
        FROM (
            VALUES
                (50, 'gateway'::VARCHAR(200)),
                (30, 'database'::VARCHAR(200)),
                (70, 'monitor'::VARCHAR(200)),
                (20, 'worker'::VARCHAR(200)),
                (40, 'cache'::VARCHAR(200)),
                (60, 'scheduler'::VARCHAR(200)),
                (80, 'backup'::VARCHAR(200)),
                (65, 'logger'::VARCHAR(200))
        ) AS sample(record_key, payload)
    LOOP
        PERFORM insert_item(ordinary_tree, sample_key, sample_value);
        PERFORM insert_item(balanced_tree, sample_key, sample_value);
    END LOOP;

    -- Demonstrate duplicate-key rejection without aborting the sample run.
    BEGIN
        PERFORM insert_item(ordinary_tree, 50, 'duplicate-gateway');
    EXCEPTION
        WHEN unique_violation THEN
            RAISE NOTICE 'Duplicate key rejected as expected';
    END;

    -- Exercise leaf, one-child, and two-child deletion paths.
    PERFORM delete_item(ordinary_tree, 20);
    PERFORM delete_item(ordinary_tree, 60);
    PERFORM delete_item(ordinary_tree, 70);

    PERFORM delete_item(balanced_tree, 20);
    PERFORM delete_item(balanced_tree, 60);
    PERFORM delete_item(balanced_tree, 70);
END;
$$;


-- Point lookup follows the selected tree's child links.
SELECT
    tree_name,
    search_item(tree_id, 50) AS key_50_value,
    search_item(tree_id, 999) AS missing_key_value
FROM tree_catalog
ORDER BY tree_id;

-- Range retrieval uses the composite primary-key index.
SELECT
    catalog.tree_name,
    result.record_key,
    result.payload
FROM tree_catalog AS catalog
CROSS JOIN LATERAL range_items(catalog.tree_id, 35, 70) AS result
ORDER BY catalog.tree_id, result.record_key;

-- Tree height and structural integrity after deletion.
SELECT
    tree_name,
    strategy,
    node_count,
    reachable_nodes,
    tree_height,
    structure_valid
FROM tree_metrics
ORDER BY tree_id;

-- CTE-based report: active records and key distribution by tree.
WITH record_statistics AS (
    SELECT
        tree_id,
        COUNT(*) AS record_count,
        MIN(record_key) AS minimum_key,
        MAX(record_key) AS maximum_key,
        AVG(record_key)::NUMERIC(12, 2) AS average_key
    FROM tree_item
    GROUP BY tree_id
)
SELECT
    catalog.tree_name,
    catalog.strategy,
    COALESCE(stats.record_count, 0) AS record_count,
    stats.minimum_key,
    stats.maximum_key,
    stats.average_key
FROM tree_catalog AS catalog
LEFT JOIN record_statistics AS stats
  ON stats.tree_id = catalog.tree_id
ORDER BY catalog.tree_id;

-- Audit history records authoritative item insertion and deletion.
SELECT
    tree_id,
    record_key,
    event_type,
    event_time,
    database_user
FROM tree_event
ORDER BY event_id;

-- Confirm that deleting an absent key is a non-destructive operation.
SELECT delete_item(
    (SELECT tree_id
     FROM tree_catalog
     WHERE tree_name = 'infrastructure-bst'),
    999
) AS deleted_missing_record;

COMMIT;
