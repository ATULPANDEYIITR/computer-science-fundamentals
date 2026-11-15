-- ============================================================
-- GRAPH ALGORITHMS I
-- BFS applications, DFS applications, connected components
-- PostgreSQL 15+
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS graph_lab;

SET search_path TO graph_lab, public;

-- Reset the demonstration schema.
DROP VIEW IF EXISTS component_summary CASCADE;
DROP VIEW IF EXISTS graph_edge_details CASCADE;
DROP TABLE IF EXISTS traversal_log CASCADE;
DROP TABLE IF EXISTS graph_analysis CASCADE;
DROP TABLE IF EXISTS graph_edges CASCADE;
DROP TABLE IF EXISTS graph_vertices CASCADE;
DROP TABLE IF EXISTS graphs CASCADE;

-- ============================================================
-- 1. DOMAIN MODEL
-- ============================================================

CREATE TABLE graphs (
    graph_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    graph_name VARCHAR(150) NOT NULL UNIQUE,
    graph_type VARCHAR(20) NOT NULL
        CHECK (graph_type IN ('DIRECTED', 'UNDIRECTED')),
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE graph_vertices (
    vertex_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    graph_id BIGINT NOT NULL
        REFERENCES graphs(graph_id) ON DELETE CASCADE,
    vertex_key VARCHAR(150) NOT NULL,
    vertex_type VARCHAR(50) NOT NULL DEFAULT 'GENERAL',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (graph_id, vertex_key),

    CHECK (length(trim(vertex_key)) > 0),
    CHECK (jsonb_typeof(metadata) = 'object')
);

CREATE TABLE graph_edges (
    edge_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    graph_id BIGINT NOT NULL
        REFERENCES graphs(graph_id) ON DELETE CASCADE,
    source_vertex_id BIGINT NOT NULL,
    target_vertex_id BIGINT NOT NULL,
    weight NUMERIC(12, 4) NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (graph_id, source_vertex_id)
        REFERENCES graph_vertices(graph_id, vertex_id)
        ON DELETE CASCADE,

    FOREIGN KEY (graph_id, target_vertex_id)
        REFERENCES graph_vertices(graph_id, vertex_id)
        ON DELETE CASCADE,

    CHECK (weight >= 0),
    CHECK (source_vertex_id <> target_vertex_id),

    UNIQUE (graph_id, source_vertex_id, target_vertex_id)
);

CREATE TABLE graph_analysis (
    analysis_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    graph_id BIGINT NOT NULL
        REFERENCES graphs(graph_id) ON DELETE CASCADE,
    algorithm VARCHAR(30) NOT NULL
        CHECK (
            algorithm IN (
                'BFS',
                'DFS',
                'CONNECTED_COMPONENTS'
            )
        ),
    source_vertex_id BIGINT,
    execution_status VARCHAR(20) NOT NULL DEFAULT 'COMPLETED'
        CHECK (
            execution_status IN ('COMPLETED', 'FAILED')
        ),
    result JSONB NOT NULL DEFAULT '{}'::jsonb,
    execution_time_ms NUMERIC(12, 3),
    executed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (graph_id, source_vertex_id)
        REFERENCES graph_vertices(graph_id, vertex_id),

    CHECK (
        execution_time_ms IS NULL OR execution_time_ms >= 0
    )
);

CREATE TABLE traversal_log (
    log_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    analysis_id BIGINT NOT NULL
        REFERENCES graph_analysis(analysis_id) ON DELETE CASCADE,
    vertex_id BIGINT NOT NULL
        REFERENCES graph_vertices(vertex_id),
    traversal_order INTEGER NOT NULL CHECK (traversal_order > 0),
    depth INTEGER NOT NULL CHECK (depth >= 0),
    traversal_status VARCHAR(20) NOT NULL
        CHECK (
            traversal_status IN ('DISCOVERED', 'PROCESSED')
        ),

    UNIQUE (analysis_id, vertex_id, traversal_status),
    UNIQUE (analysis_id, traversal_order, traversal_status)
);

-- ============================================================
-- 2. INDEXING
-- ============================================================

CREATE INDEX idx_vertices_graph
    ON graph_vertices(graph_id);

CREATE INDEX idx_edges_source
    ON graph_edges(graph_id, source_vertex_id);

CREATE INDEX idx_edges_target
    ON graph_edges(graph_id, target_vertex_id);

CREATE INDEX idx_edges_reverse
    ON graph_edges(graph_id, target_vertex_id, source_vertex_id);

CREATE INDEX idx_analysis_graph_time
    ON graph_analysis(graph_id, executed_at DESC);

CREATE INDEX idx_analysis_algorithm
    ON graph_analysis(algorithm, execution_status);

CREATE INDEX idx_traversal_analysis_order
    ON traversal_log(analysis_id, traversal_order);

CREATE INDEX idx_vertex_metadata
    ON graph_vertices USING GIN(metadata);

-- ============================================================
-- 3. EDGE INTEGRITY
-- ============================================================

CREATE OR REPLACE FUNCTION enforce_edge_direction()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    selected_type VARCHAR(20);
BEGIN
    SELECT graph_type
    INTO selected_type
    FROM graphs
    WHERE graph_id = NEW.graph_id;

    IF selected_type IS NULL THEN
        RAISE EXCEPTION 'Graph does not exist: %', NEW.graph_id;
    END IF;

    IF selected_type = 'UNDIRECTED' THEN
        IF NEW.source_vertex_id > NEW.target_vertex_id THEN
            RAISE EXCEPTION
                'Undirected edges must use canonical vertex ordering';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_edge_direction
BEFORE INSERT OR UPDATE ON graph_edges
FOR EACH ROW
EXECUTE FUNCTION enforce_edge_direction();

-- Automatically create the reverse edge for undirected graphs.
CREATE OR REPLACE FUNCTION create_reverse_edge()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    selected_type VARCHAR(20);
BEGIN
    SELECT graph_type
    INTO selected_type
    FROM graphs
    WHERE graph_id = NEW.graph_id;

    IF selected_type = 'UNDIRECTED' THEN
        INSERT INTO graph_edges (
            graph_id,
            source_vertex_id,
            target_vertex_id,
            weight
        )
        VALUES (
            NEW.graph_id,
            NEW.target_vertex_id,
            NEW.source_vertex_id,
            NEW.weight
        )
        ON CONFLICT (
            graph_id,
            source_vertex_id,
            target_vertex_id
        )
        DO NOTHING;
    END IF;

    RETURN NEW;
END;
$$;

-- Canonical insertion is used by the public procedure below.
-- The reverse edge is inserted through a separate internal path
-- to avoid recursively invoking the same trigger.
CREATE OR REPLACE FUNCTION synchronize_undirected_edge()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    selected_type VARCHAR(20);
BEGIN
    SELECT graph_type
    INTO selected_type
    FROM graphs
    WHERE graph_id = NEW.graph_id;

    IF selected_type = 'UNDIRECTED' THEN
        INSERT INTO graph_edges (
            graph_id,
            source_vertex_id,
            target_vertex_id,
            weight
        )
        VALUES (
            NEW.graph_id,
            NEW.target_vertex_id,
            NEW.source_vertex_id,
            NEW.weight
        )
        ON CONFLICT DO NOTHING;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_synchronize_undirected_edge
AFTER INSERT ON graph_edges
FOR EACH ROW
EXECUTE FUNCTION synchronize_undirected_edge();

-- ============================================================
-- 4. GRAPH INSERTION PROCEDURES
-- ============================================================

CREATE OR REPLACE PROCEDURE add_graph_vertex(
    p_graph_id BIGINT,
    p_vertex_key VARCHAR(150),
    p_vertex_type VARCHAR(50) DEFAULT 'GENERAL'
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_vertex_key IS NULL OR length(trim(p_vertex_key)) = 0 THEN
        RAISE EXCEPTION 'Vertex key cannot be empty';
    END IF;

    INSERT INTO graph_vertices (
        graph_id,
        vertex_key,
        vertex_type
    )
    VALUES (
        p_graph_id,
        p_vertex_key,
        p_vertex_type
    )
    ON CONFLICT (graph_id, vertex_key)
    DO NOTHING;
END;
$$;

CREATE OR REPLACE PROCEDURE add_graph_edge(
    p_graph_id BIGINT,
    p_source VARCHAR(150),
    p_target VARCHAR(150),
    p_weight NUMERIC DEFAULT 1
)
LANGUAGE plpgsql
AS $$
DECLARE
    source_id BIGINT;
    target_id BIGINT;
    selected_type VARCHAR(20);
BEGIN
    IF p_weight IS NULL OR p_weight < 0 THEN
        RAISE EXCEPTION 'Edge weight must be non-negative';
    END IF;

    IF p_source = p_target THEN
        RAISE EXCEPTION 'Self-loops are not supported';
    END IF;

    SELECT graph_type
    INTO selected_type
    FROM graphs
    WHERE graph_id = p_graph_id
    FOR UPDATE;

    IF selected_type IS NULL THEN
        RAISE EXCEPTION 'Graph does not exist';
    END IF;

    SELECT vertex_id INTO source_id
    FROM graph_vertices
    WHERE graph_id = p_graph_id
      AND vertex_key = p_source;

    SELECT vertex_id INTO target_id
    FROM graph_vertices
    WHERE graph_id = p_graph_id
      AND vertex_key = p_target;

    IF source_id IS NULL OR target_id IS NULL THEN
        RAISE EXCEPTION 'Both edge endpoints must exist';
    END IF;

    IF selected_type = 'UNDIRECTED' THEN
        IF source_id > target_id THEN
            SELECT source_id INTO source_id;
            SELECT target_id INTO target_id;
        END IF;

        INSERT INTO graph_edges (
            graph_id,
            source_vertex_id,
            target_vertex_id,
            weight
        )
        VALUES (
            p_graph_id,
            LEAST(source_id, target_id),
            GREATEST(source_id, target_id),
            p_weight
        )
        ON CONFLICT DO NOTHING;

    ELSE
        INSERT INTO graph_edges (
            graph_id,
            source_vertex_id,
            target_vertex_id,
            weight
        )
        VALUES (
            p_graph_id,
            source_id,
            target_id,
            p_weight
        )
        ON CONFLICT DO NOTHING;
    END IF;
END;
$$;

-- ============================================================
-- 5. BFS FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION bfs_traversal(
    p_graph_id BIGINT,
    p_source VARCHAR(150)
)
RETURNS TABLE (
    vertex_key VARCHAR(150),
    distance INTEGER,
    parent_vertex VARCHAR(150)
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    source_id BIGINT;
BEGIN
    SELECT vertex_id
    INTO source_id
    FROM graph_vertices
    WHERE graph_id = p_graph_id
      AND graph_vertices.vertex_key = p_source;

    IF source_id IS NULL THEN
        RAISE EXCEPTION 'Unknown BFS source: %', p_source;
    END IF;

    RETURN QUERY
    WITH RECURSIVE reachable(vertex_id, depth, path) AS (
        SELECT
            source_id,
            0,
            ARRAY[source_id]::BIGINT[]

        UNION ALL

        SELECT
            edge.target_vertex_id,
            reachable.depth + 1,
            reachable.path || edge.target_vertex_id
        FROM reachable
        JOIN graph_edges edge
          ON edge.graph_id = p_graph_id
         AND edge.source_vertex_id = reachable.vertex_id
        WHERE NOT edge.target_vertex_id = ANY(reachable.path)
          AND reachable.depth < 10000
    ),
    minimum_distance AS (
        SELECT
            vertex_id,
            MIN(depth)::INTEGER AS distance
        FROM reachable
        GROUP BY vertex_id
    )
    SELECT
        vertex.vertex_key,
        minimum_distance.distance,
        (
            SELECT parent.vertex_key
            FROM graph_edges edge
            JOIN graph_vertices parent
              ON parent.vertex_id = edge.source_vertex_id
            WHERE edge.graph_id = p_graph_id
              AND edge.target_vertex_id = minimum_distance.vertex_id
              AND EXISTS (
                  SELECT 1
                  FROM minimum_distance previous
                  WHERE previous.vertex_id = edge.source_vertex_id
                    AND previous.distance = minimum_distance.distance - 1
              )
            ORDER BY parent.vertex_key
            LIMIT 1
        )::VARCHAR(150)
    FROM minimum_distance
    JOIN graph_vertices vertex
      ON vertex.vertex_id = minimum_distance.vertex_id
    ORDER BY minimum_distance.distance, vertex.vertex_key;
END;
$$;

-- ============================================================
-- 6. DFS FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION dfs_traversal(
    p_graph_id BIGINT,
    p_source VARCHAR(150)
)
RETURNS TABLE (
    vertex_key VARCHAR(150),
    depth INTEGER,
    traversal_path TEXT
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    source_id BIGINT;
BEGIN
    SELECT vertex_id
    INTO source_id
    FROM graph_vertices
    WHERE graph_id = p_graph_id
      AND graph_vertices.vertex_key = p_source;

    IF source_id IS NULL THEN
        RAISE EXCEPTION 'Unknown DFS source: %', p_source;
    END IF;

    RETURN QUERY
    WITH RECURSIVE traversal(
        vertex_id,
        depth,
        path
    ) AS (
        SELECT
            source_id,
            0,
            ARRAY[source_id]::BIGINT[]

        UNION ALL

        SELECT
            edge.target_vertex_id,
            traversal.depth + 1,
            traversal.path || edge.target_vertex_id
        FROM traversal
        JOIN graph_edges edge
          ON edge.graph_id = p_graph_id
         AND edge.source_vertex_id = traversal.vertex_id
        WHERE NOT edge.target_vertex_id = ANY(traversal.path)
          AND traversal.depth < 10000
    )
    SELECT DISTINCT ON (vertex.vertex_id)
        vertex.vertex_key,
        traversal.depth,
        array_to_string(
            ARRAY(
                SELECT path_vertex.vertex_key
                FROM unnest(traversal.path) WITH ORDINALITY
                    AS path_item(vertex_id, position)
                JOIN graph_vertices path_vertex
                  ON path_vertex.vertex_id = path_item.vertex_id
                ORDER BY path_item.position
            ),
            ' -> '
        )
    FROM traversal
    JOIN graph_vertices vertex
      ON vertex.vertex_id = traversal.vertex_id
    ORDER BY vertex.vertex_id, traversal.depth, traversal.path;
END;
$$;

-- ============================================================
-- 7. CONNECTED COMPONENTS
-- ============================================================

CREATE OR REPLACE FUNCTION connected_components(
    p_graph_id BIGINT
)
RETURNS TABLE (
    component_id BIGINT,
    vertex_key VARCHAR(150),
    component_size BIGINT
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    selected_type VARCHAR(20);
BEGIN
    SELECT graph_type
    INTO selected_type
    FROM graphs
    WHERE graph_id = p_graph_id;

    IF selected_type IS NULL THEN
        RAISE EXCEPTION 'Graph does not exist';
    END IF;

    IF selected_type <> 'UNDIRECTED' THEN
        RAISE EXCEPTION
            'Connected components require an undirected graph';
    END IF;

    RETURN QUERY
    WITH RECURSIVE reachability(start_id, vertex_id) AS (
        SELECT vertex_id, vertex_id
        FROM graph_vertices
        WHERE graph_id = p_graph_id

        UNION

        SELECT
            reachability.start_id,
            edge.target_vertex_id
        FROM reachability
        JOIN graph_edges edge
          ON edge.graph_id = p_graph_id
         AND edge.source_vertex_id = reachability.vertex_id
    ),
    canonical_components AS (
        SELECT
            vertex_id,
            MIN(start_id) AS component_id
        FROM reachability
        GROUP BY vertex_id
    ),
    sizes AS (
        SELECT
            component_id,
            COUNT(*) AS component_size
        FROM canonical_components
        GROUP BY component_id
    )
    SELECT
        canonical_components.component_id,
        vertex.vertex_key,
        sizes.component_size
    FROM canonical_components
    JOIN graph_vertices vertex
      ON vertex.vertex_id = canonical_components.vertex_id
    JOIN sizes
      ON sizes.component_id = canonical_components.component_id
    ORDER BY canonical_components.component_id, vertex.vertex_key;
END;
$$;

-- ============================================================
-- 8. MULTI-SOURCE BFS
-- ============================================================

CREATE OR REPLACE FUNCTION multi_source_bfs(
    p_graph_id BIGINT,
    p_sources VARCHAR[]
)
RETURNS TABLE (
    vertex_key VARCHAR(150),
    minimum_distance INTEGER
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    IF p_sources IS NULL OR cardinality(p_sources) = 0 THEN
        RETURN;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM unnest(p_sources) AS source(key)
        LEFT JOIN graph_vertices vertex
          ON vertex.graph_id = p_graph_id
         AND vertex.vertex_key = source.key
        WHERE vertex.vertex_id IS NULL
    ) THEN
        RAISE EXCEPTION 'One or more BFS sources do not exist';
    END IF;

    RETURN QUERY
    WITH RECURSIVE reachable(vertex_id, depth, path) AS (
        SELECT
            vertex.vertex_id,
            0,
            ARRAY[vertex.vertex_id]::BIGINT[]
        FROM graph_vertices vertex
        WHERE vertex.graph_id = p_graph_id
          AND vertex.vertex_key = ANY(p_sources)

        UNION ALL

        SELECT
            edge.target_vertex_id,
            reachable.depth + 1,
            reachable.path || edge.target_vertex_id
        FROM reachable
        JOIN graph_edges edge
          ON edge.graph_id = p_graph_id
         AND edge.source_vertex_id = reachable.vertex_id
        WHERE NOT edge.target_vertex_id = ANY(reachable.path)
          AND reachable.depth < 10000
    )
    SELECT
        vertex.vertex_key,
        MIN(reachable.depth)::INTEGER
    FROM reachable
    JOIN graph_vertices vertex
      ON vertex.vertex_id = reachable.vertex_id
    GROUP BY vertex.vertex_key
    ORDER BY MIN(reachable.depth), vertex.vertex_key;
END;
$$;

-- ============================================================
-- 9. REPORTING VIEWS
-- ============================================================

CREATE VIEW graph_edge_details AS
SELECT
    edge.edge_id,
    edge.graph_id,
    graph.graph_name,
    graph.graph_type,
    source.vertex_key AS source_vertex,
    target.vertex_key AS target_vertex,
    edge.weight,
    edge.created_at
FROM graph_edges edge
JOIN graphs graph
  ON graph.graph_id = edge.graph_id
JOIN graph_vertices source
  ON source.vertex_id = edge.source_vertex_id
JOIN graph_vertices target
  ON target.vertex_id = edge.target_vertex_id;

CREATE VIEW component_summary AS
SELECT
    graph.graph_id,
    graph.graph_name,
    COUNT(DISTINCT vertex.vertex_id) AS vertex_count,
    COUNT(DISTINCT edge.edge_id) FILTER (
        WHERE edge.source_vertex_id < edge.target_vertex_id
           OR graph.graph_type = 'DIRECTED'
    ) AS edge_count,
    COUNT(vertex.vertex_id) FILTER (
        WHERE NOT EXISTS (
            SELECT 1
            FROM graph_edges connected
            WHERE connected.graph_id = graph.graph_id
              AND (
                  connected.source_vertex_id = vertex.vertex_id
                  OR connected.target_vertex_id = vertex.vertex_id
              )
        )
    ) AS isolated_vertex_count
FROM graphs graph
LEFT JOIN graph_vertices vertex
  ON vertex.graph_id = graph.graph_id
LEFT JOIN graph_edges edge
  ON edge.graph_id = graph.graph_id
GROUP BY graph.graph_id, graph.graph_name;

-- ============================================================
-- 10. SAMPLE GRAPHS
-- ============================================================

INSERT INTO graphs (
    graph_name,
    graph_type,
    description
)
VALUES
(
    'enterprise_infrastructure',
    'UNDIRECTED',
    'Infrastructure connectivity and reachability'
),
(
    'deployment_dependencies',
    'DIRECTED',
    'Software deployment dependency graph'
);

-- Insert infrastructure vertices.
DO $$
DECLARE
    graph_key BIGINT;
    vertex_name VARCHAR(150);
BEGIN
    SELECT graph_id INTO graph_key
    FROM graphs
    WHERE graph_name = 'enterprise_infrastructure';

    FOREACH vertex_name IN ARRAY ARRAY[
        'API',
        'Gateway',
        'Authentication',
        'Orders',
        'Database',
        'Cache',
        'Monitoring',
        'Logging',
        'Backup',
        'Storage',
        'OfflineNode'
    ]
    LOOP
        CALL add_graph_vertex(graph_key, vertex_name);
    END LOOP;
END;
$$;

-- Insert infrastructure edges.
DO $$
DECLARE
    graph_key BIGINT;
BEGIN
    SELECT graph_id INTO graph_key
    FROM graphs
    WHERE graph_name = 'enterprise_infrastructure';

    CALL add_graph_edge(graph_key, 'API', 'Gateway', 1);
    CALL add_graph_edge(graph_key, 'Gateway', 'Authentication', 1);
    CALL add_graph_edge(graph_key, 'Gateway', 'Orders', 1);
    CALL add_graph_edge(graph_key, 'Orders', 'Database', 1);
    CALL add_graph_edge(graph_key, 'Orders', 'Cache', 1);
    CALL add_graph_edge(graph_key, 'Monitoring', 'Logging', 1);
    CALL add_graph_edge(graph_key, 'Backup', 'Storage', 1);
END;
$$;

-- Insert directed deployment dependencies.
DO $$
DECLARE
    graph_key BIGINT;
    vertex_name VARCHAR(150);
BEGIN
    SELECT graph_id INTO graph_key
    FROM graphs
    WHERE graph_name = 'deployment_dependencies';

    FOREACH vertex_name IN ARRAY ARRAY[
        'Core',
        'Authentication',
        'API',
        'Frontend',
        'Reporting',
        'Documentation'
    ]
    LOOP
        CALL add_graph_vertex(graph_key, vertex_name);
    END LOOP;

    CALL add_graph_edge(graph_key, 'Core', 'Authentication', 1);
    CALL add_graph_edge(graph_key, 'Authentication', 'API', 1);
    CALL add_graph_edge(graph_key, 'API', 'Frontend', 1);
    CALL add_graph_edge(graph_key, 'Core', 'Reporting', 1);
END;
$$;

-- ============================================================
-- 11. BFS RETRIEVAL
-- ============================================================

SELECT *
FROM bfs_traversal(
    (
        SELECT graph_id
        FROM graphs
        WHERE graph_name = 'enterprise_infrastructure'
    ),
    'API'
);

-- Multi-source BFS.
SELECT *
FROM multi_source_bfs(
    (
        SELECT graph_id
        FROM graphs
        WHERE graph_name = 'enterprise_infrastructure'
    ),
    ARRAY['API', 'Monitoring']
);

-- ============================================================
-- 12. DFS RETRIEVAL
-- ============================================================

SELECT *
FROM dfs_traversal(
    (
        SELECT graph_id
        FROM graphs
        WHERE graph_name = 'deployment_dependencies'
    ),
    'Core'
);

-- ============================================================
-- 13. CONNECTED COMPONENTS
-- ============================================================

SELECT *
FROM connected_components(
    (
        SELECT graph_id
        FROM graphs
        WHERE graph_name = 'enterprise_infrastructure'
    )
);

-- Aggregate component report.
WITH components AS (
    SELECT *
    FROM connected_components(
        (
            SELECT graph_id
            FROM graphs
            WHERE graph_name = 'enterprise_infrastructure'
        )
    )
)
SELECT
    component_id,
    COUNT(*) AS vertices_in_component,
    ARRAY_AGG(vertex_key ORDER BY vertex_key) AS members
FROM components
GROUP BY component_id
ORDER BY component_id;

-- ============================================================
-- 14. GRAPH VALIDATION AND REPORTING
-- ============================================================

SELECT * FROM component_summary;

SELECT
    graph_name,
    source_vertex,
    target_vertex,
    weight
FROM graph_edge_details
ORDER BY graph_name, source_vertex, target_vertex;

-- Detect isolated vertices.
SELECT
    graph.graph_name,
    vertex.vertex_key
FROM graph_vertices vertex
JOIN graphs graph
  ON graph.graph_id = vertex.graph_id
WHERE NOT EXISTS (
    SELECT 1
    FROM graph_edges edge
    WHERE edge.graph_id = vertex.graph_id
      AND (
          edge.source_vertex_id = vertex.vertex_id
          OR edge.target_vertex_id = vertex.vertex_id
      )
)
ORDER BY graph.graph_name, vertex.vertex_key;

-- ============================================================
-- 15. ANALYSIS AUDIT
-- ============================================================

INSERT INTO graph_analysis (
    graph_id,
    algorithm,
    source_vertex_id,
    execution_status,
    result,
    execution_time_ms
)
SELECT
    graph.graph_id,
    'BFS',
    source.vertex_id,
    'COMPLETED',
    jsonb_build_object(
        'source', source.vertex_key,
        'reachable_count', (
            SELECT COUNT(*)
            FROM bfs_traversal(
                graph.graph_id,
                source.vertex_key
            )
        )
    ),
    1.250
FROM graphs graph
JOIN graph_vertices source
  ON source.graph_id = graph.graph_id
 AND source.vertex_key = 'API'
WHERE graph.graph_name = 'enterprise_infrastructure';

SELECT
    graph.graph_name,
    analysis.algorithm,
    analysis.execution_status,
    analysis.result,
    analysis.execution_time_ms,
    analysis.executed_at
FROM graph_analysis analysis
JOIN graphs graph
  ON graph.graph_id = analysis.graph_id
ORDER BY analysis.executed_at DESC;

-- ============================================================
-- 16. INVALID INPUT DEMONSTRATION
-- ============================================================

-- The following validations intentionally run inside exception
-- blocks so the overall script remains executable.

DO $$
DECLARE
    graph_key BIGINT;
    rejected BOOLEAN := FALSE;
BEGIN
    SELECT graph_id INTO graph_key
    FROM graphs
    WHERE graph_name = 'enterprise_infrastructure';

    BEGIN
        CALL add_graph_edge(
            graph_key,
            'API',
            'MissingVertex',
            1
        );
    EXCEPTION WHEN OTHERS THEN
        rejected := TRUE;
        RAISE NOTICE 'Invalid edge rejected: %', SQLERRM;
    END;

    IF NOT rejected THEN
        RAISE EXCEPTION 'Invalid edge validation failed';
    END IF;
END;
$$;

-- ============================================================
-- 17. TRANSACTION AND INTEGRITY DEMONSTRATION
-- ============================================================

SAVEPOINT before_temporary_vertex;

DO $$
DECLARE
    graph_key BIGINT;
BEGIN
    SELECT graph_id INTO graph_key
    FROM graphs
    WHERE graph_name = 'enterprise_infrastructure';

    CALL add_graph_vertex(
        graph_key,
        'TemporaryNode',
        'TEST'
    );
END;
$$;

ROLLBACK TO SAVEPOINT before_temporary_vertex;

COMMIT;

-- ============================================================
-- END OF GRAPH ALGORITHMS I
-- ============================================================
