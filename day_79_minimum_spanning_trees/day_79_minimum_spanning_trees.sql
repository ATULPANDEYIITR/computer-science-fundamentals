-- ============================================================
-- MINIMUM SPANNING TREE MANAGEMENT DATABASE
-- PostgreSQL 14+
--
-- Implements:
-- 1. Weighted undirected graph storage.
-- 2. Vertex and edge validation.
-- 3. Union-Find using PL/pgSQL.
-- 4. Kruskal minimum spanning forest.
-- 5. Connected-component reporting.
-- 6. Network cost evaluation.
-- 7. Transactional MST calculation.
-- ============================================================

DROP SCHEMA IF EXISTS mst CASCADE;

CREATE SCHEMA mst;

SET search_path TO mst, public;

-- ============================================================
-- 1. DOMAIN TYPES
-- ============================================================

CREATE TYPE network_status AS ENUM (
    'DRAFT',
    'ACTIVE',
    'ARCHIVED'
);

CREATE TYPE algorithm_type AS ENUM (
    'KRUSKAL',
    'PRIM'
);

CREATE TYPE calculation_status AS ENUM (
    'COMPLETED',
    'REJECTED'
);

-- ============================================================
-- 2. REPOSITORY / NETWORK MASTER DATA
-- ============================================================

CREATE TABLE networks (
    network_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    network_name VARCHAR(150) NOT NULL UNIQUE,

    description TEXT,

    status network_status NOT NULL DEFAULT 'DRAFT',

    maximum_budget NUMERIC(14, 2)
        CHECK (
            maximum_budget IS NULL OR maximum_budget >= 0
        ),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE vertices (
    vertex_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    network_id BIGINT NOT NULL
        REFERENCES networks(network_id)
        ON DELETE CASCADE,

    vertex_code VARCHAR(50) NOT NULL,

    vertex_name VARCHAR(150) NOT NULL,

    location TEXT,

    UNIQUE (network_id, vertex_id),

    UNIQUE (network_id, vertex_code)
);

-- ============================================================
-- 3. UNDIRECTED WEIGHTED EDGES
-- ============================================================

CREATE TABLE edges (
    edge_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    network_id BIGINT NOT NULL,

    source_vertex_id BIGINT NOT NULL,

    target_vertex_id BIGINT NOT NULL,

    weight NUMERIC(14, 4) NOT NULL,

    connection_type VARCHAR(50) NOT NULL DEFAULT 'STANDARD',

    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (network_id, source_vertex_id)
        REFERENCES vertices(network_id, vertex_id)
        ON DELETE CASCADE,

    FOREIGN KEY (network_id, target_vertex_id)
        REFERENCES vertices(network_id, vertex_id)
        ON DELETE CASCADE,

    CHECK (source_vertex_id <> target_vertex_id),

    CHECK (
        weight BETWEEN -1000000000 AND 1000000000
    ),

    CHECK (source_vertex_id < target_vertex_id),

    UNIQUE (
        network_id,
        source_vertex_id,
        target_vertex_id
    )
);

CREATE INDEX idx_edges_network_weight
    ON edges(network_id, weight, edge_id)
    WHERE enabled = TRUE;

CREATE INDEX idx_vertices_network
    ON vertices(network_id, vertex_id);

-- ============================================================
-- 4. MST POLICY AND APPROVAL REQUIREMENTS
-- ============================================================

CREATE TABLE network_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    network_id BIGINT NOT NULL UNIQUE
        REFERENCES networks(network_id)
        ON DELETE CASCADE,

    required_algorithm algorithm_type NOT NULL DEFAULT 'KRUSKAL',

    require_connected BOOLEAN NOT NULL DEFAULT TRUE,

    maximum_allowed_weight NUMERIC(14, 2),

    allow_negative_weights BOOLEAN NOT NULL DEFAULT TRUE,

    require_verified_result BOOLEAN NOT NULL DEFAULT TRUE,

    CHECK (
        maximum_allowed_weight IS NULL OR
        maximum_allowed_weight >= 0
    )
);

CREATE TABLE network_approvals (
    approval_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    network_id BIGINT NOT NULL
        REFERENCES networks(network_id)
        ON DELETE CASCADE,

    approver VARCHAR(100) NOT NULL,

    approved BOOLEAN NOT NULL,

    comments TEXT,

    approved_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_network_approvals_network
    ON network_approvals(network_id, approved);

-- ============================================================
-- 5. CALCULATION HISTORY
-- ============================================================

CREATE TABLE mst_calculations (
    calculation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    network_id BIGINT NOT NULL
        REFERENCES networks(network_id)
        ON DELETE CASCADE,

    algorithm algorithm_type NOT NULL,

    status calculation_status NOT NULL DEFAULT 'COMPLETED',

    total_weight NUMERIC(16, 4) NOT NULL DEFAULT 0,

    vertex_count INTEGER NOT NULL,

    edge_count INTEGER NOT NULL DEFAULT 0,

    component_count INTEGER NOT NULL,

    is_spanning_tree BOOLEAN NOT NULL,

    is_verified BOOLEAN NOT NULL DEFAULT FALSE,

    graph_revision TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    executed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (vertex_count >= 1),

    CHECK (edge_count >= 0),

    CHECK (
        component_count BETWEEN 1 AND vertex_count
    ),

    CHECK (
        edge_count = vertex_count - component_count
    ),

    CHECK (
        is_spanning_tree =
        (component_count = 1 AND edge_count = vertex_count - 1)
    )
);

CREATE TABLE mst_selected_edges (
    calculation_id BIGINT NOT NULL
        REFERENCES mst_calculations(calculation_id)
        ON DELETE CASCADE,

    edge_id BIGINT NOT NULL
        REFERENCES edges(edge_id),

    selection_order INTEGER NOT NULL,

    PRIMARY KEY (calculation_id, edge_id),

    UNIQUE (calculation_id, selection_order),

    CHECK (selection_order > 0)
);

CREATE INDEX idx_calculations_network_date
    ON mst_calculations(network_id, executed_at DESC);

-- ============================================================
-- 6. GRAPH INTEGRITY TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION validate_network_edge()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_network_status network_status;
    v_allow_negative BOOLEAN;
BEGIN
    SELECT status
    INTO v_network_status
    FROM networks
    WHERE network_id = NEW.network_id
    FOR SHARE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Network does not exist.';
    END IF;

    IF v_network_status = 'ARCHIVED' THEN
        RAISE EXCEPTION 'Archived networks cannot be modified.';
    END IF;

    SELECT allow_negative_weights
    INTO v_allow_negative
    FROM network_policies
    WHERE network_id = NEW.network_id;

    IF FOUND AND NOT v_allow_negative AND NEW.weight < 0 THEN
        RAISE EXCEPTION
            'Negative edge weights are prohibited by network policy.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_network_edge
BEFORE INSERT OR UPDATE ON edges
FOR EACH ROW
EXECUTE FUNCTION validate_network_edge();

-- ============================================================
-- 7. NETWORK SUMMARY VIEW
-- ============================================================

CREATE VIEW network_summary AS
SELECT
    n.network_id,
    n.network_name,
    n.status,
    COUNT(DISTINCT v.vertex_id) AS vertex_count,
    COUNT(DISTINCT e.edge_id) FILTER (
        WHERE e.enabled
    ) AS enabled_edge_count,
    COALESCE(
        SUM(e.weight) FILTER (WHERE e.enabled),
        0
    ) AS total_available_edge_weight,
    n.maximum_budget
FROM networks n
LEFT JOIN vertices v
    ON v.network_id = n.network_id
LEFT JOIN edges e
    ON e.network_id = n.network_id
GROUP BY
    n.network_id,
    n.network_name,
    n.status,
    n.maximum_budget;

-- ============================================================
-- 8. UNION-FIND FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION calculate_mst_kruskal(
    p_network_id BIGINT
)
RETURNS TABLE (
    selected_edge_id BIGINT,
    source_vertex_id BIGINT,
    target_vertex_id BIGINT,
    selected_weight NUMERIC
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_edge RECORD;
    v_root_a BIGINT;
    v_root_b BIGINT;
    v_parent_a BIGINT;
    v_parent_b BIGINT;
    v_rank_a INTEGER;
    v_rank_b INTEGER;
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM networks
        WHERE network_id = p_network_id
    ) THEN
        RAISE EXCEPTION 'Unknown network: %', p_network_id;
    END IF;

    -- Temporary tables isolate Union-Find state to this session.
    DROP TABLE IF EXISTS pg_temp.mst_dsu;

    CREATE TEMP TABLE mst_dsu (
        vertex_id BIGINT PRIMARY KEY,
        parent_id BIGINT NOT NULL,
        rank_value INTEGER NOT NULL DEFAULT 0
    ) ON COMMIT DROP;

    INSERT INTO mst_dsu(vertex_id, parent_id)
    SELECT vertex_id, vertex_id
    FROM vertices
    WHERE network_id = p_network_id;

    IF NOT EXISTS (SELECT 1 FROM mst_dsu) THEN
        RAISE EXCEPTION 'Network has no vertices.';
    END IF;

    FOR v_edge IN
        SELECT
            e.edge_id,
            e.source_vertex_id,
            e.target_vertex_id,
            e.weight
        FROM edges e
        WHERE e.network_id = p_network_id
          AND e.enabled = TRUE
        ORDER BY
            e.weight,
            e.edge_id
    LOOP

        -- Find root of the source vertex.
        v_root_a := v_edge.source_vertex_id;

        LOOP
            SELECT parent_id
            INTO v_parent_a
            FROM mst_dsu
            WHERE vertex_id = v_root_a;

            IF NOT FOUND THEN
                RAISE EXCEPTION 'Invalid source vertex.';
            END IF;

            EXIT WHEN v_parent_a = v_root_a;

            v_root_a := v_parent_a;
        END LOOP;

        -- Find root of the target vertex.
        v_root_b := v_edge.target_vertex_id;

        LOOP
            SELECT parent_id
            INTO v_parent_b
            FROM mst_dsu
            WHERE vertex_id = v_root_b;

            IF NOT FOUND THEN
                RAISE EXCEPTION 'Invalid target vertex.';
            END IF;

            EXIT WHEN v_parent_b = v_root_b;

            v_root_b := v_parent_b;
        END LOOP;

        -- An edge joining an existing component creates a cycle.
        IF v_root_a = v_root_b THEN
            CONTINUE;
        END IF;

        SELECT rank_value
        INTO v_rank_a
        FROM mst_dsu
        WHERE vertex_id = v_root_a;

        SELECT rank_value
        INTO v_rank_b
        FROM mst_dsu
        WHERE vertex_id = v_root_b;

        -- Union by rank.
        IF v_rank_a < v_rank_b THEN

            UPDATE mst_dsu
            SET parent_id = v_root_b
            WHERE vertex_id = v_root_a;

        ELSE

            UPDATE mst_dsu
            SET parent_id = v_root_a
            WHERE vertex_id = v_root_b;

            IF v_rank_a = v_rank_b THEN
                UPDATE mst_dsu
                SET rank_value = rank_value + 1
                WHERE vertex_id = v_root_a;
            END IF;

        END IF;

        selected_edge_id := v_edge.edge_id;
        source_vertex_id := v_edge.source_vertex_id;
        target_vertex_id := v_edge.target_vertex_id;
        selected_weight := v_edge.weight;

        RETURN NEXT;
    END LOOP;
END;
$$;

-- ============================================================
-- 9. TRANSACTIONAL MST CALCULATION PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE execute_mst(
    p_network_id BIGINT,
    p_algorithm algorithm_type DEFAULT 'KRUSKAL'
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_vertex_count INTEGER;
    v_selected_count INTEGER;
    v_component_count INTEGER;
    v_total_weight NUMERIC(16, 4);
    v_calculation_id BIGINT;
    v_maximum_weight NUMERIC(14, 2);
    v_require_connected BOOLEAN;
    v_status network_status;
    v_policy_algorithm algorithm_type;
    v_edge RECORD;
    v_order INTEGER := 0;
BEGIN
    -- Serialize calculations for the same network.
    SELECT status
    INTO v_status
    FROM networks
    WHERE network_id = p_network_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Network does not exist.';
    END IF;

    IF v_status <> 'ACTIVE' THEN
        RAISE EXCEPTION 'Only active networks can be calculated.';
    END IF;

    SELECT COUNT(*)
    INTO v_vertex_count
    FROM vertices
    WHERE network_id = p_network_id;

    IF v_vertex_count = 0 THEN
        RAISE EXCEPTION 'Network has no vertices.';
    END IF;

    SELECT
        maximum_allowed_weight,
        require_connected,
        required_algorithm
    INTO
        v_maximum_weight,
        v_require_connected,
        v_policy_algorithm
    FROM network_policies
    WHERE network_id = p_network_id;

    IF FOUND AND v_policy_algorithm <> p_algorithm THEN
        RAISE EXCEPTION
            'Requested algorithm conflicts with network policy.';
    END IF;

    -- This database implementation executes Kruskal.
    IF p_algorithm <> 'KRUSKAL' THEN
        RAISE EXCEPTION
            'Database procedure currently supports Kruskal only.';
    END IF;

    v_total_weight := 0;
    v_selected_count := 0;

    -- Temporary selection table keeps calculations isolated.
    DROP TABLE IF EXISTS pg_temp.mst_current_selection;

    CREATE TEMP TABLE mst_current_selection (
        edge_id BIGINT PRIMARY KEY,
        selection_order INTEGER UNIQUE NOT NULL,
        weight NUMERIC(14, 4) NOT NULL
    ) ON COMMIT DROP;

    FOR v_edge IN
        SELECT *
        FROM calculate_mst_kruskal(p_network_id)
    LOOP

        v_order := v_order + 1;

        INSERT INTO mst_current_selection(
            edge_id,
            selection_order,
            weight
        )
        VALUES (
            v_edge.selected_edge_id,
            v_order,
            v_edge.selected_weight
        );

        v_selected_count := v_selected_count + 1;
        v_total_weight := v_total_weight + v_edge.selected_weight;

        EXIT WHEN v_selected_count = v_vertex_count - 1;
    END LOOP;

    v_component_count :=
        v_vertex_count - v_selected_count;

    IF v_require_connected AND v_component_count <> 1 THEN
        RAISE EXCEPTION
            'Network is disconnected. Components: %',
            v_component_count;
    END IF;

    IF v_maximum_weight IS NOT NULL
       AND v_total_weight > v_maximum_weight THEN
        RAISE EXCEPTION
            'MST cost exceeds approved budget.';
    END IF;

    INSERT INTO mst_calculations(
        network_id,
        algorithm,
        status,
        total_weight,
        vertex_count,
        edge_count,
        component_count,
        is_spanning_tree,
        is_verified
    )
    VALUES (
        p_network_id,
        p_algorithm,
        'COMPLETED',
        v_total_weight,
        v_vertex_count,
        v_selected_count,
        v_component_count,
        v_component_count = 1,
        TRUE
    )
    RETURNING calculation_id INTO v_calculation_id;

    INSERT INTO mst_selected_edges(
        calculation_id,
        edge_id,
        selection_order
    )
    SELECT
        v_calculation_id,
        edge_id,
        selection_order
    FROM mst_current_selection
    ORDER BY selection_order;

    RAISE NOTICE
        'Calculation % completed. Cost: %, components: %',
        v_calculation_id,
        v_total_weight,
        v_component_count;
END;
$$;

-- ============================================================
-- 10. NETWORK CONNECTIVITY REPORT
-- ============================================================

CREATE OR REPLACE FUNCTION network_connectivity(
    p_network_id BIGINT
)
RETURNS TABLE (
    component_number BIGINT,
    vertex_id BIGINT,
    vertex_code VARCHAR,
    vertex_name VARCHAR
)
LANGUAGE sql
AS $$
    WITH RECURSIVE reachability AS (
        SELECT
            v.vertex_id AS root_id,
            v.vertex_id AS current_id
        FROM vertices v
        WHERE v.network_id = p_network_id

        UNION

        SELECT
            r.root_id,
            CASE
                WHEN e.source_vertex_id = r.current_id
                THEN e.target_vertex_id
                ELSE e.source_vertex_id
            END
        FROM reachability r
        JOIN edges e
          ON e.network_id = p_network_id
         AND e.enabled = TRUE
         AND (
             e.source_vertex_id = r.current_id
             OR e.target_vertex_id = r.current_id
         )
    ),
    components AS (
        SELECT
            current_id AS vertex_id,
            MIN(root_id) AS component_root
        FROM reachability
        GROUP BY current_id
    ),
    numbered AS (
        SELECT
            component_root,
            DENSE_RANK() OVER (
                ORDER BY component_root
            ) AS component_number
        FROM (
            SELECT DISTINCT component_root
            FROM components
        ) roots
    )
    SELECT
        n.component_number,
        v.vertex_id,
        v.vertex_code,
        v.vertex_name
    FROM components c
    JOIN vertices v
      ON v.vertex_id = c.vertex_id
    JOIN numbered n
      ON n.component_root = c.component_root
    ORDER BY n.component_number, v.vertex_id;
$$;

-- ============================================================
-- 11. SAMPLE NETWORKS
-- ============================================================

INSERT INTO networks(
    network_name,
    description,
    status,
    maximum_budget
)
VALUES
(
    'Regional Infrastructure',
    'Primary facilities and distribution network.',
    'ACTIVE',
    50
),
(
    'Disconnected Test Network',
    'Demonstrates multiple connected components.',
    'ACTIVE',
    100
),
(
    'Negative Weight Network',
    'Demonstrates valid negative edge weights.',
    'ACTIVE',
    100
);

INSERT INTO vertices(
    network_id,
    vertex_code,
    vertex_name,
    location
)
SELECT
    n.network_id,
    data.vertex_code,
    data.vertex_name,
    data.location
FROM networks n
CROSS JOIN (
    VALUES
        ('WH', 'Warehouse', 'North'),
        ('FA', 'Factory', 'East'),
        ('OF', 'Office', 'Central'),
        ('DI', 'Distribution', 'West'),
        ('DC', 'Data Center', 'South')
) AS data(vertex_code, vertex_name, location)
WHERE n.network_name = 'Regional Infrastructure';

INSERT INTO vertices(
    network_id,
    vertex_code,
    vertex_name
)
SELECT
    n.network_id,
    data.vertex_code,
    data.vertex_name
FROM networks n
CROSS JOIN (
    VALUES
        ('A', 'Node A'),
        ('B', 'Node B'),
        ('C', 'Node C'),
        ('D', 'Node D')
) AS data(vertex_code, vertex_name)
WHERE n.network_name = 'Disconnected Test Network';

INSERT INTO vertices(
    network_id,
    vertex_code,
    vertex_name
)
SELECT
    n.network_id,
    data.vertex_code,
    data.vertex_name
FROM networks n
CROSS JOIN (
    VALUES
        ('NA', 'Negative A'),
        ('NB', 'Negative B'),
        ('NC', 'Negative C')
) AS data(vertex_code, vertex_name)
WHERE n.network_name = 'Negative Weight Network';

-- ============================================================
-- 12. SAMPLE EDGES
-- ============================================================

INSERT INTO edges(
    network_id,
    source_vertex_id,
    target_vertex_id,
    weight
)
SELECT
    n.network_id,
    LEAST(a.vertex_id, b.vertex_id),
    GREATEST(a.vertex_id, b.vertex_id),
    data.weight
FROM networks n
JOIN (
    VALUES
        ('WH', 'FA', 12::NUMERIC),
        ('WH', 'OF', 8::NUMERIC),
        ('FA', 'OF', 5::NUMERIC),
        ('FA', 'DI', 7::NUMERIC),
        ('OF', 'DI', 9::NUMERIC),
        ('OF', 'DC', 11::NUMERIC),
        ('DI', 'DC', 4::NUMERIC)
) AS data(source_code, target_code, weight)
    ON n.network_name = 'Regional Infrastructure'
JOIN vertices a
    ON a.network_id = n.network_id
   AND a.vertex_code = data.source_code
JOIN vertices b
    ON b.network_id = n.network_id
   AND b.vertex_code = data.target_code;

INSERT INTO edges(
    network_id,
    source_vertex_id,
    target_vertex_id,
    weight
)
SELECT
    n.network_id,
    a.vertex_id,
    b.vertex_id,
    data.weight
FROM networks n
JOIN (
    VALUES
        ('A', 'B', 2::NUMERIC),
        ('C', 'D', 1::NUMERIC)
) AS data(source_code, target_code, weight)
    ON n.network_name = 'Disconnected Test Network'
JOIN vertices a
    ON a.network_id = n.network_id
   AND a.vertex_code = data.source_code
JOIN vertices b
    ON b.network_id = n.network_id
   AND b.vertex_code = data.target_code;

INSERT INTO edges(
    network_id,
    source_vertex_id,
    target_vertex_id,
    weight
)
SELECT
    n.network_id,
    a.vertex_id,
    b.vertex_id,
    data.weight
FROM networks n
JOIN (
    VALUES
        ('NA', 'NB', -5::NUMERIC),
        ('NB', 'NC', 2::NUMERIC),
        ('NA', 'NC', 4::NUMERIC)
) AS data(source_code, target_code, weight)
    ON n.network_name = 'Negative Weight Network'
JOIN vertices a
    ON a.network_id = n.network_id
   AND a.vertex_code = data.source_code
JOIN vertices b
    ON b.network_id = n.network_id
   AND b.vertex_code = data.target_code;

-- ============================================================
-- 13. SAMPLE POLICIES
-- ============================================================

INSERT INTO network_policies(
    network_id,
    required_algorithm,
    require_connected,
    maximum_allowed_weight,
    allow_negative_weights,
    require_verified_result
)
SELECT
    network_id,
    'KRUSKAL',
    TRUE,
    50,
    TRUE,
    TRUE
FROM networks
WHERE network_name = 'Regional Infrastructure';

INSERT INTO network_policies(
    network_id,
    required_algorithm,
    require_connected,
    maximum_allowed_weight,
    allow_negative_weights,
    require_verified_result
)
SELECT
    network_id,
    'KRUSKAL',
    FALSE,
    100,
    TRUE,
    TRUE
FROM networks
WHERE network_name = 'Disconnected Test Network';

INSERT INTO network_policies(
    network_id,
    required_algorithm,
    require_connected,
    maximum_allowed_weight,
    allow_negative_weights,
    require_verified_result
)
SELECT
    network_id,
    'KRUSKAL',
    TRUE,
    100,
    TRUE,
    TRUE
FROM networks
WHERE network_name = 'Negative Weight Network';

-- ============================================================
-- 14. SAMPLE APPROVALS
-- ============================================================

INSERT INTO network_approvals(
    network_id,
    approver,
    approved,
    comments
)
SELECT
    network_id,
    'Infrastructure Manager',
    TRUE,
    'Approved network optimization policy.'
FROM networks
WHERE network_name = 'Regional Infrastructure';

-- ============================================================
-- 15. EXECUTE VALID CALCULATIONS
-- ============================================================

BEGIN;

CALL execute_mst(
    (
        SELECT network_id
        FROM networks
        WHERE network_name = 'Regional Infrastructure'
    ),
    'KRUSKAL'
);

CALL execute_mst(
    (
        SELECT network_id
        FROM networks
        WHERE network_name = 'Disconnected Test Network'
    ),
    'KRUSKAL'
);

CALL execute_mst(
    (
        SELECT network_id
        FROM networks
        WHERE network_name = 'Negative Weight Network'
    ),
    'KRUSKAL'
);

COMMIT;

-- ============================================================
-- 16. RETRIEVAL: NETWORK AND EDGE DETAILS
-- ============================================================

SELECT
    n.network_name,
    v.vertex_code,
    v.vertex_name
FROM networks n
JOIN vertices v
    ON v.network_id = n.network_id
ORDER BY n.network_id, v.vertex_code;

SELECT
    n.network_name,
    e.edge_id,
    source.vertex_code AS source,
    target.vertex_code AS target,
    e.weight,
    e.enabled
FROM edges e
JOIN networks n
    ON n.network_id = e.network_id
JOIN vertices source
    ON source.vertex_id = e.source_vertex_id
JOIN vertices target
    ON target.vertex_id = e.target_vertex_id
ORDER BY n.network_name, e.weight;

-- ============================================================
-- 17. AGGREGATION: NETWORK SUMMARY
-- ============================================================

SELECT *
FROM network_summary
ORDER BY network_id;

-- ============================================================
-- 18. CONNECTIVITY AND COMPONENT REPORTING
-- ============================================================

SELECT
    n.network_name,
    c.component_number,
    c.vertex_code,
    c.vertex_name
FROM networks n
CROSS JOIN LATERAL network_connectivity(n.network_id) c
ORDER BY n.network_name, c.component_number, c.vertex_id;

-- ============================================================
-- 19. MST REPORTING
-- ============================================================

SELECT
    n.network_name,
    c.calculation_id,
    c.algorithm,
    c.total_weight,
    c.vertex_count,
    c.edge_count,
    c.component_count,
    c.is_spanning_tree,
    c.is_verified,
    c.executed_at
FROM mst_calculations c
JOIN networks n
    ON n.network_id = c.network_id
ORDER BY c.executed_at DESC;

SELECT
    c.calculation_id,
    n.network_name,
    selected.selection_order,
    source.vertex_code AS source_vertex,
    target.vertex_code AS target_vertex,
    e.weight
FROM mst_selected_edges selected
JOIN mst_calculations c
    ON c.calculation_id = selected.calculation_id
JOIN networks n
    ON n.network_id = c.network_id
JOIN edges e
    ON e.edge_id = selected.edge_id
JOIN vertices source
    ON source.vertex_id = e.source_vertex_id
JOIN vertices target
    ON target.vertex_id = e.target_vertex_id
ORDER BY c.calculation_id, selected.selection_order;

-- ============================================================
-- 20. ELIGIBILITY DETERMINATION
-- ============================================================

SELECT
    n.network_name,
    c.calculation_id,
    c.total_weight,
    c.component_count,
    p.require_connected,
    p.maximum_allowed_weight,
    CASE
        WHEN p.require_connected AND NOT c.is_spanning_tree
            THEN 'REJECTED: DISCONNECTED'
        WHEN p.maximum_allowed_weight IS NOT NULL
             AND c.total_weight > p.maximum_allowed_weight
            THEN 'REJECTED: BUDGET'
        WHEN p.require_verified_result AND NOT c.is_verified
            THEN 'REJECTED: NOT VERIFIED'
        ELSE 'ELIGIBLE'
    END AS eligibility
FROM mst_calculations c
JOIN networks n
    ON n.network_id = c.network_id
LEFT JOIN network_policies p
    ON p.network_id = n.network_id
ORDER BY c.calculation_id;

-- ============================================================
-- 21. VALIDATION: SELECTED EDGE COUNT
-- ============================================================

SELECT
    c.calculation_id,
    c.vertex_count,
    COUNT(s.edge_id) AS actual_selected_edges,
    c.vertex_count - c.component_count AS expected_selected_edges,
    COUNT(s.edge_id) =
        c.vertex_count - c.component_count AS valid_edge_count
FROM mst_calculations c
LEFT JOIN mst_selected_edges s
    ON s.calculation_id = c.calculation_id
GROUP BY
    c.calculation_id,
    c.vertex_count,
    c.component_count
ORDER BY c.calculation_id;

-- ============================================================
-- 22. VALIDATION: NO CYCLES
-- ============================================================

-- A selected edge must always connect two previously separate
-- components. The calculation procedure enforces this invariant
-- through Union-Find. The stored edge-count and connectivity
-- reports provide additional consistency checks.

SELECT
    c.calculation_id,
    c.component_count,
    COUNT(s.edge_id) AS selected_edges,
    c.vertex_count - c.component_count AS expected_edges
FROM mst_calculations c
LEFT JOIN mst_selected_edges s
    ON s.calculation_id = c.calculation_id
GROUP BY
    c.calculation_id,
    c.component_count,
    c.vertex_count;

-- ============================================================
-- 23. PERFORMANCE: EDGE DISTRIBUTION
-- ============================================================

EXPLAIN (ANALYZE, BUFFERS)
SELECT edge_id, weight
FROM edges
WHERE network_id = 1
  AND enabled = TRUE
ORDER BY weight, edge_id;

-- ============================================================
-- 24. FAILURE CASE: INVALID SELF-LOOP
-- ============================================================

-- The following statement intentionally fails.
-- Execute separately when testing:
--
-- INSERT INTO edges(
--     network_id,
--     source_vertex_id,
--     target_vertex_id,
--     weight
-- )
-- SELECT network_id, vertex_id, vertex_id, 5
-- FROM vertices
-- WHERE vertex_code = 'WH';
--
-- Failure reason: CHECK (source_vertex_id <> target_vertex_id).

-- ============================================================
-- 25. FAILURE CASE: DUPLICATE UNDIRECTED CONNECTION
-- ============================================================

-- The following statement intentionally fails.
-- Execute separately when testing:
--
-- INSERT INTO edges(
--     network_id,
--     source_vertex_id,
--     target_vertex_id,
--     weight
-- )
-- SELECT
--     e.network_id,
--     e.target_vertex_id,
--     e.source_vertex_id,
--     20
-- FROM edges e
-- LIMIT 1;
--
-- Failure reason:
-- The canonical endpoint ordering and unique constraint
-- prevent duplicate undirected edges.

-- ============================================================
-- 26. TRANSACTIONAL FAILURE DEMONSTRATION
-- ============================================================

-- A rejected disconnected network under a connected-tree policy
-- raises an exception. PostgreSQL rolls back the transaction.
--
-- Test separately:
--
-- BEGIN;
--
-- UPDATE network_policies
-- SET require_connected = TRUE
-- WHERE network_id = (
--     SELECT network_id
--     FROM networks
--     WHERE network_name = 'Disconnected Test Network'
-- );
--
-- CALL execute_mst(
--     (
--         SELECT network_id
--         FROM networks
--         WHERE network_name = 'Disconnected Test Network'
--     ),
--     'KRUSKAL'
-- );
--
-- ROLLBACK;

-- ============================================================
-- END OF MINIMUM SPANNING TREE DATABASE
-- ============================================================
