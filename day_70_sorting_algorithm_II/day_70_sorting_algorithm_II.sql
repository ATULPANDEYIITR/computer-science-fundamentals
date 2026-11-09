/*
 * Sorting Algorithms II
 * Merge Sort, Quick Sort and Heap Sort
 *
 * PostgreSQL 15+
 *
 * Implements:
 * - Algorithm registry
 * - Sorting benchmark datasets
 * - Benchmark execution records
 * - Actual merge sort implementation
 * - Actual quicksort implementation
 * - Actual heap sort implementation
 * - Input and result validation
 * - Benchmark reporting
 * - Performance indexes
 * - Transactional workflow
 */

BEGIN;

CREATE SCHEMA IF NOT EXISTS sorting_lab;

SET search_path TO sorting_lab, public;

-- Remove existing demonstration objects in dependency order.
DROP VIEW IF EXISTS benchmark_comparison CASCADE;
DROP TABLE IF EXISTS benchmark_runs CASCADE;
DROP TABLE IF EXISTS benchmark_datasets CASCADE;
DROP TABLE IF EXISTS sorting_algorithms CASCADE;

DROP FUNCTION IF EXISTS merge_sort(INTEGER[]) CASCADE;
DROP FUNCTION IF EXISTS quick_sort(INTEGER[]) CASCADE;
DROP FUNCTION IF EXISTS heap_sort(INTEGER[]) CASCADE;
DROP FUNCTION IF EXISTS merge_sort_range(INTEGER[], INTEGER, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS quick_sort_range(INTEGER[], INTEGER, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS heap_sift_down(INTEGER[], INTEGER, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS execute_sort(VARCHAR, INTEGER[]) CASCADE;
DROP FUNCTION IF EXISTS validate_sort_result(INTEGER[], INTEGER[]) CASCADE;
DROP FUNCTION IF EXISTS record_benchmark(VARCHAR, BIGINT, VARCHAR) CASCADE;

CREATE TABLE sorting_algorithms (
    algorithm_id SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    algorithm_code VARCHAR(30) NOT NULL UNIQUE,
    algorithm_name VARCHAR(100) NOT NULL,
    average_time_complexity VARCHAR(30) NOT NULL,
    worst_time_complexity VARCHAR(30) NOT NULL,
    auxiliary_space VARCHAR(30) NOT NULL,
    is_stable BOOLEAN NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE benchmark_datasets (
    dataset_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset_name VARCHAR(100) NOT NULL UNIQUE,
    input_values INTEGER[] NOT NULL,
    input_size INTEGER GENERATED ALWAYS AS (
        cardinality(input_values)
    ) STORED,
    distribution_type VARCHAR(30) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_distribution CHECK (
        distribution_type IN (
            'random',
            'sorted',
            'reverse',
            'duplicates',
            'all_equal',
            'custom'
        )
    )
);

CREATE TABLE benchmark_runs (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset_id BIGINT NOT NULL
        REFERENCES benchmark_datasets(dataset_id),
    algorithm_id SMALLINT NOT NULL
        REFERENCES sorting_algorithms(algorithm_id),
    input_size INTEGER NOT NULL CHECK (input_size >= 0),
    comparisons BIGINT NOT NULL CHECK (comparisons >= 0),
    swaps BIGINT NOT NULL CHECK (swaps >= 0),
    writes BIGINT NOT NULL CHECK (writes >= 0),
    elapsed_microseconds BIGINT NOT NULL
        CHECK (elapsed_microseconds >= 0),
    is_correct BOOLEAN NOT NULL,
    execution_status VARCHAR(20) NOT NULL,
    error_message TEXT,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_execution_status CHECK (
        execution_status IN (
            'SUCCESS',
            'FAILED',
            'REJECTED'
        )
    )
);

CREATE INDEX idx_benchmark_runs_dataset
    ON benchmark_runs(dataset_id, executed_at DESC);

CREATE INDEX idx_benchmark_runs_algorithm
    ON benchmark_runs(algorithm_id, executed_at DESC);

CREATE INDEX idx_benchmark_success
    ON benchmark_runs(is_correct, algorithm_id)
    WHERE execution_status = 'SUCCESS';

INSERT INTO sorting_algorithms (
    algorithm_code,
    algorithm_name,
    average_time_complexity,
    worst_time_complexity,
    auxiliary_space,
    is_stable,
    description
)
VALUES
(
    'MERGE',
    'Merge Sort',
    'O(n log n)',
    'O(n log n)',
    'O(n)',
    TRUE,
    'Divide-and-conquer stable sorting using merge operations.'
),
(
    'QUICK',
    'Quick Sort',
    'O(n log n)',
    'O(n^2)',
    'O(log n) average',
    FALSE,
    'Partition-based sorting using a pivot and three-way partitioning.'
),
(
    'HEAP',
    'Heap Sort',
    'O(n log n)',
    'O(n log n)',
    'O(1) auxiliary',
    FALSE,
    'Comparison sorting using bottom-up binary heap construction.'
);

INSERT INTO benchmark_datasets (
    dataset_name,
    input_values,
    distribution_type
)
VALUES
(
    'random_small',
    ARRAY[38, 27, 43, 3, 9, 82, 10, 3],
    'random'
),
(
    'already_sorted',
    ARRAY[1, 2, 3, 4, 5, 6, 7, 8],
    'sorted'
),
(
    'reverse_sorted',
    ARRAY[9, 8, 7, 6, 5, 4, 3, 2, 1],
    'reverse'
),
(
    'duplicate_heavy',
    ARRAY[5, 5, 2, 2, 5, 1, 1, 2],
    'duplicates'
),
(
    'single_element',
    ARRAY[42],
    'custom'
),
(
    'empty_dataset',
    ARRAY[]::INTEGER[],
    'custom'
),
(
    'all_equal',
    ARRAY[7, 7, 7, 7, 7, 7],
    'all_equal'
);

-- ---------------------------------------------------------
-- MERGE SORT
-- ---------------------------------------------------------

CREATE OR REPLACE FUNCTION merge_sort_range(
    p_values INTEGER[],
    p_left INTEGER,
    p_right INTEGER
)
RETURNS INTEGER[]
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
DECLARE
    v_result INTEGER[] := p_values;
    v_left_part INTEGER[];
    v_right_part INTEGER[];
    v_middle INTEGER;
    i INTEGER;
    j INTEGER;
    k INTEGER;
    n INTEGER;
BEGIN
    n := cardinality(p_values);

    IF p_left < 1 OR p_right > n OR p_left > p_right THEN
        IF p_left > p_right THEN
            RETURN v_result;
        END IF;

        RAISE EXCEPTION 'Invalid merge sort range';
    END IF;

    IF p_left >= p_right THEN
        RETURN v_result;
    END IF;

    v_middle := (p_left + p_right) / 2;

    v_result := merge_sort_range(
        v_result,
        p_left,
        v_middle
    );

    v_result := merge_sort_range(
        v_result,
        v_middle + 1,
        p_right
    );

    v_left_part := v_result[p_left:v_middle];
    v_right_part := v_result[v_middle + 1:p_right];

    i := 1;
    j := 1;
    k := p_left;

    WHILE i <= cardinality(v_left_part)
      AND j <= cardinality(v_right_part)
    LOOP
        -- Left-first selection on equality preserves stability.
        IF v_left_part[i] <= v_right_part[j] THEN
            v_result[k] := v_left_part[i];
            i := i + 1;
        ELSE
            v_result[k] := v_right_part[j];
            j := j + 1;
        END IF;

        k := k + 1;
    END LOOP;

    WHILE i <= cardinality(v_left_part) LOOP
        v_result[k] := v_left_part[i];
        i := i + 1;
        k := k + 1;
    END LOOP;

    WHILE j <= cardinality(v_right_part) LOOP
        v_result[k] := v_right_part[j];
        j := j + 1;
        k := k + 1;
    END LOOP;

    RETURN v_result;
END;
$$;

CREATE OR REPLACE FUNCTION merge_sort(
    p_values INTEGER[]
)
RETURNS INTEGER[]
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
BEGIN
    IF cardinality(p_values) <= 1 THEN
        RETURN p_values;
    END IF;

    RETURN merge_sort_range(
        p_values,
        1,
        cardinality(p_values)
    );
END;
$$;

-- ---------------------------------------------------------
-- QUICK SORT
-- ---------------------------------------------------------

CREATE OR REPLACE FUNCTION quick_sort_range(
    p_values INTEGER[],
    p_low INTEGER,
    p_high INTEGER
)
RETURNS INTEGER[]
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
DECLARE
    v_result INTEGER[] := p_values;
    v_pivot INTEGER;
    v_middle INTEGER;
    v_i INTEGER;
    v_j INTEGER;
    v_temp INTEGER;
BEGIN
    IF p_low >= p_high THEN
        RETURN v_result;
    END IF;

    -- Middle-element pivot limits sensitivity to ordered input.
    v_middle := p_low + (p_high - p_low) / 2;
    v_pivot := v_result[v_middle];

    v_i := p_low;
    v_j := p_high;

    WHILE v_i <= v_j LOOP
        WHILE v_result[v_i] < v_pivot LOOP
            v_i := v_i + 1;
        END LOOP;

        WHILE v_result[v_j] > v_pivot LOOP
            v_j := v_j - 1;
        END LOOP;

        IF v_i <= v_j THEN
            v_temp := v_result[v_i];
            v_result[v_i] := v_result[v_j];
            v_result[v_j] := v_temp;

            v_i := v_i + 1;
            v_j := v_j - 1;
        END IF;
    END LOOP;

    IF p_low < v_j THEN
        v_result := quick_sort_range(
            v_result,
            p_low,
            v_j
        );
    END IF;

    IF v_i < p_high THEN
        v_result := quick_sort_range(
            v_result,
            v_i,
            p_high
        );
    END IF;

    RETURN v_result;
END;
$$;

CREATE OR REPLACE FUNCTION quick_sort(
    p_values INTEGER[]
)
RETURNS INTEGER[]
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
BEGIN
    IF cardinality(p_values) <= 1 THEN
        RETURN p_values;
    END IF;

    RETURN quick_sort_range(
        p_values,
        1,
        cardinality(p_values)
    );
END;
$$;

-- ---------------------------------------------------------
-- HEAP SORT
-- ---------------------------------------------------------

CREATE OR REPLACE FUNCTION heap_sift_down(
    p_values INTEGER[],
    p_root INTEGER,
    p_end INTEGER
)
RETURNS INTEGER[]
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
DECLARE
    v_result INTEGER[] := p_values;
    v_root INTEGER := p_root;
    v_child INTEGER;
    v_temp INTEGER;
BEGIN
    WHILE 2 * v_root + 1 <= p_end LOOP
        v_child := 2 * v_root + 1;

        IF v_child + 1 <= p_end
           AND v_result[v_child + 1] > v_result[v_child]
        THEN
            v_child := v_child + 1;
        END IF;

        IF v_result[v_root] >= v_result[v_child] THEN
            EXIT;
        END IF;

        v_temp := v_result[v_root];
        v_result[v_root] := v_result[v_child];
        v_result[v_child] := v_temp;

        v_root := v_child;
    END LOOP;

    RETURN v_result;
END;
$$;

CREATE OR REPLACE FUNCTION heap_sort(
    p_values INTEGER[]
)
RETURNS INTEGER[]
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
DECLARE
    v_result INTEGER[] := p_values;
    v_n INTEGER := cardinality(p_values);
    v_root INTEGER;
    v_end INTEGER;
    v_temp INTEGER;
BEGIN
    IF v_n <= 1 THEN
        RETURN v_result;
    END IF;

    -- Build the max heap from the last internal node.
    FOR v_root IN REVERSE (v_n / 2 - 1)..0 LOOP
        v_result := heap_sift_down(
            v_result,
            v_root,
            v_n - 1
        );
    END LOOP;

    -- Extract the maximum and restore the reduced heap.
    FOR v_end IN REVERSE (v_n - 1)..1 LOOP
        v_temp := v_result[1];
        v_result[1] := v_result[v_end + 1];
        v_result[v_end + 1] := v_temp;

        v_result := heap_sift_down(
            v_result,
            0,
            v_end - 1
        );
    END LOOP;

    RETURN v_result;
END;
$$;

-- ---------------------------------------------------------
-- ALGORITHM DISPATCH AND VALIDATION
-- ---------------------------------------------------------

CREATE OR REPLACE FUNCTION execute_sort(
    p_algorithm VARCHAR,
    p_values INTEGER[]
)
RETURNS INTEGER[]
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
BEGIN
    CASE upper(p_algorithm)
        WHEN 'MERGE' THEN
            RETURN merge_sort(p_values);

        WHEN 'QUICK' THEN
            RETURN quick_sort(p_values);

        WHEN 'HEAP' THEN
            RETURN heap_sort(p_values);

        ELSE
            RAISE EXCEPTION
                'Unsupported sorting algorithm: %',
                p_algorithm;
    END CASE;
END;
$$;

CREATE OR REPLACE FUNCTION validate_sort_result(
    p_original INTEGER[],
    p_sorted INTEGER[]
)
RETURNS BOOLEAN
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
DECLARE
    v_expected INTEGER[];
BEGIN
    IF cardinality(p_original) <> cardinality(p_sorted) THEN
        RETURN FALSE;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM generate_subscripts(p_sorted, 1) AS s(i)
        WHERE s.i > 1
          AND p_sorted[s.i - 1] > p_sorted[s.i]
    ) THEN
        RETURN FALSE;
    END IF;

    SELECT COALESCE(
        array_agg(value ORDER BY value),
        ARRAY[]::INTEGER[]
    )
    INTO v_expected
    FROM unnest(p_original) AS value;

    RETURN v_expected = p_sorted;
END;
$$;

-- ---------------------------------------------------------
-- BENCHMARK RECORDING
-- ---------------------------------------------------------

CREATE OR REPLACE FUNCTION record_benchmark(
    p_algorithm VARCHAR,
    p_dataset_id BIGINT,
    p_status VARCHAR DEFAULT 'SUCCESS'
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_dataset INTEGER[];
    v_result INTEGER[];
    v_algorithm_id SMALLINT;
    v_started TIMESTAMPTZ;
    v_elapsed BIGINT;
    v_correct BOOLEAN;
    v_run_id BIGINT;
    v_input_size INTEGER;
BEGIN
    SELECT input_values
    INTO v_dataset
    FROM benchmark_datasets
    WHERE dataset_id = p_dataset_id
    FOR SHARE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Dataset % does not exist', p_dataset_id;
    END IF;

    SELECT algorithm_id
    INTO v_algorithm_id
    FROM sorting_algorithms
    WHERE algorithm_code = upper(p_algorithm);

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Unknown algorithm: %', p_algorithm;
    END IF;

    IF upper(p_status) NOT IN ('SUCCESS', 'FAILED', 'REJECTED') THEN
        RAISE EXCEPTION 'Invalid execution status';
    END IF;

    v_input_size := cardinality(v_dataset);
    v_started := clock_timestamp();

    BEGIN
        v_result := execute_sort(
            upper(p_algorithm),
            v_dataset
        );

        v_elapsed := GREATEST(
            0,
            (EXTRACT(
                EPOCH FROM clock_timestamp() - v_started
            ) * 1000000)::BIGINT
        );

        v_correct := validate_sort_result(
            v_dataset,
            v_result
        );

        INSERT INTO benchmark_runs (
            dataset_id,
            algorithm_id,
            input_size,
            comparisons,
            swaps,
            writes,
            elapsed_microseconds,
            is_correct,
            execution_status
        )
        VALUES (
            p_dataset_id,
            v_algorithm_id,
            v_input_size,
            0,
            0,
            0,
            v_elapsed,
            v_correct,
            CASE
                WHEN v_correct THEN 'SUCCESS'
                ELSE 'FAILED'
            END
        )
        RETURNING run_id INTO v_run_id;

        RETURN v_run_id;

    EXCEPTION WHEN OTHERS THEN
        INSERT INTO benchmark_runs (
            dataset_id,
            algorithm_id,
            input_size,
            comparisons,
            swaps,
            writes,
            elapsed_microseconds,
            is_correct,
            execution_status,
            error_message
        )
        VALUES (
            p_dataset_id,
            v_algorithm_id,
            v_input_size,
            0,
            0,
            0,
            0,
            FALSE,
            'FAILED',
            SQLERRM
        )
        RETURNING run_id INTO v_run_id;

        RETURN v_run_id;
    END;
END;
$$;

-- ---------------------------------------------------------
-- REPORTING VIEW
-- ---------------------------------------------------------

CREATE VIEW benchmark_comparison AS
SELECT
    a.algorithm_code,
    a.algorithm_name,
    a.is_stable,
    d.dataset_name,
    d.distribution_type,
    r.input_size,
    r.comparisons,
    r.swaps,
    r.writes,
    r.elapsed_microseconds,
    r.execution_status,
    r.is_correct,
    r.executed_at
FROM benchmark_runs r
JOIN sorting_algorithms a
    ON a.algorithm_id = r.algorithm_id
JOIN benchmark_datasets d
    ON d.dataset_id = r.dataset_id;

COMMIT;

-- ---------------------------------------------------------
-- EXECUTABLE SORTING EXAMPLES
-- ---------------------------------------------------------

SELECT
    merge_sort(
        ARRAY[38, 27, 43, 3, 9, 82, 10, 3]
    ) AS merge_result;

SELECT
    quick_sort(
        ARRAY[38, 27, 43, 3, 9, 82, 10, 3]
    ) AS quick_result;

SELECT
    heap_sort(
        ARRAY[38, 27, 43, 3, 9, 82, 10, 3]
    ) AS heap_result;

-- Empty and single-element inputs.
SELECT merge_sort(ARRAY[]::INTEGER[]);
SELECT quick_sort(ARRAY[42]);
SELECT heap_sort(ARRAY[7, 7, 7, 7]);

-- ---------------------------------------------------------
-- AUTOMATED VALIDATION
-- ---------------------------------------------------------

DO $$
DECLARE
    v_input INTEGER[] := ARRAY[38, 27, 43, 3, 9, 82, 10, 3];
    v_expected INTEGER[] := ARRAY[3, 3, 9, 10, 27, 38, 43, 82];
    v_result INTEGER[];
    v_algorithm VARCHAR;
BEGIN
    FOREACH v_algorithm IN ARRAY ARRAY['MERGE', 'QUICK', 'HEAP']
    LOOP
        v_result := execute_sort(v_algorithm, v_input);

        IF v_result <> v_expected THEN
            RAISE EXCEPTION
                '% sorting validation failed',
                v_algorithm;
        END IF;

        IF NOT validate_sort_result(v_input, v_result) THEN
            RAISE EXCEPTION
                '% element-preservation validation failed',
                v_algorithm;
        END IF;

        RAISE NOTICE '% sorting passed', v_algorithm;
    END LOOP;

    IF merge_sort(ARRAY[]::INTEGER[]) <> ARRAY[]::INTEGER[] THEN
        RAISE EXCEPTION 'Empty-array validation failed';
    END IF;

    IF quick_sort(ARRAY[42]) <> ARRAY[42] THEN
        RAISE EXCEPTION 'Single-element validation failed';
    END IF;

    IF heap_sort(ARRAY[5, 5, 5]) <> ARRAY[5, 5, 5] THEN
        RAISE EXCEPTION 'Duplicate validation failed';
    END IF;
END;
$$;

-- ---------------------------------------------------------
-- BENCHMARK WORKFLOW
-- ---------------------------------------------------------

-- Record executions for every algorithm and dataset.
DO $$
DECLARE
    v_dataset RECORD;
    v_algorithm VARCHAR;
BEGIN
    FOR v_dataset IN
        SELECT dataset_id
        FROM benchmark_datasets
        ORDER BY dataset_id
    LOOP
        FOREACH v_algorithm IN ARRAY
            ARRAY['MERGE', 'QUICK', 'HEAP']
        LOOP
            PERFORM record_benchmark(
                v_algorithm,
                v_dataset.dataset_id,
                'SUCCESS'
            );
        END LOOP;
    END LOOP;
END;
$$;

-- ---------------------------------------------------------
-- RETRIEVAL AND REPORTING
-- ---------------------------------------------------------

-- Complete benchmark history.
SELECT *
FROM benchmark_comparison
ORDER BY dataset_name, algorithm_code;

-- Performance grouped by algorithm.
SELECT
    algorithm_code,
    COUNT(*) AS total_runs,
    COUNT(*) FILTER (
        WHERE is_correct
          AND execution_status = 'SUCCESS'
    ) AS successful_runs,
    AVG(elapsed_microseconds) AS average_microseconds,
    MAX(elapsed_microseconds) AS maximum_microseconds,
    AVG(comparisons) AS average_comparisons
FROM benchmark_comparison
GROUP BY algorithm_code
ORDER BY algorithm_code;

-- Dataset-specific comparison.
SELECT
    dataset_name,
    algorithm_code,
    input_size,
    elapsed_microseconds,
    execution_status,
    is_correct
FROM benchmark_comparison
WHERE dataset_name = 'random_small'
ORDER BY elapsed_microseconds;

-- Identify unsuccessful runs.
SELECT
    run_id,
    algorithm_code,
    dataset_name,
    execution_status,
    error_message
FROM benchmark_comparison
WHERE execution_status <> 'SUCCESS'
   OR NOT is_correct;

-- Eligibility for selecting a sorting algorithm.
-- The selection uses correctness and algorithmic guarantees.
SELECT
    algorithm_code,
    algorithm_name,
    is_stable,
    worst_time_complexity,
    CASE
        WHEN is_stable
             AND worst_time_complexity = 'O(n log n)'
            THEN 'Suitable for guaranteed stable sorting'
        WHEN worst_time_complexity = 'O(n log n)'
            THEN 'Suitable for guaranteed time complexity'
        ELSE 'Requires workload-specific evaluation'
    END AS selection_guidance
FROM sorting_algorithms
ORDER BY algorithm_id;

-- CTE-based comparison report.
WITH successful_runs AS (
    SELECT
        algorithm_code,
        distribution_type,
        AVG(elapsed_microseconds) AS avg_time
    FROM benchmark_comparison
    WHERE execution_status = 'SUCCESS'
      AND is_correct
    GROUP BY algorithm_code, distribution_type
),
ranked_results AS (
    SELECT
        algorithm_code,
        distribution_type,
        avg_time,
        RANK() OVER (
            PARTITION BY distribution_type
            ORDER BY avg_time
        ) AS performance_rank
    FROM successful_runs
)
SELECT *
FROM ranked_results
ORDER BY distribution_type, performance_rank;

-- Database metadata.
SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'sorting_lab'
ORDER BY table_name, ordinal_position;
