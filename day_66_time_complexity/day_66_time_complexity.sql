-- ============================================================
-- TIME COMPLEXITY AND ASYMPTOTIC PERFORMANCE ANALYSIS
-- PostgreSQL 14+
--
-- Models:
-- 1. Algorithms and complexity classifications.
-- 2. Big-O, Big-Omega and Big-Theta definitions.
-- 3. Input-size-specific workload measurements.
-- 4. Performance policies and governance.
-- 5. Operation-count benchmarking.
-- 6. Validation, reporting and workload eligibility.
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS complexity_lab;

SET search_path TO complexity_lab, public;

-- ------------------------------------------------------------
-- 1. ENUMERATIONS
-- ------------------------------------------------------------

CREATE TYPE complexity_class AS ENUM (
    'CONSTANT',
    'LOGARITHMIC',
    'LINEAR',
    'LINEARITHMIC',
    'QUADRATIC',
    'CUBIC',
    'EXPONENTIAL'
);

CREATE TYPE workload_status AS ENUM (
    'PENDING',
    'ACCEPTED',
    'REJECTED',
    'COMPLETED',
    'FAILED'
);

CREATE TYPE bound_type AS ENUM (
    'UPPER',
    'LOWER',
    'TIGHT'
);

-- ------------------------------------------------------------
-- 2. COMPLEXITY DEFINITIONS
-- ------------------------------------------------------------

CREATE TABLE complexity_definitions (
    complexity_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    complexity_name complexity_class NOT NULL UNIQUE,
    big_o TEXT NOT NULL,
    big_omega TEXT NOT NULL,
    big_theta TEXT NOT NULL,
    growth_description TEXT NOT NULL,
    growth_rank SMALLINT NOT NULL UNIQUE,
    CONSTRAINT valid_growth_rank CHECK (growth_rank > 0)
);

INSERT INTO complexity_definitions (
    complexity_name,
    big_o,
    big_omega,
    big_theta,
    growth_description,
    growth_rank
)
VALUES
(
    'CONSTANT',
    'O(1)',
    'Omega(1)',
    'Theta(1)',
    'Fixed number of operations.',
    1
),
(
    'LOGARITHMIC',
    'O(log n)',
    'Omega(log n)',
    'Theta(log n)',
    'Input repeatedly reduced by a constant factor.',
    2
),
(
    'LINEAR',
    'O(n)',
    'Omega(n)',
    'Theta(n)',
    'Operations proportional to input size.',
    3
),
(
    'LINEARITHMIC',
    'O(n log n)',
    'Omega(n log n)',
    'Theta(n log n)',
    'Efficient comparison-based sorting.',
    4
),
(
    'QUADRATIC',
    'O(n^2)',
    'Omega(n^2)',
    'Theta(n^2)',
    'Two complete nested loops.',
    5
),
(
    'CUBIC',
    'O(n^3)',
    'Omega(n^3)',
    'Theta(n^3)',
    'Three nested loops.',
    6
),
(
    'EXPONENTIAL',
    'O(2^n)',
    'Omega(2^n)',
    'Theta(2^n)',
    'Exponential branching.',
    7
);

-- ------------------------------------------------------------
-- 3. ALGORITHM REGISTRY
-- ------------------------------------------------------------

CREATE TABLE algorithms (
    algorithm_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    algorithm_name VARCHAR(120) NOT NULL UNIQUE,
    complexity_id BIGINT NOT NULL REFERENCES complexity_definitions,
    best_case TEXT NOT NULL,
    average_case TEXT NOT NULL,
    worst_case TEXT NOT NULL,
    auxiliary_space TEXT NOT NULL,
    stable BOOLEAN NOT NULL DEFAULT FALSE,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO algorithms (
    algorithm_name,
    complexity_id,
    best_case,
    average_case,
    worst_case,
    auxiliary_space,
    stable,
    description
)
SELECT
    input.algorithm_name,
    definition.complexity_id,
    input.best_case,
    input.average_case,
    input.worst_case,
    input.auxiliary_space,
    input.stable,
    input.description
FROM (
    VALUES
    (
        'Constant Lookup',
        'CONSTANT',
        'O(1)',
        'O(1)',
        'O(1)',
        'O(1)',
        FALSE,
        'Direct indexed lookup.'
    ),
    (
        'Binary Search',
        'LOGARITHMIC',
        'O(1)',
        'O(log n)',
        'O(log n)',
        'O(1)',
        FALSE,
        'Search in a sorted array.'
    ),
    (
        'Linear Search',
        'LINEAR',
        'O(1)',
        'O(n)',
        'O(n)',
        'O(1)',
        FALSE,
        'Sequential element inspection.'
    ),
    (
        'Merge Sort',
        'LINEARITHMIC',
        'O(n log n)',
        'O(n log n)',
        'O(n log n)',
        'O(n)',
        TRUE,
        'Divide-and-conquer stable sorting.'
    ),
    (
        'Bubble Sort',
        'QUADRATIC',
        'O(n)',
        'O(n^2)',
        'O(n^2)',
        'O(1)',
        TRUE,
        'Adjacent element comparisons with early termination.'
    ),
    (
        'Three-Level Nested Loop',
        'CUBIC',
        'O(n^3)',
        'O(n^3)',
        'O(n^3)',
        'O(1)',
        FALSE,
        'Three nested complete traversals.'
    ),
    (
        'Naive Fibonacci',
        'EXPONENTIAL',
        'O(1)',
        'O(2^n)',
        'O(2^n)',
        'O(n)',
        FALSE,
        'Recursive Fibonacci without memoization.'
    )
) AS input(
    algorithm_name,
    class_name,
    best_case,
    average_case,
    worst_case,
    auxiliary_space,
    stable,
    description
)
JOIN complexity_definitions definition
    ON definition.complexity_name::TEXT = input.class_name;

-- ------------------------------------------------------------
-- 4. PERFORMANCE POLICIES
-- ------------------------------------------------------------

CREATE TABLE performance_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    policy_name VARCHAR(120) NOT NULL UNIQUE,
    maximum_input_size BIGINT NOT NULL,
    maximum_operations BIGINT NOT NULL,
    maximum_elapsed_ms NUMERIC(14, 3),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (maximum_input_size >= 0),
    CHECK (maximum_operations >= 0),
    CHECK (maximum_elapsed_ms IS NULL OR maximum_elapsed_ms >= 0)
);

CREATE TABLE policy_allowed_complexities (
    policy_id BIGINT NOT NULL REFERENCES performance_policies
        ON DELETE CASCADE,
    complexity_id BIGINT NOT NULL REFERENCES complexity_definitions,
    PRIMARY KEY (policy_id, complexity_id)
);

INSERT INTO performance_policies (
    policy_name,
    maximum_input_size,
    maximum_operations,
    maximum_elapsed_ms
)
VALUES
(
    'STANDARD_API',
    100000,
    1000000,
    5000
),
(
    'HIGH_PERFORMANCE',
    1000000,
    10000000,
    10000
),
(
    'RESEARCH_EXPERIMENT',
    10000,
    100000000,
    60000
);

-- Standard API allows efficient complexity classes.
INSERT INTO policy_allowed_complexities
SELECT
    policy.policy_id,
    definition.complexity_id
FROM performance_policies policy
CROSS JOIN complexity_definitions definition
WHERE policy.policy_name = 'STANDARD_API'
AND definition.complexity_name IN (
    'CONSTANT',
    'LOGARITHMIC',
    'LINEAR',
    'LINEARITHMIC'
);

-- High-performance policy has stricter complexity restrictions.
INSERT INTO policy_allowed_complexities
SELECT
    policy.policy_id,
    definition.complexity_id
FROM performance_policies policy
CROSS JOIN complexity_definitions definition
WHERE policy.policy_name = 'HIGH_PERFORMANCE'
AND definition.complexity_name IN (
    'CONSTANT',
    'LOGARITHMIC',
    'LINEAR'
);

-- Research workloads permit more expensive algorithms.
INSERT INTO policy_allowed_complexities
SELECT
    policy.policy_id,
    definition.complexity_id
FROM performance_policies policy
CROSS JOIN complexity_definitions definition
WHERE policy.policy_name = 'RESEARCH_EXPERIMENT'
AND definition.complexity_name IN (
    'CONSTANT',
    'LOGARITHMIC',
    'LINEAR',
    'LINEARITHMIC',
    'QUADRATIC'
);

-- ------------------------------------------------------------
-- 5. WORKLOADS
-- ------------------------------------------------------------

CREATE TABLE workloads (
    workload_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    workload_code VARCHAR(60) NOT NULL UNIQUE,
    algorithm_id BIGINT NOT NULL REFERENCES algorithms,
    policy_id BIGINT NOT NULL REFERENCES performance_policies,
    input_size BIGINT NOT NULL,
    expected_operations BIGINT NOT NULL,
    measured_operations BIGINT,
    elapsed_ms NUMERIC(14, 3),
    status workload_status NOT NULL DEFAULT 'PENDING',
    rejection_reason TEXT,
    submitted_by VARCHAR(100) NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,

    CHECK (input_size >= 0),
    CHECK (expected_operations >= 0),
    CHECK (measured_operations IS NULL OR measured_operations >= 0),
    CHECK (elapsed_ms IS NULL OR elapsed_ms >= 0)
);

CREATE INDEX idx_workloads_status
ON workloads(status);

CREATE INDEX idx_workloads_algorithm
ON workloads(algorithm_id, input_size);

CREATE INDEX idx_workloads_submission
ON workloads(submitted_at DESC);

-- ------------------------------------------------------------
-- 6. WORKLOAD VALIDATION TRIGGER
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_workload()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    selected_policy performance_policies%ROWTYPE;
    selected_complexity BIGINT;
BEGIN
    SELECT *
    INTO selected_policy
    FROM performance_policies
    WHERE policy_id = NEW.policy_id
    AND active = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Selected performance policy is inactive or missing.';
    END IF;

    SELECT complexity_id
    INTO selected_complexity
    FROM algorithms
    WHERE algorithm_id = NEW.algorithm_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Algorithm does not exist.';
    END IF;

    IF NEW.input_size > selected_policy.maximum_input_size THEN
        NEW.status := 'REJECTED';
        NEW.rejection_reason := 'Input size exceeds policy limit.';
        RETURN NEW;
    END IF;

    IF NEW.expected_operations > selected_policy.maximum_operations THEN
        NEW.status := 'REJECTED';
        NEW.rejection_reason := 'Expected operations exceed policy limit.';
        RETURN NEW;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM policy_allowed_complexities
        WHERE policy_id = NEW.policy_id
        AND complexity_id = selected_complexity
    ) THEN
        NEW.status := 'REJECTED';
        NEW.rejection_reason := 'Complexity class is not permitted.';
        RETURN NEW;
    END IF;

    IF NEW.status = 'REJECTED' THEN
        RAISE EXCEPTION 'Rejected status must be determined by validation.';
    END IF;

    NEW.status := 'ACCEPTED';
    NEW.rejection_reason := NULL;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_workload
BEFORE INSERT OR UPDATE OF algorithm_id, policy_id, input_size,
expected_operations
ON workloads
FOR EACH ROW
EXECUTE FUNCTION validate_workload();

-- ------------------------------------------------------------
-- 7. WORKLOAD COMPLETION AND MEASUREMENTS
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION complete_workload(
    p_workload_code VARCHAR,
    p_operations BIGINT,
    p_elapsed_ms NUMERIC
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    current_workload workloads%ROWTYPE;
    current_policy performance_policies%ROWTYPE;
BEGIN
    IF p_operations < 0 OR p_elapsed_ms < 0 THEN
        RAISE EXCEPTION 'Measurement values cannot be negative.';
    END IF;

    SELECT *
    INTO current_workload
    FROM workloads
    WHERE workload_code = p_workload_code
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Workload not found: %', p_workload_code;
    END IF;

    IF current_workload.status <> 'ACCEPTED' THEN
        RAISE EXCEPTION
            'Only accepted workloads can be completed. Current status: %',
            current_workload.status;
    END IF;

    SELECT *
    INTO current_policy
    FROM performance_policies
    WHERE policy_id = current_workload.policy_id;

    UPDATE workloads
    SET measured_operations = p_operations,
        elapsed_ms = p_elapsed_ms,
        status = CASE
            WHEN p_operations > current_policy.maximum_operations
                THEN 'FAILED'::workload_status
            WHEN current_policy.maximum_elapsed_ms IS NOT NULL
                 AND p_elapsed_ms > current_policy.maximum_elapsed_ms
                THEN 'FAILED'::workload_status
            ELSE 'COMPLETED'::workload_status
        END,
        rejection_reason = CASE
            WHEN p_operations > current_policy.maximum_operations
                THEN 'Measured operations exceeded policy.'
            WHEN current_policy.maximum_elapsed_ms IS NOT NULL
                 AND p_elapsed_ms > current_policy.maximum_elapsed_ms
                THEN 'Execution time exceeded policy.'
            ELSE NULL
        END,
        completed_at = CURRENT_TIMESTAMP
    WHERE workload_id = current_workload.workload_id;
END;
$$;

-- ------------------------------------------------------------
-- 8. SAMPLE WORKLOADS
-- ------------------------------------------------------------

INSERT INTO workloads (
    workload_code,
    algorithm_id,
    policy_id,
    input_size,
    expected_operations,
    submitted_by
)
SELECT
    input.workload_code,
    algorithm.algorithm_id,
    policy.policy_id,
    input.input_size,
    input.expected_operations,
    input.submitted_by
FROM (
    VALUES
    ('JOB-001', 'Binary Search', 'STANDARD_API', 1000::BIGINT, 10::BIGINT, 'developer_a'),
    ('JOB-002', 'Linear Search', 'STANDARD_API', 1000, 1000, 'developer_b'),
    ('JOB-003', 'Merge Sort', 'STANDARD_API', 1000, 10000, 'developer_c'),
    ('JOB-004', 'Bubble Sort', 'STANDARD_API', 500, 250000, 'developer_d'),
    ('JOB-005', 'Three-Level Nested Loop', 'STANDARD_API', 100, 1000000, 'developer_e'),
    ('JOB-006', 'Bubble Sort', 'RESEARCH_EXPERIMENT', 100, 5050, 'researcher_a'),
    ('JOB-007', 'Constant Lookup', 'HIGH_PERFORMANCE', 10000, 1, 'developer_f')
) AS input(
    workload_code,
    algorithm_name,
    policy_name,
    input_size,
    expected_operations,
    submitted_by
)
JOIN algorithms algorithm
    ON algorithm.algorithm_name = input.algorithm_name
JOIN performance_policies policy
    ON policy.policy_name = input.policy_name;

-- ------------------------------------------------------------
-- 9. COMPLETE ACCEPTED WORKLOADS
-- ------------------------------------------------------------

SELECT complete_workload('JOB-001', 10, 0.120);
SELECT complete_workload('JOB-002', 1000, 0.800);
SELECT complete_workload('JOB-003', 8500, 2.500);
SELECT complete_workload('JOB-006', 4950, 1.200);

-- ------------------------------------------------------------
-- 10. COMPLEXITY COMPARISON VIEW
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW algorithm_complexity_report AS
SELECT
    a.algorithm_id,
    a.algorithm_name,
    c.complexity_name,
    c.big_o,
    c.big_omega,
    c.big_theta,
    a.best_case,
    a.average_case,
    a.worst_case,
    a.auxiliary_space,
    a.stable,
    c.growth_rank
FROM algorithms a
JOIN complexity_definitions c
    ON c.complexity_id = a.complexity_id;

-- ------------------------------------------------------------
-- 11. WORKLOAD REPORTING VIEW
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW workload_performance_report AS
SELECT
    w.workload_code,
    a.algorithm_name,
    c.complexity_name,
    c.big_o,
    p.policy_name,
    w.input_size,
    w.expected_operations,
    w.measured_operations,
    w.elapsed_ms,
    w.status,
    w.rejection_reason,
    w.submitted_by,
    w.submitted_at,
    w.completed_at
FROM workloads w
JOIN algorithms a
    ON a.algorithm_id = w.algorithm_id
JOIN complexity_definitions c
    ON c.complexity_id = a.complexity_id
JOIN performance_policies p
    ON p.policy_id = w.policy_id;

-- ------------------------------------------------------------
-- 12. GROWTH FUNCTION EVALUATION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION evaluate_growth(
    p_input_size BIGINT
)
RETURNS TABLE (
    growth_function TEXT,
    estimated_operations NUMERIC
)
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    n NUMERIC;
BEGIN
    IF p_input_size < 0 OR p_input_size > 1000000 THEN
        RAISE EXCEPTION 'Input size must be between 0 and 1000000.';
    END IF;

    n := p_input_size;

    RETURN QUERY
    SELECT 'O(1)'::TEXT, 1::NUMERIC
    UNION ALL
    SELECT 'O(log n)', CASE
        WHEN n <= 1 THEN 0::NUMERIC
        ELSE LN(n) / LN(2)
    END
    UNION ALL
    SELECT 'O(n)', n
    UNION ALL
    SELECT 'O(n log n)', CASE
        WHEN n <= 1 THEN 0::NUMERIC
        ELSE n * LN(n) / LN(2)
    END
    UNION ALL
    SELECT 'O(n^2)', n * n
    UNION ALL
    SELECT 'O(n^3)', n * n * n;
END;
$$;

-- ------------------------------------------------------------
-- 13. ASYMPTOTIC BOUND EVALUATION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION check_asymptotic_bound(
    p_measured NUMERIC,
    p_reference NUMERIC,
    p_constant NUMERIC,
    p_type bound_type
)
RETURNS BOOLEAN
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    IF p_measured < 0 OR p_reference < 0 OR p_constant <= 0 THEN
        RAISE EXCEPTION 'Invalid bound comparison values.';
    END IF;

    IF p_reference = 0 THEN
        IF p_type = 'UPPER' THEN
            RETURN p_measured = 0;
        ELSIF p_type = 'LOWER' THEN
            RETURN p_measured >= 0;
        ELSE
            RETURN p_measured = 0;
        END IF;
    END IF;

    IF p_type = 'UPPER' THEN
        RETURN p_measured <= p_constant * p_reference;
    ELSIF p_type = 'LOWER' THEN
        RETURN p_measured >= p_reference / p_constant;
    ELSE
        RETURN
            p_measured <= p_constant * p_reference
            AND
            p_measured >= p_reference / p_constant;
    END IF;
END;
$$;

-- ------------------------------------------------------------
-- 14. AGGREGATION AND REPORTING
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW complexity_workload_statistics AS
SELECT
    c.complexity_name,
    c.big_o,
    COUNT(w.workload_id) AS total_workloads,
    COUNT(*) FILTER (
        WHERE w.status = 'COMPLETED'
    ) AS completed_workloads,
    COUNT(*) FILTER (
        WHERE w.status = 'REJECTED'
    ) AS rejected_workloads,
    COUNT(*) FILTER (
        WHERE w.status = 'FAILED'
    ) AS failed_workloads,
    AVG(w.elapsed_ms) FILTER (
        WHERE w.status = 'COMPLETED'
    ) AS average_execution_ms,
    MAX(w.input_size) AS maximum_input_size
FROM complexity_definitions c
LEFT JOIN algorithms a
    ON a.complexity_id = c.complexity_id
LEFT JOIN workloads w
    ON w.algorithm_id = a.algorithm_id
GROUP BY
    c.complexity_name,
    c.big_o,
    c.growth_rank;

-- ------------------------------------------------------------
-- 15. ELIGIBILITY DETERMINATION FUNCTION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION is_workload_eligible(
    p_workload_code VARCHAR
)
RETURNS BOOLEAN
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    current_status workload_status;
BEGIN
    SELECT status
    INTO current_status
    FROM workloads
    WHERE workload_code = p_workload_code;

    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;

    RETURN current_status = 'ACCEPTED';
END;
$$;

-- ------------------------------------------------------------
-- 16. RETRIEVAL QUERIES
-- ------------------------------------------------------------

-- Algorithm complexity catalog.
SELECT *
FROM algorithm_complexity_report
ORDER BY growth_rank;

-- Workload details.
SELECT *
FROM workload_performance_report
ORDER BY workload_code;

-- Input-size growth comparison.
SELECT *
FROM evaluate_growth(1000);

-- Aggregate performance report.
SELECT *
FROM complexity_workload_statistics
ORDER BY
    CASE complexity_name
        WHEN 'CONSTANT' THEN 1
        WHEN 'LOGARITHMIC' THEN 2
        WHEN 'LINEAR' THEN 3
        WHEN 'LINEARITHMIC' THEN 4
        WHEN 'QUADRATIC' THEN 5
        WHEN 'CUBIC' THEN 6
        WHEN 'EXPONENTIAL' THEN 7
    END;

-- Eligibility evaluation.
SELECT
    workload_code,
    is_workload_eligible(workload_code) AS eligible
FROM workloads
ORDER BY workload_code;

-- Formal upper-bound check.
SELECT check_asymptotic_bound(
    1000,
    1000,
    1,
    'UPPER'
) AS linear_upper_bound_valid;

-- Formal tight-bound check.
SELECT check_asymptotic_bound(
    1000,
    1000,
    1,
    'TIGHT'
) AS linear_tight_bound_valid;

-- ------------------------------------------------------------
-- 17. TRANSACTION AND FAILURE HANDLING
-- ------------------------------------------------------------

SAVEPOINT before_invalid_workload;

-- This workload is rejected because its quadratic complexity
-- is not permitted by STANDARD_API.

INSERT INTO workloads (
    workload_code,
    algorithm_id,
    policy_id,
    input_size,
    expected_operations,
    submitted_by
)
SELECT
    'JOB-008',
    a.algorithm_id,
    p.policy_id,
    100,
    10000,
    'developer_g'
FROM algorithms a
CROSS JOIN performance_policies p
WHERE a.algorithm_name = 'Bubble Sort'
AND p.policy_name = 'STANDARD_API';

RELEASE SAVEPOINT before_invalid_workload;

-- The trigger records JOB-008 as REJECTED instead of accepting it.

SELECT
    workload_code,
    status,
    rejection_reason
FROM workloads
WHERE workload_code = 'JOB-008';

COMMIT;

-- ------------------------------------------------------------
-- 18. DATABASE PERFORMANCE INSPECTION
-- ------------------------------------------------------------

EXPLAIN (COSTS, VERBOSE)
SELECT *
FROM workloads
WHERE status = 'COMPLETED'
ORDER BY submitted_at DESC;

-- Statistics and execution plans are database-specific.
-- Estimated plan cost is not the same as algorithmic complexity.
