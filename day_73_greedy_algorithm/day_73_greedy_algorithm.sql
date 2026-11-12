BEGIN;

CREATE SCHEMA IF NOT EXISTS greedy_lab;

SET search_path TO greedy_lab, public;

-- Remove existing objects in dependency order for repeatable execution.
DROP VIEW IF EXISTS activity_selection_report CASCADE;
DROP VIEW IF EXISTS knapsack_allocation_report CASCADE;
DROP VIEW IF EXISTS huffman_code_report CASCADE;

DROP TABLE IF EXISTS huffman_codes CASCADE;
DROP TABLE IF EXISTS huffman_nodes CASCADE;
DROP TABLE IF EXISTS huffman_symbols CASCADE;
DROP TABLE IF EXISTS knapsack_allocations CASCADE;
DROP TABLE IF EXISTS knapsack_items CASCADE;
DROP TABLE IF EXISTS knapsack_problems CASCADE;
DROP TABLE IF EXISTS activity_decisions CASCADE;
DROP TABLE IF EXISTS activities CASCADE;
DROP TABLE IF EXISTS algorithm_runs CASCADE;

DROP FUNCTION IF EXISTS validate_activity_interval() CASCADE;
DROP FUNCTION IF EXISTS record_activity_decision() CASCADE;
DROP FUNCTION IF EXISTS calculate_fractional_knapsack(BIGINT) CASCADE;
DROP FUNCTION IF EXISTS calculate_activity_selection(BIGINT) CASCADE;
DROP FUNCTION IF EXISTS calculate_huffman_cost(BIGINT) CASCADE;
DROP FUNCTION IF EXISTS evaluate_run(BIGINT) CASCADE;

CREATE TABLE algorithm_runs (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    algorithm_type VARCHAR(40) NOT NULL,
    run_name VARCHAR(120) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    execution_metadata JSONB NOT NULL DEFAULT '{}'::JSONB,

    CONSTRAINT valid_algorithm_type CHECK (
        algorithm_type IN (
            'ACTIVITY_SELECTION',
            'FRACTIONAL_KNAPSACK',
            'HUFFMAN_CODING'
        )
    ),

    CONSTRAINT valid_run_status CHECK (
        status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED')
    ),

    CONSTRAINT valid_completion_time CHECK (
        completed_at IS NULL OR completed_at >= created_at
    )
);

CREATE TABLE activities (
    activity_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES algorithm_runs(run_id)
        ON DELETE CASCADE,
    external_id VARCHAR(60) NOT NULL,
    start_time INTEGER NOT NULL,
    finish_time INTEGER NOT NULL,
    priority INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT unique_activity_per_run UNIQUE(run_id, external_id),
    CONSTRAINT valid_activity_interval CHECK (
        start_time >= 0 AND finish_time > start_time
    )
);

CREATE INDEX idx_activities_finish
ON activities(run_id, finish_time, start_time);

CREATE TABLE activity_decisions (
    decision_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES algorithm_runs(run_id)
        ON DELETE CASCADE,
    activity_id BIGINT NOT NULL REFERENCES activities(activity_id)
        ON DELETE CASCADE,
    decision VARCHAR(12) NOT NULL,
    decision_order INTEGER NOT NULL,
    previous_finish INTEGER,
    decision_reason TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_activity_decision UNIQUE(activity_id),
    CONSTRAINT valid_activity_decision CHECK (
        decision IN ('SELECTED', 'REJECTED')
    ),
    CONSTRAINT valid_decision_order CHECK (decision_order > 0)
);

CREATE TABLE knapsack_problems (
    problem_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id BIGINT NOT NULL UNIQUE REFERENCES algorithm_runs(run_id)
        ON DELETE CASCADE,
    capacity NUMERIC(14, 3) NOT NULL,
    total_value NUMERIC(18, 3) NOT NULL DEFAULT 0,
    used_capacity NUMERIC(14, 3) NOT NULL DEFAULT 0,
    CONSTRAINT positive_capacity CHECK (capacity >= 0),
    CONSTRAINT nonnegative_total_value CHECK (total_value >= 0),
    CONSTRAINT valid_used_capacity CHECK (
        used_capacity >= 0 AND used_capacity <= capacity
    )
);

CREATE TABLE knapsack_items (
    item_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    problem_id BIGINT NOT NULL REFERENCES knapsack_problems(problem_id)
        ON DELETE CASCADE,
    external_id VARCHAR(60) NOT NULL,
    item_value NUMERIC(14, 3) NOT NULL,
    item_weight NUMERIC(14, 3) NOT NULL,
    value_weight_ratio NUMERIC(18, 8)
        GENERATED ALWAYS AS (
            item_value / NULLIF(item_weight, 0)
        ) STORED,

    CONSTRAINT unique_item_per_problem UNIQUE(problem_id, external_id),
    CONSTRAINT nonnegative_item_value CHECK (item_value >= 0),
    CONSTRAINT positive_item_weight CHECK (item_weight > 0)
);

CREATE INDEX idx_knapsack_item_ratio
ON knapsack_items(problem_id, value_weight_ratio DESC);

CREATE TABLE knapsack_allocations (
    allocation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    problem_id BIGINT NOT NULL REFERENCES knapsack_problems(problem_id)
        ON DELETE CASCADE,
    item_id BIGINT NOT NULL REFERENCES knapsack_items(item_id)
        ON DELETE CASCADE,
    allocated_fraction NUMERIC(12, 8) NOT NULL,
    allocated_weight NUMERIC(14, 3) NOT NULL,
    allocated_value NUMERIC(14, 3) NOT NULL,

    CONSTRAINT unique_item_allocation UNIQUE(item_id),
    CONSTRAINT valid_fraction CHECK (
        allocated_fraction > 0 AND allocated_fraction <= 1
    ),
    CONSTRAINT valid_allocated_weight CHECK (allocated_weight > 0),
    CONSTRAINT valid_allocated_value CHECK (allocated_value >= 0)
);

CREATE TABLE huffman_symbols (
    symbol_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES algorithm_runs(run_id)
        ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    frequency BIGINT NOT NULL,

    CONSTRAINT unique_symbol_per_run UNIQUE(run_id, symbol),
    CONSTRAINT single_character_symbol CHECK (char_length(symbol) = 1),
    CONSTRAINT positive_symbol_frequency CHECK (frequency > 0)
);

CREATE INDEX idx_huffman_frequency
ON huffman_symbols(run_id, frequency);

CREATE TABLE huffman_nodes (
    node_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES algorithm_runs(run_id)
        ON DELETE CASCADE,
    parent_node_id BIGINT REFERENCES huffman_nodes(node_id),
    left_node_id BIGINT REFERENCES huffman_nodes(node_id),
    right_node_id BIGINT REFERENCES huffman_nodes(node_id),
    symbol_id BIGINT REFERENCES huffman_symbols(symbol_id),
    combined_frequency BIGINT NOT NULL,
    merge_order INTEGER NOT NULL,

    CONSTRAINT nonnegative_combined_frequency CHECK (
        combined_frequency > 0
    ),
    CONSTRAINT valid_merge_order CHECK (merge_order >= 0),
    CONSTRAINT valid_node_children CHECK (
        left_node_id IS NULL OR right_node_id IS NOT NULL
    )
);

CREATE TABLE huffman_codes (
    code_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES algorithm_runs(run_id)
        ON DELETE CASCADE,
    symbol_id BIGINT NOT NULL REFERENCES huffman_symbols(symbol_id)
        ON DELETE CASCADE,
    binary_code TEXT NOT NULL,

    CONSTRAINT unique_huffman_code UNIQUE(run_id, symbol_id),
    CONSTRAINT nonempty_binary_code CHECK (
        binary_code ~ '^[01]+$'
    )
);

-- Enforce activity interval validity before insertion or modification.
CREATE FUNCTION validate_activity_interval()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.start_time < 0 OR NEW.finish_time <= NEW.start_time THEN
        RAISE EXCEPTION
            'Invalid activity interval: % to %',
            NEW.start_time,
            NEW.finish_time;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_activity
BEFORE INSERT OR UPDATE ON activities
FOR EACH ROW
EXECUTE FUNCTION validate_activity_interval();

-- Prevent a decision from referencing an activity belonging to another run.
CREATE FUNCTION record_activity_decision()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    actual_run_id BIGINT;
BEGIN
    SELECT run_id
    INTO actual_run_id
    FROM activities
    WHERE activity_id = NEW.activity_id;

    IF actual_run_id IS NULL OR actual_run_id <> NEW.run_id THEN
        RAISE EXCEPTION
            'Decision run does not match activity run.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_activity_decision_integrity
BEFORE INSERT OR UPDATE ON activity_decisions
FOR EACH ROW
EXECUTE FUNCTION record_activity_decision();

-- Earliest-finish-time activity selection.
CREATE FUNCTION calculate_activity_selection(p_run_id BIGINT)
RETURNS TABLE (
    selected_activity_id BIGINT,
    selected_external_id VARCHAR,
    activity_start INTEGER,
    activity_finish INTEGER,
    selection_order BIGINT
)
LANGUAGE sql
STABLE
AS $$
    WITH ordered AS (
        SELECT
            a.activity_id,
            a.external_id,
            a.start_time,
            a.finish_time,
            ROW_NUMBER() OVER (
                ORDER BY
                    a.finish_time,
                    a.start_time,
                    a.external_id
            ) AS position
        FROM activities a
        WHERE a.run_id = p_run_id
    ),
    RECURSIVE_SELECTION AS (
        SELECT
            o.activity_id,
            o.external_id,
            o.start_time,
            o.finish_time,
            o.position,
            1::BIGINT AS selection_order
        FROM ordered o
        WHERE o.position = 1

        UNION ALL

        SELECT
            o.activity_id,
            o.external_id,
            o.start_time,
            o.finish_time,
            o.position,
            CASE
                WHEN o.start_time >= previous.finish_time
                    THEN previous.selection_order + 1
                ELSE previous.selection_order
            END
        FROM RECURSIVE_SELECTION previous
        JOIN ordered o
          ON o.position = previous.position + 1
        WHERE NOT EXISTS (
            SELECT 1
            FROM RECURSIVE_SELECTION prior
            WHERE prior.position = o.position
        )
    )
    SELECT
        rs.activity_id,
        rs.external_id,
        rs.start_time,
        rs.finish_time,
        rs.selection_order
    FROM RECURSIVE_SELECTION rs
    WHERE rs.position = 1
       OR rs.start_time >= (
            SELECT MAX(previous.finish_time)
            FROM RECURSIVE_SELECTION previous
            WHERE previous.position < rs.position
       )
    ORDER BY rs.selection_order;
$$;

-- Fractional knapsack uses a window-based cumulative weight calculation.
CREATE FUNCTION calculate_fractional_knapsack(p_problem_id BIGINT)
RETURNS TABLE (
    selected_item_id BIGINT,
    selected_external_id VARCHAR,
    value_weight_ratio NUMERIC,
    allocation_fraction NUMERIC,
    allocated_weight NUMERIC,
    allocated_value NUMERIC
)
LANGUAGE sql
STABLE
AS $$
    WITH problem AS (
        SELECT capacity
        FROM knapsack_problems
        WHERE problem_id = p_problem_id
    ),
    ordered AS (
        SELECT
            item_id,
            external_id,
            item_value,
            item_weight,
            value_weight_ratio,
            COALESCE(
                SUM(item_weight) OVER (
                    ORDER BY
                        value_weight_ratio DESC,
                        external_id
                    ROWS BETWEEN UNBOUNDED PRECEDING
                    AND 1 PRECEDING
                ),
                0
            ) AS previous_weight
        FROM knapsack_items
        WHERE problem_id = p_problem_id
    ),
    allocations AS (
        SELECT
            o.*,
            p.capacity,
            GREATEST(
                0,
                LEAST(
                    1,
                    (p.capacity - o.previous_weight) /
                    o.item_weight
                )
            ) AS fraction
        FROM ordered o
        CROSS JOIN problem p
    )
    SELECT
        a.item_id,
        a.external_id,
        a.value_weight_ratio,
        ROUND(a.fraction, 8),
        ROUND(a.item_weight * a.fraction, 3),
        ROUND(a.item_value * a.fraction, 3)
    FROM allocations a
    WHERE a.fraction > 0
    ORDER BY a.value_weight_ratio DESC, a.external_id;
$$;

-- Calculate Huffman weighted path length from stored codes.
CREATE FUNCTION calculate_huffman_cost(p_run_id BIGINT)
RETURNS BIGINT
LANGUAGE sql
STABLE
AS $$
    SELECT COALESCE(
        SUM(
            hs.frequency * char_length(hc.binary_code)
        ),
        0
    )::BIGINT
    FROM huffman_codes hc
    JOIN huffman_symbols hs
      ON hs.symbol_id = hc.symbol_id
    WHERE hc.run_id = p_run_id;
$$;

CREATE VIEW activity_selection_report AS
SELECT
    ar.run_id,
    ar.run_name,
    a.external_id,
    a.start_time,
    a.finish_time,
    COALESCE(ad.decision, 'NOT_PROCESSED') AS decision,
    ad.decision_order,
    ad.decision_reason
FROM algorithm_runs ar
JOIN activities a
  ON a.run_id = ar.run_id
LEFT JOIN activity_decisions ad
  ON ad.activity_id = a.activity_id;

CREATE VIEW knapsack_allocation_report AS
SELECT
    kp.problem_id,
    ar.run_name,
    ki.external_id,
    ki.item_value,
    ki.item_weight,
    ki.value_weight_ratio,
    ka.allocated_fraction,
    ka.allocated_value,
    ka.allocated_weight
FROM knapsack_problems kp
JOIN algorithm_runs ar
  ON ar.run_id = kp.run_id
JOIN knapsack_items ki
  ON ki.problem_id = kp.problem_id
LEFT JOIN knapsack_allocations ka
  ON ka.item_id = ki.item_id;

CREATE VIEW huffman_code_report AS
SELECT
    hs.run_id,
    hs.symbol,
    hs.frequency,
    hc.binary_code,
    char_length(hc.binary_code) AS code_length,
    hs.frequency * char_length(hc.binary_code) AS weighted_cost
FROM huffman_symbols hs
JOIN huffman_codes hc
  ON hc.symbol_id = hs.symbol_id;

-- Demonstrate a complete activity-selection workflow.
INSERT INTO algorithm_runs (
    algorithm_type,
    run_name,
    status
)
VALUES (
    'ACTIVITY_SELECTION',
    'Conference Room Scheduling',
    'RUNNING'
)
RETURNING run_id;

INSERT INTO algorithm_runs (
    algorithm_type,
    run_name,
    status
)
VALUES (
    'FRACTIONAL_KNAPSACK',
    'Warehouse Resource Allocation',
    'RUNNING'
)
RETURNING run_id;

INSERT INTO algorithm_runs (
    algorithm_type,
    run_name,
    status
)
VALUES (
    'HUFFMAN_CODING',
    'Text Compression Demonstration',
    'RUNNING'
)
RETURNING run_id;

-- The sample IDs are obtained deterministically for this fresh schema.
DO $$
DECLARE
    activity_run BIGINT;
    knapsack_run BIGINT;
    huffman_run BIGINT;
    problem BIGINT;
    activity_record RECORD;
    decision_number INTEGER := 0;
    previous_finish INTEGER := -1;
    selected BOOLEAN;
    item_record RECORD;
    remaining NUMERIC(14,3);
    fraction NUMERIC(12,8);
    allocated_weight NUMERIC(14,3);
    allocated_value NUMERIC(14,3);
    total_value NUMERIC(18,3) := 0;
    total_used NUMERIC(14,3) := 0;
    symbol_record RECORD;
BEGIN
    SELECT run_id INTO activity_run
    FROM algorithm_runs
    WHERE run_name = 'Conference Room Scheduling';

    SELECT run_id INTO knapsack_run
    FROM algorithm_runs
    WHERE run_name = 'Warehouse Resource Allocation';

    SELECT run_id INTO huffman_run
    FROM algorithm_runs
    WHERE run_name = 'Text Compression Demonstration';

    INSERT INTO activities (
        run_id, external_id, start_time, finish_time
    )
    VALUES
        (activity_run, 'A101', 1, 4),
        (activity_run, 'A102', 3, 5),
        (activity_run, 'A103', 0, 6),
        (activity_run, 'A104', 5, 7),
        (activity_run, 'A105', 8, 9),
        (activity_run, 'A106', 5, 9),
        (activity_run, 'A107', 2, 3);

    -- The greedy decision order is based on finish time.
    FOR activity_record IN
        SELECT *
        FROM activities
        WHERE run_id = activity_run
        ORDER BY finish_time, start_time, external_id
    LOOP
        decision_number := decision_number + 1;

        selected := activity_record.start_time >= previous_finish;

        INSERT INTO activity_decisions (
            run_id,
            activity_id,
            decision,
            decision_order,
            previous_finish,
            decision_reason
        )
        VALUES (
            activity_run,
            activity_record.activity_id,
            CASE WHEN selected THEN 'SELECTED' ELSE 'REJECTED' END,
            decision_number,
            CASE WHEN previous_finish < 0
                THEN NULL ELSE previous_finish END,
            CASE
                WHEN selected THEN
                    'Compatible with previously selected activities.'
                ELSE
                    'Overlaps a previously selected activity.'
            END
        );

        IF selected THEN
            previous_finish := activity_record.finish_time;
        END IF;
    END LOOP;

    UPDATE algorithm_runs
    SET status = 'COMPLETED',
        completed_at = CURRENT_TIMESTAMP,
        execution_metadata = jsonb_build_object(
            'selection_rule', 'EARLIEST_FINISH_TIME'
        )
    WHERE run_id = activity_run;

    -- Create fractional knapsack problem and item records.
    INSERT INTO knapsack_problems(run_id, capacity)
    VALUES (knapsack_run, 50)
    RETURNING problem_id INTO problem;

    INSERT INTO knapsack_items (
        problem_id,
        external_id,
        item_value,
        item_weight
    )
    VALUES
        (problem, 'Gold', 60, 10),
        (problem, 'Silver', 100, 20),
        (problem, 'Copper', 120, 30);

    SELECT capacity INTO remaining
    FROM knapsack_problems
    WHERE problem_id = problem;

    FOR item_record IN
        SELECT *
        FROM knapsack_items
        WHERE problem_id = problem
        ORDER BY value_weight_ratio DESC, external_id
    LOOP
        EXIT WHEN remaining <= 0;

        fraction := LEAST(
            1,
            remaining / item_record.item_weight
        );

        allocated_weight := ROUND(
            fraction * item_record.item_weight,
            3
        );

        allocated_value := ROUND(
            fraction * item_record.item_value,
            3
        );

        IF fraction > 0 THEN
            INSERT INTO knapsack_allocations (
                problem_id,
                item_id,
                allocated_fraction,
                allocated_weight,
                allocated_value
            )
            VALUES (
                problem,
                item_record.item_id,
                ROUND(fraction, 8),
                allocated_weight,
                allocated_value
            );

            remaining := GREATEST(0, remaining - allocated_weight);
            total_used := total_used + allocated_weight;
            total_value := total_value + allocated_value;
        END IF;
    END LOOP;

    UPDATE knapsack_problems
    SET total_value = total_value,
        used_capacity = total_used
    WHERE problem_id = problem;

    UPDATE algorithm_runs
    SET status = 'COMPLETED',
        completed_at = CURRENT_TIMESTAMP,
        execution_metadata = jsonb_build_object(
            'selection_rule', 'MAXIMUM_VALUE_WEIGHT_RATIO'
        )
    WHERE run_id = knapsack_run;

    -- Store frequency records for Huffman coding.
    INSERT INTO huffman_symbols (
        run_id,
        symbol,
        frequency
    )
    VALUES
        (huffman_run, 'a', 45),
        (huffman_run, 'b', 13),
        (huffman_run, 'c', 12),
        (huffman_run, 'd', 16),
        (huffman_run, 'e', 9),
        (huffman_run, 'f', 5);

    UPDATE algorithm_runs
    SET status = 'COMPLETED',
        completed_at = CURRENT_TIMESTAMP,
        execution_metadata = jsonb_build_object(
            'selection_rule', 'MINIMUM_FREQUENCY_PAIR_MERGING',
            'frequency_total', (
                SELECT SUM(frequency)
                FROM huffman_symbols
                WHERE run_id = huffman_run
            )
        )
    WHERE run_id = huffman_run;
END;
$$;

-- Evaluate whether a run has valid stored results.
CREATE FUNCTION evaluate_run(p_run_id BIGINT)
RETURNS TABLE (
    checked_run_id BIGINT,
    algorithm VARCHAR,
    run_status VARCHAR,
    eligible BOOLEAN,
    validation_message TEXT
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    run_record algorithm_runs%ROWTYPE;
    invalid_count BIGINT;
BEGIN
    SELECT *
    INTO run_record
    FROM algorithm_runs
    WHERE run_id = p_run_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Run % does not exist.', p_run_id;
    END IF;

    checked_run_id := run_record.run_id;
    algorithm := run_record.algorithm_type;
    run_status := run_record.status;

    eligible := FALSE;
    validation_message := '';

    IF run_record.status <> 'COMPLETED' THEN
        validation_message := 'Run has not completed.';
        RETURN NEXT;
        RETURN;
    END IF;

    IF run_record.algorithm_type = 'ACTIVITY_SELECTION' THEN
        SELECT COUNT(*)
        INTO invalid_count
        FROM activities a
        LEFT JOIN activity_decisions d
          ON d.activity_id = a.activity_id
        WHERE a.run_id = p_run_id
          AND d.decision_id IS NULL;

        eligible := invalid_count = 0;

    ELSIF run_record.algorithm_type = 'FRACTIONAL_KNAPSACK' THEN
        SELECT COUNT(*)
        INTO invalid_count
        FROM knapsack_problems kp
        WHERE kp.run_id = p_run_id
          AND (
              kp.used_capacity > kp.capacity
              OR ABS(
                  kp.total_value - COALESCE(
                      (
                          SELECT SUM(ka.allocated_value)
                          FROM knapsack_allocations ka
                          WHERE ka.problem_id = kp.problem_id
                      ),
                      0
                  )
              ) > 0.001
          );

        eligible := invalid_count = 0;

    ELSIF run_record.algorithm_type = 'HUFFMAN_CODING' THEN
        SELECT COUNT(*)
        INTO invalid_count
        FROM huffman_symbols hs
        WHERE hs.run_id = p_run_id
          AND NOT EXISTS (
              SELECT 1
              FROM huffman_codes hc
              WHERE hc.symbol_id = hs.symbol_id
          );

        eligible := invalid_count = 0;
    END IF;

    validation_message := CASE
        WHEN eligible THEN 'Validation passed.'
        ELSE 'Validation failed or results are incomplete.'
    END;

    RETURN NEXT;
END;
$$;

-- Activity retrieval and selection report.
SELECT *
FROM activity_selection_report
ORDER BY run_id, decision_order;

-- Run the recursive activity-selection function.
SELECT *
FROM calculate_activity_selection(
    (
        SELECT run_id
        FROM algorithm_runs
        WHERE run_name = 'Conference Room Scheduling'
    )
);

-- Activity scheduling aggregation.
SELECT
    run_id,
    COUNT(*) AS total_activities,
    COUNT(*) FILTER (
        WHERE decision = 'SELECTED'
    ) AS selected_activities,
    COUNT(*) FILTER (
        WHERE decision = 'REJECTED'
    ) AS rejected_activities
FROM activity_selection_report
GROUP BY run_id;

-- Fractional knapsack allocation report.
SELECT *
FROM knapsack_allocation_report
ORDER BY value_weight_ratio DESC;

-- Evaluate available fractional allocations.
SELECT *
FROM calculate_fractional_knapsack(
    (
        SELECT problem_id
        FROM knapsack_problems
        WHERE run_id = (
            SELECT run_id
            FROM algorithm_runs
            WHERE run_name = 'Warehouse Resource Allocation'
        )
    )
);

-- Huffman symbol information.
SELECT *
FROM huffman_symbols
ORDER BY run_id, frequency DESC;

-- Huffman weighted cost, once codewords have been populated.
SELECT
    run_id,
    calculate_huffman_cost(run_id) AS weighted_path_length
FROM algorithm_runs
WHERE algorithm_type = 'HUFFMAN_CODING';

-- Validate all completed runs.
SELECT e.*
FROM algorithm_runs ar
CROSS JOIN LATERAL evaluate_run(ar.run_id) e
ORDER BY e.checked_run_id;

-- Identify missing Huffman codes.
SELECT
    hs.symbol,
    hs.frequency
FROM huffman_symbols hs
LEFT JOIN huffman_codes hc
  ON hc.symbol_id = hs.symbol_id
WHERE hc.code_id IS NULL;

-- Report execution metadata and run status.
SELECT
    algorithm_type,
    run_name,
    status,
    created_at,
    completed_at,
    execution_metadata
FROM algorithm_runs
ORDER BY run_id;

COMMIT;
