DROP SCHEMA IF EXISTS graph_lab CASCADE;
CREATE SCHEMA graph_lab;

SET search_path = graph_lab, public;

CREATE TYPE graph_direction AS ENUM ('DIRECTED', 'UNDIRECTED');

CREATE TABLE graph (
    graph_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    graph_name TEXT NOT NULL UNIQUE,
    direction graph_direction NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE vertex (
    vertex_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    graph_id BIGINT NOT NULL REFERENCES graph(graph_id) ON DELETE CASCADE,
    vertex_key TEXT NOT NULL,
    label TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT uq_vertex_graph_key UNIQUE (graph_id, vertex_key),
    CONSTRAINT ck_vertex_key_nonempty CHECK (length(trim(vertex_key)) > 0),
    CONSTRAINT ck_vertex_label_nonempty CHECK (length(trim(label)) > 0)
);

CREATE TABLE edge (
    edge_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    graph_id BIGINT NOT NULL REFERENCES graph(graph_id) ON DELETE CASCADE,
    source_vertex_id BIGINT NOT NULL REFERENCES vertex(vertex_id) ON DELETE CASCADE,
    target_vertex_id BIGINT NOT NULL REFERENCES vertex(vertex_id) ON DELETE CASCADE,
    weight NUMERIC(12, 4) NOT NULL DEFAULT 1.0,
    edge_label TEXT NOT NULL DEFAULT '',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_edge_weight_nonnegative CHECK (weight >= 0),
    CONSTRAINT ck_edge_vertices_distinct CHECK (
        source_vertex_id <> target_vertex_id
    )
);

CREATE UNIQUE INDEX uq_directed_edge
ON edge(graph_id, source_vertex_id, target_vertex_id);

CREATE TABLE graph_policy (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    graph_id BIGINT NOT NULL UNIQUE REFERENCES graph(graph_id) ON DELETE CASCADE,
    allow_negative_weights BOOLEAN NOT NULL DEFAULT FALSE,
    require_connected BOOLEAN NOT NULL DEFAULT FALSE,
    max_vertices INTEGER NOT NULL DEFAULT 10000,
    max_edges INTEGER NOT NULL DEFAULT 50000,
    CONSTRAINT ck_policy_limits CHECK (
        max_vertices > 0 AND max_edges > 0
    )
);

CREATE INDEX idx_vertex_graph ON vertex(graph_id);
CREATE INDEX idx_edge_graph_source ON edge(graph_id, source_vertex_id);
CREATE INDEX idx_edge_graph_target ON edge(graph_id, target_vertex_id);
CREATE INDEX idx_edge_weight ON edge(graph_id, weight);

CREATE OR REPLACE FUNCTION validate_edge_graph_membership()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    source_graph BIGINT;
    target_graph BIGINT;
    direction_value graph_direction;
BEGIN
    SELECT graph_id
    INTO source_graph
    FROM vertex
    WHERE vertex_id = NEW.source_vertex_id;

    SELECT graph_id
    INTO target_graph
    FROM vertex
    WHERE vertex_id = NEW.target_vertex_id;

    IF source_graph IS NULL OR target_graph IS NULL THEN
        RAISE EXCEPTION 'Both edge vertices must exist';
    END IF;

    IF source_graph <> NEW.graph_id OR target_graph <> NEW.graph_id THEN
        RAISE EXCEPTION
            'Edge endpoints must belong to the edge graph';
    END IF;

    SELECT direction
    INTO direction_value
    FROM graph
    WHERE graph_id = NEW.graph_id;

    IF direction_value = 'UNDIRECTED'
       AND EXISTS (
            SELECT 1
            FROM edge e
            WHERE e.graph_id = NEW.graph_id
              AND e.source_vertex_id = NEW.target_vertex_id
              AND e.target_vertex_id = NEW.source_vertex_id
              AND e.edge_id <> COALESCE(NEW.edge_id, -1)
       )
    THEN
        RAISE EXCEPTION
            'Undirected graph cannot contain duplicate reverse edges';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_edge_graph_membership
BEFORE INSERT OR UPDATE ON edge
FOR EACH ROW
EXECUTE FUNCTION validate_edge_graph_membership();

CREATE OR REPLACE FUNCTION enforce_graph_limits()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    vertex_limit INTEGER;
    edge_limit INTEGER;
    current_vertices INTEGER;
    current_edges INTEGER;
BEGIN
    SELECT max_vertices, max_edges
    INTO vertex_limit, edge_limit
    FROM graph_policy
    WHERE graph_id = NEW.graph_id;

    IF TG_TABLE_NAME = 'vertex' THEN
        SELECT count(*)
        INTO current_vertices
        FROM vertex
        WHERE graph_id = NEW.graph_id;

        IF current_vertices >= vertex_limit THEN
            RAISE EXCEPTION
                'Vertex limit exceeded for graph %', NEW.graph_id;
        END IF;
    ELSE
        SELECT count(*)
        INTO current_edges
        FROM edge
        WHERE graph_id = NEW.graph_id;

        IF current_edges >= edge_limit THEN
            RAISE EXCEPTION
                'Edge limit exceeded for graph %', NEW.graph_id;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_enforce_vertex_limit
BEFORE INSERT ON vertex
FOR EACH ROW
EXECUTE FUNCTION enforce_graph_limits();

CREATE TRIGGER trg_enforce_edge_limit
BEFORE INSERT ON edge
FOR EACH ROW
EXECUTE FUNCTION enforce_graph_limits();

CREATE OR REPLACE FUNCTION graph_edge_count(p_graph_id BIGINT)
RETURNS BIGINT
LANGUAGE SQL
STABLE
AS $$
    SELECT count(*)
    FROM edge
    WHERE graph_id = p_graph_id;
$$;

CREATE OR REPLACE FUNCTION graph_vertex_count(p_graph_id BIGINT)
RETURNS BIGINT
LANGUAGE SQL
STABLE
AS $$
    SELECT count(*)
    FROM vertex
    WHERE graph_id = p_graph_id;
$$;

CREATE OR REPLACE FUNCTION reachable_vertices(
    p_graph_id BIGINT,
    p_start_vertex_id BIGINT
)
RETURNS TABLE (
    vertex_id BIGINT,
    distance INTEGER
)
LANGUAGE sql
STABLE
AS $$
    WITH RECURSIVE traversal(vertex_id, distance) AS (
        SELECT p_start_vertex_id, 0

        UNION

        SELECT
            e.target_vertex_id,
            t.distance + 1
        FROM traversal t
        JOIN edge e
          ON e.source_vertex_id = t.vertex_id
         AND e.graph_id = p_graph_id
    )
    SELECT vertex_id, min(distance)
    FROM traversal
    GROUP BY vertex_id
    ORDER BY min(distance), vertex_id;
$$;

CREATE OR REPLACE FUNCTION weighted_reachability(
    p_graph_id BIGINT,
    p_start_vertex_id BIGINT
)
RETURNS TABLE (
    vertex_id BIGINT,
    minimum_known_cost NUMERIC
)
LANGUAGE sql
STABLE
AS $$
    WITH RECURSIVE paths(vertex_id, total_cost, visited) AS (
        SELECT
            p_start_vertex_id,
            0::numeric,
            ARRAY[p_start_vertex_id]::BIGINT[]

        UNION ALL

        SELECT
            e.target_vertex_id,
            p.total_cost + e.weight,
            p.visited || e.target_vertex_id
        FROM paths p
        JOIN edge e
          ON e.graph_id = p_graph_id
         AND e.source_vertex_id = p.vertex_id
        WHERE NOT e.target_vertex_id = ANY(p.visited)
    )
    SELECT
        vertex_id,
        min(total_cost)
    FROM paths
    GROUP BY vertex_id
    ORDER BY min(total_cost), vertex_id;
$$;

CREATE OR REPLACE VIEW graph_statistics AS
SELECT
    g.graph_id,
    g.graph_name,
    g.direction,
    count(DISTINCT v.vertex_id) AS vertex_count,
    count(DISTINCT e.edge_id) AS edge_count,
    COALESCE(avg(e.weight), 0) AS average_edge_weight,
    COALESCE(min(e.weight), 0) AS minimum_edge_weight,
    COALESCE(max(e.weight), 0) AS maximum_edge_weight
FROM graph g
LEFT JOIN vertex v
    ON v.graph_id = g.graph_id
LEFT JOIN edge e
    ON e.graph_id = g.graph_id
GROUP BY g.graph_id, g.graph_name, g.direction;

CREATE OR REPLACE VIEW edge_report AS
SELECT
    e.edge_id,
    g.graph_name,
    sv.vertex_key AS source_vertex,
    tv.vertex_key AS target_vertex,
    e.weight,
    e.edge_label
FROM edge e
JOIN graph g
    ON g.graph_id = e.graph_id
JOIN vertex sv
    ON sv.vertex_id = e.source_vertex_id
JOIN vertex tv
    ON tv.vertex_id = e.target_vertex_id;

BEGIN;

INSERT INTO graph (graph_name, direction, description)
VALUES (
    'india_delivery_network',
    'DIRECTED',
    'Directed weighted transportation network measured in travel hours'
);

INSERT INTO graph_policy (
    graph_id,
    allow_negative_weights,
    require_connected,
    max_vertices,
    max_edges
)
SELECT graph_id, FALSE, FALSE, 100, 500
FROM graph
WHERE graph_name = 'india_delivery_network';

INSERT INTO vertex (graph_id, vertex_key, label)
SELECT graph_id, city, city
FROM graph
CROSS JOIN (
    VALUES
        ('Lucknow'),
        ('Kanpur'),
        ('Ayodhya'),
        ('Varanasi'),
        ('Agra'),
        ('Delhi'),
        ('Jaipur'),
        ('Patna'),
        ('Ahmedabad'),
        ('Kolkata'),
        ('Mumbai'),
        ('Bengaluru'),
        ('Guwahati')
) AS cities(city)
WHERE graph_name = 'india_delivery_network';

INSERT INTO edge (
    graph_id,
    source_vertex_id,
    target_vertex_id,
    weight,
    edge_label
)
SELECT
    g.graph_id,
    source_vertex.vertex_id,
    target_vertex.vertex_id,
    routes.weight,
    'transport route'
FROM graph g
JOIN (
    VALUES
        ('Lucknow', 'Kanpur', 1.5),
        ('Lucknow', 'Ayodhya', 2.0),
        ('Kanpur', 'Agra', 3.0),
        ('Ayodhya', 'Varanasi', 2.5),
        ('Agra', 'Delhi', 2.0),
        ('Varanasi', 'Patna', 4.0),
        ('Delhi', 'Jaipur', 3.0),
        ('Delhi', 'Patna', 5.0),
        ('Jaipur', 'Ahmedabad', 4.0),
        ('Patna', 'Kolkata', 5.0),
        ('Ahmedabad', 'Mumbai', 6.0),
        ('Kolkata', 'Guwahati', 7.0),
        ('Mumbai', 'Bengaluru', 7.0)
) AS routes(source_name, target_name, weight)
    ON TRUE
JOIN vertex source_vertex
    ON source_vertex.graph_id = g.graph_id
   AND source_vertex.vertex_key = routes.source_name
JOIN vertex target_vertex
    ON target_vertex.graph_id = g.graph_id
   AND target_vertex.vertex_key = routes.target_name
WHERE g.graph_name = 'india_delivery_network';

COMMIT;

-- Basic graph retrieval.
SELECT *
FROM edge_report
ORDER BY source_vertex, target_vertex;

-- Graph-level aggregation.
SELECT *
FROM graph_statistics;

-- Outgoing weighted routes from Delhi.
SELECT
    source_vertex,
    target_vertex,
    weight
FROM edge_report
WHERE graph_name = 'india_delivery_network'
  AND source_vertex = 'Delhi'
ORDER BY weight;

-- Validate that all edge weights satisfy the graph's policy.
SELECT
    g.graph_name,
    count(*) AS invalid_weight_count
FROM graph g
JOIN edge e
    ON e.graph_id = g.graph_id
JOIN graph_policy p
    ON p.graph_id = g.graph_id
WHERE e.weight < 0
  AND p.allow_negative_weights = FALSE
GROUP BY g.graph_name;

-- Reachability from Lucknow using recursive traversal.
SELECT
    v.vertex_key,
    r.distance
FROM graph g
JOIN vertex start_vertex
    ON start_vertex.graph_id = g.graph_id
JOIN reachable_vertices(
    g.graph_id,
    start_vertex.vertex_id
) r
    ON TRUE
JOIN vertex v
    ON v.vertex_id = r.vertex_id
WHERE g.graph_name = 'india_delivery_network'
  AND start_vertex.vertex_key = 'Lucknow'
ORDER BY r.distance, v.vertex_key;

-- Weighted path exploration without cycles.
SELECT
    v.vertex_key,
    wr.minimum_known_cost
FROM graph g
JOIN vertex start_vertex
    ON start_vertex.graph_id = g.graph_id
JOIN weighted_reachability(
    g.graph_id,
    start_vertex.vertex_id
) wr
    ON TRUE
JOIN vertex v
    ON v.vertex_id = wr.vertex_id
WHERE g.graph_name = 'india_delivery_network'
  AND start_vertex.vertex_key = 'Lucknow'
ORDER BY wr.minimum_known_cost, v.vertex_key;

-- Identify vertices with no outgoing edges.
SELECT
    v.vertex_key
FROM vertex v
WHERE v.graph_id = (
    SELECT graph_id
    FROM graph
    WHERE graph_name = 'india_delivery_network'
)
AND NOT EXISTS (
    SELECT 1
    FROM edge e
    WHERE e.source_vertex_id = v.vertex_id
)
ORDER BY v.vertex_key;

-- Identify vertices with no incoming edges.
SELECT
    v.vertex_key
FROM vertex v
WHERE v.graph_id = (
    SELECT graph_id
    FROM graph
    WHERE graph_name = 'india_delivery_network'
)
AND NOT EXISTS (
    SELECT 1
    FROM edge e
    WHERE e.target_vertex_id = v.vertex_id
)
ORDER BY v.vertex_key;

-- Transactional insertion of a new route.
BEGIN;

WITH graph_row AS (
    SELECT graph_id
    FROM graph
    WHERE graph_name = 'india_delivery_network'
),
source_row AS (
    SELECT v.vertex_id, v.graph_id
    FROM vertex v
    JOIN graph_row g
      ON g.graph_id = v.graph_id
    WHERE v.vertex_key = 'Delhi'
),
target_row AS (
    SELECT v.vertex_id, v.graph_id
    FROM vertex v
    JOIN graph_row g
      ON g.graph_id = v.graph_id
    WHERE v.vertex_key = 'Mumbai'
)
INSERT INTO edge (
    graph_id,
    source_vertex_id,
    target_vertex_id,
    weight,
    edge_label
)
SELECT
    s.graph_id,
    s.vertex_id,
    t.vertex_id,
    9.0,
    'temporary direct route'
FROM source_row s
JOIN target_row t
  ON t.graph_id = s.graph_id
ON CONFLICT (graph_id, source_vertex_id, target_vertex_id)
DO UPDATE
SET weight = EXCLUDED.weight,
    edge_label = EXCLUDED.edge_label;

COMMIT;

-- Verify the transactional change.
SELECT *
FROM edge_report
WHERE source_vertex = 'Delhi'
  AND target_vertex = 'Mumbai';

-- A negative-weight insertion is rejected by the database constraint.
-- The following statement intentionally fails and should not be used
-- as part of an automated successful deployment:
-- INSERT INTO edge (
--     graph_id, source_vertex_id, target_vertex_id, weight
-- )
-- SELECT
--     g.graph_id, v1.vertex_id, v2.vertex_id, -5
-- FROM graph g
-- JOIN vertex v1 ON v1.graph_id = g.graph_id
-- JOIN vertex v2 ON v2.graph_id = g.graph_id
-- WHERE g.graph_name = 'india_delivery_network'
--   AND v1.vertex_key = 'Delhi'
--   AND v2.vertex_key = 'Mumbai';

-- The relational model stores the graph explicitly:
-- graph -> vertex -> edge
-- while recursive CTEs provide reachability analysis.
