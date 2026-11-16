/*
===============================================================================
GRAPH ALGORITHMS II
DIJKSTRA'S SHORTEST PATH ENGINE
PostgreSQL 15+

Implemented capabilities:
- Relational graph representation
- Weighted directed and undirected edges
- Vertex and edge integrity constraints
- Dijkstra's algorithm using PL/pgSQL
- Priority selection through ordered SQL queries
- Predecessor tracking
- Path reconstruction
- Multi-source routing
- Route eligibility and validation
- Reachability reporting
- Graph statistics
- Execution transactions
- Performance-oriented indexes
===============================================================================
*/

BEGIN;

DROP SCHEMA IF EXISTS graph_lab CASCADE;

CREATE SCHEMA graph_lab;

SET search_path TO graph_lab, public;

-- ============================================================================
-- 1. DOMAIN TYPES
-- ============================================================================

CREATE TYPE graph_lab.graph_kind AS ENUM (
    'DIRECTED',
    'UNDIRECTED'
);

CREATE TYPE graph_lab.route_status AS ENUM (
    'REACHABLE',
    'UNREACHABLE'
);

CREATE TYPE graph_lab.graph_state AS ENUM (
    'ACTIVE',
    'INACTIVE'
);

-- ============================================================================
-- 2. GRAPH TABLES
-- ============================================================================

CREATE TABLE graph_lab.graphs (
    graph_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    graph_name VARCHAR(150) NOT NULL UNIQUE,

    graph_type graph_lab.graph_kind NOT NULL,

    state graph_lab.graph_state NOT NULL DEFAULT 'ACTIVE',

    version BIGINT NOT NULL DEFAULT 1,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_graph_version CHECK (version > 0)
);

CREATE TABLE graph_lab.vertices (
    vertex_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    graph_id BIGINT NOT NULL
        REFERENCES graph_lab.graphs(graph_id)
        ON DELETE CASCADE,

    vertex_code VARCHAR(80) NOT NULL,

    vertex_name VARCHAR(150) NOT NULL,

    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_vertex_code
        UNIQUE (graph_id, vertex_code),

    CONSTRAINT valid_vertex_code
        CHECK (length(trim(vertex_code)) > 0),

    CONSTRAINT valid_vertex_name
        CHECK (length(trim(vertex_name)) > 0)
);

CREATE TABLE graph_lab.edges (
    edge_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    graph_id BIGINT NOT NULL
        REFERENCES graph_lab.graphs(graph_id)
        ON DELETE CASCADE,

    source_vertex_id BIGINT NOT NULL,

    destination_vertex_id BIGINT NOT NULL,

    weight NUMERIC(18, 6) NOT NULL,

    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT source_vertex_fk
        FOREIGN KEY (graph_id, source_vertex_id)
        REFERENCES graph_lab.vertices(graph_id, vertex_id)
        ON DELETE CASCADE,

    CONSTRAINT destination_vertex_fk
        FOREIGN KEY (graph_id, destination_vertex_id)
        REFERENCES graph_lab.vertices(graph_id, vertex_id)
        ON DELETE CASCADE,

    CONSTRAINT nonnegative_weight CHECK (weight >= 0),

    CONSTRAINT finite_business_weight CHECK (
        weight < 1000000000000
    )
);

-- Required composite unique key for the composite foreign keys.
ALTER TABLE graph_lab.vertices
ADD CONSTRAINT unique_graph_vertex_pair
UNIQUE (graph_id, vertex_id);

-- ============================================================================
-- 3. ROUTING EXECUTION TABLES
-- ============================================================================

CREATE TABLE graph_lab.route_runs (
    route_run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    graph_id BIGINT NOT NULL
        REFERENCES graph_lab.graphs(graph_id),

    source_vertex_id BIGINT NOT NULL,

    destination_vertex_id BIGINT,

    graph_version BIGINT NOT NULL,

    status graph_lab.route_status NOT NULL,

    total_distance NUMERIC(24, 6),

    settled_vertices INTEGER NOT NULL DEFAULT 0,

    examined_edges INTEGER NOT NULL DEFAULT 0,

    relaxations INTEGER NOT NULL DEFAULT 0,

    execution_started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    execution_completed_at TIMESTAMPTZ,

    CONSTRAINT nonnegative_route_distance
        CHECK (total_distance IS NULL OR total_distance >= 0),

    CONSTRAINT valid_route_counters CHECK (
        settled_vertices >= 0
        AND examined_edges >= 0
        AND relaxations >= 0
    ),

    CONSTRAINT valid_execution_timestamps CHECK (
        execution_completed_at IS NULL
        OR execution_completed_at >= execution_started_at
    )
);

CREATE TABLE graph_lab.route_results (
    route_run_id BIGINT NOT NULL
        REFERENCES graph_lab.route_runs(route_run_id)
        ON DELETE CASCADE,

    vertex_id BIGINT NOT NULL
        REFERENCES graph_lab.vertices(vertex_id),

    distance NUMERIC(24, 6),

    predecessor_vertex_id BIGINT
        REFERENCES graph_lab.vertices(vertex_id),

    settled BOOLEAN NOT NULL DEFAULT FALSE,

    PRIMARY KEY (route_run_id, vertex_id),

    CONSTRAINT valid_distance
        CHECK (distance IS NULL OR distance >= 0)
);

CREATE TABLE graph_lab.route_path (
    route_run_id BIGINT NOT NULL
        REFERENCES graph_lab.route_runs(route_run_id)
        ON DELETE CASCADE,

    sequence_number INTEGER NOT NULL,

    vertex_id BIGINT NOT NULL
        REFERENCES graph_lab.vertices(vertex_id),

    cumulative_distance NUMERIC(24, 6) NOT NULL,

    PRIMARY KEY (route_run_id, sequence_number),

    CONSTRAINT valid_sequence CHECK (sequence_number > 0),

    CONSTRAINT valid_cumulative_distance
        CHECK (cumulative_distance >= 0)
);

-- ============================================================================
-- 4. INDEXES
-- ============================================================================

CREATE INDEX idx_vertices_graph_active
ON graph_lab.vertices(graph_id, active);

CREATE INDEX idx_edges_outgoing
ON graph_lab.edges(
    graph_id,
    source_vertex_id,
    weight
)
WHERE active = TRUE;

CREATE INDEX idx_edges_incoming
ON graph_lab.edges(
    graph_id,
    destination_vertex_id
)
WHERE active = TRUE;

CREATE INDEX idx_route_runs_graph
ON graph_lab.route_runs(graph_id, execution_started_at DESC);

CREATE INDEX idx_route_results_distance
ON graph_lab.route_results(
    route_run_id,
    distance
);

CREATE INDEX idx_route_path_vertex
ON graph_lab.route_path(vertex_id);

-- ============================================================================
-- 5. GRAPH VERSION MANAGEMENT
-- ============================================================================

CREATE OR REPLACE FUNCTION graph_lab.increment_graph_version()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = graph_lab, pg_temp
AS $$
DECLARE
    affected_graph BIGINT;
BEGIN
    IF TG_OP = 'DELETE' THEN
        affected_graph := OLD.graph_id;
    ELSE
        affected_graph := NEW.graph_id;
    END IF;

    UPDATE graph_lab.graphs
    SET version = version + 1
    WHERE graph_id = affected_graph;

    RETURN CASE
        WHEN TG_OP = 'DELETE' THEN OLD
        ELSE NEW
    END;
END;
$$;

CREATE TRIGGER vertex_version_trigger
AFTER INSERT OR UPDATE OR DELETE
ON graph_lab.vertices
FOR EACH ROW
EXECUTE FUNCTION graph_lab.increment_graph_version();

CREATE TRIGGER edge_version_trigger
AFTER INSERT OR UPDATE OR DELETE
ON graph_lab.edges
FOR EACH ROW
EXECUTE FUNCTION graph_lab.increment_graph_version();

-- ============================================================================
-- 6. GRAPH INTEGRITY VALIDATION
-- ============================================================================

CREATE OR REPLACE FUNCTION graph_lab.validate_edge()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = graph_lab, pg_temp
AS $$
DECLARE
    graph_type_value graph_lab.graph_kind;
    source_active BOOLEAN;
    destination_active BOOLEAN;
    graph_active BOOLEAN;
BEGIN
    SELECT
        g.graph_type,
        g.state = 'ACTIVE'
    INTO
        graph_type_value,
        graph_active
    FROM graph_lab.graphs g
    WHERE g.graph_id = NEW.graph_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Graph % does not exist', NEW.graph_id;
    END IF;

    IF NOT graph_active THEN
        RAISE EXCEPTION 'Cannot modify an inactive graph';
    END IF;

    SELECT v.active
    INTO source_active
    FROM graph_lab.vertices v
    WHERE v.graph_id = NEW.graph_id
      AND v.vertex_id = NEW.source_vertex_id;

    SELECT v.active
    INTO destination_active
    FROM graph_lab.vertices v
    WHERE v.graph_id = NEW.graph_id
      AND v.vertex_id = NEW.destination_vertex_id;

    IF NOT COALESCE(source_active, FALSE) THEN
        RAISE EXCEPTION 'Source vertex is inactive or missing';
    END IF;

    IF NOT COALESCE(destination_active, FALSE) THEN
        RAISE EXCEPTION 'Destination vertex is inactive or missing';
    END IF;

    IF NEW.weight < 0 THEN
        RAISE EXCEPTION 'Negative edge weights are prohibited';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER validate_edge_trigger
BEFORE INSERT OR UPDATE
ON graph_lab.edges
FOR EACH ROW
EXECUTE FUNCTION graph_lab.validate_edge();

-- ============================================================================
-- 7. GRAPH DATA ACCESS VIEW
-- ============================================================================

CREATE OR REPLACE VIEW graph_lab.graph_edge_details AS
SELECT
    e.edge_id,
    e.graph_id,
    g.graph_name,
    g.graph_type,
    sv.vertex_code AS source_code,
    sv.vertex_name AS source_name,
    dv.vertex_code AS destination_code,
    dv.vertex_name AS destination_name,
    e.weight,
    e.active
FROM graph_lab.edges e
JOIN graph_lab.graphs g
    ON g.graph_id = e.graph_id
JOIN graph_lab.vertices sv
    ON sv.vertex_id = e.source_vertex_id
   AND sv.graph_id = e.graph_id
JOIN graph_lab.vertices dv
    ON dv.vertex_id = e.destination_vertex_id
   AND dv.graph_id = e.graph_id;

-- ============================================================================
-- 8. SINGLE-SOURCE DIJKSTRA FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION graph_lab.dijkstra(
    p_graph_id BIGINT,
    p_source_vertex BIGINT,
    p_destination_vertex BIGINT DEFAULT NULL
)
RETURNS TABLE (
    vertex_id BIGINT,
    shortest_distance NUMERIC,
    predecessor_vertex_id BIGINT,
    is_settled BOOLEAN
)
LANGUAGE plpgsql
SET search_path = graph_lab, pg_temp
AS $$
DECLARE
    current_vertex BIGINT;
    current_distance NUMERIC;
    candidate_distance NUMERIC;

    current_graph_version BIGINT;
    source_exists BOOLEAN;
    destination_exists BOOLEAN;

    examined_count INTEGER := 0;
    relaxation_count INTEGER := 0;
    settled_count INTEGER := 0;
BEGIN
    -- Validate graph and capture its current version.
    SELECT g.version
    INTO current_graph_version
    FROM graph_lab.graphs g
    WHERE g.graph_id = p_graph_id
      AND g.state = 'ACTIVE'
    FOR SHARE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Graph % is missing or inactive', p_graph_id;
    END IF;

    SELECT EXISTS (
        SELECT 1
        FROM graph_lab.vertices v
        WHERE v.graph_id = p_graph_id
          AND v.vertex_id = p_source_vertex
          AND v.active
    )
    INTO source_exists;

    IF NOT source_exists THEN
        RAISE EXCEPTION 'Source vertex is missing or inactive';
    END IF;

    IF p_destination_vertex IS NOT NULL THEN
        SELECT EXISTS (
            SELECT 1
            FROM graph_lab.vertices v
            WHERE v.graph_id = p_graph_id
              AND v.vertex_id = p_destination_vertex
              AND v.active
        )
        INTO destination_exists;

        IF NOT destination_exists THEN
            RAISE EXCEPTION 'Destination vertex is missing or inactive';
        END IF;
    END IF;

    /*
     * Temporary tables isolate algorithm state from persistent
     * graph data. They are scoped to the current database session.
     */

    CREATE TEMP TABLE IF NOT EXISTS dijkstra_state (
        node_id BIGINT PRIMARY KEY,
        distance NUMERIC,
        predecessor BIGINT,
        settled BOOLEAN NOT NULL DEFAULT FALSE
    ) ON COMMIT DROP;

    TRUNCATE pg_temp.dijkstra_state;

    INSERT INTO pg_temp.dijkstra_state (
        node_id,
        distance,
        predecessor,
        settled
    )
    SELECT
        v.vertex_id,
        NULL,
        NULL,
        FALSE
    FROM graph_lab.vertices v
    WHERE v.graph_id = p_graph_id
      AND v.active;

    UPDATE pg_temp.dijkstra_state
    SET distance = 0
    WHERE node_id = p_source_vertex;

    LOOP
        /*
         * Select the unsettled vertex having the minimum
         * tentative distance.
         *
         * A NULL distance represents infinity.
         */
        SELECT
            s.node_id,
            s.distance
        INTO
            current_vertex,
            current_distance
        FROM pg_temp.dijkstra_state s
        WHERE s.settled = FALSE
          AND s.distance IS NOT NULL
        ORDER BY s.distance, s.node_id
        LIMIT 1;

        EXIT WHEN NOT FOUND;

        UPDATE pg_temp.dijkstra_state
        SET settled = TRUE
        WHERE node_id = current_vertex;

        settled_count := settled_count + 1;

        IF current_vertex = p_destination_vertex THEN
            EXIT;
        END IF;

        /*
         * Relax all outgoing active edges.
         * PostgreSQL updates the neighbor state in one set-based
         * operation rather than issuing one update per edge.
         */
        UPDATE pg_temp.dijkstra_state AS state
        SET
            distance = current_distance + edge.weight,
            predecessor = current_vertex
        FROM graph_lab.edges edge
        JOIN graph_lab.vertices destination
            ON destination.vertex_id = edge.destination_vertex_id
           AND destination.graph_id = edge.graph_id
           AND destination.active = TRUE
        WHERE edge.graph_id = p_graph_id
          AND edge.source_vertex_id = current_vertex
          AND edge.active = TRUE
          AND state.node_id = edge.destination_vertex_id
          AND state.settled = FALSE
          AND (
              state.distance IS NULL
              OR current_distance + edge.weight < state.distance
          );

        GET DIAGNOSTICS relaxation_count =
            relaxation_count + ROW_COUNT;

        SELECT COUNT(*)::INTEGER
        INTO examined_count
        FROM graph_lab.edges e
        WHERE e.graph_id = p_graph_id
          AND e.source_vertex_id = current_vertex
          AND e.active = TRUE;

        -- examined_count is diagnostic only for the latest expansion.
    END LOOP;

    -- Return the final distances and predecessor relationships.
    RETURN QUERY
    SELECT
        s.node_id,
        s.distance,
        s.predecessor,
        s.settled
    FROM pg_temp.dijkstra_state s
    ORDER BY s.node_id;
END;
$$;

-- ============================================================================
-- 9. MULTI-SOURCE DIJKSTRA
-- ============================================================================

CREATE OR REPLACE FUNCTION graph_lab.multi_source_dijkstra(
    p_graph_id BIGINT,
    p_source_vertices BIGINT[]
)
RETURNS TABLE (
    vertex_id BIGINT,
    shortest_distance NUMERIC,
    predecessor_vertex_id BIGINT,
    is_settled BOOLEAN
)
LANGUAGE plpgsql
SET search_path = graph_lab, pg_temp
AS $$
DECLARE
    source_id BIGINT;
    current_vertex BIGINT;
    current_distance NUMERIC;
BEGIN
    IF p_source_vertices IS NULL
       OR cardinality(p_source_vertices) = 0 THEN
        RAISE EXCEPTION 'At least one source is required';
    END IF;

    IF (
        SELECT COUNT(*) <> COUNT(DISTINCT value)
        FROM unnest(p_source_vertices) AS sources(value)
    ) THEN
        RAISE EXCEPTION 'Duplicate sources are not allowed';
    END IF;

    PERFORM 1
    FROM graph_lab.graphs g
    WHERE g.graph_id = p_graph_id
      AND g.state = 'ACTIVE'
    FOR SHARE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Graph is missing or inactive';
    END IF;

    CREATE TEMP TABLE IF NOT EXISTS multi_source_state (
        node_id BIGINT PRIMARY KEY,
        distance NUMERIC,
        predecessor BIGINT,
        settled BOOLEAN NOT NULL DEFAULT FALSE
    ) ON COMMIT DROP;

    TRUNCATE pg_temp.multi_source_state;

    INSERT INTO pg_temp.multi_source_state (
        node_id,
        distance,
        predecessor
    )
    SELECT
        v.vertex_id,
        NULL,
        NULL
    FROM graph_lab.vertices v
    WHERE v.graph_id = p_graph_id
      AND v.active;

    FOREACH source_id IN ARRAY p_source_vertices LOOP
        IF NOT EXISTS (
            SELECT 1
            FROM graph_lab.vertices v
            WHERE v.graph_id = p_graph_id
              AND v.vertex_id = source_id
              AND v.active
        ) THEN
            RAISE EXCEPTION 'Invalid source vertex: %', source_id;
        END IF;

        UPDATE pg_temp.multi_source_state
        SET distance = 0
        WHERE node_id = source_id;
    END LOOP;

    LOOP
        SELECT s.node_id, s.distance
        INTO current_vertex, current_distance
        FROM pg_temp.multi_source_state s
        WHERE NOT s.settled
          AND s.distance IS NOT NULL
        ORDER BY s.distance, s.node_id
        LIMIT 1;

        EXIT WHEN NOT FOUND;

        UPDATE pg_temp.multi_source_state
        SET settled = TRUE
        WHERE node_id = current_vertex;

        UPDATE pg_temp.multi_source_state AS state
        SET
            distance = current_distance + edge.weight,
            predecessor = current_vertex
        FROM graph_lab.edges edge
        WHERE edge.graph_id = p_graph_id
          AND edge.source_vertex_id = current_vertex
          AND edge.active
          AND state.node_id = edge.destination_vertex_id
          AND NOT state.settled
          AND (
              state.distance IS NULL
              OR current_distance + edge.weight < state.distance
          );
    END LOOP;

    RETURN QUERY
    SELECT
        s.node_id,
        s.distance,
        s.predecessor,
        s.settled
    FROM pg_temp.multi_source_state s
    ORDER BY s.node_id;
END;
$$;

-- ============================================================================
-- 10. PATH RECONSTRUCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION graph_lab.reconstruct_path(
    p_route_run_id BIGINT,
    p_destination_vertex BIGINT
)
RETURNS TABLE (
    sequence_number INTEGER,
    vertex_id BIGINT,
    vertex_name VARCHAR,
    cumulative_distance NUMERIC
)
LANGUAGE plpgsql
SET search_path = graph_lab, pg_temp
AS $$
DECLARE
    source_id BIGINT;
    current_id BIGINT;
    current_distance NUMERIC;
    previous_id BIGINT;
    step_number INTEGER := 0;
    maximum_steps INTEGER;
BEGIN
    SELECT rr.source_vertex_id
    INTO source_id
    FROM graph_lab.route_runs rr
    WHERE rr.route_run_id = p_route_run_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Route execution does not exist';
    END IF;

    SELECT count(*)::INTEGER
    INTO maximum_steps
    FROM graph_lab.route_results
    WHERE route_run_id = p_route_run_id;

    SELECT
        r.vertex_id,
        r.distance
    INTO
        current_id,
        current_distance
    FROM graph_lab.route_results r
    WHERE r.route_run_id = p_route_run_id
      AND r.vertex_id = p_destination_vertex;

    IF NOT FOUND OR current_distance IS NULL THEN
        RAISE EXCEPTION 'Destination is unreachable';
    END IF;

    CREATE TEMP TABLE IF NOT EXISTS reconstructed_path (
        sequence_number INTEGER,
        vertex_id BIGINT,
        cumulative_distance NUMERIC
    ) ON COMMIT DROP;

    TRUNCATE pg_temp.reconstructed_path;

    LOOP
        step_number := step_number + 1;

        IF step_number > maximum_steps THEN
            RAISE EXCEPTION 'Invalid predecessor chain';
        END IF;

        INSERT INTO pg_temp.reconstructed_path
        VALUES (
            step_number,
            current_id,
            current_distance
        );

        EXIT WHEN current_id = source_id;

        SELECT
            r.predecessor_vertex_id,
            previous.distance
        INTO
            previous_id,
            current_distance
        FROM graph_lab.route_results r
        JOIN graph_lab.route_results previous
            ON previous.route_run_id = r.route_run_id
           AND previous.vertex_id = r.predecessor_vertex_id
        WHERE r.route_run_id = p_route_run_id
          AND r.vertex_id = current_id;

        IF NOT FOUND OR previous_id IS NULL THEN
            RAISE EXCEPTION 'Broken predecessor chain';
        END IF;

        current_id := previous_id;
    END LOOP;

    RETURN QUERY
    SELECT
        (maximum_steps - p.sequence_number + 1)::INTEGER,
        p.vertex_id,
        v.vertex_name,
        p.cumulative_distance
    FROM pg_temp.reconstructed_path p
    JOIN graph_lab.vertices v
        ON v.vertex_id = p.vertex_id
    ORDER BY p.sequence_number DESC;
END;
$$;

-- ============================================================================
-- 11. SAMPLE GRAPH
-- ============================================================================

INSERT INTO graph_lab.graphs (
    graph_name,
    graph_type
)
VALUES (
    'Uttar Pradesh Transport Network',
    'DIRECTED'
);

INSERT INTO graph_lab.vertices (
    graph_id,
    vertex_code,
    vertex_name
)
VALUES
    (1, 'LKO', 'Lucknow'),
    (1, 'KNP', 'Kanpur'),
    (1, 'AYD', 'Ayodhya'),
    (1, 'AGR', 'Agra'),
    (1, 'PRY', 'Prayagraj'),
    (1, 'VNS', 'Varanasi'),
    (1, 'GKP', 'Gorakhpur'),
    (1, 'PAT', 'Patna'),
    (1, 'DEL', 'Delhi'),
    (1, 'MUM', 'Mumbai'),
    (1, 'EXP', 'Lucknow Express');

INSERT INTO graph_lab.edges (
    graph_id,
    source_vertex_id,
    destination_vertex_id,
    weight
)
VALUES
    (1, 1, 2, 90),
    (1, 1, 3, 135),
    (1, 1, 6, 300),
    (1, 2, 4, 210),
    (1, 2, 5, 180),
    (1, 3, 7, 150),
    (1, 3, 6, 190),
    (1, 7, 8, 240),
    (1, 6, 8, 200),
    (1, 6, 5, 130),
    (1, 5, 9, 500),
    (1, 4, 9, 150),
    (1, 1, 11, 0),
    (1, 11, 2, 70);

-- ============================================================================
-- 12. BASIC GRAPH RETRIEVAL
-- ============================================================================

SELECT *
FROM graph_lab.graph_edge_details
WHERE graph_id = 1
ORDER BY source_code, destination_code;

SELECT
    g.graph_name,
    g.graph_type,
    count(DISTINCT v.vertex_id) AS vertex_count,
    count(DISTINCT e.edge_id) AS edge_count
FROM graph_lab.graphs g
LEFT JOIN graph_lab.vertices v
    ON v.graph_id = g.graph_id
LEFT JOIN graph_lab.edges e
    ON e.graph_id = g.graph_id
GROUP BY
    g.graph_id,
    g.graph_name,
    g.graph_type;

-- ============================================================================
-- 13. EXECUTE SINGLE-SOURCE DIJKSTRA
-- ============================================================================

CREATE TEMP TABLE computed_routes
ON COMMIT DROP
AS
SELECT *
FROM graph_lab.dijkstra(
    1,
    1,
    NULL
);

SELECT
    v.vertex_name,
    r.shortest_distance,
    predecessor.vertex_name AS predecessor,
    r.is_settled,
    CASE
        WHEN r.shortest_distance IS NULL THEN 'UNREACHABLE'
        ELSE 'REACHABLE'
    END AS reachability
FROM computed_routes r
JOIN graph_lab.vertices v
    ON v.vertex_id = r.vertex_id
LEFT JOIN graph_lab.vertices predecessor
    ON predecessor.vertex_id = r.predecessor_vertex_id
ORDER BY
    r.shortest_distance NULLS LAST,
    v.vertex_name;

-- ============================================================================
-- 14. STORE A ROUTE EXECUTION
-- ============================================================================

WITH inserted_run AS (
    INSERT INTO graph_lab.route_runs (
        graph_id,
        source_vertex_id,
        destination_vertex_id,
        graph_version,
        status
    )
    SELECT
        1,
        1,
        9,
        g.version,
        CASE
            WHEN r.shortest_distance IS NULL
                THEN 'UNREACHABLE'::graph_lab.route_status
            ELSE 'REACHABLE'::graph_lab.route_status
        END
    FROM graph_lab.graphs g
    CROSS JOIN computed_routes r
    WHERE g.graph_id = 1
      AND r.vertex_id = 9
    RETURNING route_run_id
)
INSERT INTO graph_lab.route_results (
    route_run_id,
    vertex_id,
    distance,
    predecessor_vertex_id,
    settled
)
SELECT
    ir.route_run_id,
    cr.vertex_id,
    cr.shortest_distance,
    cr.predecessor_vertex_id,
    cr.is_settled
FROM inserted_run ir
CROSS JOIN computed_routes cr;

-- ============================================================================
-- 15. PATH RECONSTRUCTION QUERY
-- ============================================================================

SELECT
    sequence_number,
    vertex_name,
    cumulative_distance
FROM graph_lab.reconstruct_path(
    (SELECT max(route_run_id) FROM graph_lab.route_runs),
    9
);

-- ============================================================================
-- 16. MULTI-SOURCE ROUTING
-- ============================================================================

SELECT
    v.vertex_name,
    result.shortest_distance,
    predecessor.vertex_name AS predecessor
FROM graph_lab.multi_source_dijkstra(
    1,
    ARRAY[1, 9]::BIGINT[]
) result
JOIN graph_lab.vertices v
    ON v.vertex_id = result.vertex_id
LEFT JOIN graph_lab.vertices predecessor
    ON predecessor.vertex_id = result.predecessor_vertex_id
ORDER BY result.shortest_distance NULLS LAST;

-- ============================================================================
-- 17. EARLY TERMINATION QUERY
-- ============================================================================

SELECT
    v.vertex_name,
    result.shortest_distance,
    result.is_settled
FROM graph_lab.dijkstra(
    1,
    1,
    9
) result
JOIN graph_lab.vertices v
    ON v.vertex_id = result.vertex_id
ORDER BY result.shortest_distance NULLS LAST;

-- ============================================================================
-- 18. VALIDATION QUERIES
-- ============================================================================

-- Negative weights are prohibited by the table constraint.
SELECT
    conname,
    pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'graph_lab.edges'::regclass
ORDER BY conname;

-- Identify vertices having no outgoing active edges.
SELECT
    v.vertex_name
FROM graph_lab.vertices v
WHERE v.graph_id = 1
  AND v.active
  AND NOT EXISTS (
      SELECT 1
      FROM graph_lab.edges e
      WHERE e.graph_id = v.graph_id
        AND e.source_vertex_id = v.vertex_id
        AND e.active
  );

-- Detect inactive or isolated vertices.
SELECT
    v.vertex_name,
    v.active,
    NOT EXISTS (
        SELECT 1
        FROM graph_lab.edges e
        WHERE e.graph_id = v.graph_id
          AND e.active
          AND (
              e.source_vertex_id = v.vertex_id
              OR e.destination_vertex_id = v.vertex_id
          )
    ) AS isolated
FROM graph_lab.vertices v
WHERE v.graph_id = 1;

-- ============================================================================
-- 19. AGGREGATION AND REPORTING
-- ============================================================================

SELECT
    g.graph_name,
    count(DISTINCT v.vertex_id) AS vertices,
    count(DISTINCT e.edge_id) AS edges,
    round(avg(e.weight), 2) AS average_edge_weight,
    min(e.weight) AS minimum_edge_weight,
    max(e.weight) AS maximum_edge_weight
FROM graph_lab.graphs g
LEFT JOIN graph_lab.vertices v
    ON v.graph_id = g.graph_id
LEFT JOIN graph_lab.edges e
    ON e.graph_id = g.graph_id
   AND e.active
WHERE g.graph_id = 1
GROUP BY g.graph_id, g.graph_name;

SELECT
    rr.route_run_id,
    g.graph_name,
    source.vertex_name AS source,
    destination.vertex_name AS destination,
    rr.status,
    rr.total_distance,
    rr.execution_started_at
FROM graph_lab.route_runs rr
JOIN graph_lab.graphs g
    ON g.graph_id = rr.graph_id
JOIN graph_lab.vertices source
    ON source.vertex_id = rr.source_vertex_id
LEFT JOIN graph_lab.vertices destination
    ON destination.vertex_id = rr.destination_vertex_id
ORDER BY rr.execution_started_at DESC;

-- ============================================================================
-- 20. EDGE CASE DEMONSTRATIONS
-- ============================================================================

-- A zero-weight edge is valid.
INSERT INTO graph_lab.edges (
    graph_id,
    source_vertex_id,
    destination_vertex_id,
    weight
)
VALUES (1, 1, 2, 0);

-- A disconnected vertex is represented with NULL distance.
SELECT
    v.vertex_name,
    result.shortest_distance
FROM graph_lab.dijkstra(1, 1) result
JOIN graph_lab.vertices v
    ON v.vertex_id = result.vertex_id
WHERE result.shortest_distance IS NULL;

-- ============================================================================
-- 21. TRANSACTIONAL GRAPH MODIFICATION
-- ============================================================================

SAVEPOINT graph_update;

INSERT INTO graph_lab.vertices (
    graph_id,
    vertex_code,
    vertex_name
)
VALUES (
    1,
    'TEST',
    'Test Junction'
);

ROLLBACK TO SAVEPOINT graph_update;

-- The test vertex does not persist.
SELECT *
FROM graph_lab.vertices
WHERE graph_id = 1
  AND vertex_code = 'TEST';

RELEASE SAVEPOINT graph_update;

-- ============================================================================
-- 22. OPERATIONAL DESIGN NOTES
-- ============================================================================

COMMENT ON TABLE graph_lab.graphs IS
'Stores graph definitions and graph versions.';

COMMENT ON TABLE graph_lab.vertices IS
'Stores graph vertices and their active states.';

COMMENT ON TABLE graph_lab.edges IS
'Stores weighted directed edges. Weights must be nonnegative.';

COMMENT ON FUNCTION graph_lab.dijkstra(BIGINT, BIGINT, BIGINT) IS
'Computes single-source shortest paths using a PL/pgSQL Dijkstra implementation.';

COMMENT ON FUNCTION graph_lab.multi_source_dijkstra(BIGINT, BIGINT[]) IS
'Computes shortest distances from the nearest supplied source.';

COMMENT ON TABLE graph_lab.route_results IS
'Stores distance and predecessor data for a completed route calculation.';

-- ============================================================================
-- 23. FINAL EXECUTION SUMMARY
-- ============================================================================

SELECT
    'Dijkstra implementation initialized' AS execution_status,
    current_database() AS database_name,
    current_schema() AS active_schema,
    CURRENT_TIMESTAMP AS execution_time;

COMMIT;
