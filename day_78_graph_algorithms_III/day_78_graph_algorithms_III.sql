/*
 * GRAPH ALGORITHMS III
 *
 * PostgreSQL implementation of:
 * - Directed weighted graphs.
 * - Bellman-Ford shortest paths.
 * - Floyd-Warshall all-pairs shortest paths.
 * - Negative-cycle detection.
 * - Negative-infinity propagation.
 * - Shortest-path reporting.
 *
 * Requires PostgreSQL 15+.
 *
 * The implementation uses NUMERIC weights to avoid the rounding
 * problems associated with binary floating-point arithmetic.
 */

BEGIN;

DROP SCHEMA IF EXISTS graph_algorithms CASCADE;

CREATE SCHEMA graph_algorithms;

SET search_path TO graph_algorithms, public;

-- ============================================================
-- 1. DOMAIN TABLES
-- ============================================================

CREATE TABLE graph (
    graph_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    graph_name VARCHAR(150) NOT NULL UNIQUE,
    vertex_count INTEGER NOT NULL CHECK (vertex_count > 0),
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE graph_vertex (
    graph_id BIGINT NOT NULL REFERENCES graph(graph_id)
        ON DELETE CASCADE,
    vertex_id INTEGER NOT NULL CHECK (vertex_id >= 0),
    vertex_name VARCHAR(120) NOT NULL,
    PRIMARY KEY (graph_id, vertex_id),
    UNIQUE (graph_id, vertex_name)
);

CREATE TABLE graph_edge (
    edge_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    graph_id BIGINT NOT NULL,
    source_vertex INTEGER NOT NULL,
    destination_vertex INTEGER NOT NULL,
    weight NUMERIC(20, 6) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (graph_id, source_vertex)
        REFERENCES graph_vertex(graph_id, vertex_id)
        ON DELETE CASCADE,

    FOREIGN KEY (graph_id, destination_vertex)
        REFERENCES graph_vertex(graph_id, vertex_id)
        ON DELETE CASCADE
);

CREATE INDEX idx_graph_edge_source
    ON graph_edge(graph_id, source_vertex);

CREATE INDEX idx_graph_edge_destination
    ON graph_edge(graph_id, destination_vertex);

CREATE INDEX idx_graph_edge_weight
    ON graph_edge(graph_id, weight);

-- ============================================================
-- 2. ANALYSIS CONFIGURATION AND RESULTS
-- ============================================================

CREATE TABLE analysis_run (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    graph_id BIGINT NOT NULL REFERENCES graph(graph_id)
        ON DELETE CASCADE,

    algorithm VARCHAR(30) NOT NULL CHECK (
        algorithm IN ('BELLMAN_FORD', 'FLOYD_WARSHALL')
    ),

    source_vertex INTEGER,
    status VARCHAR(30) NOT NULL DEFAULT 'PENDING' CHECK (
        status IN ('PENDING', 'COMPLETED', 'FAILED')
    ),

    graph_version BIGINT NOT NULL DEFAULT 0,
    negative_cycle_detected BOOLEAN NOT NULL DEFAULT FALSE,
    execution_message TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,

    FOREIGN KEY (graph_id, source_vertex)
        REFERENCES graph_vertex(graph_id, vertex_id),

    CHECK (
        (algorithm = 'BELLMAN_FORD' AND source_vertex IS NOT NULL)
        OR
        (algorithm = 'FLOYD_WARSHALL' AND source_vertex IS NULL)
    )
);

CREATE TABLE shortest_path_result (
    run_id BIGINT NOT NULL REFERENCES analysis_run(run_id)
        ON DELETE CASCADE,

    source_vertex INTEGER NOT NULL,
    destination_vertex INTEGER NOT NULL,

    distance NUMERIC(30, 6),
    path_status VARCHAR(30) NOT NULL CHECK (
        path_status IN (
            'FINITE',
            'UNREACHABLE',
            'NEGATIVE_INFINITY'
        )
    ),

    predecessor_vertex INTEGER,
    path_vertices INTEGER[] NOT NULL DEFAULT '{}',

    PRIMARY KEY (
        run_id,
        source_vertex,
        destination_vertex
    ),

    CHECK (
        (path_status = 'FINITE' AND distance IS NOT NULL)
        OR
        (
            path_status = 'UNREACHABLE'
            AND distance IS NULL
        )
        OR
        (
            path_status = 'NEGATIVE_INFINITY'
            AND distance IS NULL
        )
    )
);

CREATE INDEX idx_path_result_status
    ON shortest_path_result(run_id, path_status);

CREATE TABLE negative_cycle (
    cycle_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES analysis_run(run_id)
        ON DELETE CASCADE,
    representative_vertex INTEGER NOT NULL,
    cycle_vertices INTEGER[] NOT NULL,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 3. GRAPH VALIDATION
-- ============================================================

CREATE OR REPLACE FUNCTION validate_graph_vertex_count()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.vertex_count <= 0 THEN
        RAISE EXCEPTION 'Graph must contain at least one vertex.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_graph
BEFORE INSERT OR UPDATE OF vertex_count
ON graph
FOR EACH ROW
EXECUTE FUNCTION validate_graph_vertex_count();

CREATE OR REPLACE FUNCTION validate_graph_vertex_id()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    expected_count INTEGER;
BEGIN
    SELECT vertex_count
    INTO expected_count
    FROM graph
    WHERE graph_id = NEW.graph_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Graph does not exist.';
    END IF;

    IF NEW.vertex_id >= expected_count THEN
        RAISE EXCEPTION
            'Vertex % exceeds graph vertex count %.',
            NEW.vertex_id,
            expected_count;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_vertex
BEFORE INSERT OR UPDATE OF graph_id, vertex_id
ON graph_vertex
FOR EACH ROW
EXECUTE FUNCTION validate_graph_vertex_id();

CREATE OR REPLACE FUNCTION validate_graph_edge()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    expected_count INTEGER;
BEGIN
    SELECT vertex_count
    INTO expected_count
    FROM graph
    WHERE graph_id = NEW.graph_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Graph does not exist.';
    END IF;

    IF NEW.source_vertex >= expected_count
       OR NEW.destination_vertex >= expected_count THEN
        RAISE EXCEPTION 'Edge references an invalid vertex.';
    END IF;

    IF NEW.weight IS NULL THEN
        RAISE EXCEPTION 'Edge weight cannot be NULL.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_edge
BEFORE INSERT OR UPDATE
ON graph_edge
FOR EACH ROW
EXECUTE FUNCTION validate_graph_edge();

-- ============================================================
-- 4. GRAPH CREATION PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE create_graph(
    p_graph_name VARCHAR,
    p_vertex_count INTEGER,
    p_description TEXT DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    new_graph_id BIGINT;
    i INTEGER;
BEGIN
    IF p_graph_name IS NULL OR BTRIM(p_graph_name) = '' THEN
        RAISE EXCEPTION 'Graph name cannot be empty.';
    END IF;

    IF p_vertex_count <= 0 OR p_vertex_count > 500 THEN
        RAISE EXCEPTION
            'Vertex count must be between 1 and 500.';
    END IF;

    INSERT INTO graph(
        graph_name,
        vertex_count,
        description
    )
    VALUES (
        p_graph_name,
        p_vertex_count,
        p_description
    )
    RETURNING graph_id INTO new_graph_id;

    FOR i IN 0..p_vertex_count - 1 LOOP
        INSERT INTO graph_vertex(
            graph_id,
            vertex_id,
            vertex_name
        )
        VALUES (
            new_graph_id,
            i,
            'Vertex ' || i
        );
    END LOOP;
END;
$$;

-- ============================================================
-- 5. ANALYSIS INITIALIZATION
-- ============================================================

CREATE OR REPLACE FUNCTION start_analysis(
    p_graph_id BIGINT,
    p_algorithm VARCHAR,
    p_source INTEGER DEFAULT NULL
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_run_id BIGINT;
    v_count INTEGER;
    v_graph_version BIGINT;
BEGIN
    SELECT vertex_count
    INTO v_count
    FROM graph
    WHERE graph_id = p_graph_id
    FOR SHARE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Graph not found.';
    END IF;

    IF p_algorithm NOT IN (
        'BELLMAN_FORD',
        'FLOYD_WARSHALL'
    ) THEN
        RAISE EXCEPTION 'Unsupported algorithm.';
    END IF;

    IF p_algorithm = 'BELLMAN_FORD' THEN
        IF p_source IS NULL OR p_source < 0 OR p_source >= v_count THEN
            RAISE EXCEPTION 'Invalid Bellman-Ford source.';
        END IF;
    ELSE
        IF p_source IS NOT NULL THEN
            RAISE EXCEPTION
                'Floyd-Warshall does not require a source vertex.';
        END IF;
    END IF;

    SELECT COUNT(*)
    INTO v_graph_version
    FROM graph_edge
    WHERE graph_id = p_graph_id;

    INSERT INTO analysis_run(
        graph_id,
        algorithm,
        source_vertex,
        graph_version,
        status
    )
    VALUES (
        p_graph_id,
        p_algorithm,
        p_source,
        v_graph_version,
        'PENDING'
    )
    RETURNING run_id INTO v_run_id;

    RETURN v_run_id;
END;
$$;

-- ============================================================
-- 6. BELLMAN-FORD IMPLEMENTATION
-- ============================================================

CREATE OR REPLACE PROCEDURE execute_bellman_ford(
    p_run_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_graph_id BIGINT;
    v_source INTEGER;
    v_n INTEGER;
    v_dist NUMERIC(30, 6)[];
    v_pred INTEGER[];
    v_affected BOOLEAN[];
    v_queue INTEGER[];
    v_vertex INTEGER;
    v_edge RECORD;
    v_candidate NUMERIC(30, 6);
    v_changed BOOLEAN;
    v_iteration INTEGER;
    v_witness INTEGER;
    v_cycle INTEGER[];
    v_current INTEGER;
    v_cycle_start INTEGER;
    v_steps INTEGER;
    v_graph_version BIGINT;
BEGIN
    SELECT
        r.graph_id,
        r.source_vertex,
        g.vertex_count,
        r.graph_version
    INTO
        v_graph_id,
        v_source,
        v_n,
        v_graph_version
    FROM analysis_run r
    JOIN graph g ON g.graph_id = r.graph_id
    WHERE r.run_id = p_run_id
      AND r.algorithm = 'BELLMAN_FORD'
      AND r.status = 'PENDING'
    FOR UPDATE OF r;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Pending Bellman-Ford analysis not found.';
    END IF;

    IF (
        SELECT COUNT(*)
        FROM graph_edge
        WHERE graph_id = v_graph_id
    ) <> v_graph_version THEN
        RAISE EXCEPTION 'Graph changed after analysis initialization.';
    END IF;

    v_dist := array_fill(
        NULL::NUMERIC,
        ARRAY[v_n]
    );

    v_pred := array_fill(
        NULL::INTEGER,
        ARRAY[v_n]
    );

    v_affected := array_fill(
        FALSE,
        ARRAY[v_n]
    );

    v_dist[v_source + 1] := 0;

    FOR v_iteration IN 1..v_n - 1 LOOP
        v_changed := FALSE;

        FOR v_edge IN
            SELECT source_vertex, destination_vertex, weight
            FROM graph_edge
            WHERE graph_id = v_graph_id
            ORDER BY edge_id
        LOOP
            IF v_dist[v_edge.source_vertex + 1] IS NULL THEN
                CONTINUE;
            END IF;

            v_candidate :=
                v_dist[v_edge.source_vertex + 1] + v_edge.weight;

            IF v_dist[v_edge.destination_vertex + 1] IS NULL
               OR v_candidate <
                  v_dist[v_edge.destination_vertex + 1] THEN

                v_dist[v_edge.destination_vertex + 1] := v_candidate;

                v_pred[v_edge.destination_vertex + 1] :=
                    v_edge.source_vertex;

                v_changed := TRUE;
            END IF;
        END LOOP;

        EXIT WHEN NOT v_changed;
    END LOOP;

    -- Find vertices that remain relaxable.
    v_queue := ARRAY[]::INTEGER[];
    v_witness := NULL;

    FOR v_edge IN
        SELECT source_vertex, destination_vertex, weight
        FROM graph_edge
        WHERE graph_id = v_graph_id
        ORDER BY edge_id
    LOOP
        IF v_dist[v_edge.source_vertex + 1] IS NULL THEN
            CONTINUE;
        END IF;

        v_candidate :=
            v_dist[v_edge.source_vertex + 1] + v_edge.weight;

        IF v_dist[v_edge.destination_vertex + 1] IS NULL
           OR v_candidate <
              v_dist[v_edge.destination_vertex + 1] THEN

            v_dist[v_edge.destination_vertex + 1] := v_candidate;

            v_pred[v_edge.destination_vertex + 1] :=
                v_edge.source_vertex;

            IF NOT v_affected[v_edge.destination_vertex + 1] THEN
                v_affected[v_edge.destination_vertex + 1] := TRUE;

                v_queue := array_append(
                    v_queue,
                    v_edge.destination_vertex
                );
            END IF;

            v_witness := v_edge.destination_vertex;
        END IF;
    END LOOP;

    -- Breadth-first propagation from affected vertices.
    WHILE COALESCE(array_length(v_queue, 1), 0) > 0 LOOP
        v_vertex := v_queue[1];
        v_queue := v_queue[2:];

        FOR v_edge IN
            SELECT destination_vertex
            FROM graph_edge
            WHERE graph_id = v_graph_id
              AND source_vertex = v_vertex
        LOOP
            IF NOT v_affected[v_edge.destination_vertex + 1] THEN
                v_affected[v_edge.destination_vertex + 1] := TRUE;

                v_queue := array_append(
                    v_queue,
                    v_edge.destination_vertex
                );
            END IF;
        END LOOP;
    END LOOP;

    -- Attempt to reconstruct one negative cycle witness.
    v_cycle := ARRAY[]::INTEGER[];

    IF v_witness IS NOT NULL THEN
        v_current := v_witness;
        v_steps := 0;

        WHILE v_steps < v_n LOOP
            EXIT WHEN v_pred[v_current + 1] IS NULL;

            v_current := v_pred[v_current + 1];
            v_steps := v_steps + 1;
        END LOOP;

        IF v_steps = v_n THEN
            v_cycle_start := v_current;
            v_cycle := ARRAY[v_current];

            v_current := v_pred[v_current + 1];
            v_steps := 0;

            WHILE v_current IS NOT NULL
              AND v_current <> v_cycle_start
              AND v_steps < v_n LOOP

                v_cycle := array_append(v_cycle, v_current);
                v_current := v_pred[v_current + 1];
                v_steps := v_steps + 1;
            END LOOP;

            IF v_current = v_cycle_start THEN
                v_cycle := array_append(v_cycle, v_cycle_start);
                v_cycle := ARRAY(
                    SELECT x
                    FROM unnest(v_cycle) WITH ORDINALITY AS t(x, ord)
                    ORDER BY ord DESC
                );

                INSERT INTO negative_cycle(
                    run_id,
                    representative_vertex,
                    cycle_vertices
                )
                VALUES (
                    p_run_id,
                    v_cycle_start,
                    v_cycle
                );
            END IF;
        END IF;
    END IF;

    -- Store one result for every destination.
    FOR v_vertex IN 0..v_n - 1 LOOP
        IF v_affected[v_vertex + 1] THEN
            INSERT INTO shortest_path_result(
                run_id,
                source_vertex,
                destination_vertex,
                distance,
                path_status
            )
            VALUES (
                p_run_id,
                v_source,
                v_vertex,
                NULL,
                'NEGATIVE_INFINITY'
            );

        ELSIF v_dist[v_vertex + 1] IS NULL THEN
            INSERT INTO shortest_path_result(
                run_id,
                source_vertex,
                destination_vertex,
                distance,
                path_status
            )
            VALUES (
                p_run_id,
                v_source,
                v_vertex,
                NULL,
                'UNREACHABLE'
            );

        ELSE
            INSERT INTO shortest_path_result(
                run_id,
                source_vertex,
                destination_vertex,
                distance,
                path_status,
                predecessor_vertex
            )
            VALUES (
                p_run_id,
                v_source,
                v_vertex,
                v_dist[v_vertex + 1],
                'FINITE',
                v_pred[v_vertex + 1]
            );
        END IF;
    END LOOP;

    UPDATE analysis_run
    SET status = 'COMPLETED',
        negative_cycle_detected = (
            COALESCE(array_length(v_cycle, 1), 0) > 0
        ),
        completed_at = CURRENT_TIMESTAMP,
        execution_message = 'Bellman-Ford analysis completed.'
    WHERE run_id = p_run_id;
END;
$$;

-- ============================================================
-- 7. FLOYD-WARSHALL IMPLEMENTATION
-- ============================================================

CREATE OR REPLACE PROCEDURE execute_floyd_warshall(
    p_run_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_graph_id BIGINT;
    v_n INTEGER;
    v_k INTEGER;
    v_i INTEGER;
    v_j INTEGER;
    v_dist NUMERIC(30, 6)[][];
    v_next INTEGER[][];
    v_edge RECORD;
    v_candidate NUMERIC(30, 6);
    v_negative BOOLEAN := FALSE;
    v_graph_version BIGINT;
    v_affected BOOLEAN;
BEGIN
    SELECT
        r.graph_id,
        g.vertex_count,
        r.graph_version
    INTO
        v_graph_id,
        v_n,
        v_graph_version
    FROM analysis_run r
    JOIN graph g ON g.graph_id = r.graph_id
    WHERE r.run_id = p_run_id
      AND r.algorithm = 'FLOYD_WARSHALL'
      AND r.status = 'PENDING'
    FOR UPDATE OF r;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Pending Floyd-Warshall analysis not found.';
    END IF;

    IF (
        SELECT COUNT(*)
        FROM graph_edge
        WHERE graph_id = v_graph_id
    ) <> v_graph_version THEN
        RAISE EXCEPTION 'Graph changed after analysis initialization.';
    END IF;

    v_dist := array_fill(
        NULL::NUMERIC,
        ARRAY[v_n, v_n]
    );

    v_next := array_fill(
        NULL::INTEGER,
        ARRAY[v_n, v_n]
    );

    FOR v_i IN 0..v_n - 1 LOOP
        v_dist[v_i + 1][v_i + 1] := 0;
        v_next[v_i + 1][v_i + 1] := v_i;
    END LOOP;

    FOR v_edge IN
        SELECT source_vertex, destination_vertex, weight
        FROM graph_edge
        WHERE graph_id = v_graph_id
    LOOP
        IF v_dist[v_edge.source_vertex + 1]
                    [v_edge.destination_vertex + 1] IS NULL
           OR v_edge.weight <
              v_dist[v_edge.source_vertex + 1]
                  [v_edge.destination_vertex + 1] THEN

            v_dist[v_edge.source_vertex + 1]
                  [v_edge.destination_vertex + 1] := v_edge.weight;

            v_next[v_edge.source_vertex + 1]
                  [v_edge.destination_vertex + 1] :=
                v_edge.destination_vertex;
        END IF;
    END LOOP;

    FOR v_k IN 0..v_n - 1 LOOP
        FOR v_i IN 0..v_n - 1 LOOP
            IF v_dist[v_i + 1][v_k + 1] IS NULL THEN
                CONTINUE;
            END IF;

            FOR v_j IN 0..v_n - 1 LOOP
                IF v_dist[v_k + 1][v_j + 1] IS NULL THEN
                    CONTINUE;
                END IF;

                v_candidate :=
                    v_dist[v_i + 1][v_k + 1]
                    + v_dist[v_k + 1][v_j + 1];

                IF v_dist[v_i + 1][v_j + 1] IS NULL
                   OR v_candidate <
                      v_dist[v_i + 1][v_j + 1] THEN

                    v_dist[v_i + 1][v_j + 1] := v_candidate;

                    v_next[v_i + 1][v_j + 1] :=
                        v_next[v_i + 1][v_k + 1];
                END IF;
            END LOOP;
        END LOOP;
    END LOOP;

    FOR v_i IN 0..v_n - 1 LOOP
        IF v_dist[v_i + 1][v_i + 1] < 0 THEN
            v_negative := TRUE;

            INSERT INTO negative_cycle(
                run_id,
                representative_vertex,
                cycle_vertices
            )
            VALUES (
                p_run_id,
                v_i,
                ARRAY[v_i]
            );
        END IF;
    END LOOP;

    -- Each source-destination pair is classified independently.
    FOR v_i IN 0..v_n - 1 LOOP
        FOR v_j IN 0..v_n - 1 LOOP

            v_affected := FALSE;

            FOR v_k IN 0..v_n - 1 LOOP
                IF v_dist[v_k + 1][v_k + 1] < 0
                   AND v_dist[v_i + 1][v_k + 1] IS NOT NULL
                   AND v_dist[v_k + 1][v_j + 1] IS NOT NULL THEN

                    v_affected := TRUE;
                    EXIT;
                END IF;
            END LOOP;

            IF v_affected THEN
                INSERT INTO shortest_path_result(
                    run_id,
                    source_vertex,
                    destination_vertex,
                    distance,
                    path_status
                )
                VALUES (
                    p_run_id,
                    v_i,
                    v_j,
                    NULL,
                    'NEGATIVE_INFINITY'
                );

            ELSIF v_dist[v_i + 1][v_j + 1] IS NULL THEN
                INSERT INTO shortest_path_result(
                    run_id,
                    source_vertex,
                    destination_vertex,
                    distance,
                    path_status
                )
                VALUES (
                    p_run_id,
                    v_i,
                    v_j,
                    NULL,
                    'UNREACHABLE'
                );

            ELSE
                INSERT INTO shortest_path_result(
                    run_id,
                    source_vertex,
                    destination_vertex,
                    distance,
                    path_status
                )
                VALUES (
                    p_run_id,
                    v_i,
                    v_j,
                    v_dist[v_i + 1][v_j + 1],
                    'FINITE'
                );
            END IF;
        END LOOP;
    END LOOP;

    UPDATE analysis_run
    SET status = 'COMPLETED',
        negative_cycle_detected = v_negative,
        completed_at = CURRENT_TIMESTAMP,
        execution_message = 'Floyd-Warshall analysis completed.'
    WHERE run_id = p_run_id;
END;
$$;

-- ============================================================
-- 8. ANALYSIS REPORTING VIEWS
-- ============================================================

CREATE VIEW v_graph_inventory AS
SELECT
    g.graph_id,
    g.graph_name,
    g.vertex_count,
    COUNT(DISTINCT v.vertex_id) AS registered_vertices,
    COUNT(DISTINCT e.edge_id) AS edge_count,
    COUNT(DISTINCT e.edge_id)
        FILTER (WHERE e.weight < 0) AS negative_edge_count
FROM graph g
LEFT JOIN graph_vertex v
    ON v.graph_id = g.graph_id
LEFT JOIN graph_edge e
    ON e.graph_id = g.graph_id
GROUP BY
    g.graph_id,
    g.graph_name,
    g.vertex_count;

CREATE VIEW v_analysis_summary AS
SELECT
    r.run_id,
    g.graph_name,
    r.algorithm,
    r.source_vertex,
    r.status,
    r.negative_cycle_detected,
    COUNT(s.destination_vertex) AS analyzed_pairs,
    COUNT(*) FILTER (
        WHERE s.path_status = 'FINITE'
    ) AS finite_paths,
    COUNT(*) FILTER (
        WHERE s.path_status = 'UNREACHABLE'
    ) AS unreachable_paths,
    COUNT(*) FILTER (
        WHERE s.path_status = 'NEGATIVE_INFINITY'
    ) AS undefined_paths,
    r.started_at,
    r.completed_at
FROM analysis_run r
JOIN graph g
    ON g.graph_id = r.graph_id
LEFT JOIN shortest_path_result s
    ON s.run_id = r.run_id
GROUP BY
    r.run_id,
    g.graph_name,
    r.algorithm,
    r.source_vertex,
    r.status,
    r.negative_cycle_detected,
    r.started_at,
    r.completed_at;

CREATE VIEW v_negative_cycle_reports AS
SELECT
    nc.cycle_id,
    nc.run_id,
    g.graph_name,
    r.algorithm,
    nc.representative_vertex,
    nc.cycle_vertices,
    nc.detected_at
FROM negative_cycle nc
JOIN analysis_run r
    ON r.run_id = nc.run_id
JOIN graph g
    ON g.graph_id = r.graph_id;

-- ============================================================
-- 9. SAMPLE GRAPH DATA
-- ============================================================

CALL create_graph(
    'Bellman-Ford Sample',
    6,
    'Directed graph with negative edges but no negative cycles.'
);

CALL create_graph(
    'Negative Cycle Sample',
    6,
    'Directed graph containing a reachable negative cycle.'
);

CALL create_graph(
    'Floyd-Warshall Sample',
    5,
    'All-pairs shortest path demonstration.'
);

-- Bellman-Ford graph.
INSERT INTO graph_edge(
    graph_id,
    source_vertex,
    destination_vertex,
    weight
)
SELECT
    1,
    data.source_vertex,
    data.destination_vertex,
    data.weight
FROM (
    VALUES
        (0, 1, 4::NUMERIC),
        (0, 2, 5::NUMERIC),
        (1, 2, -2::NUMERIC),
        (1, 3, 6::NUMERIC),
        (2, 3, 3::NUMERIC),
        (3, 4, 2::NUMERIC),
        (4, 5, 1::NUMERIC)
) AS data(source_vertex, destination_vertex, weight);

-- Negative-cycle graph.
INSERT INTO graph_edge(
    graph_id,
    source_vertex,
    destination_vertex,
    weight
)
SELECT
    2,
    data.source_vertex,
    data.destination_vertex,
    data.weight
FROM (
    VALUES
        (0, 1, 2::NUMERIC),
        (1, 2, 2::NUMERIC),
        (2, 3, -5::NUMERIC),
        (3, 1, 1::NUMERIC),
        (3, 4, 4::NUMERIC),
        (0, 5, 10::NUMERIC)
) AS data(source_vertex, destination_vertex, weight);

-- Floyd-Warshall graph.
INSERT INTO graph_edge(
    graph_id,
    source_vertex,
    destination_vertex,
    weight
)
SELECT
    3,
    data.source_vertex,
    data.destination_vertex,
    data.weight
FROM (
    VALUES
        (0, 1, 3::NUMERIC),
        (0, 2, 10::NUMERIC),
        (1, 2, -2::NUMERIC),
        (1, 3, 7::NUMERIC),
        (2, 3, 2::NUMERIC),
        (3, 4, 1::NUMERIC),
        (4, 1, 8::NUMERIC)
) AS data(source_vertex, destination_vertex, weight);

-- ============================================================
-- 10. EXECUTION WORKFLOW
-- ============================================================

DO $$
DECLARE
    v_run BIGINT;
BEGIN
    -- Single-source shortest paths.
    v_run := start_analysis(1, 'BELLMAN_FORD', 0);
    CALL execute_bellman_ford(v_run);

    -- Reachable negative-cycle detection.
    v_run := start_analysis(2, 'BELLMAN_FORD', 0);
    CALL execute_bellman_ford(v_run);

    -- All-pairs shortest paths.
    v_run := start_analysis(3, 'FLOYD_WARSHALL', NULL);
    CALL execute_floyd_warshall(v_run);
END;
$$;

COMMIT;

-- ============================================================
-- 11. RETRIEVAL QUERIES
-- ============================================================

-- Graph inventory.
SELECT *
FROM v_graph_inventory
ORDER BY graph_id;

-- Analysis execution report.
SELECT *
FROM v_analysis_summary
ORDER BY run_id;

-- Bellman-Ford finite routes from source 0.
SELECT
    g.graph_name,
    s.source_vertex,
    s.destination_vertex,
    s.distance,
    s.path_status,
    s.predecessor_vertex
FROM shortest_path_result s
JOIN analysis_run r ON r.run_id = s.run_id
JOIN graph g ON g.graph_id = r.graph_id
WHERE r.algorithm = 'BELLMAN_FORD'
  AND r.source_vertex = 0
ORDER BY r.run_id, s.destination_vertex;

-- Negative-cycle reports.
SELECT *
FROM v_negative_cycle_reports
ORDER BY run_id, cycle_id;

-- ============================================================
-- 12. VALIDATION AND AGGREGATION
-- ============================================================

-- Count all path classifications.
SELECT
    r.run_id,
    r.algorithm,
    s.path_status,
    COUNT(*) AS path_count
FROM analysis_run r
JOIN shortest_path_result s
    ON s.run_id = r.run_id
GROUP BY
    r.run_id,
    r.algorithm,
    s.path_status
ORDER BY
    r.run_id,
    s.path_status;

-- Validate that completed analyses contain expected result counts.
SELECT
    r.run_id,
    r.algorithm,
    g.vertex_count,
    COUNT(s.destination_vertex) AS actual_results,
    CASE
        WHEN r.algorithm = 'BELLMAN_FORD'
             AND COUNT(s.destination_vertex) = g.vertex_count
            THEN 'VALID'
        WHEN r.algorithm = 'FLOYD_WARSHALL'
             AND COUNT(s.destination_vertex) =
                 g.vertex_count * g.vertex_count
            THEN 'VALID'
        ELSE 'INVALID'
    END AS validation_status
FROM analysis_run r
JOIN graph g ON g.graph_id = r.graph_id
LEFT JOIN shortest_path_result s
    ON s.run_id = r.run_id
GROUP BY
    r.run_id,
    r.algorithm,
    g.vertex_count;

-- Identify finite routes with negative total costs.
SELECT
    r.run_id,
    g.graph_name,
    s.source_vertex,
    s.destination_vertex,
    s.distance
FROM shortest_path_result s
JOIN analysis_run r ON r.run_id = s.run_id
JOIN graph g ON g.graph_id = r.graph_id
WHERE s.path_status = 'FINITE'
  AND s.distance < 0
ORDER BY r.run_id, s.distance;

-- ============================================================
-- 13. ELIGIBILITY DETERMINATION
-- ============================================================

CREATE OR REPLACE FUNCTION evaluate_route(
    p_run_id BIGINT,
    p_source INTEGER,
    p_destination INTEGER,
    p_reject_negative_infinity BOOLEAN DEFAULT TRUE
)
RETURNS TABLE (
    permitted BOOLEAN,
    route_status VARCHAR,
    route_distance NUMERIC,
    decision_reason TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_status VARCHAR;
    v_distance NUMERIC;
BEGIN
    SELECT
        s.path_status,
        s.distance
    INTO
        v_status,
        v_distance
    FROM shortest_path_result s
    WHERE s.run_id = p_run_id
      AND s.source_vertex = p_source
      AND s.destination_vertex = p_destination;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Requested source-destination result does not exist.';
    END IF;

    IF v_status = 'FINITE' THEN
        RETURN QUERY
        SELECT
            TRUE,
            v_status,
            v_distance,
            'A finite shortest path is available.'::TEXT;

    ELSIF v_status = 'UNREACHABLE' THEN
        RETURN QUERY
        SELECT
            FALSE,
            v_status,
            NULL::NUMERIC,
            'Destination is unreachable.'::TEXT;

    ELSE
        RETURN QUERY
        SELECT
            NOT p_reject_negative_infinity,
            v_status,
            NULL::NUMERIC,
            'A reachable negative cycle makes the shortest distance undefined.'::TEXT;
    END IF;
END;
$$;

-- Evaluate a finite route.
SELECT *
FROM evaluate_route(1, 0, 5);

-- Evaluate a route affected by a negative cycle.
SELECT *
FROM evaluate_route(2, 0, 4);

-- ============================================================
-- 14. TRANSACTION FAILURE DEMONSTRATION
-- ============================================================

-- This block deliberately tests validation and rolls back its
-- internal changes without damaging the committed sample data.

DO $$
BEGIN
    BEGIN
        INSERT INTO graph_edge(
            graph_id,
            source_vertex,
            destination_vertex,
            weight
        )
        VALUES (1, 0, 99, 5);

    EXCEPTION
        WHEN foreign_key_violation OR raise_exception THEN
            RAISE NOTICE
                'Invalid edge rejected by database integrity rules.';
    END;
END;
$$;

-- ============================================================
-- 15. CTE-BASED REPORTING
-- ============================================================

WITH run_statistics AS (
    SELECT
        run_id,
        COUNT(*) FILTER (
            WHERE path_status = 'FINITE'
        ) AS finite_count,
        COUNT(*) FILTER (
            WHERE path_status = 'UNREACHABLE'
        ) AS unreachable_count,
        COUNT(*) FILTER (
            WHERE path_status = 'NEGATIVE_INFINITY'
        ) AS negative_infinity_count
    FROM shortest_path_result
    GROUP BY run_id
),
ranked_runs AS (
    SELECT
        run_id,
        finite_count,
        unreachable_count,
        negative_infinity_count,
        DENSE_RANK() OVER (
            ORDER BY negative_infinity_count DESC
        ) AS risk_rank
    FROM run_statistics
)
SELECT
    r.run_id,
    r.algorithm,
    rr.finite_count,
    rr.unreachable_count,
    rr.negative_infinity_count,
    rr.risk_rank
FROM ranked_runs rr
JOIN analysis_run r
    ON r.run_id = rr.run_id
ORDER BY rr.risk_rank, r.run_id;

-- ============================================================
-- 16. COMPLETED ANALYSIS INTEGRITY
-- ============================================================

SELECT
    r.run_id,
    r.status,
    r.negative_cycle_detected,
    COUNT(nc.cycle_id) AS detected_cycle_records
FROM analysis_run r
LEFT JOIN negative_cycle nc
    ON nc.run_id = r.run_id
GROUP BY
    r.run_id,
    r.status,
    r.negative_cycle_detected
ORDER BY r.run_id;
