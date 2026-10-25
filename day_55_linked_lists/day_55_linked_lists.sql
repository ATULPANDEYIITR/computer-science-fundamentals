DROP SCHEMA IF EXISTS linked_lists CASCADE;
CREATE SCHEMA linked_lists;

SET search_path TO linked_lists, public;

-- A repository of linked-list structures. The database stores the logical
-- node relationships explicitly so pointer invariants can be validated.
CREATE TYPE list_kind AS ENUM ('singly', 'doubly', 'circular');

CREATE TABLE linked_list (
    list_id      BIGSERIAL PRIMARY KEY,
    name         TEXT NOT NULL UNIQUE,
    kind         list_kind NOT NULL,
    description  TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE list_node (
    node_id       BIGSERIAL PRIMARY KEY,
    list_id       BIGINT NOT NULL REFERENCES linked_list(list_id) ON DELETE CASCADE,
    node_position BIGINT NOT NULL CHECK (node_position >= 0),
    value         INTEGER NOT NULL,
    next_node_id  BIGINT REFERENCES list_node(node_id),
    prev_node_id  BIGINT REFERENCES list_node(node_id),

    CONSTRAINT uq_list_position UNIQUE (list_id, node_position),
    CONSTRAINT uq_list_node_pair UNIQUE (list_id, node_id)
);

CREATE INDEX idx_list_node_list_position
    ON list_node(list_id, node_position);

CREATE INDEX idx_list_node_next
    ON list_node(next_node_id);

CREATE INDEX idx_list_node_prev
    ON list_node(prev_node_id);

CREATE TABLE list_operation (
    operation_id BIGSERIAL PRIMARY KEY,
    list_id      BIGINT NOT NULL REFERENCES linked_list(list_id) ON DELETE CASCADE,
    operation    TEXT NOT NULL CHECK (
        operation IN (
            'append',
            'prepend',
            'insert',
            'remove',
            'reverse',
            'rotate',
            'traverse',
            'validate'
        )
    ),
    operation_status TEXT NOT NULL CHECK (
        operation_status IN ('success', 'rejected', 'failed')
    ),
    affected_node_id BIGINT REFERENCES list_node(node_id) ON DELETE SET NULL,
    details TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Structural constraints that can be enforced without knowing whether the
-- complete list is circular are handled by a validation function below.
CREATE OR REPLACE FUNCTION validate_list_structure(p_list_id BIGINT)
RETURNS TABLE (
    list_id BIGINT,
    valid BOOLEAN,
    issue_count INTEGER,
    issue_description TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_kind list_kind;
    v_count INTEGER;
    v_distinct_targets INTEGER;
    v_head_count INTEGER;
    v_tail_count INTEGER;
    v_issues INTEGER := 0;
    v_issue_text TEXT := '';
BEGIN
    SELECT kind
    INTO v_kind
    FROM linked_list
    WHERE linked_list.list_id = p_list_id;

    IF NOT FOUND THEN
        RETURN QUERY
        SELECT p_list_id, FALSE, 1, 'List does not exist';
        RETURN;
    END IF;

    SELECT COUNT(*)
    INTO v_count
    FROM list_node
    WHERE list_node.list_id = p_list_id;

    IF v_count = 0 THEN
        RETURN QUERY
        SELECT p_list_id, TRUE, 0, 'Empty list is structurally valid';
        RETURN;
    END IF;

    SELECT COUNT(*)
    INTO v_head_count
    FROM list_node n
    WHERE n.list_id = p_list_id
      AND n.prev_node_id IS NULL;

    SELECT COUNT(*)
    INTO v_tail_count
    FROM list_node n
    WHERE n.list_id = p_list_id
      AND n.next_node_id IS NULL;

    IF v_kind IN ('singly', 'doubly') AND v_head_count <> 1 THEN
        v_issues := v_issues + 1;
        v_issue_text := v_issue_text || 'Expected exactly one null-prev head. ';
    END IF;

    IF v_kind IN ('singly', 'doubly') AND v_tail_count <> 1 THEN
        v_issues := v_issues + 1;
        v_issue_text := v_issue_text || 'Expected exactly one null-next tail. ';
    END IF;

    IF v_kind = 'singly' THEN
        IF EXISTS (
            SELECT 1
            FROM list_node
            WHERE list_id = p_list_id
              AND prev_node_id IS NOT NULL
        ) THEN
            v_issues := v_issues + 1;
            v_issue_text := v_issue_text ||
                'Singly linked nodes cannot contain prev pointers. ';
        END IF;
    END IF;

    IF v_kind = 'doubly' THEN
        IF EXISTS (
            SELECT 1
            FROM list_node n
            WHERE n.list_id = p_list_id
              AND n.next_node_id IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1
                  FROM list_node target
                  WHERE target.node_id = n.next_node_id
                    AND target.prev_node_id = n.node_id
              )
        ) THEN
            v_issues := v_issues + 1;
            v_issue_text := v_issue_text ||
                'Doubly linked next/prev relationship is inconsistent. ';
        END IF;
    END IF;

    IF v_kind = 'circular' THEN
        IF EXISTS (
            SELECT 1
            FROM list_node
            WHERE list_id = p_list_id
              AND next_node_id IS NULL
        ) THEN
            v_issues := v_issues + 1;
            v_issue_text := v_issue_text ||
                'Circular lists cannot have a null next pointer. ';
        END IF;

        IF NOT EXISTS (
            SELECT 1
            FROM list_node tail
            JOIN list_node head
              ON head.list_id = tail.list_id
             AND head.node_position = 0
            WHERE tail.list_id = p_list_id
              AND tail.node_position = v_count - 1
              AND tail.next_node_id = head.node_id
        ) THEN
            v_issues := v_issues + 1;
            v_issue_text := v_issue_text ||
                'Circular tail must point to the head. ';
        END IF;
    END IF;

    RETURN QUERY
    SELECT
        p_list_id,
        v_issues = 0,
        v_issues,
        CASE
            WHEN v_issues = 0 THEN 'Structure is valid'
            ELSE trim(v_issue_text)
        END;
END;
$$;

CREATE OR REPLACE FUNCTION record_operation(
    p_list_id BIGINT,
    p_operation TEXT,
    p_status TEXT,
    p_node_id BIGINT,
    p_details TEXT
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_operation_id BIGINT;
BEGIN
    INSERT INTO list_operation (
        list_id,
        operation,
        operation_status,
        affected_node_id,
        details
    )
    VALUES (
        p_list_id,
        p_operation,
        p_status,
        p_node_id,
        p_details
    )
    RETURNING operation_id INTO v_operation_id;

    RETURN v_operation_id;
END;
$$;

-- Sample structures.

INSERT INTO linked_list (name, kind, description)
VALUES
(
    'customer-processing-singly',
    'singly',
    'Forward-only processing queue'
),
(
    'browser-history-doubly',
    'doubly',
    'History navigation requiring forward and backward traversal'
),
(
    'round-robin-circular',
    'circular',
    'Repeated scheduling cycle'
);

INSERT INTO list_node
    (list_id, node_position, value)
SELECT
    l.list_id,
    v.position,
    v.value
FROM linked_list l
JOIN (
    VALUES
        ('customer-processing-singly', 0, 10),
        ('customer-processing-singly', 1, 20),
        ('customer-processing-singly', 2, 30),
        ('browser-history-doubly', 0, 100),
        ('browser-history-doubly', 1, 200),
        ('browser-history-doubly', 2, 300),
        ('round-robin-circular', 0, 1000),
        ('round-robin-circular', 1, 2000),
        ('round-robin-circular', 2, 3000),
        ('round-robin-circular', 3, 4000)
) AS v(list_name, position, value)
ON l.name = v.list_name;

-- Establish singly-linked forward relationships.
UPDATE list_node n
SET next_node_id = target.node_id
FROM list_node target
WHERE n.list_id = target.list_id
  AND n.list_id = (
      SELECT list_id
      FROM linked_list
      WHERE name = 'customer-processing-singly'
  )
  AND target.node_position = n.node_position + 1;

-- Establish doubly-linked relationships.
UPDATE list_node n
SET
    next_node_id = target_next.node_id,
    prev_node_id = target_prev.node_id
FROM list_node target_next
LEFT JOIN list_node target_prev
    ON target_prev.list_id = n.list_id
   AND target_prev.node_position = n.node_position - 1
WHERE n.list_id = target_next.list_id
  AND n.list_id = (
      SELECT list_id
      FROM linked_list
      WHERE name = 'browser-history-doubly'
  )
  AND target_next.node_position = n.node_position + 1;

UPDATE list_node n
SET prev_node_id = target.node_id
FROM list_node target
WHERE n.list_id = target.list_id
  AND n.list_id = (
      SELECT list_id
      FROM linked_list
      WHERE name = 'browser-history-doubly'
  )
  AND target.node_position = n.node_position - 1;

-- Establish the circular next-pointer chain.
UPDATE list_node n
SET next_node_id = target.node_id
FROM list_node target
WHERE n.list_id = target.list_id
  AND n.list_id = (
      SELECT list_id
      FROM linked_list
      WHERE name = 'round-robin-circular'
  )
  AND target.node_position =
      CASE
          WHEN n.node_position = 3 THEN 0
          ELSE n.node_position + 1
      END;

INSERT INTO list_operation (
    list_id,
    operation,
    operation_status,
    details
)
SELECT list_id, 'validate', 'success', 'Initial structure loaded'
FROM linked_list;

-- Transactional mutation example: append a node to a singly linked list.
BEGIN;

WITH list_info AS (
    SELECT list_id
    FROM linked_list
    WHERE name = 'customer-processing-singly'
),
new_position AS (
    SELECT
        list_id,
        COALESCE(MAX(node_position), -1) + 1 AS position
    FROM list_node
    WHERE list_id = (SELECT list_id FROM list_info)
    GROUP BY list_id
)
INSERT INTO list_node (list_id, node_position, value)
SELECT list_id, position, 40
FROM new_position;

WITH list_info AS (
    SELECT list_id
    FROM linked_list
    WHERE name = 'customer-processing-singly'
),
last_two AS (
    SELECT node_id, node_position
    FROM list_node
    WHERE list_id = (SELECT list_id FROM list_info)
    ORDER BY node_position DESC
    LIMIT 2
)
UPDATE list_node n
SET next_node_id = target.node_id
FROM last_two target
WHERE n.list_id = (SELECT list_id FROM list_info)
  AND n.node_position = target.node_position - 1;

COMMIT;

-- Validation report for every list.
SELECT *
FROM linked_list
CROSS JOIN LATERAL validate_list_structure(linked_list.list_id);

-- Retrieve nodes in logical sequence.
SELECT
    l.name,
    l.kind,
    n.node_position,
    n.value,
    n.next_node_id,
    n.prev_node_id
FROM linked_list l
JOIN list_node n
  ON n.list_id = l.list_id
ORDER BY l.list_id, n.node_position;

-- Aggregate list statistics.
SELECT
    l.kind,
    COUNT(DISTINCT l.list_id) AS list_count,
    COUNT(n.node_id) AS node_count,
    MIN(n.value) AS minimum_value,
    MAX(n.value) AS maximum_value,
    AVG(n.value)::NUMERIC(12, 2) AS average_value
FROM linked_list l
LEFT JOIN list_node n
  ON n.list_id = l.list_id
GROUP BY l.kind
ORDER BY l.kind;

-- Detect orphaned references.
SELECT
    n.node_id,
    n.list_id,
    n.next_node_id,
    n.prev_node_id
FROM list_node n
LEFT JOIN list_node next_node
  ON next_node.node_id = n.next_node_id
LEFT JOIN list_node prev_node
  ON prev_node.node_id = n.prev_node_id
WHERE (n.next_node_id IS NOT NULL AND next_node.node_id IS NULL)
   OR (n.prev_node_id IS NOT NULL AND prev_node.node_id IS NULL);

-- Show the circular successor chain.
WITH RECURSIVE circular_walk AS (
    SELECT
        n.list_id,
        n.node_id,
        n.value,
        n.next_node_id,
        0 AS depth
    FROM list_node n
    JOIN linked_list l
      ON l.list_id = n.list_id
    WHERE l.name = 'round-robin-circular'
      AND n.node_position = 0

    UNION ALL

    SELECT
        cw.list_id,
        next_node.node_id,
        next_node.value,
        next_node.next_node_id,
        cw.depth + 1
    FROM circular_walk cw
    JOIN list_node next_node
      ON next_node.node_id = cw.next_node_id
    WHERE cw.depth < (
        SELECT COUNT(*) - 1
        FROM list_node
        WHERE list_id = cw.list_id
    )
)
SELECT
    depth,
    node_id,
    value,
    next_node_id
FROM circular_walk
ORDER BY depth;

-- Record a rejected operation to represent an invalid index.
SELECT record_operation(
    (
        SELECT list_id
        FROM linked_list
        WHERE name = 'customer-processing-singly'
    ),
    'remove',
    'rejected',
    NULL,
    'Index 999 is outside the current list bounds'
);

-- Review the operation history.
SELECT
    l.name,
    o.operation,
    o.operation_status,
    o.details,
    o.occurred_at
FROM list_operation o
JOIN linked_list l
  ON l.list_id = o.list_id
ORDER BY o.occurred_at, o.operation_id;
