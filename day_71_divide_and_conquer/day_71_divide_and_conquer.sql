-- ============================================================
-- DIVIDE AND CONQUER ALGORITHM MANAGEMENT DATABASE
-- PostgreSQL 14+
--
-- Domain:
-- Algorithm definitions
-- Decomposition strategies
-- Recurrence relations
-- Algorithm executions
-- Recursive call measurements
-- Performance observations
-- Complexity classification
-- Validation and reporting
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS divide_conquer;

SET search_path TO divide_conquer, public;

-- ------------------------------------------------------------
-- 1. DOMAIN TYPES
-- ------------------------------------------------------------

CREATE TYPE algorithm_category AS ENUM (
    'SEARCHING',
    'SORTING',
    'OPTIMIZATION',
    'MULTIPLICATION'
);

CREATE TYPE execution_status AS ENUM (
    'QUEUED',
    'RUNNING',
    'COMPLETED',
    'FAILED',
    'CANCELLED'
);

CREATE TYPE complexity_class AS ENUM (
    'LOGARITHMIC',
    'LINEAR',
    'LINEARITHMIC',
    'QUADRATIC',
    'POLYNOMIAL',
    'EXPONENTIAL',
    'UNKNOWN'
);

-- ------------------------------------------------------------
-- 2. ALGORITHM CATALOG
-- ------------------------------------------------------------

CREATE TABLE algorithms (
    algorithm_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    algorithm_name VARCHAR(100) NOT NULL UNIQUE,
    category algorithm_category NOT NULL,
    description TEXT NOT NULL,
    stable BOOLEAN NOT NULL DEFAULT FALSE,
    in_place BOOLEAN NOT NULL DEFAULT FALSE,
    average_complexity VARCHAR(100) NOT NULL,
    worst_complexity VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE recurrence_models (
    recurrence_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    algorithm_id BIGINT NOT NULL REFERENCES algorithms(algorithm_id),
    recurrence_expression TEXT NOT NULL,
    subproblem_count INTEGER NOT NULL CHECK (subproblem_count >= 1),
    division_factor INTEGER NOT NULL CHECK (division_factor >= 2),
    combine_exponent NUMERIC(10, 4) NOT NULL
        CHECK (combine_exponent >= 0),
    critical_exponent NUMERIC(20, 8) NOT NULL,
    complexity_description VARCHAR(150) NOT NULL,
    assumptions TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (algorithm_id, recurrence_expression)
);

-- ------------------------------------------------------------
-- 3. DECOMPOSITION STRATEGIES
-- ------------------------------------------------------------

CREATE TABLE decomposition_strategies (
    strategy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    algorithm_id BIGINT NOT NULL REFERENCES algorithms(algorithm_id),
    step_number INTEGER NOT NULL CHECK (step_number > 0),
    phase VARCHAR(20) NOT NULL CHECK (
        phase IN ('DIVIDE', 'CONQUER', 'COMBINE')
    ),
    operation_description TEXT NOT NULL,
    expected_cost VARCHAR(100),
    UNIQUE (algorithm_id, step_number)
);

-- ------------------------------------------------------------
-- 4. EXECUTION RECORDS
-- ------------------------------------------------------------

CREATE TABLE algorithm_executions (
    execution_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    algorithm_id BIGINT NOT NULL REFERENCES algorithms(algorithm_id),
    recurrence_id BIGINT REFERENCES recurrence_models(recurrence_id),
    input_size BIGINT NOT NULL CHECK (input_size >= 0),
    input_fingerprint VARCHAR(128),
    execution_status execution_status NOT NULL DEFAULT 'QUEUED',
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    elapsed_microseconds BIGINT CHECK (
        elapsed_microseconds IS NULL OR elapsed_microseconds >= 0
    ),
    recursive_calls BIGINT NOT NULL DEFAULT 0
        CHECK (recursive_calls >= 0),
    peak_memory_bytes BIGINT CHECK (
        peak_memory_bytes IS NULL OR peak_memory_bytes >= 0
    ),
    error_code VARCHAR(100),
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        (execution_status = 'RUNNING' AND started_at IS NOT NULL
            AND completed_at IS NULL)
        OR
        (execution_status IN ('QUEUED', 'CANCELLED')
            AND completed_at IS NULL)
        OR
        (execution_status IN ('COMPLETED', 'FAILED')
            AND started_at IS NOT NULL
            AND completed_at IS NOT NULL)
    ),

    CHECK (
        execution_status <> 'COMPLETED'
        OR elapsed_microseconds IS NOT NULL
    )
);

CREATE INDEX idx_execution_algorithm
    ON algorithm_executions(algorithm_id, created_at DESC);

CREATE INDEX idx_execution_status
    ON algorithm_executions(execution_status, created_at DESC);

CREATE INDEX idx_execution_input_size
    ON algorithm_executions(algorithm_id, input_size);

-- ------------------------------------------------------------
-- 5. RECURSION TRACE
-- ------------------------------------------------------------

CREATE TABLE recursion_traces (
    trace_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    execution_id BIGINT NOT NULL
        REFERENCES algorithm_executions(execution_id)
        ON DELETE CASCADE,
    parent_trace_id BIGINT REFERENCES recursion_traces(trace_id),
    depth INTEGER NOT NULL CHECK (depth >= 0),
    subproblem_size BIGINT NOT NULL CHECK (subproblem_size >= 0),
    operation VARCHAR(30) NOT NULL CHECK (
        operation IN ('DIVIDE', 'BASE_CASE', 'COMBINE')
    ),
    execution_sequence BIGINT NOT NULL CHECK (execution_sequence > 0),
    UNIQUE (execution_id, execution_sequence)
);

CREATE INDEX idx_trace_execution_depth
    ON recursion_traces(execution_id, depth);

-- ------------------------------------------------------------
-- 6. PERFORMANCE OBSERVATIONS
-- ------------------------------------------------------------

CREATE TABLE performance_observations (
    observation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    execution_id BIGINT NOT NULL
        REFERENCES algorithm_executions(execution_id)
        ON DELETE CASCADE,
    input_size BIGINT NOT NULL CHECK (input_size >= 0),
    elapsed_microseconds BIGINT NOT NULL CHECK (
        elapsed_microseconds >= 0
    ),
    recursive_calls BIGINT NOT NULL CHECK (recursive_calls >= 0),
    environment_name VARCHAR(100) NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_observation_size
    ON performance_observations(input_size, recorded_at);

-- ------------------------------------------------------------
-- 7. FUNCTION: CALCULATE CRITICAL EXPONENT
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION calculate_critical_exponent(
    p_a INTEGER,
    p_b INTEGER
)
RETURNS NUMERIC
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
BEGIN
    IF p_a < 1 OR p_b < 2 THEN
        RAISE EXCEPTION
            'Invalid recurrence: a must be >= 1 and b must be >= 2';
    END IF;

    RETURN ROUND(
        LN(p_a::NUMERIC) / LN(p_b::NUMERIC),
        8
    );
END;
$$;

-- ------------------------------------------------------------
-- 8. FUNCTION: CLASSIFY RECURRENCE
--
-- For T(n) = aT(n/b) + Theta(n^d).
-- The regularity condition is assumed for case 3.
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION classify_recurrence(
    p_a INTEGER,
    p_b INTEGER,
    p_d NUMERIC
)
RETURNS TEXT
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
DECLARE
    v_critical NUMERIC;
    v_epsilon NUMERIC := 0.00000001;
BEGIN
    IF p_a < 1 OR p_b < 2 OR p_d < 0 THEN
        RAISE EXCEPTION 'Invalid recurrence parameters';
    END IF;

    v_critical := calculate_critical_exponent(p_a, p_b);

    IF p_d < v_critical - v_epsilon THEN
        RETURN 'Theta(n^' || ROUND(v_critical, 3) || ')';
    ELSIF ABS(p_d - v_critical) <= v_epsilon THEN
        RETURN 'Theta(n^' || ROUND(v_critical, 3) || ' log n)';
    ELSE
        RETURN 'Theta(n^' || ROUND(p_d, 3) || ')';
    END IF;
END;
$$;

-- ------------------------------------------------------------
-- 9. EXECUTION STATE VALIDATION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_execution_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN

        IF OLD.execution_status IN (
            'COMPLETED', 'FAILED', 'CANCELLED'
        ) THEN
            RAISE EXCEPTION
                'Terminal execution states cannot be modified';
        END IF;

        IF NEW.execution_status = 'RUNNING'
           AND OLD.execution_status <> 'QUEUED' THEN
            RAISE EXCEPTION
                'Only queued executions can start';
        END IF;

        IF NEW.execution_status IN ('COMPLETED', 'FAILED')
           AND OLD.execution_status <> 'RUNNING' THEN
            RAISE EXCEPTION
                'Execution must be running before termination';
        END IF;

        IF NEW.execution_status = 'CANCELLED'
           AND OLD.execution_status NOT IN ('QUEUED', 'RUNNING') THEN
            RAISE EXCEPTION
                'Execution cannot be cancelled from this state';
        END IF;

    END IF;

    IF NEW.execution_status = 'RUNNING'
       AND NEW.started_at IS NULL THEN
        NEW.started_at := CURRENT_TIMESTAMP;
    END IF;

    IF NEW.execution_status IN ('COMPLETED', 'FAILED')
       AND NEW.completed_at IS NULL THEN
        NEW.completed_at := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_execution_transition
BEFORE UPDATE ON algorithm_executions
FOR EACH ROW
EXECUTE FUNCTION validate_execution_transition();

-- ------------------------------------------------------------
-- 10. PROCEDURE: START EXECUTION
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE start_execution(
    p_execution_id BIGINT
)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE algorithm_executions
    SET execution_status = 'RUNNING',
        started_at = CURRENT_TIMESTAMP
    WHERE execution_id = p_execution_id
      AND execution_status = 'QUEUED';

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Execution % is missing or not queued',
            p_execution_id;
    END IF;
END;
$$;

-- ------------------------------------------------------------
-- 11. PROCEDURE: COMPLETE EXECUTION
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE complete_execution(
    p_execution_id BIGINT,
    p_elapsed BIGINT,
    p_recursive_calls BIGINT
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_elapsed < 0 OR p_recursive_calls < 0 THEN
        RAISE EXCEPTION 'Metrics cannot be negative';
    END IF;

    UPDATE algorithm_executions
    SET execution_status = 'COMPLETED',
        elapsed_microseconds = p_elapsed,
        recursive_calls = p_recursive_calls,
        completed_at = CURRENT_TIMESTAMP
    WHERE execution_id = p_execution_id
      AND execution_status = 'RUNNING';

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Execution % is not running',
            p_execution_id;
    END IF;
END;
$$;

-- ------------------------------------------------------------
-- 12. REPORTING VIEW
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW execution_summary AS
SELECT
    a.algorithm_name,
    a.category,
    COUNT(e.execution_id) AS total_executions,
    COUNT(*) FILTER (
        WHERE e.execution_status = 'COMPLETED'
    ) AS successful_executions,
    COUNT(*) FILTER (
        WHERE e.execution_status = 'FAILED'
    ) AS failed_executions,
    AVG(e.elapsed_microseconds)
        FILTER (
            WHERE e.execution_status = 'COMPLETED'
        ) AS average_execution_microseconds,
    MAX(e.input_size) AS maximum_input_size,
    AVG(e.recursive_calls)
        FILTER (
            WHERE e.execution_status = 'COMPLETED'
        ) AS average_recursive_calls
FROM algorithms a
LEFT JOIN algorithm_executions e
    ON a.algorithm_id = e.algorithm_id
GROUP BY a.algorithm_id, a.algorithm_name, a.category;

-- ------------------------------------------------------------
-- 13. INSERT ALGORITHM CATALOG
-- ------------------------------------------------------------

INSERT INTO algorithms (
    algorithm_name,
    category,
    description,
    stable,
    in_place,
    average_complexity,
    worst_complexity
)
VALUES
(
    'Binary Search',
    'SEARCHING',
    'Repeatedly halves the sorted search interval.',
    FALSE,
    TRUE,
    'O(log n)',
    'O(log n)'
),
(
    'Merge Sort',
    'SORTING',
    'Divides input into halves and merges sorted partitions.',
    TRUE,
    FALSE,
    'O(n log n)',
    'O(n log n)'
),
(
    'Quick Sort',
    'SORTING',
    'Partitions elements around a pivot.',
    FALSE,
    TRUE,
    'O(n log n)',
    'O(n^2)'
),
(
    'Maximum Subarray',
    'OPTIMIZATION',
    'Finds the maximum-sum contiguous subarray using recursive decomposition.',
    FALSE,
    FALSE,
    'O(n log n)',
    'O(n log n)'
),
(
    'Karatsuba Multiplication',
    'MULTIPLICATION',
    'Uses three recursive multiplications instead of four.',
    FALSE,
    FALSE,
    'O(n^1.585)',
    'O(n^1.585)'
);

-- ------------------------------------------------------------
-- 14. INSERT RECURRENCE MODELS
-- ------------------------------------------------------------

INSERT INTO recurrence_models (
    algorithm_id,
    recurrence_expression,
    subproblem_count,
    division_factor,
    combine_exponent,
    critical_exponent,
    complexity_description,
    assumptions
)
SELECT
    a.algorithm_id,
    r.expression,
    r.subproblems,
    r.divisor,
    r.d,
    calculate_critical_exponent(r.subproblems, r.divisor),
    classify_recurrence(r.subproblems, r.divisor, r.d),
    r.assumptions
FROM (
    VALUES
    (
        'Binary Search',
        'T(n) = T(n/2) + Theta(1)',
        1, 2, 0::NUMERIC,
        'One subproblem; constant work per level.'
    ),
    (
        'Merge Sort',
        'T(n) = 2T(n/2) + Theta(n)',
        2, 2, 1::NUMERIC,
        'Two equal partitions; linear merge.'
    ),
    (
        'Quick Sort',
        'T(n) = 2T(n/2) + Theta(n)',
        2, 2, 1::NUMERIC,
        'Balanced partition approximation; worst case differs.'
    ),
    (
        'Maximum Subarray',
        'T(n) = 2T(n/2) + Theta(n)',
        2, 2, 1::NUMERIC,
        'Linear crossing-subarray calculation.'
    ),
    (
        'Karatsuba Multiplication',
        'T(n) = 3T(n/2) + Theta(n)',
        3, 2, 1::NUMERIC,
        'Three recursive multiplications.'
    )
) AS r(
    algorithm_name,
    expression,
    subproblems,
    divisor,
    d,
    assumptions
)
JOIN algorithms a
    ON a.algorithm_name = r.algorithm_name;

-- ------------------------------------------------------------
-- 15. INSERT DECOMPOSITION PHASES
-- ------------------------------------------------------------

INSERT INTO decomposition_strategies (
    algorithm_id,
    step_number,
    phase,
    operation_description,
    expected_cost
)
SELECT
    a.algorithm_id,
    s.step_number,
    s.phase,
    s.description,
    s.expected_cost
FROM (
    VALUES
    ('Merge Sort', 1, 'DIVIDE',
        'Split input into two approximately equal partitions.',
        'O(1) partition boundary calculation'),
    ('Merge Sort', 2, 'CONQUER',
        'Recursively sort both partitions.',
        '2T(n/2)'),
    ('Merge Sort', 3, 'COMBINE',
        'Merge two sorted partitions.',
        'O(n)'),
    ('Quick Sort', 1, 'DIVIDE',
        'Choose pivot and partition elements.',
        'O(n)'),
    ('Quick Sort', 2, 'CONQUER',
        'Sort the lower and higher partitions.',
        'T(k) + T(n-k-1)'),
    ('Quick Sort', 3, 'COMBINE',
        'Concatenate partitions around the pivot.',
        'O(1) excluding output allocation'),
    ('Maximum Subarray', 1, 'DIVIDE',
        'Split the array into left and right segments.',
        'O(1)'),
    ('Maximum Subarray', 2, 'CONQUER',
        'Find the best subarray in each segment.',
        '2T(n/2)'),
    ('Maximum Subarray', 3, 'COMBINE',
        'Calculate the best subarray crossing the midpoint.',
        'O(n)')
) AS s(
    algorithm_name,
    step_number,
    phase,
    description,
    expected_cost
)
JOIN algorithms a
    ON a.algorithm_name = s.algorithm_name;

-- ------------------------------------------------------------
-- 16. SAMPLE EXECUTION RECORDS
-- ------------------------------------------------------------

INSERT INTO algorithm_executions (
    algorithm_id,
    recurrence_id,
    input_size,
    input_fingerprint,
    execution_status,
    started_at,
    completed_at,
    elapsed_microseconds,
    recursive_calls
)
SELECT
    a.algorithm_id,
    r.recurrence_id,
    sample.input_size,
    sample.fingerprint,
    'COMPLETED',
    CURRENT_TIMESTAMP - INTERVAL '2 seconds',
    CURRENT_TIMESTAMP,
    sample.elapsed,
    sample.calls
FROM (
    VALUES
    ('Merge Sort', 1000::BIGINT, 'merge-1000', 150, 1999::BIGINT),
    ('Merge Sort', 5000::BIGINT, 'merge-5000', 950, 9999::BIGINT),
    ('Merge Sort', 10000::BIGINT, 'merge-10000', 2100, 19999::BIGINT),
    ('Quick Sort', 1000::BIGINT, 'quick-1000', 120, 900::BIGINT),
    ('Binary Search', 10000::BIGINT, 'binary-10000', 8, 0::BIGINT),
    ('Maximum Subarray', 1000::BIGINT, 'maximum-1000', 180, 1999::BIGINT),
    ('Karatsuba Multiplication', 1024::BIGINT, 'karatsuba-1024', 400, 1500::BIGINT)
) AS sample(
    algorithm_name,
    input_size,
    fingerprint,
    elapsed,
    calls
)
JOIN algorithms a
    ON a.algorithm_name = sample.algorithm_name
LEFT JOIN recurrence_models r
    ON r.algorithm_id = a.algorithm_id;

-- ------------------------------------------------------------
-- 17. FAILURE CASE
-- ------------------------------------------------------------

INSERT INTO algorithm_executions (
    algorithm_id,
    input_size,
    execution_status,
    started_at,
    completed_at,
    error_code,
    error_message
)
SELECT
    algorithm_id,
    100,
    'FAILED',
    CURRENT_TIMESTAMP - INTERVAL '1 minute',
    CURRENT_TIMESTAMP,
    'INVALID_INPUT',
    'Binary search rejected an unsorted input.'
FROM algorithms
WHERE algorithm_name = 'Binary Search';

-- ------------------------------------------------------------
-- 18. VALIDATION QUERIES
-- ------------------------------------------------------------

-- Identify missing recurrence models.
SELECT
    a.algorithm_name
FROM algorithms a
LEFT JOIN recurrence_models r
    ON r.algorithm_id = a.algorithm_id
WHERE r.recurrence_id IS NULL;

-- Check execution metric consistency.
SELECT
    execution_id,
    execution_status,
    elapsed_microseconds,
    recursive_calls
FROM algorithm_executions
WHERE
    (execution_status = 'COMPLETED'
        AND elapsed_microseconds IS NULL)
    OR recursive_calls < 0;

-- ------------------------------------------------------------
-- 19. RETRIEVAL: ALGORITHM AND RECURRENCE CATALOG
-- ------------------------------------------------------------

SELECT
    a.algorithm_name,
    a.category,
    a.average_complexity,
    a.worst_complexity,
    r.recurrence_expression,
    r.complexity_description
FROM algorithms a
LEFT JOIN recurrence_models r
    ON r.algorithm_id = a.algorithm_id
ORDER BY a.algorithm_name;

-- ------------------------------------------------------------
-- 20. AGGREGATION: EXECUTION PERFORMANCE
-- ------------------------------------------------------------

SELECT
    algorithm_name,
    total_executions,
    successful_executions,
    failed_executions,
    ROUND(average_execution_microseconds, 2)
        AS average_microseconds,
    ROUND(average_recursive_calls, 2)
        AS average_recursive_calls
FROM execution_summary
ORDER BY algorithm_name;

-- ------------------------------------------------------------
-- 21. CTE: PERFORMANCE COMPARISON
-- ------------------------------------------------------------

WITH measurements AS (
    SELECT
        a.algorithm_name,
        e.input_size,
        e.elapsed_microseconds,
        e.recursive_calls,
        LAG(e.elapsed_microseconds) OVER (
            PARTITION BY a.algorithm_id
            ORDER BY e.input_size
        ) AS previous_elapsed,
        LAG(e.input_size) OVER (
            PARTITION BY a.algorithm_id
            ORDER BY e.input_size
        ) AS previous_size
    FROM algorithm_executions e
    JOIN algorithms a
        ON a.algorithm_id = e.algorithm_id
    WHERE e.execution_status = 'COMPLETED'
)
SELECT
    algorithm_name,
    input_size,
    elapsed_microseconds,
    recursive_calls,
    CASE
        WHEN previous_size > 0
        THEN ROUND(
            input_size::NUMERIC / previous_size,
            3
        )
    END AS input_growth_ratio,
    CASE
        WHEN previous_elapsed > 0
        THEN ROUND(
            elapsed_microseconds::NUMERIC / previous_elapsed,
            3
        )
    END AS execution_growth_ratio
FROM measurements
ORDER BY algorithm_name, input_size;

-- ------------------------------------------------------------
-- 22. ELIGIBILITY DETERMINATION
-- ------------------------------------------------------------

-- An execution is eligible for performance analysis only when
-- it has completed and its required metrics are available.

SELECT
    e.execution_id,
    a.algorithm_name,
    e.input_size,
    CASE
        WHEN e.execution_status = 'COMPLETED'
             AND e.elapsed_microseconds IS NOT NULL
             AND e.recursive_calls >= 0
        THEN TRUE
        ELSE FALSE
    END AS eligible_for_analysis
FROM algorithm_executions e
JOIN algorithms a
    ON a.algorithm_id = e.algorithm_id;

-- ------------------------------------------------------------
-- 23. RECURSION TRACE REPORT
-- ------------------------------------------------------------

SELECT
    execution_id,
    depth,
    COUNT(*) AS operations_at_depth,
    MAX(subproblem_size) AS maximum_subproblem_size,
    MIN(subproblem_size) AS minimum_subproblem_size
FROM recursion_traces
GROUP BY execution_id, depth
ORDER BY execution_id, depth;

-- ------------------------------------------------------------
-- 24. TRANSACTIONAL EXECUTION WORKFLOW
-- ------------------------------------------------------------

DO $$
DECLARE
    v_algorithm_id BIGINT;
    v_execution_id BIGINT;
BEGIN
    SELECT algorithm_id
    INTO STRICT v_algorithm_id
    FROM algorithms
    WHERE algorithm_name = 'Merge Sort';

    INSERT INTO algorithm_executions (
        algorithm_id,
        input_size,
        execution_status
    )
    VALUES (
        v_algorithm_id,
        25000,
        'QUEUED'
    )
    RETURNING execution_id INTO v_execution_id;

    CALL start_execution(v_execution_id);

    CALL complete_execution(
        v_execution_id,
        4500,
        49999
    );

    INSERT INTO performance_observations (
        execution_id,
        input_size,
        elapsed_microseconds,
        recursive_calls,
        environment_name
    )
    VALUES (
        v_execution_id,
        25000,
        4500,
        49999,
        'LOCAL_BENCHMARK'
    );

    RAISE NOTICE 'Completed execution ID: %', v_execution_id;
END;
$$;

-- ------------------------------------------------------------
-- 25. RECURRENCE CLASSIFICATION EXAMPLES
-- ------------------------------------------------------------

SELECT
    recurrence_name,
    recurrence_expression,
    classify_recurrence(a, b, d) AS calculated_complexity
FROM (
    VALUES
        ('Binary Search', 'T(n)=T(n/2)+1', 1, 2, 0::NUMERIC),
        ('Merge Sort', 'T(n)=2T(n/2)+n', 2, 2, 1::NUMERIC),
        ('Karatsuba', 'T(n)=3T(n/2)+n', 3, 2, 1::NUMERIC),
        ('Strassen', 'T(n)=7T(n/2)+n^2', 7, 2, 2::NUMERIC)
) AS examples(
    recurrence_name,
    recurrence_expression,
    a,
    b,
    d
);

-- ------------------------------------------------------------
-- 26. FINAL DATABASE REPORT
-- ------------------------------------------------------------

SELECT
    a.algorithm_name,
    a.category,
    a.average_complexity,
    a.worst_complexity,
    COUNT(e.execution_id) AS recorded_executions,
    COUNT(e.execution_id) FILTER (
        WHERE e.execution_status = 'COMPLETED'
    ) AS completed_executions
FROM algorithms a
LEFT JOIN algorithm_executions e
    ON e.algorithm_id = a.algorithm_id
GROUP BY
    a.algorithm_id,
    a.algorithm_name,
    a.category,
    a.average_complexity,
    a.worst_complexity
ORDER BY a.algorithm_name;

COMMIT;
