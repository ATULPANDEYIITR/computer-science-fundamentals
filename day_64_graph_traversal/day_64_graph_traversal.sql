-- Graph Traversal: PostgreSQL graph model and traversal workflow.
--
-- Features:
--   1. Directed and undirected graph storage
--   2. Vertex and edge integrity constraints
--   3. Edge availability for changing transport conditions
--   4. BFS and DFS using a database-managed traversal queue/stack
--   5. Shortest paths in unweighted graphs
--   6. Reachability checks
--   7. Vertex degree reporting
--   8. Directed dependency traversal
--
-- Run this script in a fresh PostgreSQL database.
-- The script creates the graph_lab schema.

BEGIN;

CREATE SCHEMA IF NOT EXISTS graph_lab;

CREATE TABLE graph_lab.graph_model (
    graph_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    graph_name VARCHAR(150) NOT NULL UNIQUE,
    is_directed BOOLEAN NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT graph_name_not_blank
        CHECK (length(trim(graph_name)) > 0)
);

CREATE TABLE graph_lab.vertex (
    graph_id BIGINT NOT NULL,
    vertex_id BIGINT NOT NULL,
    label VARCHAR(150) NOT NULL,
    vertex_type VARCHAR(40) NOT NULL DEFAULT 'GENERAL',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT vertex_pk
        PRIMARY KEY (graph_id, vertex_id),

    CONSTRAINT vertex_graph_fk
        FOREIGN KEY (graph_id)
        REFERENCES graph_lab.graph_model (graph_id)
        ON DELETE CASCADE,

    CONSTRAINT vertex_label_unique
        UNIQUE (graph_id, label),

    CONSTRAINT vertex_label_not_blank
        CHECK (length(trim(label)) > 0),

    CONSTRAINT vertex_type_not_blank
        CHECK (length(trim(vertex_type)) > 0)
);

CREATE TABLE graph_lab.edge (
    graph_id BIGINT NOT NULL,
    source_vertex_id BIGINT NOT NULL,
    target_vertex_id BIGINT NOT NULL,
    is_open BOOLEAN NOT NULL DEFAULT TRUE,
    closure_reason VARCHAR(250),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT edge_pk
        PRIMARY KEY (
            graph_id,
            source_vertex_id,
            target_vertex_id
        ),

    CONSTRAINT edge_graph_fk
        FOREIGN KEY (graph_id)
        REFERENCES graph_lab.graph_model (graph_id)
        ON DELETE CASCADE,

    CONSTRAINT edge_source_fk
        FOREIGN KEY (graph_id, source_vertex_id)
        REFERENCES graph_lab.vertex (graph_id, vertex_id)
        ON DELETE CASCADE,

    CONSTRAINT edge_target_fk
        FOREIGN KEY (graph_id, target_vertex_id)
        REFERENCES graph_lab.vertex (graph_id, vertex_id)
        ON DELETE CASCADE,

    CONSTRAINT edge_closure_reason_check
        CHECK (
            is_open = TRUE
            OR (
                closure_reason IS NOT NULL
                AND length(trim(closure_reason)) > 0
            )
        )
);

-- The primary key supports lookups by graph and source vertex.
-- This index supports reverse lookups and incoming-edge analysis.
CREATE INDEX edge_incoming_lookup_idx
    ON graph_lab.edge (
        graph_id,
        target_vertex_id,
        source_vertex_id
    );

CREATE INDEX edge_open_outgoing_idx
    ON graph_lab.edge (
        graph_id,
        source_vertex_id,
        target_vertex_id
    )
    WHERE is_open = TRUE;

CREATE INDEX vertex_type_lookup_idx
    ON graph_lab.vertex (graph_id, vertex_type);

-- For an undirected graph, one canonical edge is stored:
-- source_vertex_id must be smaller than target_vertex_id.
-- Traversal interprets that stored edge in both directions.
CREATE OR REPLACE FUNCTION graph_lab.validate_edge_orientation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_is_directed BOOLEAN;
BEGIN
    SELECT gm.is_directed
    INTO v_is_directed
    FROM graph_lab.graph_model AS gm
    WHERE gm.graph_id = NEW.graph_id;

    IF v_is_directed = FALSE
       AND NEW.source_vertex_id >= NEW.target_vertex_id THEN
        RAISE EXCEPTION
            'Undirected edges must use canonical ordering: source < target. '
            'Received % -> %.',
            NEW.source_vertex_id,
            NEW.target_vertex_id
            USING ERRCODE = 'check_violation';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER edge_orientation_guard
BEFORE INSERT OR UPDATE OF
    graph_id,
    source_vertex_id,
    target_vertex_id
ON graph_lab.edge
FOR EACH ROW
EXECUTE FUNCTION graph_lab.validate_edge_orientation();

-- A unified traversal function.
--
-- BFS selects the earliest inserted, unexpanded vertex.
-- DFS selects the latest inserted, unexpanded vertex.
--
-- For deterministic DFS, neighbors are inserted in descending order.
-- The last inserted neighbor is therefore the first one removed
-- from the stack.
--
-- Each vertex is inserted into traversal_state only once. This
-- prevents cycles and duplicate processing.
CREATE OR REPLACE FUNCTION graph_lab.traverse(
    p_graph_id BIGINT,
    p_start_vertex_id BIGINT,
    p_algorithm TEXT
)
RETURNS TABLE (
    visit_order INTEGER,
    vertex_id BIGINT,
    depth INTEGER,
    predecessor_vertex_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_algorithm TEXT;
    v_current_vertex BIGINT;
    v_current_depth INTEGER;
    v_current_queue_order BIGINT;
    v_neighbor BIGINT;
    v_visit_order INTEGER := 0;
BEGIN
    v_algorithm := upper(trim(p_algorithm));

    IF v_algorithm IS NULL
       OR v_algorithm NOT IN ('BFS', 'DFS') THEN
        RAISE EXCEPTION
            'Unsupported traversal algorithm: %',
            p_algorithm
            USING ERRCODE = 'invalid_parameter_value';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM graph_lab.graph_model AS gm
        WHERE gm.graph_id = p_graph_id
    ) THEN
        RAISE EXCEPTION
            'Graph does not exist: %',
            p_graph_id
            USING ERRCODE = 'foreign_key_violation';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM graph_lab.vertex AS v
        WHERE v.graph_id = p_graph_id
          AND v.vertex_id = p_start_vertex_id
    ) THEN
        RAISE EXCEPTION
            'Starting vertex % does not exist in graph %.',
            p_start_vertex_id,
            p_graph_id
            USING ERRCODE = 'foreign_key_violation';
    END IF;

    /*
     * Temporary tables are isolated by database session.
     * ON COMMIT DROP avoids leaving traversal state after the
     * transaction completes.
     */
    CREATE TEMP TABLE IF NOT EXISTS graph_traversal_state (
        queue_order BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        vertex_id BIGINT NOT NULL UNIQUE,
        depth INTEGER NOT NULL,
        predecessor_vertex_id BIGINT,
        visit_order INTEGER,
        expanded BOOLEAN NOT NULL DEFAULT FALSE
    ) ON COMMIT DROP;

    TRUNCATE TABLE pg_temp.graph_traversal_state
        RESTART IDENTITY;

    INSERT INTO pg_temp.graph_traversal_state (
        vertex_id,
        depth,
        predecessor_vertex_id
    )
    VALUES (
        p_start_vertex_id,
        0,
        NULL
    );

    LOOP
        /*
         * BFS: oldest discovered vertex first.
         * DFS: newest discovered vertex first.
         */
        SELECT
            state.queue_order,
            state.vertex_id,
            state.depth
        INTO
            v_current_queue_order,
            v_current_vertex,
            v_current_depth
        FROM pg_temp.graph_traversal_state AS state
        WHERE state.expanded = FALSE
        ORDER BY
            CASE
                WHEN v_algorithm = 'BFS' THEN state.queue_order
            END ASC,
            CASE
                WHEN v_algorithm = 'DFS' THEN state.queue_order
            END DESC
        LIMIT 1;

        EXIT WHEN NOT FOUND;

        v_visit_order := v_visit_order + 1;

        UPDATE pg_temp.graph_traversal_state AS state
        SET
            expanded = TRUE,
            visit_order = v_visit_order
        WHERE state.queue_order = v_current_queue_order;

        /*
         * Directed graphs use source -> target only.
         * Undirected graphs also expose target -> source.
         * Closed edges are excluded from both forms of traversal.
         */
        FOR v_neighbor IN
            SELECT adjacency.neighbor_id
            FROM (
                SELECT e.target_vertex_id AS neighbor_id
                FROM graph_lab.edge AS e
                WHERE e.graph_id = p_graph_id
                  AND e.source_vertex_id = v_current_vertex
                  AND e.is_open = TRUE

                UNION

                SELECT e.source_vertex_id AS neighbor_id
                FROM graph_lab.edge AS e
                JOIN graph_lab.graph_model AS gm
                  ON gm.graph_id = e.graph_id
                WHERE e.graph_id = p_graph_id
                  AND e.target_vertex_id = v_current_vertex
                  AND e.is_open = TRUE
                  AND gm.is_directed = FALSE
            ) AS adjacency
            ORDER BY
                CASE
                    WHEN v_algorithm = 'BFS'
                    THEN adjacency.neighbor_id
                END ASC,
                CASE
                    WHEN v_algorithm = 'DFS'
                    THEN adjacency.neighbor_id
                END DESC
        LOOP
            INSERT INTO pg_temp.graph_traversal_state (
                vertex_id,
                depth,
                predecessor_vertex_id
            )
            VALUES (
                v_neighbor,
                v_current_depth + 1,
                v_current_vertex
            )
            ON CONFLICT (vertex_id) DO NOTHING;
        END LOOP;
    END LOOP;

    RETURN QUERY
    SELECT
        state.visit_order,
        state.vertex_id,
        state.depth,
        state.predecessor_vertex_id
    FROM pg_temp.graph_traversal_state AS state
    ORDER BY state.visit_order;
END;
$$;

-- Reconstruct a minimum-edge path using the BFS predecessor tree.
-- The recursive CTE follows predecessor links backwards from
-- the target until it reaches the starting vertex.
CREATE OR REPLACE FUNCTION graph_lab.shortest_path(
    p_graph_id BIGINT,
    p_start_vertex_id BIGINT,
    p_target_vertex_id BIGINT
)
RETURNS BIGINT[]
LANGUAGE plpgsql
AS $$
DECLARE
    v_path BIGINT[];
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM graph_lab.vertex AS v
        WHERE v.graph_id = p_graph_id
          AND v.vertex_id = p_target_vertex_id
    ) THEN
        RAISE EXCEPTION
            'Target vertex % does not exist in graph %.',
            p_target_vertex_id,
            p_graph_id
            USING ERRCODE = 'foreign_key_violation';
    END IF;

    WITH RECURSIVE
    bfs AS MATERIALIZED (
        SELECT *
        FROM graph_lab.traverse(
            p_graph_id,
            p_start_vertex_id,
            'BFS'
        )
    ),
    backtrack(vertex_id, path) AS (
        SELECT
            p_target_vertex_id,
            ARRAY[p_target_vertex_id]::BIGINT[]
        WHERE EXISTS (
            SELECT 1
            FROM bfs
            WHERE bfs.vertex_id = p_target_vertex_id
        )

        UNION ALL

        SELECT
            bfs.predecessor_vertex_id,
            array_prepend(
                bfs.predecessor_vertex_id,
                backtrack.path
            )
        FROM backtrack
        JOIN bfs
          ON bfs.vertex_id = backtrack.vertex_id
        WHERE bfs.predecessor_vertex_id IS NOT NULL
    )
    SELECT backtrack.path
    INTO v_path
    FROM backtrack
    WHERE backtrack.vertex_id = p_start_vertex_id
    LIMIT 1;

    -- NULL means the target exists but is unreachable.
    RETURN v_path;
END;
$$;

CREATE OR REPLACE FUNCTION graph_lab.is_reachable(
    p_graph_id BIGINT,
    p_start_vertex_id BIGINT,
    p_target_vertex_id BIGINT
)
RETURNS BOOLEAN
LANGUAGE sql
AS $$
    SELECT graph_lab.shortest_path(
        p_graph_id,
        p_start_vertex_id,
        p_target_vertex_id
    ) IS NOT NULL;
$$;

-- This view converts undirected stored edges into both traversal
-- directions, while retaining the directed graph interpretation.
CREATE OR REPLACE VIEW graph_lab.vertex_degree_summary AS
WITH adjacency AS (
    SELECT
        e.graph_id,
        e.source_vertex_id AS from_vertex,
        e.target_vertex_id AS to_vertex
    FROM graph_lab.edge AS e
    WHERE e.is_open = TRUE

    UNION ALL

    SELECT
        e.graph_id,
        e.target_vertex_id AS from_vertex,
        e.source_vertex_id AS to_vertex
    FROM graph_lab.edge AS e
    JOIN graph_lab.graph_model AS gm
      ON gm.graph_id = e.graph_id
    WHERE e.is_open = TRUE
      AND gm.is_directed = FALSE
),
outgoing AS (
    SELECT
        graph_id,
        from_vertex AS vertex_id,
        COUNT(*) AS out_degree
    FROM adjacency
    GROUP BY graph_id, from_vertex
),
incoming AS (
    SELECT
        graph_id,
        to_vertex AS vertex_id,
        COUNT(*) AS in_degree
    FROM adjacency
    GROUP BY graph_id, to_vertex
)
SELECT
    v.graph_id,
    v.vertex_id,
    v.label,
    v.vertex_type,
    COALESCE(outgoing.out_degree, 0) AS out_degree,
    COALESCE(incoming.in_degree, 0) AS in_degree
FROM graph_lab.vertex AS v
LEFT JOIN outgoing
  ON outgoing.graph_id = v.graph_id
 AND outgoing.vertex_id = v.vertex_id
LEFT JOIN incoming
  ON incoming.graph_id = v.graph_id
 AND incoming.vertex_id = v.vertex_id;

-- Sample graphs and records.
DO $$
DECLARE
    v_road_graph BIGINT;
    v_service_graph BIGINT;
BEGIN
    INSERT INTO graph_lab.graph_model (
        graph_name,
        is_directed,
        description
    )
    VALUES (
        'Emergency Transport Network',
        FALSE,
        'Undirected road network with temporary road closures.'
    )
    RETURNING graph_id INTO v_road_graph;

    INSERT INTO graph_lab.vertex (
        graph_id,
        vertex_id,
        label,
        vertex_type
    )
    VALUES
        (v_road_graph, 1, 'Dispatch Center', 'CONTROL'),
        (v_road_graph, 2, 'West Junction', 'JUNCTION'),
        (v_road_graph, 3, 'East Junction', 'JUNCTION'),
        (v_road_graph, 4, 'West Shelter', 'SHELTER'),
        (v_road_graph, 5, 'Central Bridge', 'INFRASTRUCTURE'),
        (v_road_graph, 6, 'South Shelter', 'SHELTER'),
        (v_road_graph, 7, 'Supply Depot', 'DEPOT'),
        (v_road_graph, 8, 'Remote Outpost', 'OUTPOST');

    INSERT INTO graph_lab.edge (
        graph_id,
        source_vertex_id,
        target_vertex_id,
        is_open,
        closure_reason
    )
    VALUES
        (v_road_graph, 1, 2, TRUE, NULL),
        (v_road_graph, 1, 3, TRUE, NULL),
        (v_road_graph, 2, 4, TRUE, NULL),
        (v_road_graph, 2, 5, FALSE, 'Structural inspection'),
        (v_road_graph, 3, 5, FALSE, 'Flooded access road'),
        (v_road_graph, 5, 6, TRUE, NULL),
        (v_road_graph, 6, 7, TRUE, NULL),
        (v_road_graph, 3, 8, TRUE, NULL);

    INSERT INTO graph_lab.graph_model (
        graph_name,
        is_directed,
        description
    )
    VALUES (
        'Service Dependency Network',
        TRUE,
        'Directed dependency-to-consumer impact graph.'
    )
    RETURNING graph_id INTO v_service_graph;

    INSERT INTO graph_lab.vertex (
        graph_id,
        vertex_id,
        label,
        vertex_type
    )
    VALUES
        (v_service_graph, 1, 'Customer Database', 'DATABASE'),
        (v_service_graph, 2, 'Orders API', 'SERVICE'),
        (v_service_graph, 3, 'Billing API', 'SERVICE'),
        (v_service_graph, 4, 'Checkout API', 'SERVICE'),
        (v_service_graph, 5, 'Web Frontend', 'APPLICATION'),
        (v_service_graph, 6, 'Finance Report', 'APPLICATION'),
        (v_service_graph, 7, 'Identity Service', 'SERVICE');

    INSERT INTO graph_lab.edge (
        graph_id,
        source_vertex_id,
        target_vertex_id
    )
    VALUES
        (v_service_graph, 1, 2),
        (v_service_graph, 1, 3),
        (v_service_graph, 2, 4),
        (v_service_graph, 3, 4),
        (v_service_graph, 3, 6),
        (v_service_graph, 4, 5),
        (v_service_graph, 7, 4);
END;
$$;

-- ------------------------------------------------------------
-- Retrieval and traversal
-- ------------------------------------------------------------

-- BFS from the emergency dispatch center.
SELECT *
FROM graph_lab.traverse(
    (
        SELECT graph_id
        FROM graph_lab.graph_model
        WHERE graph_name = 'Emergency Transport Network'
    ),
    1,
    'BFS'
);

-- DFS from the emergency dispatch center.
SELECT *
FROM graph_lab.traverse(
    (
        SELECT graph_id
        FROM graph_lab.graph_model
        WHERE graph_name = 'Emergency Transport Network'
    ),
    1,
    'DFS'
);

-- The path to West Shelter is available.
SELECT graph_lab.shortest_path(
    (
        SELECT graph_id
        FROM graph_lab.graph_model
        WHERE graph_name = 'Emergency Transport Network'
    ),
    1,
    4
) AS shortest_path_to_west_shelter;

-- The target exists, but road closures make it unreachable.
SELECT graph_lab.shortest_path(
    (
        SELECT graph_id
        FROM graph_lab.graph_model
        WHERE graph_name = 'Emergency Transport Network'
    ),
    1,
    7
) AS shortest_path_to_supply_depot;

-- Explicit reachability checks.
SELECT
    graph_lab.is_reachable(
        (
            SELECT graph_id
            FROM graph_lab.graph_model
            WHERE graph_name = 'Emergency Transport Network'
        ),
        1,
        4
    ) AS west_shelter_reachable,
    graph_lab.is_reachable(
        (
            SELECT graph_id
            FROM graph_lab.graph_model
            WHERE graph_name = 'Emergency Transport Network'
        ),
        1,
        7
    ) AS supply_depot_reachable;

-- ------------------------------------------------------------
-- Directed dependency traversal
-- ------------------------------------------------------------

-- BFS identifies downstream services affected by the database.
SELECT *
FROM graph_lab.traverse(
    (
        SELECT graph_id
        FROM graph_lab.graph_model
        WHERE graph_name = 'Service Dependency Network'
    ),
    1,
    'BFS'
);

-- DFS provides a depth-first inspection order.
SELECT *
FROM graph_lab.traverse(
    (
        SELECT graph_id
        FROM graph_lab.graph_model
        WHERE graph_name = 'Service Dependency Network'
    ),
    1,
    'DFS'
);

-- Minimum dependency chain from the database to the frontend.
SELECT graph_lab.shortest_path(
    (
        SELECT graph_id
        FROM graph_lab.graph_model
        WHERE graph_name = 'Service Dependency Network'
    ),
    1,
    5
) AS database_to_frontend_path;

-- ------------------------------------------------------------
-- Validation and reporting
-- ------------------------------------------------------------

-- Graph-level counts.
SELECT
    gm.graph_name,
    gm.is_directed,
    COUNT(DISTINCT v.vertex_id) AS vertex_count,
    COUNT(DISTINCT e.source_vertex_id, e.target_vertex_id) AS edge_count,
    COUNT(DISTINCT e.source_vertex_id, e.target_vertex_id)
        FILTER (WHERE e.is_open = FALSE) AS closed_edge_count
FROM graph_lab.graph_model AS gm
LEFT JOIN graph_lab.vertex AS v
  ON v.graph_id = gm.graph_id
LEFT JOIN graph_lab.edge AS e
  ON e.graph_id = gm.graph_id
GROUP BY gm.graph_id, gm.graph_name, gm.is_directed
ORDER BY gm.graph_name;

-- Validate that every stored edge connects two vertices in its graph.
-- Composite foreign keys enforce this rule at write time.
SELECT
    e.graph_id,
    COUNT(*) AS invalid_edge_count
FROM graph_lab.edge AS e
LEFT JOIN graph_lab.vertex AS source_vertex
  ON source_vertex.graph_id = e.graph_id
 AND source_vertex.vertex_id = e.source_vertex_id
LEFT JOIN graph_lab.vertex AS target_vertex
  ON target_vertex.graph_id = e.graph_id
 AND target_vertex.vertex_id = e.target_vertex_id
WHERE source_vertex.vertex_id IS NULL
   OR target_vertex.vertex_id IS NULL
GROUP BY e.graph_id;

-- Degree reporting counts available adjacency relationships.
SELECT
    gm.graph_name,
    summary.vertex_id,
    summary.label,
    summary.vertex_type,
    summary.in_degree,
    summary.out_degree
FROM graph_lab.vertex_degree_summary AS summary
JOIN graph_lab.graph_model AS gm
  ON gm.graph_id = summary.graph_id
ORDER BY gm.graph_name, summary.vertex_id;

-- Report open and closed road segments.
SELECT
    source.label AS source_location,
    target.label AS target_location,
    e.is_open,
    e.closure_reason
FROM graph_lab.edge AS e
JOIN graph_lab.vertex AS source
  ON source.graph_id = e.graph_id
 AND source.vertex_id = e.source_vertex_id
JOIN graph_lab.vertex AS target
  ON target.graph_id = e.graph_id
 AND target.vertex_id = e.target_vertex_id
JOIN graph_lab.graph_model AS gm
  ON gm.graph_id = e.graph_id
WHERE gm.graph_name = 'Emergency Transport Network'
ORDER BY e.source_vertex_id, e.target_vertex_id;

-- Example of a database-level validation failure:
-- The following insert is rejected because an undirected edge
-- must use source_vertex_id < target_vertex_id.
--
-- INSERT INTO graph_lab.edge (
--     graph_id, source_vertex_id, target_vertex_id
-- )
-- SELECT graph_id, 2, 1
-- FROM graph_lab.graph_model
-- WHERE graph_name = 'Emergency Transport Network';

COMMIT;
