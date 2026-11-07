-- ============================================================
-- SEARCHING ALGORITHMS
-- PostgreSQL implementation
-- Linear Search, Binary Search, Interpolation Search
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS searching_lab;

SET search_path TO searching_lab, public;

-- ------------------------------------------------------------
-- Dataset management
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS search_datasets (
    dataset_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset_name VARCHAR(120) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS search_values (
    value_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset_id BIGINT NOT NULL
        REFERENCES search_datasets(dataset_id)
        ON DELETE CASCADE,
    position INTEGER NOT NULL CHECK (position >= 0),
    search_value INTEGER NOT NULL,
    UNIQUE (dataset_id, position)
);

CREATE INDEX IF NOT EXISTS idx_search_values_dataset_position
    ON search_values(dataset_id, position);

CREATE INDEX IF NOT EXISTS idx_search_values_dataset_value
    ON search_values(dataset_id, search_value);

-- ------------------------------------------------------------
-- Search execution history
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS search_history (
    search_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset_id BIGINT NOT NULL
        REFERENCES search_datasets(dataset_id),
    algorithm VARCHAR(20) NOT NULL
        CHECK (
            algorithm IN (
                'LINEAR',
                'BINARY',
                'INTERPOLATION'
            )
        ),
    target_value INTEGER NOT NULL,
    result_position INTEGER,
    comparisons BIGINT NOT NULL CHECK (comparisons >= 0),
    execution_time_microseconds NUMERIC(18, 6)
        NOT NULL CHECK (execution_time_microseconds >= 0),
    found BOOLEAN NOT NULL,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        (found AND result_position IS NOT NULL)
        OR
        (NOT found AND result_position IS NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_search_history_dataset_time
    ON search_history(dataset_id, executed_at DESC);

CREATE INDEX IF NOT EXISTS idx_search_history_algorithm
    ON search_history(algorithm, found);

-- ------------------------------------------------------------
-- Validate whether a dataset is sorted.
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION is_dataset_sorted(
    p_dataset_id BIGINT
)
RETURNS BOOLEAN
LANGUAGE SQL
STABLE
AS $$
    SELECT NOT EXISTS (
        SELECT 1
        FROM search_values current_value
        JOIN search_values previous_value
          ON previous_value.dataset_id = current_value.dataset_id
         AND previous_value.position = current_value.position - 1
        WHERE current_value.dataset_id = p_dataset_id
          AND current_value.search_value < previous_value.search_value
    );
$$;

-- ------------------------------------------------------------
-- Linear search.
-- Supports unsorted data.
-- Returns the first matching zero-based position.
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION linear_search(
    p_dataset_id BIGINT,
    p_target INTEGER
)
RETURNS TABLE (
    result_position INTEGER,
    comparisons BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    item RECORD;
    v_comparisons BIGINT := 0;
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM search_datasets
        WHERE dataset_id = p_dataset_id
    ) THEN
        RAISE EXCEPTION 'Dataset % does not exist', p_dataset_id;
    END IF;

    FOR item IN
        SELECT position, search_value
        FROM search_values
        WHERE dataset_id = p_dataset_id
        ORDER BY position
    LOOP
        v_comparisons := v_comparisons + 1;

        IF item.search_value = p_target THEN
            result_position := item.position;
            comparisons := v_comparisons;
            RETURN NEXT;
            RETURN;
        END IF;
    END LOOP;

    result_position := NULL;
    comparisons := v_comparisons;
    RETURN NEXT;
END;
$$;

-- ------------------------------------------------------------
-- Binary search.
-- Requires ascending sorted data.
-- Lower-bound logic returns the first duplicate.
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION binary_search(
    p_dataset_id BIGINT,
    p_target INTEGER
)
RETURNS TABLE (
    result_position INTEGER,
    comparisons BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_low INTEGER;
    v_high INTEGER;
    v_middle INTEGER;
    v_value INTEGER;
    v_comparisons BIGINT := 0;
    v_result INTEGER := NULL;
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM search_datasets
        WHERE dataset_id = p_dataset_id
    ) THEN
        RAISE EXCEPTION 'Dataset % does not exist', p_dataset_id;
    END IF;

    IF NOT is_dataset_sorted(p_dataset_id) THEN
        RAISE EXCEPTION 'Binary search requires sorted data';
    END IF;

    SELECT
        MIN(position),
        MAX(position)
    INTO v_low, v_high
    FROM search_values
    WHERE dataset_id = p_dataset_id;

    WHILE v_low IS NOT NULL AND v_low <= v_high LOOP
        v_middle := v_low + ((v_high - v_low) / 2);

        SELECT search_value
        INTO v_value
        FROM search_values
        WHERE dataset_id = p_dataset_id
          AND position = v_middle;

        v_comparisons := v_comparisons + 1;

        IF v_value = p_target THEN
            v_result := v_middle;
            v_high := v_middle - 1;

        ELSIF v_value < p_target THEN
            v_low := v_middle + 1;

        ELSE
            v_high := v_middle - 1;
        END IF;
    END LOOP;

    result_position := v_result;
    comparisons := v_comparisons;
    RETURN NEXT;
END;
$$;

-- ------------------------------------------------------------
-- Interpolation search.
-- Most useful for approximately uniform numeric distributions.
-- Uses NUMERIC arithmetic to prevent integer multiplication
-- overflow during position estimation.
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION interpolation_search(
    p_dataset_id BIGINT,
    p_target INTEGER
)
RETURNS TABLE (
    result_position INTEGER,
    comparisons BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_low INTEGER;
    v_high INTEGER;
    v_low_value INTEGER;
    v_high_value INTEGER;
    v_position INTEGER;
    v_value INTEGER;
    v_estimate NUMERIC;
    v_comparisons BIGINT := 0;
    v_result INTEGER := NULL;
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM search_datasets
        WHERE dataset_id = p_dataset_id
    ) THEN
        RAISE EXCEPTION 'Dataset % does not exist', p_dataset_id;
    END IF;

    IF NOT is_dataset_sorted(p_dataset_id) THEN
        RAISE EXCEPTION 'Interpolation search requires sorted data';
    END IF;

    SELECT MIN(position), MAX(position)
    INTO v_low, v_high
    FROM search_values
    WHERE dataset_id = p_dataset_id;

    WHILE v_low IS NOT NULL AND v_low <= v_high LOOP
        SELECT search_value
        INTO v_low_value
        FROM search_values
        WHERE dataset_id = p_dataset_id
          AND position = v_low;

        SELECT search_value
        INTO v_high_value
        FROM search_values
        WHERE dataset_id = p_dataset_id
          AND position = v_high;

        v_comparisons := v_comparisons + 1;

        IF p_target < v_low_value OR p_target > v_high_value THEN
            EXIT;
        END IF;

        -- Handle a constant-valued search interval.
        IF v_low_value = v_high_value THEN
            IF v_low_value = p_target THEN
                v_result := v_low;
            END IF;
            EXIT;
        END IF;

        v_estimate :=
            v_low::NUMERIC
            +
            (
                (p_target::NUMERIC - v_low_value::NUMERIC)
                *
                (v_high - v_low)::NUMERIC
            )
            /
            (v_high_value::NUMERIC - v_low_value::NUMERIC);

        v_position := GREATEST(
            v_low,
            LEAST(v_high, FLOOR(v_estimate)::INTEGER)
        );

        SELECT search_value
        INTO v_value
        FROM search_values
        WHERE dataset_id = p_dataset_id
          AND position = v_position;

        v_comparisons := v_comparisons + 1;

        IF v_value = p_target THEN
            v_result := v_position;
            v_high := v_position - 1;

        ELSIF v_value < p_target THEN
            v_low := v_position + 1;

        ELSE
            v_high := v_position - 1;
        END IF;
    END LOOP;

    result_position := v_result;
    comparisons := v_comparisons;
    RETURN NEXT;
END;
$$;

-- ------------------------------------------------------------
-- Unified search function.
-- Executes the requested algorithm and records its metrics.
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION execute_search(
    p_dataset_id BIGINT,
    p_algorithm VARCHAR(20),
    p_target INTEGER
)
RETURNS TABLE (
    algorithm VARCHAR(20),
    target_value INTEGER,
    result_position INTEGER,
    comparisons BIGINT,
    found BOOLEAN,
    execution_time_microseconds NUMERIC(18, 6)
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_position INTEGER;
    v_comparisons BIGINT;
    v_start TIMESTAMPTZ;
    v_elapsed NUMERIC(18, 6);
BEGIN
    IF p_algorithm NOT IN (
        'LINEAR',
        'BINARY',
        'INTERPOLATION'
    ) THEN
        RAISE EXCEPTION 'Unsupported algorithm: %', p_algorithm;
    END IF;

    v_start := clock_timestamp();

    CASE p_algorithm
        WHEN 'LINEAR' THEN
            SELECT s.result_position, s.comparisons
            INTO v_position, v_comparisons
            FROM linear_search(p_dataset_id, p_target) s;

        WHEN 'BINARY' THEN
            SELECT s.result_position, s.comparisons
            INTO v_position, v_comparisons
            FROM binary_search(p_dataset_id, p_target) s;

        WHEN 'INTERPOLATION' THEN
            SELECT s.result_position, s.comparisons
            INTO v_position, v_comparisons
            FROM interpolation_search(p_dataset_id, p_target) s;
    END CASE;

    v_elapsed :=
        EXTRACT(EPOCH FROM (clock_timestamp() - v_start))
        * 1000000;

    INSERT INTO search_history (
        dataset_id,
        algorithm,
        target_value,
        result_position,
        comparisons,
        execution_time_microseconds,
        found
    )
    VALUES (
        p_dataset_id,
        p_algorithm,
        p_target,
        v_position,
        v_comparisons,
        v_elapsed,
        v_position IS NOT NULL
    );

    algorithm := p_algorithm;
    target_value := p_target;
    result_position := v_position;
    comparisons := v_comparisons;
    found := v_position IS NOT NULL;
    execution_time_microseconds := v_elapsed;

    RETURN NEXT;
END;
$$;

-- ------------------------------------------------------------
-- Stored procedure for loading dataset values.
-- Existing positions are replaced atomically.
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE load_dataset(
    p_dataset_id BIGINT,
    p_values INTEGER[]
)
LANGUAGE plpgsql
AS $$
DECLARE
    i INTEGER;
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM search_datasets
        WHERE dataset_id = p_dataset_id
    ) THEN
        RAISE EXCEPTION 'Dataset does not exist';
    END IF;

    IF p_values IS NULL THEN
        RAISE EXCEPTION 'Dataset values cannot be NULL';
    END IF;

    DELETE FROM search_values
    WHERE dataset_id = p_dataset_id;

    FOR i IN 1..COALESCE(array_length(p_values, 1), 0) LOOP
        INSERT INTO search_values (
            dataset_id,
            position,
            search_value
        )
        VALUES (
            p_dataset_id,
            i - 1,
            p_values[i]
        );
    END LOOP;
END;
$$;

-- ------------------------------------------------------------
-- Reporting view
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW search_performance_report AS
SELECT
    d.dataset_name,
    h.algorithm,
    COUNT(*) AS total_searches,
    COUNT(*) FILTER (WHERE h.found) AS successful_searches,
    COUNT(*) FILTER (WHERE NOT h.found) AS failed_searches,
    ROUND(AVG(h.comparisons), 2) AS average_comparisons,
    ROUND(
        AVG(h.execution_time_microseconds),
        3
    ) AS average_execution_microseconds,
    MAX(h.executed_at) AS last_execution
FROM search_history h
JOIN search_datasets d
    ON d.dataset_id = h.dataset_id
GROUP BY d.dataset_name, h.algorithm;

-- ------------------------------------------------------------
-- Sample datasets
-- ------------------------------------------------------------

INSERT INTO search_datasets (
    dataset_name,
    description
)
VALUES
    (
        'uniform_inventory',
        'Sorted inventory identifiers with approximately uniform spacing.'
    ),
    (
        'duplicate_inventory',
        'Sorted inventory identifiers containing duplicate values.'
    ),
    (
        'unsorted_inventory',
        'Unsorted values for linear-search demonstrations.'
    ),
    (
        'constant_inventory',
        'Dataset containing identical values.'
    )
ON CONFLICT (dataset_name) DO NOTHING;

-- Sample values are inserted only when the dataset is empty.

DO $$
DECLARE
    v_uniform BIGINT;
    v_duplicate BIGINT;
    v_unsorted BIGINT;
    v_constant BIGINT;
BEGIN
    SELECT dataset_id INTO v_uniform
    FROM search_datasets
    WHERE dataset_name = 'uniform_inventory';

    SELECT dataset_id INTO v_duplicate
    FROM search_datasets
    WHERE dataset_name = 'duplicate_inventory';

    SELECT dataset_id INTO v_unsorted
    FROM search_datasets
    WHERE dataset_name = 'unsorted_inventory';

    SELECT dataset_id INTO v_constant
    FROM search_datasets
    WHERE dataset_name = 'constant_inventory';

    IF NOT EXISTS (
        SELECT 1 FROM search_values WHERE dataset_id = v_uniform
    ) THEN
        CALL load_dataset(
            v_uniform,
            ARRAY[100, 200, 300, 400, 500, 600, 700, 800]
        );
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM search_values WHERE dataset_id = v_duplicate
    ) THEN
        CALL load_dataset(
            v_duplicate,
            ARRAY[5, 5, 5, 10, 10, 20, 30]
        );
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM search_values WHERE dataset_id = v_unsorted
    ) THEN
        CALL load_dataset(
            v_unsorted,
            ARRAY[40, 10, 30, 20, 50]
        );
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM search_values WHERE dataset_id = v_constant
    ) THEN
        CALL load_dataset(
            v_constant,
            ARRAY[7, 7, 7, 7, 7]
        );
    END IF;
END;
$$;

-- ------------------------------------------------------------
-- Retrieval queries
-- ------------------------------------------------------------

SELECT
    d.dataset_name,
    v.position,
    v.search_value
FROM search_values v
JOIN search_datasets d
    ON d.dataset_id = v.dataset_id
ORDER BY d.dataset_name, v.position;

-- ------------------------------------------------------------
-- Sorted-data validation
-- ------------------------------------------------------------

SELECT
    dataset_name,
    is_dataset_sorted(dataset_id) AS sorted_ascending
FROM search_datasets
ORDER BY dataset_name;

-- ------------------------------------------------------------
-- Execute each algorithm against the same dataset.
-- ------------------------------------------------------------

DO $$
DECLARE
    v_dataset BIGINT;
BEGIN
    SELECT dataset_id INTO v_dataset
    FROM search_datasets
    WHERE dataset_name = 'uniform_inventory';

    PERFORM * FROM execute_search(v_dataset, 'LINEAR', 500);
    PERFORM * FROM execute_search(v_dataset, 'BINARY', 500);
    PERFORM * FROM execute_search(v_dataset, 'INTERPOLATION', 500);

    PERFORM * FROM execute_search(v_dataset, 'LINEAR', 999);
    PERFORM * FROM execute_search(v_dataset, 'BINARY', 999);
    PERFORM * FROM execute_search(v_dataset, 'INTERPOLATION', 999);
END;
$$;

-- Duplicate-value test: first matching position is returned.

SELECT *
FROM execute_search(
    (
        SELECT dataset_id
        FROM search_datasets
        WHERE dataset_name = 'duplicate_inventory'
    ),
    'BINARY',
    10
);

SELECT *
FROM execute_search(
    (
        SELECT dataset_id
        FROM search_datasets
        WHERE dataset_name = 'duplicate_inventory'
    ),
    'INTERPOLATION',
    10
);

-- Constant-value edge case.

SELECT *
FROM execute_search(
    (
        SELECT dataset_id
        FROM search_datasets
        WHERE dataset_name = 'constant_inventory'
    ),
    'INTERPOLATION',
    7
);

-- ------------------------------------------------------------
-- CTE-based algorithm evaluation
-- ------------------------------------------------------------

WITH evaluation AS (
    SELECT
        d.dataset_name,
        h.algorithm,
        h.target_value,
        h.found,
        h.comparisons,
        h.execution_time_microseconds
    FROM search_history h
    JOIN search_datasets d
        ON d.dataset_id = h.dataset_id
)
SELECT
    algorithm,
    COUNT(*) AS requests,
    COUNT(*) FILTER (WHERE found) AS matches,
    ROUND(AVG(comparisons), 2) AS avg_comparisons,
    ROUND(AVG(execution_time_microseconds), 3) AS avg_time_microseconds
FROM evaluation
GROUP BY algorithm
ORDER BY avg_comparisons;

-- ------------------------------------------------------------
-- Detailed performance reporting
-- ------------------------------------------------------------

SELECT *
FROM search_performance_report
ORDER BY dataset_name, algorithm;

-- ------------------------------------------------------------
-- Workflow processing: identify unsorted datasets.
-- ------------------------------------------------------------

SELECT
    dataset_name,
    dataset_id
FROM search_datasets
WHERE NOT is_dataset_sorted(dataset_id);

-- Linear search remains eligible for unsorted datasets.
SELECT *
FROM execute_search(
    (
        SELECT dataset_id
        FROM search_datasets
        WHERE dataset_name = 'unsorted_inventory'
    ),
    'LINEAR',
    30
);

-- ------------------------------------------------------------
-- Transaction demonstration for dataset maintenance.
-- ------------------------------------------------------------

SAVEPOINT before_inventory_update;

DO $$
DECLARE
    v_dataset BIGINT;
BEGIN
    SELECT dataset_id INTO v_dataset
    FROM search_datasets
    WHERE dataset_name = 'uniform_inventory';

    INSERT INTO search_values (
        dataset_id,
        position,
        search_value
    )
    SELECT
        v_dataset,
        COALESCE(MAX(position), -1) + 1,
        900
    FROM search_values
    WHERE dataset_id = v_dataset;
END;
$$;

-- Inspect the inserted value before committing.
SELECT *
FROM search_values
WHERE dataset_id = (
    SELECT dataset_id
    FROM search_datasets
    WHERE dataset_name = 'uniform_inventory'
)
ORDER BY position DESC
LIMIT 1;

-- Keep the demonstrated update.
RELEASE SAVEPOINT before_inventory_update;

COMMIT;

-- ------------------------------------------------------------
-- Operational notes
-- ------------------------------------------------------------

-- 1. Linear search supports unsorted data.
-- 2. Binary search requires ascending sorted data.
-- 3. Interpolation search requires ascending sorted numeric data.
-- 4. Duplicate matches return the first position.
-- 5. Database position values are zero-based.
-- 6. The comparison count measures algorithm-level comparisons.
-- 7. Execution time includes database function execution overhead.
-- 8. Concurrent dataset modifications should be controlled through
--    appropriate transaction isolation and application locking.
-- 9. The dataset position index supports ordered access.
-- 10. For large indexed datasets, PostgreSQL's native B-tree index
--     operations may outperform procedural search functions.
