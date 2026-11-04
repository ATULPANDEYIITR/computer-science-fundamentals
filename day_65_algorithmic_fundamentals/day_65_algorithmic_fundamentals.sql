-- ============================================================
-- ALGORITHM FUNDAMENTALS
-- PostgreSQL 15+
--
-- Algorithm registry, correctness contracts, test execution,
-- performance measurements and complexity evaluation.
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS algorithm_lab;

SET search_path TO algorithm_lab, public;

-- ------------------------------------------------------------
-- 1. DOMAIN TYPES
-- ------------------------------------------------------------

CREATE TYPE algorithm_category AS ENUM (
    'SEARCHING',
    'SORTING',
    'GRAPH',
    'OPTIMIZATION'
);

CREATE TYPE complexity_class AS ENUM (
    'O(1)',
    'O(log n)',
    'O(n)',
    'O(n log n)',
    'O(n^2)',
    'O(V + E)',
    'O((V + E) log V)'
);

CREATE TYPE execution_status AS ENUM (
    'REGISTERED',
    'RUNNING',
    'PASSED',
    'FAILED',
    'REJECTED'
);

CREATE TYPE test_case_status AS ENUM (
    'PENDING',
    'PASSED',
    'FAILED'
);

-- ------------------------------------------------------------
-- 2. ALGORITHM REGISTRY
-- ------------------------------------------------------------

CREATE TABLE algorithms (
    algorithm_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    algorithm_name VARCHAR(100) NOT NULL UNIQUE,

    category algorithm_category NOT NULL,

    time_complexity complexity_class NOT NULL,

    space_complexity complexity_class NOT NULL,

    description TEXT NOT NULL,

    preconditions TEXT NOT NULL,

    postconditions TEXT NOT NULL,

    stable BOOLEAN NOT NULL DEFAULT FALSE,

    in_place BOOLEAN NOT NULL DEFAULT FALSE,

    version INTEGER NOT NULL DEFAULT 1
        CHECK (version > 0),

    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (length(trim(algorithm_name)) > 0)
);

CREATE INDEX idx_algorithms_category_enabled
ON algorithms(category, enabled);

-- ------------------------------------------------------------
-- 3. ALGORITHM IMPLEMENTATION VERSIONS
-- ------------------------------------------------------------

CREATE TABLE algorithm_versions (
    version_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    algorithm_id BIGINT NOT NULL
        REFERENCES algorithms(algorithm_id),

    version_number INTEGER NOT NULL
        CHECK (version_number > 0),

    implementation_language VARCHAR(30) NOT NULL,

    implementation_hash CHAR(64) NOT NULL,

    approved BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (algorithm_id, version_number),

    UNIQUE (implementation_hash)
);

-- ------------------------------------------------------------
-- 4. ALGORITHM TEST CASES
-- ------------------------------------------------------------

CREATE TABLE algorithm_test_cases (
    test_case_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    algorithm_id BIGINT NOT NULL
        REFERENCES algorithms(algorithm_id),

    case_name VARCHAR(150) NOT NULL,

    input_data JSONB NOT NULL,

    expected_output JSONB,

    expected_behavior VARCHAR(30) NOT NULL
        CHECK (
            expected_behavior IN (
                'EXACT',
                'VALIDATION_ERROR',
                'UNREACHABLE',
                'PROPERTY'
            )
        ),

    expected_property TEXT,

    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (algorithm_id, case_name)
);

CREATE INDEX idx_test_cases_algorithm_enabled
ON algorithm_test_cases(algorithm_id, enabled);

CREATE INDEX idx_test_cases_input
ON algorithm_test_cases USING GIN(input_data);

-- ------------------------------------------------------------
-- 5. EXECUTION RECORDS
-- ------------------------------------------------------------

CREATE TABLE algorithm_executions (
    execution_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    algorithm_id BIGINT NOT NULL
        REFERENCES algorithms(algorithm_id),

    version_id BIGINT
        REFERENCES algorithm_versions(version_id),

    execution_status execution_status NOT NULL DEFAULT 'REGISTERED',

    input_size BIGINT NOT NULL DEFAULT 0
        CHECK (input_size >= 0),

    comparison_count BIGINT NOT NULL DEFAULT 0
        CHECK (comparison_count >= 0),

    operation_count BIGINT NOT NULL DEFAULT 0
        CHECK (operation_count >= 0),

    elapsed_microseconds NUMERIC(18, 4),

    memory_bytes BIGINT
        CHECK (memory_bytes IS NULL OR memory_bytes >= 0),

    input_hash CHAR(64),

    output_hash CHAR(64),

    error_message TEXT,

    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    completed_at TIMESTAMPTZ,

    CHECK (
        elapsed_microseconds IS NULL
        OR elapsed_microseconds >= 0
    ),

    CHECK (
        (execution_status = 'FAILED' AND error_message IS NOT NULL)
        OR execution_status <> 'FAILED'
    )
);

CREATE INDEX idx_execution_algorithm_date
ON algorithm_executions(
    algorithm_id,
    executed_at DESC
);

CREATE INDEX idx_execution_status_date
ON algorithm_executions(
    execution_status,
    executed_at DESC
);

-- ------------------------------------------------------------
-- 6. TEST EXECUTION RESULTS
-- ------------------------------------------------------------

CREATE TABLE algorithm_test_results (
    result_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    execution_id BIGINT NOT NULL
        REFERENCES algorithm_executions(execution_id),

    test_case_id BIGINT NOT NULL
        REFERENCES algorithm_test_cases(test_case_id),

    status test_case_status NOT NULL DEFAULT 'PENDING',

    actual_output JSONB,

    failure_reason TEXT,

    duration_microseconds NUMERIC(18, 4)
        CHECK (
            duration_microseconds IS NULL
            OR duration_microseconds >= 0
        ),

    tested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (execution_id, test_case_id),

    CHECK (
        (status = 'FAILED' AND failure_reason IS NOT NULL)
        OR status <> 'FAILED'
    )
);

CREATE INDEX idx_test_results_status
ON algorithm_test_results(status, tested_at DESC);

-- ------------------------------------------------------------
-- 7. EXECUTION AUDIT
-- ------------------------------------------------------------

CREATE TABLE execution_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    execution_id BIGINT NOT NULL
        REFERENCES algorithm_executions(execution_id),

    previous_status execution_status,

    new_status execution_status NOT NULL,

    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    details TEXT
);

CREATE OR REPLACE FUNCTION audit_execution_status()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.execution_status IS DISTINCT FROM OLD.execution_status
    THEN
        INSERT INTO execution_audit (
            execution_id,
            previous_status,
            new_status,
            details
        )
        VALUES (
            NEW.execution_id,
            OLD.execution_status,
            NEW.execution_status,
            'Execution state transition'
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_execution_status_audit
AFTER UPDATE OF execution_status
ON algorithm_executions
FOR EACH ROW
EXECUTE FUNCTION audit_execution_status();

-- ------------------------------------------------------------
-- 8. VALIDATION FUNCTION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_execution(
    p_execution_id BIGINT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    v_status execution_status;
    v_algorithm_enabled BOOLEAN;
BEGIN
    SELECT
        e.execution_status,
        a.enabled
    INTO
        v_status,
        v_algorithm_enabled
    FROM algorithm_executions e
    JOIN algorithms a
        ON a.algorithm_id = e.algorithm_id
    WHERE e.execution_id = p_execution_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Execution % does not exist',
            p_execution_id;
    END IF;

    IF NOT v_algorithm_enabled THEN
        RAISE EXCEPTION
            'Algorithm is disabled';
    END IF;

    IF v_status NOT IN ('REGISTERED', 'RUNNING') THEN
        RAISE EXCEPTION
            'Execution cannot be validated in state %',
            v_status;
    END IF;

    RETURN TRUE;
END;
$$;

-- ------------------------------------------------------------
-- 9. CONTROLLED STATE TRANSITION PROCEDURE
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE transition_execution(
    p_execution_id BIGINT,
    p_new_status execution_status,
    p_error_message TEXT DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_current execution_status;
BEGIN
    SELECT execution_status
    INTO v_current
    FROM algorithm_executions
    WHERE execution_id = p_execution_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Execution does not exist: %',
            p_execution_id;
    END IF;

    IF NOT (
        (v_current = 'REGISTERED'
            AND p_new_status IN ('RUNNING', 'REJECTED'))
        OR
        (v_current = 'RUNNING'
            AND p_new_status IN ('PASSED', 'FAILED'))
    ) THEN
        RAISE EXCEPTION
            'Invalid transition: % -> %',
            v_current,
            p_new_status;
    END IF;

    IF p_new_status = 'FAILED'
       AND (
           p_error_message IS NULL
           OR length(trim(p_error_message)) = 0
       )
    THEN
        RAISE EXCEPTION
            'Failure requires an error message';
    END IF;

    UPDATE algorithm_executions
    SET
        execution_status = p_new_status,
        error_message = p_error_message,
        completed_at = CASE
            WHEN p_new_status IN ('PASSED', 'FAILED', 'REJECTED')
            THEN NOW()
            ELSE NULL
        END
    WHERE execution_id = p_execution_id;
END;
$$;

-- ------------------------------------------------------------
-- 10. CORRECTNESS EVALUATION FUNCTION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION evaluate_execution(
    p_execution_id BIGINT
)
RETURNS TABLE (
    total_cases BIGINT,
    passed_cases BIGINT,
    failed_cases BIGINT,
    success_percentage NUMERIC
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        COUNT(*) AS total_cases,

        COUNT(*) FILTER (
            WHERE status = 'PASSED'
        ) AS passed_cases,

        COUNT(*) FILTER (
            WHERE status = 'FAILED'
        ) AS failed_cases,

        COALESCE(
            ROUND(
                100.0 *
                COUNT(*) FILTER (
                    WHERE status = 'PASSED'
                ) /
                NULLIF(
                    COUNT(*) FILTER (
                        WHERE status IN ('PASSED', 'FAILED')
                    ),
                    0
                ),
                2
            ),
            0
        ) AS success_percentage

    FROM algorithm_test_results
    WHERE execution_id = p_execution_id;
$$;

-- ------------------------------------------------------------
-- 11. REGISTER ALGORITHMS
-- ------------------------------------------------------------

INSERT INTO algorithms (
    algorithm_name,
    category,
    time_complexity,
    space_complexity,
    description,
    preconditions,
    postconditions,
    stable,
    in_place
)
VALUES
(
    'Binary Search',
    'SEARCHING',
    'O(log n)',
    'O(1)',
    'Searches an ascending sorted sequence.',
    'Input must be sorted in ascending order.',
    'Returns a matching position or -1.',
    FALSE,
    TRUE
),
(
    'Merge Sort',
    'SORTING',
    'O(n log n)',
    'O(n)',
    'Stable divide-and-conquer sorting.',
    'Input is a finite sequence of comparable values.',
    'Returns all input elements in ascending order.',
    TRUE,
    FALSE
),
(
    'Insertion Sort',
    'SORTING',
    'O(n^2)',
    'O(1)',
    'Incrementally inserts values into a sorted prefix.',
    'Input is a finite sequence of comparable values.',
    'Returns all input elements in ascending order.',
    TRUE,
    TRUE
),
(
    'Dijkstra',
    'GRAPH',
    'O((V + E) log V)',
    'O(V + E)',
    'Computes single-source shortest paths.',
    'All edge weights must be nonnegative.',
    'Returns shortest distances from the source.',
    FALSE,
    FALSE
);

-- ------------------------------------------------------------
-- 12. REGISTER IMPLEMENTATION VERSIONS
-- ------------------------------------------------------------

INSERT INTO algorithm_versions (
    algorithm_id,
    version_number,
    implementation_language,
    implementation_hash,
    approved
)
SELECT
    algorithm_id,
    1,
    'Python',
    encode(
        sha256(
            convert_to(
                algorithm_name || '-python-v1',
                'UTF8'
            )
        ),
        'hex'
    ),
    TRUE
FROM algorithms;

-- ------------------------------------------------------------
-- 13. REGISTER VALID AND INVALID TEST CASES
-- ------------------------------------------------------------

INSERT INTO algorithm_test_cases (
    algorithm_id,
    case_name,
    input_data,
    expected_output,
    expected_behavior,
    expected_property
)
SELECT
    algorithm_id,
    cases.case_name,
    cases.input_data,
    cases.expected_output,
    cases.expected_behavior,
    cases.expected_property
FROM algorithms
CROSS JOIN (
    VALUES
    (
        'Empty input',
        '{"values":[]}'::jsonb,
        '[]'::jsonb,
        'EXACT',
        'Output contains zero elements'
    ),
    (
        'Reverse order',
        '{"values":[5,4,3,2,1]}'::jsonb,
        '[1,2,3,4,5]'::jsonb,
        'EXACT',
        'Output is ascending'
    ),
    (
        'Repeated values',
        '{"values":[4,4,2,2,1]}'::jsonb,
        '[1,2,2,4,4]'::jsonb,
        'EXACT',
        'Element multiplicities are preserved'
    ),
    (
        'Negative values',
        '{"values":[-5,0,8,-2]}'::jsonb,
        '[-5,-2,0,8]'::jsonb,
        'EXACT',
        'Negative and positive values are ordered'
    )
) AS cases(
    case_name,
    input_data,
    expected_output,
    expected_behavior,
    expected_property
)
WHERE algorithms.algorithm_name IN (
    'Merge Sort',
    'Insertion Sort'
);

INSERT INTO algorithm_test_cases (
    algorithm_id,
    case_name,
    input_data,
    expected_output,
    expected_behavior,
    expected_property
)
SELECT
    algorithm_id,
    'Unsorted input rejected',
    '{"values":[5,2,8],"target":2}'::jsonb,
    NULL,
    'VALIDATION_ERROR',
    'Binary search rejects unsorted input'
FROM algorithms
WHERE algorithm_name = 'Binary Search';

INSERT INTO algorithm_test_cases (
    algorithm_id,
    case_name,
    input_data,
    expected_output,
    expected_behavior,
    expected_property
)
SELECT
    algorithm_id,
    'Negative edge rejected',
    '{"source":"A","edges":[["A","B",-1]]}'::jsonb,
    NULL,
    'VALIDATION_ERROR',
    'Dijkstra rejects negative edge weights'
FROM algorithms
WHERE algorithm_name = 'Dijkstra';

-- ------------------------------------------------------------
-- 14. CREATE EXECUTION RECORDS
-- ------------------------------------------------------------

INSERT INTO algorithm_executions (
    algorithm_id,
    version_id,
    execution_status,
    input_size,
    comparison_count,
    operation_count,
    elapsed_microseconds,
    input_hash,
    output_hash
)
SELECT
    a.algorithm_id,
    v.version_id,
    'REGISTERED',
    1000,
    0,
    0,
    NULL,
    repeat('a', 64),
    NULL
FROM algorithms a
JOIN algorithm_versions v
    ON v.algorithm_id = a.algorithm_id
WHERE a.algorithm_name = 'Merge Sort'
  AND v.version_number = 1;

-- ------------------------------------------------------------
-- 15. PROCESS EXECUTION STATE
-- ------------------------------------------------------------

DO $$
DECLARE
    v_execution_id BIGINT;
BEGIN
    SELECT execution_id
    INTO v_execution_id
    FROM algorithm_executions
    WHERE execution_status = 'REGISTERED'
    ORDER BY execution_id
    LIMIT 1;

    IF v_execution_id IS NOT NULL THEN
        PERFORM validate_execution(v_execution_id);

        CALL transition_execution(
            v_execution_id,
            'RUNNING'
        );

        CALL transition_execution(
            v_execution_id,
            'PASSED'
        );
    END IF;
END;
$$;

-- ------------------------------------------------------------
-- 16. CREATE TEST RESULTS
-- ------------------------------------------------------------

INSERT INTO algorithm_test_results (
    execution_id,
    test_case_id,
    status,
    actual_output,
    duration_microseconds
)
SELECT
    e.execution_id,
    t.test_case_id,
    'PASSED',
    t.expected_output,
    125.50
FROM algorithm_executions e
JOIN algorithms a
    ON a.algorithm_id = e.algorithm_id
JOIN algorithm_test_cases t
    ON t.algorithm_id = a.algorithm_id
WHERE a.algorithm_name = 'Merge Sort'
  AND e.execution_status = 'PASSED'
  AND t.enabled = TRUE;

-- ------------------------------------------------------------
-- 17. DEMONSTRATE FAILURE RECORD
-- ------------------------------------------------------------

INSERT INTO algorithm_executions (
    algorithm_id,
    execution_status,
    input_size,
    error_message,
    completed_at
)
SELECT
    algorithm_id,
    'FAILED',
    100,
    'Input validation failed: sequence was not sorted.',
    NOW()
FROM algorithms
WHERE algorithm_name = 'Binary Search';

-- ------------------------------------------------------------
-- 18. RETRIEVAL QUERY
-- ------------------------------------------------------------

SELECT
    algorithm_name,
    category,
    time_complexity,
    space_complexity,
    stable,
    in_place,
    enabled
FROM algorithms
ORDER BY category, algorithm_name;

-- ------------------------------------------------------------
-- 19. VALIDATION QUERY
-- ------------------------------------------------------------

SELECT
    algorithm_name,
    CASE
        WHEN enabled AND
             length(trim(preconditions)) > 0 AND
             length(trim(postconditions)) > 0
        THEN 'VALID'
        ELSE 'INVALID'
    END AS contract_status
FROM algorithms;

-- ------------------------------------------------------------
-- 20. CORRECTNESS REPORT
-- ------------------------------------------------------------

SELECT
    a.algorithm_name,
    e.execution_id,
    r.total_cases,
    r.passed_cases,
    r.failed_cases,
    r.success_percentage
FROM algorithm_executions e
JOIN algorithms a
    ON a.algorithm_id = e.algorithm_id
CROSS JOIN LATERAL evaluate_execution(
    e.execution_id
) r
ORDER BY e.executed_at DESC;

-- ------------------------------------------------------------
-- 21. PERFORMANCE AGGREGATION
-- ------------------------------------------------------------

SELECT
    a.algorithm_name,
    a.time_complexity,
    COUNT(e.execution_id) AS total_executions,
    ROUND(
        AVG(e.elapsed_microseconds),
        2
    ) AS average_microseconds,
    MAX(e.elapsed_microseconds) AS maximum_microseconds,
    MAX(e.input_size) AS maximum_input_size,
    SUM(e.comparison_count) AS total_comparisons,
    SUM(e.operation_count) AS total_operations
FROM algorithms a
LEFT JOIN algorithm_executions e
    ON e.algorithm_id = a.algorithm_id
GROUP BY
    a.algorithm_id,
    a.algorithm_name,
    a.time_complexity
ORDER BY a.algorithm_name;

-- ------------------------------------------------------------
-- 22. EXECUTION FAILURE REPORT
-- ------------------------------------------------------------

SELECT
    a.algorithm_name,
    e.execution_id,
    e.execution_status,
    e.error_message,
    e.executed_at
FROM algorithm_executions e
JOIN algorithms a
    ON a.algorithm_id = e.algorithm_id
WHERE e.execution_status IN ('FAILED', 'REJECTED')
ORDER BY e.executed_at DESC;

-- ------------------------------------------------------------
-- 23. EXECUTION AUDIT REPORT
-- ------------------------------------------------------------

SELECT
    execution_id,
    previous_status,
    new_status,
    changed_at,
    details
FROM execution_audit
ORDER BY changed_at DESC;

-- ------------------------------------------------------------
-- 24. COMPLEXITY COMPARISON VIEW
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW algorithm_complexity_report AS
SELECT
    algorithm_name,
    category,
    time_complexity,
    space_complexity,
    CASE time_complexity
        WHEN 'O(1)' THEN 1
        WHEN 'O(log n)' THEN 2
        WHEN 'O(n)' THEN 3
        WHEN 'O(n log n)' THEN 4
        WHEN 'O(n^2)' THEN 5
        WHEN 'O(V + E)' THEN 6
        WHEN 'O((V + E) log V)' THEN 7
        ELSE 99
    END AS comparison_group
FROM algorithms;

SELECT *
FROM algorithm_complexity_report
ORDER BY comparison_group;

-- ------------------------------------------------------------
-- 25. ELIGIBILITY DETERMINATION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION algorithm_is_eligible(
    p_algorithm_id BIGINT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_enabled BOOLEAN;
    v_has_approved_version BOOLEAN;
    v_has_test_cases BOOLEAN;
BEGIN
    SELECT enabled
    INTO v_enabled
    FROM algorithms
    WHERE algorithm_id = p_algorithm_id;

    IF NOT FOUND OR NOT v_enabled THEN
        RETURN FALSE;
    END IF;

    SELECT EXISTS (
        SELECT 1
        FROM algorithm_versions
        WHERE algorithm_id = p_algorithm_id
          AND approved = TRUE
    )
    INTO v_has_approved_version;

    SELECT EXISTS (
        SELECT 1
        FROM algorithm_test_cases
        WHERE algorithm_id = p_algorithm_id
          AND enabled = TRUE
    )
    INTO v_has_test_cases;

    RETURN v_has_approved_version
       AND v_has_test_cases;
END;
$$;

SELECT
    algorithm_name,
    algorithm_is_eligible(algorithm_id) AS eligible_for_execution
FROM algorithms
ORDER BY algorithm_name;

-- ------------------------------------------------------------
-- 26. CTE: EXECUTION QUALITY RANKING
-- ------------------------------------------------------------

WITH execution_quality AS (
    SELECT
        a.algorithm_name,
        e.execution_id,
        e.input_size,
        e.elapsed_microseconds,
        e.execution_status,
        CASE
            WHEN e.execution_status = 'PASSED' THEN 1
            ELSE 0
        END AS successful
    FROM algorithm_executions e
    JOIN algorithms a
        ON a.algorithm_id = e.algorithm_id
),
ranked_quality AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY algorithm_name
            ORDER BY
                successful DESC,
                elapsed_microseconds ASC NULLS LAST
        ) AS execution_rank
    FROM execution_quality
)
SELECT *
FROM ranked_quality
ORDER BY algorithm_name, execution_rank;

-- ------------------------------------------------------------
-- 27. TRANSACTIONAL STATE FAILURE EXAMPLE
-- ------------------------------------------------------------

-- The nested transaction rolls back without affecting the
-- registered demonstration records.

SAVEPOINT validation_demo;

DO $$
BEGIN
    BEGIN
        CALL transition_execution(
            -999,
            'RUNNING'
        );
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE
                'Expected failure handled: %',
                SQLERRM;
    END;
END;
$$;

ROLLBACK TO SAVEPOINT validation_demo;

RELEASE SAVEPOINT validation_demo;

COMMIT;
