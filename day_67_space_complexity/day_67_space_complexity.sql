/*
 * SPACE COMPLEXITY
 *
 * PostgreSQL memory analysis and algorithm resource governance.
 *
 * Models:
 * - Algorithm implementations and memory profiles
 * - Auxiliary-space classifications
 * - Memory budgets
 * - Execution records
 * - Algorithm trade-offs
 * - Dynamic programming storage
 * - Streaming versus materialized processing
 * - Resource-policy enforcement
 * - Memory consumption reporting
 *
 * Requires PostgreSQL 14 or later.
 */

DROP SCHEMA IF EXISTS space_complexity CASCADE;

CREATE SCHEMA space_complexity;

SET search_path TO space_complexity, public;

-- =========================================================
-- 1. ENUM TYPES
-- =========================================================

CREATE TYPE space_classification AS ENUM (
    'O(1)',
    'O(log n)',
    'O(n)',
    'O(n log n)',
    'O(n^2)'
);

CREATE TYPE execution_status AS ENUM (
    'PENDING',
    'RUNNING',
    'COMPLETED',
    'REJECTED',
    'FAILED'
);

CREATE TYPE memory_strategy AS ENUM (
    'IN_PLACE',
    'ITERATIVE',
    'RECURSIVE',
    'MATERIALIZED',
    'STREAMING',
    'DYNAMIC_PROGRAMMING'
);

-- =========================================================
-- 2. ALGORITHM CATALOG
-- =========================================================

CREATE TABLE algorithms (
    algorithm_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    algorithm_name VARCHAR(120) NOT NULL UNIQUE,

    category VARCHAR(60) NOT NULL,

    time_complexity VARCHAR(30) NOT NULL,

    auxiliary_space space_classification NOT NULL,

    input_space_included BOOLEAN NOT NULL DEFAULT FALSE,

    strategy memory_strategy NOT NULL,

    description TEXT NOT NULL,

    CONSTRAINT valid_algorithm_name
        CHECK (length(trim(algorithm_name)) > 0)
);

INSERT INTO algorithms (
    algorithm_name,
    category,
    time_complexity,
    auxiliary_space,
    input_space_included,
    strategy,
    description
)
VALUES
(
    'Constant Space Sum',
    'Aggregation',
    'O(n)',
    'O(1)',
    FALSE,
    'ITERATIVE',
    'Aggregates input using a fixed number of variables.'
),
(
    'Array Copy',
    'Array Processing',
    'O(n)',
    'O(n)',
    FALSE,
    'MATERIALIZED',
    'Creates a separate copy of the input array.'
),
(
    'In-Place Reverse',
    'Array Processing',
    'O(n)',
    'O(1)',
    FALSE,
    'IN_PLACE',
    'Reverses elements through index swapping.'
),
(
    'Recursive Binary Search',
    'Searching',
    'O(log n)',
    'O(log n)',
    FALSE,
    'RECURSIVE',
    'Uses recursive call frames.'
),
(
    'Iterative Binary Search',
    'Searching',
    'O(log n)',
    'O(1)',
    FALSE,
    'ITERATIVE',
    'Uses loop variables instead of recursive calls.'
),
(
    'Hash-Based Deduplication',
    'Data Processing',
    'O(n) average',
    'O(n)',
    FALSE,
    'MATERIALIZED',
    'Uses a hash structure to retain distinct values.'
),
(
    'Full Fibonacci Table',
    'Dynamic Programming',
    'O(n)',
    'O(n)',
    FALSE,
    'DYNAMIC_PROGRAMMING',
    'Stores all previously calculated Fibonacci values.'
),
(
    'Optimized Fibonacci',
    'Dynamic Programming',
    'O(n)',
    'O(1)',
    FALSE,
    'ITERATIVE',
    'Stores only the two previous Fibonacci values.'
),
(
    'Full Knapsack Table',
    'Dynamic Programming',
    'O(nW)',
    'O(nW)',
    FALSE,
    'DYNAMIC_PROGRAMMING',
    'Stores the complete dynamic programming table.'
),
(
    'Optimized Knapsack',
    'Dynamic Programming',
    'O(nW)',
    'O(W)',
    FALSE,
    'DYNAMIC_PROGRAMMING',
    'Uses a one-dimensional dynamic programming array.'
),
(
    'Streaming Aggregation',
    'Data Processing',
    'O(n)',
    'O(1)',
    FALSE,
    'STREAMING',
    'Processes records without retaining the complete input.'
),
(
    'Matrix Allocation',
    'Matrix Processing',
    'O(n^2)',
    'O(n^2)',
    FALSE,
    'MATERIALIZED',
    'Allocates an n by n matrix.'
);

-- =========================================================
-- 3. MEMORY POLICIES
-- =========================================================

CREATE TABLE memory_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    policy_name VARCHAR(100) NOT NULL UNIQUE,

    maximum_memory_bytes BIGINT NOT NULL,

    maximum_input_size BIGINT NOT NULL,

    allow_recursive_execution BOOLEAN NOT NULL DEFAULT TRUE,

    allow_quadratic_storage BOOLEAN NOT NULL DEFAULT FALSE,

    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT positive_memory_budget
        CHECK (maximum_memory_bytes > 0),

    CONSTRAINT positive_input_limit
        CHECK (maximum_input_size >= 0)
);

INSERT INTO memory_policies (
    policy_name,
    maximum_memory_bytes,
    maximum_input_size,
    allow_recursive_execution,
    allow_quadratic_storage,
    enabled
)
VALUES
(
    'Development',
    67108864,
    100000,
    TRUE,
    TRUE,
    TRUE
),
(
    'Production',
    16777216,
    50000,
    FALSE,
    FALSE,
    TRUE
),
(
    'Restricted Environment',
    1048576,
    10000,
    FALSE,
    FALSE,
    TRUE
);

-- =========================================================
-- 4. ALGORITHM EXECUTION RECORDS
-- =========================================================

CREATE TABLE algorithm_executions (
    execution_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    algorithm_id BIGINT NOT NULL
        REFERENCES algorithms(algorithm_id),

    policy_id BIGINT NOT NULL
        REFERENCES memory_policies(policy_id),

    input_size BIGINT NOT NULL,

    estimated_auxiliary_bytes BIGINT NOT NULL,

    estimated_total_bytes BIGINT NOT NULL,

    actual_memory_bytes BIGINT,

    status execution_status NOT NULL DEFAULT 'PENDING',

    execution_notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    completed_at TIMESTAMPTZ,

    CONSTRAINT nonnegative_input
        CHECK (input_size >= 0),

    CONSTRAINT nonnegative_estimated_auxiliary
        CHECK (estimated_auxiliary_bytes >= 0),

    CONSTRAINT nonnegative_estimated_total
        CHECK (estimated_total_bytes >= 0),

    CONSTRAINT nonnegative_actual_memory
        CHECK (
            actual_memory_bytes IS NULL
            OR actual_memory_bytes >= 0
        ),

    CONSTRAINT valid_completion_time
        CHECK (
            completed_at IS NULL
            OR completed_at >= created_at
        )
);

CREATE INDEX idx_execution_algorithm
    ON algorithm_executions(algorithm_id);

CREATE INDEX idx_execution_status_created
    ON algorithm_executions(status, created_at DESC);

CREATE INDEX idx_execution_policy
    ON algorithm_executions(policy_id, status);

-- =========================================================
-- 5. MEMORY ESTIMATION FUNCTION
-- =========================================================

CREATE OR REPLACE FUNCTION estimate_memory(
    p_element_count BIGINT,
    p_bytes_per_element BIGINT,
    p_fixed_overhead BIGINT DEFAULT 0
)
RETURNS BIGINT
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
DECLARE
    v_result NUMERIC;
BEGIN
    IF p_element_count < 0
       OR p_bytes_per_element < 0
       OR p_fixed_overhead < 0 THEN
        RAISE EXCEPTION 'Memory parameters cannot be negative.';
    END IF;

    v_result :=
        p_element_count::NUMERIC
        * p_bytes_per_element::NUMERIC
        + p_fixed_overhead::NUMERIC;

    IF v_result > 9223372036854775807::NUMERIC THEN
        RAISE EXCEPTION 'Memory estimate exceeds BIGINT capacity.';
    END IF;

    RETURN v_result::BIGINT;
END;
$$;

-- =========================================================
-- 6. MATRIX MEMORY ESTIMATION
-- =========================================================

CREATE OR REPLACE FUNCTION estimate_matrix_memory(
    p_rows BIGINT,
    p_columns BIGINT,
    p_bytes_per_element BIGINT
)
RETURNS BIGINT
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
DECLARE
    v_result NUMERIC;
BEGIN
    IF p_rows < 0 OR p_columns < 0 OR p_bytes_per_element < 0 THEN
        RAISE EXCEPTION 'Matrix parameters cannot be negative.';
    END IF;

    v_result :=
        p_rows::NUMERIC
        * p_columns::NUMERIC
        * p_bytes_per_element::NUMERIC;

    IF v_result > 9223372036854775807::NUMERIC THEN
        RAISE EXCEPTION 'Matrix estimate exceeds BIGINT capacity.';
    END IF;

    RETURN v_result::BIGINT;
END;
$$;

-- =========================================================
-- 7. MEMORY BUDGET EVALUATION
-- =========================================================

CREATE OR REPLACE FUNCTION evaluate_memory_budget(
    p_policy_id BIGINT,
    p_algorithm_id BIGINT,
    p_input_size BIGINT,
    p_auxiliary_bytes BIGINT,
    p_total_bytes BIGINT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_policy memory_policies%ROWTYPE;
    v_algorithm algorithms%ROWTYPE;
BEGIN
    SELECT *
    INTO v_policy
    FROM memory_policies
    WHERE policy_id = p_policy_id;

    IF NOT FOUND OR NOT v_policy.enabled THEN
        RAISE EXCEPTION 'Memory policy is unavailable.';
    END IF;

    SELECT *
    INTO v_algorithm
    FROM algorithms
    WHERE algorithm_id = p_algorithm_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Algorithm does not exist.';
    END IF;

    IF p_input_size < 0
       OR p_auxiliary_bytes < 0
       OR p_total_bytes < 0 THEN
        RAISE EXCEPTION 'Memory parameters cannot be negative.';
    END IF;

    IF p_input_size > v_policy.maximum_input_size THEN
        RETURN FALSE;
    END IF;

    IF p_total_bytes > v_policy.maximum_memory_bytes THEN
        RETURN FALSE;
    END IF;

    IF v_algorithm.strategy = 'RECURSIVE'
       AND NOT v_policy.allow_recursive_execution THEN
        RETURN FALSE;
    END IF;

    IF v_algorithm.auxiliary_space = 'O(n^2)'
       AND NOT v_policy.allow_quadratic_storage THEN
        RETURN FALSE;
    END IF;

    RETURN TRUE;
END;
$$;

-- =========================================================
-- 8. EXECUTION VALIDATION TRIGGER
-- =========================================================

CREATE OR REPLACE FUNCTION validate_execution()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.status = 'RUNNING' THEN
        IF NOT evaluate_memory_budget(
            NEW.policy_id,
            NEW.algorithm_id,
            NEW.input_size,
            NEW.estimated_auxiliary_bytes,
            NEW.estimated_total_bytes
        ) THEN
            RAISE EXCEPTION
                'Execution rejected by memory governance policy.';
        END IF;
    END IF;

    IF NEW.status = 'COMPLETED' THEN
        IF NEW.completed_at IS NULL THEN
            NEW.completed_at := CURRENT_TIMESTAMP;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_execution
BEFORE INSERT OR UPDATE
ON algorithm_executions
FOR EACH ROW
EXECUTE FUNCTION validate_execution();

-- =========================================================
-- 9. EXECUTION PROCESSING FUNCTION
-- =========================================================

CREATE OR REPLACE FUNCTION submit_execution(
    p_algorithm_id BIGINT,
    p_policy_id BIGINT,
    p_input_size BIGINT,
    p_auxiliary_bytes BIGINT,
    p_total_bytes BIGINT
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_execution_id BIGINT;
    v_accepted BOOLEAN;
BEGIN
    IF p_input_size < 0
       OR p_auxiliary_bytes < 0
       OR p_total_bytes < 0 THEN
        RAISE EXCEPTION 'Input and memory estimates must be non-negative.';
    END IF;

    v_accepted := evaluate_memory_budget(
        p_policy_id,
        p_algorithm_id,
        p_input_size,
        p_auxiliary_bytes,
        p_total_bytes
    );

    INSERT INTO algorithm_executions (
        algorithm_id,
        policy_id,
        input_size,
        estimated_auxiliary_bytes,
        estimated_total_bytes,
        status,
        execution_notes
    )
    VALUES (
        p_algorithm_id,
        p_policy_id,
        p_input_size,
        p_auxiliary_bytes,
        p_total_bytes,
        CASE
            WHEN v_accepted THEN 'RUNNING'::execution_status
            ELSE 'REJECTED'::execution_status
        END,
        CASE
            WHEN v_accepted THEN 'Accepted by memory policy.'
            ELSE 'Rejected by memory policy.'
        END
    )
    RETURNING execution_id INTO v_execution_id;

    RETURN v_execution_id;
END;
$$;

-- =========================================================
-- 10. EXECUTION COMPLETION PROCEDURE
-- =========================================================

CREATE OR REPLACE PROCEDURE complete_execution(
    p_execution_id BIGINT,
    p_actual_memory_bytes BIGINT,
    p_notes TEXT DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_actual_memory_bytes < 0 THEN
        RAISE EXCEPTION 'Actual memory cannot be negative.';
    END IF;

    UPDATE algorithm_executions
    SET
        actual_memory_bytes = p_actual_memory_bytes,
        status = 'COMPLETED',
        completed_at = CURRENT_TIMESTAMP,
        execution_notes = COALESCE(
            p_notes,
            'Execution completed.'
        )
    WHERE execution_id = p_execution_id
      AND status = 'RUNNING';

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Execution does not exist or is not running.';
    END IF;
END;
$$;

-- =========================================================
-- 11. SAMPLE EXECUTION DATA
-- =========================================================

BEGIN;

-- Constant-space sum: accepted.
SELECT submit_execution(
    (SELECT algorithm_id FROM algorithms
     WHERE algorithm_name = 'Constant Space Sum'),
    (SELECT policy_id FROM memory_policies
     WHERE policy_name = 'Production'),
    10000,
    64,
    40064
);

-- Array copy: accepted within production memory.
SELECT submit_execution(
    (SELECT algorithm_id FROM algorithms
     WHERE algorithm_name = 'Array Copy'),
    (SELECT policy_id FROM memory_policies
     WHERE policy_name = 'Production'),
    10000,
    40000,
    80000
);

-- Recursive search: rejected because recursion is disabled.
SELECT submit_execution(
    (SELECT algorithm_id FROM algorithms
     WHERE algorithm_name = 'Recursive Binary Search'),
    (SELECT policy_id FROM memory_policies
     WHERE policy_name = 'Production'),
    10000,
    1024,
    4096
);

-- Quadratic storage: rejected by production policy.
SELECT submit_execution(
    (SELECT algorithm_id FROM algorithms
     WHERE algorithm_name = 'Matrix Allocation'),
    (SELECT policy_id FROM memory_policies
     WHERE policy_name = 'Production'),
    1000,
    4000000,
    4100000
);

-- Streaming aggregation: accepted.
SELECT submit_execution(
    (SELECT algorithm_id FROM algorithms
     WHERE algorithm_name = 'Streaming Aggregation'),
    (SELECT policy_id FROM memory_policies
     WHERE policy_name = 'Production'),
    50000,
    64,
    100000
);

-- Optimized dynamic programming: accepted.
SELECT submit_execution(
    (SELECT algorithm_id FROM algorithms
     WHERE algorithm_name = 'Optimized Knapsack'),
    (SELECT policy_id FROM memory_policies
     WHERE policy_name = 'Production'),
    1000,
    400004,
    500000
);

-- Full dynamic programming: rejected by memory limit.
SELECT submit_execution(
    (SELECT algorithm_id FROM algorithms
     WHERE algorithm_name = 'Full Knapsack Table'),
    (SELECT policy_id FROM memory_policies
     WHERE policy_name = 'Production'),
    1000,
    40000000,
    41000000
);

COMMIT;

-- =========================================================
-- 12. COMPLETE SUCCESSFUL EXECUTIONS
-- =========================================================

UPDATE algorithm_executions
SET
    actual_memory_bytes = estimated_auxiliary_bytes,
    status = 'COMPLETED',
    completed_at = CURRENT_TIMESTAMP
WHERE status = 'RUNNING';

-- =========================================================
-- 13. RETRIEVAL QUERY
-- =========================================================

SELECT
    e.execution_id,
    a.algorithm_name,
    a.auxiliary_space,
    a.strategy,
    e.input_size,
    e.estimated_auxiliary_bytes,
    e.estimated_total_bytes,
    e.actual_memory_bytes,
    e.status,
    p.policy_name
FROM algorithm_executions e
JOIN algorithms a
    ON a.algorithm_id = e.algorithm_id
JOIN memory_policies p
    ON p.policy_id = e.policy_id
ORDER BY e.execution_id;

-- =========================================================
-- 14. MEMORY VALIDATION QUERY
-- =========================================================

SELECT
    e.execution_id,
    a.algorithm_name,
    p.policy_name,
    e.estimated_total_bytes,
    p.maximum_memory_bytes,
    CASE
        WHEN e.estimated_total_bytes <= p.maximum_memory_bytes
        THEN 'WITHIN BUDGET'
        ELSE 'EXCEEDS BUDGET'
    END AS memory_validation
FROM algorithm_executions e
JOIN algorithms a
    ON a.algorithm_id = e.algorithm_id
JOIN memory_policies p
    ON p.policy_id = e.policy_id;

-- =========================================================
-- 15. AGGREGATION REPORT
-- =========================================================

SELECT
    a.auxiliary_space,
    COUNT(*) AS execution_count,
    AVG(e.estimated_auxiliary_bytes) AS average_estimated_bytes,
    MAX(e.estimated_auxiliary_bytes) AS maximum_estimated_bytes,
    AVG(e.actual_memory_bytes) AS average_actual_bytes
FROM algorithm_executions e
JOIN algorithms a
    ON a.algorithm_id = e.algorithm_id
GROUP BY a.auxiliary_space
ORDER BY a.auxiliary_space;

-- =========================================================
-- 16. ALGORITHM TRADE-OFF REPORT
-- =========================================================

SELECT
    a.algorithm_name,
    a.time_complexity,
    a.auxiliary_space,
    a.strategy,
    a.description
FROM algorithms a
ORDER BY
    CASE a.auxiliary_space
        WHEN 'O(1)' THEN 1
        WHEN 'O(log n)' THEN 2
        WHEN 'O(n)' THEN 3
        WHEN 'O(n log n)' THEN 4
        WHEN 'O(n^2)' THEN 5
    END,
    a.algorithm_name;

-- =========================================================
-- 17. ESTIMATE LINEAR MEMORY
-- =========================================================

SELECT
    estimate_memory(100000, 8, 128)
        AS estimated_linear_memory_bytes;

-- =========================================================
-- 18. ESTIMATE QUADRATIC MEMORY
-- =========================================================

SELECT
    estimate_matrix_memory(1000, 1000, 4)
        AS estimated_matrix_memory_bytes;

-- =========================================================
-- 19. EXECUTION STATUS REPORT
-- =========================================================

SELECT
    status,
    COUNT(*) AS execution_count,
    SUM(estimated_auxiliary_bytes) AS total_estimated_auxiliary,
    SUM(estimated_total_bytes) AS total_estimated_memory
FROM algorithm_executions
GROUP BY status
ORDER BY status;

-- =========================================================
-- 20. MEMORY ESTIMATION ACCURACY
-- =========================================================

SELECT
    a.algorithm_name,
    COUNT(*) AS observations,
    AVG(e.estimated_auxiliary_bytes) AS average_estimated,
    AVG(e.actual_memory_bytes) AS average_actual,
    AVG(
        e.actual_memory_bytes - e.estimated_auxiliary_bytes
    ) AS average_difference
FROM algorithm_executions e
JOIN algorithms a
    ON a.algorithm_id = e.algorithm_id
WHERE e.actual_memory_bytes IS NOT NULL
GROUP BY a.algorithm_name
ORDER BY a.algorithm_name;

-- =========================================================
-- 21. STREAMING VERSUS MATERIALIZED STRATEGIES
-- =========================================================

SELECT
    strategy,
    COUNT(*) AS algorithms,
    AVG(estimated_auxiliary_bytes) AS average_auxiliary_bytes
FROM algorithm_executions e
JOIN algorithms a
    ON a.algorithm_id = e.algorithm_id
GROUP BY strategy
ORDER BY average_auxiliary_bytes;

-- =========================================================
-- 22. POLICY ELIGIBILITY VIEW
-- =========================================================

CREATE OR REPLACE VIEW execution_eligibility AS
SELECT
    e.execution_id,
    a.algorithm_name,
    p.policy_name,
    e.input_size,
    e.estimated_auxiliary_bytes,
    e.estimated_total_bytes,
    e.status,
    CASE
        WHEN e.status = 'REJECTED' THEN FALSE
        WHEN e.input_size > p.maximum_input_size THEN FALSE
        WHEN e.estimated_total_bytes > p.maximum_memory_bytes THEN FALSE
        ELSE TRUE
    END AS within_numeric_limits
FROM algorithm_executions e
JOIN algorithms a
    ON a.algorithm_id = e.algorithm_id
JOIN memory_policies p
    ON p.policy_id = e.policy_id;

SELECT *
FROM execution_eligibility
ORDER BY execution_id;

-- =========================================================
-- 23. CTE-BASED RANKING
-- =========================================================

WITH algorithm_memory AS (
    SELECT
        a.algorithm_name,
        a.auxiliary_space,
        AVG(e.estimated_auxiliary_bytes) AS average_bytes,
        COUNT(e.execution_id) AS total_executions
    FROM algorithms a
    LEFT JOIN algorithm_executions e
        ON e.algorithm_id = a.algorithm_id
    GROUP BY
        a.algorithm_id,
        a.algorithm_name,
        a.auxiliary_space
),
ranked_algorithms AS (
    SELECT
        *,
        DENSE_RANK() OVER (
            ORDER BY average_bytes NULLS LAST
        ) AS memory_rank
    FROM algorithm_memory
)
SELECT
    algorithm_name,
    auxiliary_space,
    average_bytes,
    total_executions,
    memory_rank
FROM ranked_algorithms
ORDER BY memory_rank, algorithm_name;

-- =========================================================
-- 24. DATABASE MEMORY ANALYSIS
-- =========================================================

SELECT
    schemaname,
    tablename,
    pg_size_pretty(
        pg_total_relation_size(
            quote_ident(schemaname) || '.' || quote_ident(tablename)
        )
    ) AS total_relation_size
FROM pg_tables
WHERE schemaname = 'space_complexity'
ORDER BY pg_total_relation_size(
    quote_ident(schemaname) || '.' || quote_ident(tablename)
) DESC;

-- =========================================================
-- 25. FINAL GOVERNANCE REPORT
-- =========================================================

SELECT
    COUNT(*) AS total_executions,
    COUNT(*) FILTER (
        WHERE status = 'COMPLETED'
    ) AS completed_executions,
    COUNT(*) FILTER (
        WHERE status = 'REJECTED'
    ) AS rejected_executions,
    COUNT(*) FILTER (
        WHERE status = 'FAILED'
    ) AS failed_executions,
    COALESCE(
        SUM(actual_memory_bytes),
        0
    ) AS total_recorded_actual_memory
FROM algorithm_executions;
