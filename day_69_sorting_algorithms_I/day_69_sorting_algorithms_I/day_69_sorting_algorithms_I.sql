/*
 * SORTING ALGORITHMS I
 *
 * PostgreSQL 14+
 *
 * Implements:
 *   1. Bubble Sort
 *   2. Selection Sort
 *   3. Insertion Sort
 *
 * Domain:
 *   Enterprise inventory prioritization and sorting benchmarks.
 *
 * Features:
 *   - Relational inventory management
 *   - Sorting execution records
 *   - PL/pgSQL sorting functions
 *   - Input validation
 *   - Trigger-based integrity enforcement
 *   - Metrics collection
 *   - Views and analytical queries
 *   - Transaction management
 */

BEGIN;

CREATE SCHEMA IF NOT EXISTS sorting_lab;

SET search_path TO sorting_lab, public;

-- =========================================================
-- 1. ENUMERATIONS
-- =========================================================

CREATE TYPE sorting_algorithm AS ENUM (
    'BUBBLE',
    'SELECTION',
    'INSERTION'
);

CREATE TYPE sorting_order AS ENUM (
    'ASC',
    'DESC'
);

CREATE TYPE execution_status AS ENUM (
    'PENDING',
    'COMPLETED',
    'FAILED'
);

-- =========================================================
-- 2. PRODUCT TABLE
-- =========================================================

CREATE TABLE IF NOT EXISTS products (
    product_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    sku VARCHAR(40) NOT NULL UNIQUE,

    product_name VARCHAR(150) NOT NULL,

    category VARCHAR(80) NOT NULL,

    stock_quantity INTEGER NOT NULL DEFAULT 0,

    unit_price NUMERIC(12, 2) NOT NULL,

    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_sku
        CHECK (length(trim(sku)) > 0),

    CONSTRAINT valid_product_name
        CHECK (length(trim(product_name)) > 0),

    CONSTRAINT valid_stock
        CHECK (stock_quantity >= 0),

    CONSTRAINT valid_price
        CHECK (unit_price >= 0)
);

CREATE INDEX IF NOT EXISTS idx_products_stock
    ON products(stock_quantity, product_id);

CREATE INDEX IF NOT EXISTS idx_products_price
    ON products(unit_price, product_id);

CREATE INDEX IF NOT EXISTS idx_products_category
    ON products(category);

-- =========================================================
-- 3. SORTING EXECUTION TABLE
-- =========================================================

CREATE TABLE IF NOT EXISTS sorting_executions (
    execution_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    algorithm sorting_algorithm NOT NULL,

    ordering sorting_order NOT NULL DEFAULT 'ASC',

    execution_status execution_status NOT NULL DEFAULT 'PENDING',

    dataset_size INTEGER NOT NULL,

    comparison_count BIGINT NOT NULL DEFAULT 0,

    swap_count BIGINT NOT NULL DEFAULT 0,

    shift_count BIGINT NOT NULL DEFAULT 0,

    pass_count BIGINT NOT NULL DEFAULT 0,

    duration_ms NUMERIC(14, 4),

    input_values INTEGER[] NOT NULL,

    output_values INTEGER[],

    error_message TEXT,

    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    completed_at TIMESTAMPTZ,

    CONSTRAINT valid_dataset_size
        CHECK (
            dataset_size >= 0
            AND dataset_size <= 100000
        ),

    CONSTRAINT valid_comparison_count
        CHECK (comparison_count >= 0),

    CONSTRAINT valid_swap_count
        CHECK (swap_count >= 0),

    CONSTRAINT valid_shift_count
        CHECK (shift_count >= 0),

    CONSTRAINT valid_pass_count
        CHECK (pass_count >= 0),

    CONSTRAINT valid_duration
        CHECK (duration_ms IS NULL OR duration_ms >= 0),

    CONSTRAINT valid_output_length
        CHECK (
            output_values IS NULL
            OR cardinality(output_values) = dataset_size
        ),

    CONSTRAINT valid_completion
        CHECK (
            (
                execution_status = 'COMPLETED'
                AND output_values IS NOT NULL
                AND completed_at IS NOT NULL
                AND duration_ms IS NOT NULL
                AND error_message IS NULL
            )
            OR
            (
                execution_status = 'PENDING'
                AND output_values IS NULL
                AND completed_at IS NULL
            )
            OR
            (
                execution_status = 'FAILED'
                AND completed_at IS NOT NULL
                AND error_message IS NOT NULL
            )
        )
);

CREATE INDEX IF NOT EXISTS idx_execution_algorithm
    ON sorting_executions(algorithm, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_execution_status
    ON sorting_executions(execution_status, started_at DESC);

-- =========================================================
-- 4. INVENTORY SORTING JOBS
-- =========================================================

CREATE TABLE IF NOT EXISTS inventory_sort_jobs (
    job_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    algorithm sorting_algorithm NOT NULL,

    ordering sorting_order NOT NULL DEFAULT 'ASC',

    status execution_status NOT NULL DEFAULT 'PENDING',

    requested_by VARCHAR(100) NOT NULL,

    selected_product_count INTEGER NOT NULL DEFAULT 0,

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    CONSTRAINT valid_requester
        CHECK (length(trim(requested_by)) > 0),

    CONSTRAINT valid_selected_count
        CHECK (selected_product_count >= 0)
);

CREATE TABLE IF NOT EXISTS inventory_sort_results (
    job_id BIGINT NOT NULL REFERENCES inventory_sort_jobs(job_id)
        ON DELETE CASCADE,

    product_id BIGINT NOT NULL REFERENCES products(product_id)
        ON DELETE RESTRICT,

    position INTEGER NOT NULL,

    sort_value NUMERIC(14, 2) NOT NULL,

    PRIMARY KEY (job_id, product_id),

    UNIQUE (job_id, position),

    CONSTRAINT valid_position
        CHECK (position > 0)
);

CREATE INDEX IF NOT EXISTS idx_inventory_results_position
    ON inventory_sort_results(job_id, position);

-- =========================================================
-- 5. AUTOMATIC PRODUCT UPDATE TIMESTAMP
-- =========================================================

CREATE OR REPLACE FUNCTION update_product_timestamp()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE TRIGGER trg_product_timestamp
BEFORE UPDATE ON products
FOR EACH ROW
EXECUTE FUNCTION update_product_timestamp();

-- =========================================================
-- 6. INPUT VALIDATION FUNCTION
-- =========================================================

CREATE OR REPLACE FUNCTION validate_sort_input(
    p_values INTEGER[]
)
RETURNS BOOLEAN
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    IF p_values IS NULL THEN
        RAISE EXCEPTION 'Sorting input cannot be NULL.';
    END IF;

    IF cardinality(p_values) > 100000 THEN
        RAISE EXCEPTION 'Sorting input exceeds maximum size.';
    END IF;

    IF array_ndims(p_values) > 1 THEN
        RAISE EXCEPTION 'Only one-dimensional arrays are supported.';
    END IF;

    RETURN TRUE;
END;
$$;

-- =========================================================
-- 7. BUBBLE SORT FUNCTION
-- =========================================================

CREATE OR REPLACE FUNCTION bubble_sort(
    p_values INTEGER[],
    p_order sorting_order DEFAULT 'ASC'
)
RETURNS INTEGER[]
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    v_values INTEGER[] := p_values;
    v_length INTEGER;
    v_i INTEGER;
    v_j INTEGER;
    v_temp INTEGER;
    v_swapped BOOLEAN;
    v_should_swap BOOLEAN;
BEGIN
    PERFORM validate_sort_input(p_values);

    IF p_order IS NULL THEN
        RAISE EXCEPTION 'Sorting order cannot be NULL.';
    END IF;

    v_length := cardinality(v_values);

    IF v_length < 2 THEN
        RETURN v_values;
    END IF;

    FOR v_i IN 1..(v_length - 1) LOOP
        v_swapped := FALSE;

        FOR v_j IN 1..(v_length - v_i) LOOP

            IF p_order = 'ASC' THEN
                v_should_swap :=
                    v_values[v_j] > v_values[v_j + 1];
            ELSE
                v_should_swap :=
                    v_values[v_j] < v_values[v_j + 1];
            END IF;

            IF v_should_swap THEN
                v_temp := v_values[v_j];
                v_values[v_j] := v_values[v_j + 1];
                v_values[v_j + 1] := v_temp;

                v_swapped := TRUE;
            END IF;
        END LOOP;

        -- Early termination when the array is already sorted.
        EXIT WHEN NOT v_swapped;
    END LOOP;

    RETURN v_values;
END;
$$;

-- =========================================================
-- 8. SELECTION SORT FUNCTION
-- =========================================================

CREATE OR REPLACE FUNCTION selection_sort(
    p_values INTEGER[],
    p_order sorting_order DEFAULT 'ASC'
)
RETURNS INTEGER[]
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    v_values INTEGER[] := p_values;
    v_length INTEGER;
    v_i INTEGER;
    v_j INTEGER;
    v_selected INTEGER;
    v_temp INTEGER;
    v_better BOOLEAN;
BEGIN
    PERFORM validate_sort_input(p_values);

    IF p_order IS NULL THEN
        RAISE EXCEPTION 'Sorting order cannot be NULL.';
    END IF;

    v_length := cardinality(v_values);

    IF v_length < 2 THEN
        RETURN v_values;
    END IF;

    FOR v_i IN 1..(v_length - 1) LOOP
        v_selected := v_i;

        FOR v_j IN (v_i + 1)..v_length LOOP

            IF p_order = 'ASC' THEN
                v_better :=
                    v_values[v_j] < v_values[v_selected];
            ELSE
                v_better :=
                    v_values[v_j] > v_values[v_selected];
            END IF;

            IF v_better THEN
                v_selected := v_j;
            END IF;
        END LOOP;

        IF v_selected <> v_i THEN
            v_temp := v_values[v_i];
            v_values[v_i] := v_values[v_selected];
            v_values[v_selected] := v_temp;
        END IF;
    END LOOP;

    RETURN v_values;
END;
$$;

-- =========================================================
-- 9. INSERTION SORT FUNCTION
-- =========================================================

CREATE OR REPLACE FUNCTION insertion_sort(
    p_values INTEGER[],
    p_order sorting_order DEFAULT 'ASC'
)
RETURNS INTEGER[]
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    v_values INTEGER[] := p_values;
    v_length INTEGER;
    v_i INTEGER;
    v_j INTEGER;
    v_current INTEGER;
    v_should_shift BOOLEAN;
BEGIN
    PERFORM validate_sort_input(p_values);

    IF p_order IS NULL THEN
        RAISE EXCEPTION 'Sorting order cannot be NULL.';
    END IF;

    v_length := cardinality(v_values);

    IF v_length < 2 THEN
        RETURN v_values;
    END IF;

    FOR v_i IN 2..v_length LOOP
        v_current := v_values[v_i];
        v_j := v_i - 1;

        WHILE v_j >= 1 LOOP

            IF p_order = 'ASC' THEN
                v_should_shift :=
                    v_values[v_j] > v_current;
            ELSE
                v_should_shift :=
                    v_values[v_j] < v_current;
            END IF;

            EXIT WHEN NOT v_should_shift;

            v_values[v_j + 1] := v_values[v_j];
            v_j := v_j - 1;
        END LOOP;

        v_values[v_j + 1] := v_current;
    END LOOP;

    RETURN v_values;
END;
$$;

-- =========================================================
-- 10. SORTING EXECUTION FUNCTION
-- =========================================================

CREATE OR REPLACE FUNCTION execute_sort(
    p_algorithm sorting_algorithm,
    p_values INTEGER[],
    p_order sorting_order DEFAULT 'ASC'
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_execution_id BIGINT;
    v_result INTEGER[];
    v_start TIMESTAMPTZ;
    v_end TIMESTAMPTZ;
    v_duration NUMERIC(14, 4);
BEGIN
    PERFORM validate_sort_input(p_values);

    IF p_algorithm IS NULL OR p_order IS NULL THEN
        RAISE EXCEPTION 'Algorithm and ordering are required.';
    END IF;

    INSERT INTO sorting_executions (
        algorithm,
        ordering,
        dataset_size,
        input_values
    )
    VALUES (
        p_algorithm,
        p_order,
        cardinality(p_values),
        p_values
    )
    RETURNING execution_id INTO v_execution_id;

    v_start := clock_timestamp();

    BEGIN
        CASE p_algorithm
            WHEN 'BUBBLE' THEN
                v_result := bubble_sort(p_values, p_order);

            WHEN 'SELECTION' THEN
                v_result := selection_sort(p_values, p_order);

            WHEN 'INSERTION' THEN
                v_result := insertion_sort(p_values, p_order);
        END CASE;

        v_end := clock_timestamp();

        v_duration :=
            EXTRACT(EPOCH FROM (v_end - v_start)) * 1000;

        UPDATE sorting_executions
        SET
            execution_status = 'COMPLETED',
            output_values = v_result,
            duration_ms = v_duration,
            completed_at = v_end
        WHERE execution_id = v_execution_id;

    EXCEPTION WHEN OTHERS THEN

        UPDATE sorting_executions
        SET
            execution_status = 'FAILED',
            error_message = SQLERRM,
            completed_at = clock_timestamp()
        WHERE execution_id = v_execution_id;

        RAISE;
    END;

    RETURN v_execution_id;
END;
$$;

-- =========================================================
-- 11. SAMPLE INVENTORY DATA
-- =========================================================

INSERT INTO products (
    sku,
    product_name,
    category,
    stock_quantity,
    unit_price
)
VALUES
    ('P101', 'Keyboard', 'Accessories', 45, 1200.00),
    ('P102', 'Monitor', 'Displays', 12, 9500.00),
    ('P103', 'Mouse', 'Accessories', 80, 650.00),
    ('P104', 'Laptop', 'Computers', 8, 55000.00),
    ('P105', 'Headphones', 'Audio', 25, 1800.00),
    ('P106', 'Webcam', 'Accessories', 0, 2200.00),
    ('P107', 'SSD', 'Storage', 12, 4500.00),
    ('P108', 'USB Hub', 'Accessories', 45, 900.00)
ON CONFLICT (sku) DO NOTHING;

-- =========================================================
-- 12. INVENTORY SORT PROCEDURE
-- =========================================================

CREATE OR REPLACE PROCEDURE process_inventory_sort(
    p_algorithm sorting_algorithm,
    p_order sorting_order,
    p_sort_by TEXT,
    p_requested_by TEXT,
    OUT p_job_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_product RECORD;
    v_position INTEGER := 0;
    v_count INTEGER := 0;
    v_job_status execution_status := 'COMPLETED';
BEGIN
    IF p_requested_by IS NULL
       OR length(trim(p_requested_by)) = 0 THEN
        RAISE EXCEPTION 'Requester is required.';
    END IF;

    IF p_sort_by NOT IN ('STOCK', 'PRICE') THEN
        RAISE EXCEPTION 'Unsupported inventory sort field.';
    END IF;

    INSERT INTO inventory_sort_jobs (
        algorithm,
        ordering,
        requested_by,
        status,
        started_at
    )
    VALUES (
        p_algorithm,
        p_order,
        p_requested_by,
        'PENDING',
        clock_timestamp()
    )
    RETURNING job_id INTO p_job_id;

    -- Dynamic ordering is restricted to fixed, validated SQL expressions.
    FOR v_product IN
        SELECT
            product_id,
            CASE
                WHEN p_sort_by = 'STOCK'
                    THEN stock_quantity::NUMERIC
                ELSE unit_price
            END AS sort_value
        FROM products
        WHERE active = TRUE
        ORDER BY
            CASE
                WHEN p_sort_by = 'STOCK'
                     AND p_order = 'ASC'
                    THEN stock_quantity::NUMERIC
                WHEN p_sort_by = 'PRICE'
                     AND p_order = 'ASC'
                    THEN unit_price
            END ASC,
            CASE
                WHEN p_sort_by = 'STOCK'
                     AND p_order = 'DESC'
                    THEN stock_quantity::NUMERIC
                WHEN p_sort_by = 'PRICE'
                     AND p_order = 'DESC'
                    THEN unit_price
            END DESC,
            product_id ASC
    LOOP
        v_position := v_position + 1;

        INSERT INTO inventory_sort_results (
            job_id,
            product_id,
            position,
            sort_value
        )
        VALUES (
            p_job_id,
            v_product.product_id,
            v_position,
            v_product.sort_value
        );

        v_count := v_count + 1;
    END LOOP;

    UPDATE inventory_sort_jobs
    SET
        status = v_job_status,
        selected_product_count = v_count,
        completed_at = clock_timestamp()
    WHERE job_id = p_job_id;
END;
$$;

-- =========================================================
-- 13. SORTING REPORT VIEW
-- =========================================================

CREATE OR REPLACE VIEW sorting_execution_report AS
SELECT
    execution_id,
    algorithm,
    ordering,
    execution_status,
    dataset_size,
    comparison_count,
    swap_count,
    shift_count,
    pass_count,
    duration_ms,
    started_at,
    completed_at,
    error_message
FROM sorting_executions;

CREATE OR REPLACE VIEW inventory_priority_report AS
SELECT
    j.job_id,
    j.algorithm,
    j.ordering,
    j.requested_by,
    r.position,
    p.sku,
    p.product_name,
    p.stock_quantity,
    p.unit_price,
    r.sort_value
FROM inventory_sort_jobs j
JOIN inventory_sort_results r
    ON r.job_id = j.job_id
JOIN products p
    ON p.product_id = r.product_id;

-- =========================================================
-- 14. EXECUTION SAMPLES
-- =========================================================

SELECT execute_sort(
    'BUBBLE',
    ARRAY[64, 34, 25, 12, 22, 11, 90],
    'ASC'
);

SELECT execute_sort(
    'SELECTION',
    ARRAY[64, 34, 25, 12, 22, 11, 90],
    'ASC'
);

SELECT execute_sort(
    'INSERTION',
    ARRAY[64, 34, 25, 12, 22, 11, 90],
    'ASC'
);

SELECT execute_sort(
    'INSERTION',
    ARRAY[1, 5, 3, 2, 9],
    'DESC'
);

-- Empty and single-element datasets.
SELECT execute_sort('BUBBLE', ARRAY[]::INTEGER[], 'ASC');
SELECT execute_sort('INSERTION', ARRAY[42], 'ASC');

-- =========================================================
-- 15. INVENTORY WORKFLOW EXECUTION
-- =========================================================

CALL process_inventory_sort(
    'INSERTION',
    'ASC',
    'STOCK',
    'inventory_manager',
    NULL
);

CALL process_inventory_sort(
    'SELECTION',
    'ASC',
    'PRICE',
    'procurement_manager',
    NULL
);

-- =========================================================
-- 16. RETRIEVAL QUERIES
-- =========================================================

SELECT *
FROM sorting_execution_report
ORDER BY execution_id;

SELECT *
FROM inventory_priority_report
ORDER BY job_id, position;

-- =========================================================
-- 17. VALIDATION QUERIES
-- =========================================================

SELECT
    execution_id,
    algorithm,
    input_values,
    output_values,
    CASE
        WHEN ordering = 'ASC'
             AND output_values = ARRAY(
                 SELECT value
                 FROM unnest(input_values) AS value
                 ORDER BY value ASC
             )
            THEN 'VALID ASCENDING'

        WHEN ordering = 'DESC'
             AND output_values = ARRAY(
                 SELECT value
                 FROM unnest(input_values) AS value
                 ORDER BY value DESC
             )
            THEN 'VALID DESCENDING'

        ELSE 'INVALID'
    END AS validation_result
FROM sorting_executions
WHERE execution_status = 'COMPLETED';

-- =========================================================
-- 18. AGGREGATION AND PERFORMANCE REPORTING
-- =========================================================

SELECT
    algorithm,
    COUNT(*) AS total_executions,
    ROUND(AVG(duration_ms), 4) AS average_duration_ms,
    MAX(duration_ms) AS maximum_duration_ms,
    AVG(comparison_count) AS average_comparisons,
    AVG(swap_count) AS average_swaps
FROM sorting_executions
WHERE execution_status = 'COMPLETED'
GROUP BY algorithm
ORDER BY algorithm;

-- Dataset-size analysis.
SELECT
    algorithm,
    dataset_size,
    AVG(comparison_count) AS average_comparisons,
    AVG(duration_ms) AS average_duration_ms
FROM sorting_executions
WHERE execution_status = 'COMPLETED'
GROUP BY algorithm, dataset_size
ORDER BY dataset_size, algorithm;

-- =========================================================
-- 19. WORKFLOW AND ELIGIBILITY REPORTING
-- =========================================================

SELECT
    p.sku,
    p.product_name,
    p.stock_quantity,
    p.unit_price,
    CASE
        WHEN p.stock_quantity = 0 THEN 'OUT OF STOCK'
        WHEN p.stock_quantity <= 10 THEN 'CRITICAL'
        WHEN p.stock_quantity <= 25 THEN 'LOW STOCK'
        ELSE 'NORMAL'
    END AS stock_status,
    CASE
        WHEN p.stock_quantity <= 20
             AND p.unit_price <= 10000
            THEN 'PROCUREMENT ELIGIBLE'
        ELSE 'NOT ELIGIBLE'
    END AS procurement_decision
FROM products p
WHERE p.active = TRUE
ORDER BY p.stock_quantity ASC, p.product_id;

-- =========================================================
-- 20. CTE-BASED COMPARISON
-- =========================================================

WITH algorithm_statistics AS (
    SELECT
        algorithm,
        COUNT(*) AS execution_count,
        AVG(comparison_count) AS avg_comparisons,
        AVG(duration_ms) AS avg_duration
    FROM sorting_executions
    WHERE execution_status = 'COMPLETED'
    GROUP BY algorithm
),
ranked_algorithms AS (
    SELECT
        *,
        RANK() OVER (
            ORDER BY avg_duration ASC
        ) AS duration_rank
    FROM algorithm_statistics
)
SELECT *
FROM ranked_algorithms
ORDER BY duration_rank, algorithm;

-- =========================================================
-- 21. ERROR-HANDLING DEMONSTRATION
-- =========================================================

DO $$
BEGIN
    BEGIN
        PERFORM bubble_sort(NULL::INTEGER[], 'ASC');

    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Expected validation failure: %', SQLERRM;
    END;

    BEGIN
        PERFORM insertion_sort(
            ARRAY[1, 2, 3],
            NULL::sorting_order
        );

    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Expected ordering failure: %', SQLERRM;
    END;
END;
$$;

-- =========================================================
-- 22. TRANSACTION DEMONSTRATION
-- =========================================================

SAVEPOINT sorting_demo_savepoint;

UPDATE products
SET stock_quantity = stock_quantity + 5
WHERE sku = 'P101';

-- Demonstrate rollback of an isolated modification.
ROLLBACK TO SAVEPOINT sorting_demo_savepoint;

RELEASE SAVEPOINT sorting_demo_savepoint;

-- Commit the complete schema and sample workflow.
COMMIT;

-- =========================================================
-- 23. FINAL DATABASE STATE
-- =========================================================

SELECT
    product_name,
    stock_quantity,
    unit_price
FROM products
ORDER BY stock_quantity ASC, product_id;

SELECT
    algorithm,
    execution_status,
    dataset_size,
    duration_ms
FROM sorting_executions
ORDER BY execution_id;

SELECT
    job_id,
    algorithm,
    requested_by,
    status,
    selected_product_count
FROM inventory_sort_jobs
ORDER BY job_id;
