DROP SCHEMA IF EXISTS data_structures_demo CASCADE;
CREATE SCHEMA data_structures_demo;
SET search_path = data_structures_demo;

-- The relational model represents structures as domain entities:
-- queues/stacks describe linear access policies, while dependency edges
-- represent a non-linear graph.

CREATE TYPE task_state AS ENUM (
    'pending',
    'running',
    'completed',
    'failed'
);

CREATE TYPE structure_kind AS ENUM (
    'stack',
    'queue',
    'linked_list',
    'tree',
    'graph',
    'hash_index',
    'priority_queue'
);

CREATE TABLE data_structures (
    structure_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    kind structure_kind NOT NULL,
    description TEXT NOT NULL,
    expected_access_pattern TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE work_items (
    work_item_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    structure_id BIGINT REFERENCES data_structures(structure_id),
    item_key TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    priority INTEGER NOT NULL DEFAULT 50
        CHECK (priority BETWEEN 1 AND 100),
    state task_state NOT NULL DEFAULT 'pending',
    inserted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    UNIQUE (structure_id, item_key),
    CHECK (
        completed_at IS NULL
        OR state = 'completed'
    )
);

CREATE TABLE graph_vertices (
    vertex_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    vertex_key TEXT NOT NULL UNIQUE,
    label TEXT NOT NULL
);

CREATE TABLE graph_edges (
    edge_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_vertex_id BIGINT NOT NULL
        REFERENCES graph_vertices(vertex_id)
        ON DELETE CASCADE,
    target_vertex_id BIGINT NOT NULL
        REFERENCES graph_vertices(vertex_id)
        ON DELETE CASCADE,
    weight INTEGER NOT NULL DEFAULT 1
        CHECK (weight >= 0),
    UNIQUE (source_vertex_id, target_vertex_id),
    CHECK (source_vertex_id <> target_vertex_id)
);

CREATE TABLE benchmark_runs (
    benchmark_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    structure_id BIGINT NOT NULL
        REFERENCES data_structures(structure_id),
    operation_name TEXT NOT NULL,
    input_size INTEGER NOT NULL CHECK (input_size > 0),
    elapsed_microseconds NUMERIC(18,3) NOT NULL
        CHECK (elapsed_microseconds >= 0),
    notes TEXT
);

CREATE INDEX idx_work_items_state_priority
    ON work_items (state, priority, inserted_at);

CREATE INDEX idx_graph_edges_source
    ON graph_edges (source_vertex_id);

CREATE INDEX idx_graph_edges_target
    ON graph_edges (target_vertex_id);

INSERT INTO data_structures
    (name, kind, description, expected_access_pattern)
VALUES
    (
        'Execution Stack',
        'stack',
        'Stores operations using last-in-first-out access.',
        'Push and pop at one end.'
    ),
    (
        'Request Queue',
        'queue',
        'Processes requests in first-in-first-out order.',
        'Insert at the tail and remove from the head.'
    ),
    (
        'Dependency Graph',
        'graph',
        'Represents relationships between processing stages.',
        'Traverse neighboring vertices.'
    ),
    (
        'Release Tree',
        'tree',
        'Maintains ordered release identifiers.',
        'Search according to ordered keys.'
    ),
    (
        'Priority Queue',
        'priority_queue',
        'Selects work according to priority.',
        'Remove the minimum priority value.'
    );

INSERT INTO graph_vertices (vertex_key, label)
VALUES
    ('compile', 'Compile source'),
    ('test', 'Run tests'),
    ('package', 'Create package'),
    ('deploy', 'Deploy release'),
    ('monitor', 'Monitor deployment');

INSERT INTO graph_edges
    (source_vertex_id, target_vertex_id, weight)
SELECT
    source.vertex_id,
    target.vertex_id,
    edges.weight
FROM (
    VALUES
        ('compile', 'test', 1),
        ('test', 'package', 1),
        ('package', 'deploy', 2),
        ('deploy', 'monitor', 1)
) AS edges(source_key, target_key, weight)
JOIN graph_vertices source
    ON source.vertex_key = edges.source_key
JOIN graph_vertices target
    ON target.vertex_key = edges.target_key;

INSERT INTO work_items
    (structure_id, item_key, payload, priority, state)
SELECT
    ds.structure_id,
    item.item_key,
    item.payload::jsonb,
    item.priority,
    item.state::task_state
FROM (
    VALUES
        (
            'Request Queue',
            'REQ-1001',
            '{"service":"identity","operation":"login"}',
            20,
            'pending'
        ),
        (
            'Request Queue',
            'REQ-1002',
            '{"service":"orders","operation":"create"}',
            40,
            'running'
        ),
        (
            'Priority Queue',
            'JOB-9001',
            '{"service":"payments","operation":"reconcile"}',
            10,
            'pending'
        ),
        (
            'Priority Queue',
            'JOB-9002',
            '{"service":"reports","operation":"generate"}',
            70,
            'completed'
        )
) AS item(structure_name, item_key, payload, priority, state)
JOIN data_structures ds
    ON ds.name = item.structure_name;

UPDATE work_items
SET completed_at = CURRENT_TIMESTAMP
WHERE item_key = 'JOB-9002';

CREATE OR REPLACE FUNCTION validate_work_item_completion()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.state = 'completed' AND NEW.completed_at IS NULL THEN
        NEW.completed_at := CURRENT_TIMESTAMP;
    END IF;

    IF NEW.state <> 'completed' AND NEW.completed_at IS NOT NULL THEN
        RAISE EXCEPTION
            'Only completed work items may have completed_at';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_work_item_completion
BEFORE INSERT OR UPDATE ON work_items
FOR EACH ROW
EXECUTE FUNCTION validate_work_item_completion();

-- A view presents linear work ordered by the priority policy.
CREATE OR REPLACE VIEW pending_priority_work AS
SELECT
    w.work_item_id,
    w.item_key,
    ds.name AS structure_name,
    w.priority,
    w.state,
    w.inserted_at
FROM work_items w
JOIN data_structures ds
    ON ds.structure_id = w.structure_id
WHERE w.state = 'pending'
ORDER BY w.priority, w.inserted_at;

-- Recursive traversal is appropriate for hierarchical or graph-like data.
WITH RECURSIVE dependency_path AS (
    SELECT
        source.vertex_key AS source_key,
        target.vertex_key AS target_key,
        1 AS depth,
        ARRAY[source.vertex_key, target.vertex_key] AS path
    FROM graph_edges e
    JOIN graph_vertices source
        ON source.vertex_id = e.source_vertex_id
    JOIN graph_vertices target
        ON target.vertex_id = e.target_vertex_id

    UNION ALL

    SELECT
        dp.source_key,
        target.vertex_key,
        dp.depth + 1,
        dp.path || target.vertex_key
    FROM dependency_path dp
    JOIN graph_vertices current_vertex
        ON current_vertex.vertex_key = dp.target_key
    JOIN graph_edges e
        ON e.source_vertex_id = current_vertex.vertex_id
    JOIN graph_vertices target
        ON target.vertex_id = e.target_vertex_id
    WHERE NOT target.vertex_key = ANY(dp.path)
)
SELECT
    source_key,
    target_key,
    depth,
    path
FROM dependency_path
ORDER BY source_key, depth;

-- Aggregation exposes the operational difference between structures.
SELECT
    ds.kind,
    COUNT(w.work_item_id) AS item_count,
    COUNT(*) FILTER (WHERE w.state = 'pending') AS pending_count,
    COUNT(*) FILTER (WHERE w.state = 'completed') AS completed_count,
    AVG(w.priority)::NUMERIC(10,2) AS average_priority
FROM data_structures ds
LEFT JOIN work_items w
    ON w.structure_id = ds.structure_id
GROUP BY ds.kind
ORDER BY ds.kind;

-- Demonstrate transactional integrity: both changes succeed together.
BEGIN;

INSERT INTO work_items (
    structure_id,
    item_key,
    payload,
    priority,
    state
)
SELECT
    structure_id,
    'REQ-TRANSACTIONAL',
    '{"service":"catalog","operation":"reindex"}'::jsonb,
    30,
    'pending'
FROM data_structures
WHERE name = 'Request Queue';

UPDATE work_items
SET state = 'completed',
    completed_at = CURRENT_TIMESTAMP
WHERE item_key = 'REQ-1002';

COMMIT;

-- Database-level validation rejects an invalid priority.
DO $$
BEGIN
    BEGIN
        INSERT INTO work_items (
            structure_id,
            item_key,
            priority
        )
        SELECT
            structure_id,
            'INVALID-PRIORITY',
            101
        FROM data_structures
        WHERE name = 'Priority Queue';

        RAISE EXCEPTION
            'Expected priority constraint to reject the row';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'Expected failure: invalid priority was rejected';
    END;
END;
$$;

INSERT INTO benchmark_runs (
    structure_id,
    operation_name,
    input_size,
    elapsed_microseconds,
    notes
)
SELECT
    structure_id,
    'ordered lookup',
    1000000,
    82.500,
    'Illustrative measurement stored for comparison; database indexes should be evaluated with EXPLAIN ANALYZE.'
FROM data_structures
WHERE name = 'Release Tree';

-- The query planner can be used to inspect whether the state/priority index
-- is appropriate for the pending-work query.
EXPLAIN (COSTS OFF)
SELECT
    work_item_id,
    item_key,
    priority
FROM work_items
WHERE state = 'pending'
ORDER BY priority, inserted_at;
