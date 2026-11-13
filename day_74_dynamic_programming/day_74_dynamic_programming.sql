-- ============================================================
-- DYNAMIC PROGRAMMING WITH POSTGRESQL
--
-- Domain:
-- Enterprise project portfolio optimization.
--
-- Algorithms:
-- 1. 0/1 Knapsack using bottom-up tabulation.
-- 2. Dynamic programming state persistence.
-- 3. Optimal substructure.
-- 4. Overlapping subproblems represented by DP states.
-- 5. Solution reconstruction.
--
-- PostgreSQL 15+
--
-- Complexity of knapsack:
-- Time:   O(number_of_projects * budget)
-- Space:  O(number_of_projects * budget)
--
-- Run as a database user with schema creation privileges.
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS dynamic_programming;

SET search_path TO dynamic_programming, public;

-- ============================================================
-- 1. ENUM TYPES
-- ============================================================

CREATE TYPE project_status AS ENUM (
    'PROPOSED',
    'APPROVED',
    'REJECTED',
    'SELECTED',
    'NOT_SELECTED'
);

CREATE TYPE algorithm_type AS ENUM (
    'MEMOIZATION',
    'TABULATION'
);

CREATE TYPE execution_status AS ENUM (
    'PENDING',
    'RUNNING',
    'COMPLETED',
    'FAILED'
);

-- ============================================================
-- 2. PROJECT PORTFOLIO
-- ============================================================

CREATE TABLE projects (
    project_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_code VARCHAR(30) NOT NULL UNIQUE,

    project_name VARCHAR(150) NOT NULL,

    resource_cost INTEGER NOT NULL,

    expected_value INTEGER NOT NULL,

    status project_status NOT NULL DEFAULT 'PROPOSED',

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT project_code_nonempty
        CHECK (length(trim(project_code)) > 0),

    CONSTRAINT project_name_nonempty
        CHECK (length(trim(project_name)) > 0),

    CONSTRAINT project_cost_positive
        CHECK (resource_cost > 0),

    CONSTRAINT project_value_nonnegative
        CHECK (expected_value >= 0)
);

CREATE INDEX idx_projects_status
    ON projects(status);

CREATE INDEX idx_projects_value
    ON projects(expected_value DESC);

-- ============================================================
-- 3. OPTIMIZATION RUNS
-- ============================================================

CREATE TABLE optimization_runs (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    run_name VARCHAR(150) NOT NULL,

    algorithm algorithm_type NOT NULL,

    available_budget INTEGER NOT NULL,

    execution_state execution_status NOT NULL DEFAULT 'PENDING',

    maximum_value BIGINT,

    total_resource_cost INTEGER,

    states_computed BIGINT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    completed_at TIMESTAMPTZ,

    error_message TEXT,

    CONSTRAINT run_name_nonempty
        CHECK (length(trim(run_name)) > 0),

    CONSTRAINT budget_nonnegative
        CHECK (available_budget >= 0),

    CONSTRAINT maximum_value_nonnegative
        CHECK (maximum_value IS NULL OR maximum_value >= 0),

    CONSTRAINT total_cost_nonnegative
        CHECK (total_resource_cost IS NULL OR total_resource_cost >= 0),

    CONSTRAINT states_nonnegative
        CHECK (states_computed IS NULL OR states_computed >= 0),

    CONSTRAINT run_completion_consistency
        CHECK (
            (
                execution_state = 'COMPLETED'
                AND maximum_value IS NOT NULL
                AND total_resource_cost IS NOT NULL
                AND states_computed IS NOT NULL
                AND completed_at IS NOT NULL
            )
            OR execution_state <> 'COMPLETED'
        )
);

CREATE INDEX idx_runs_created
    ON optimization_runs(created_at DESC);

CREATE INDEX idx_runs_state
    ON optimization_runs(execution_state);

-- ============================================================
-- 4. RUN INPUT SNAPSHOTS
--
-- An optimization run must use stable input data.
-- Changes to the project catalog must not silently alter
-- previously executed optimization results.
-- ============================================================

CREATE TABLE run_projects (
    run_id BIGINT NOT NULL REFERENCES optimization_runs(run_id)
        ON DELETE CASCADE,

    project_id BIGINT NOT NULL REFERENCES projects(project_id)
        ON DELETE RESTRICT,

    project_position INTEGER NOT NULL,

    project_code VARCHAR(30) NOT NULL,

    project_name VARCHAR(150) NOT NULL,

    resource_cost INTEGER NOT NULL,

    expected_value INTEGER NOT NULL,

    PRIMARY KEY (run_id, project_id),

    UNIQUE (run_id, project_position),

    CONSTRAINT run_position_nonnegative
        CHECK (project_position >= 1),

    CONSTRAINT run_project_cost_positive
        CHECK (resource_cost > 0),

    CONSTRAINT run_project_value_nonnegative
        CHECK (expected_value >= 0)
);

CREATE INDEX idx_run_projects_order
    ON run_projects(run_id, project_position);

-- ============================================================
-- 5. DP STATE TABLE
--
-- State definition:
--
-- dp_state(i, w) = maximum value obtainable using the
-- first i projects with available budget w.
--
-- Recurrence:
--
-- dp(i,w) = dp(i-1,w)                       if cost > w
--
-- dp(i,w) = MAX(
--      dp(i-1,w),
--      value(i) + dp(i-1,w-cost(i))
-- )                                         otherwise.
--
-- selected_project_ids stores reconstruction information.
-- ============================================================

CREATE TABLE dp_states (
    run_id BIGINT NOT NULL REFERENCES optimization_runs(run_id)
        ON DELETE CASCADE,

    item_index INTEGER NOT NULL,

    remaining_budget INTEGER NOT NULL,

    maximum_value BIGINT NOT NULL,

    selected_project_ids BIGINT[] NOT NULL DEFAULT '{}',

    PRIMARY KEY (
        run_id,
        item_index,
        remaining_budget
    ),

    CONSTRAINT state_index_nonnegative
        CHECK (item_index >= 0),

    CONSTRAINT state_budget_nonnegative
        CHECK (remaining_budget >= 0),

    CONSTRAINT state_value_nonnegative
        CHECK (maximum_value >= 0)
);

CREATE INDEX idx_dp_states_run_value
    ON dp_states(run_id, maximum_value DESC);

-- ============================================================
-- 6. SELECTED PROJECTS
-- ============================================================

CREATE TABLE selected_projects (
    run_id BIGINT NOT NULL REFERENCES optimization_runs(run_id)
        ON DELETE CASCADE,

    project_id BIGINT NOT NULL REFERENCES projects(project_id)
        ON DELETE RESTRICT,

    allocated_cost INTEGER NOT NULL,

    realized_value INTEGER NOT NULL,

    PRIMARY KEY (run_id, project_id),

    CHECK (allocated_cost > 0),

    CHECK (realized_value >= 0)
);

-- ============================================================
-- 7. VALIDATION TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION validate_project_snapshot()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_budget INTEGER;
BEGIN

    SELECT available_budget
    INTO v_budget
    FROM optimization_runs
    WHERE run_id = NEW.run_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Optimization run does not exist.';
    END IF;

    IF NEW.resource_cost <= 0 THEN
        RAISE EXCEPTION 'Project cost must be positive.';
    END IF;

    IF NEW.expected_value < 0 THEN
        RAISE EXCEPTION 'Project value cannot be negative.';
    END IF;

    IF NEW.resource_cost > v_budget THEN
        RAISE EXCEPTION
            'Project % individually exceeds run budget.',
            NEW.project_code;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_project_snapshot
BEFORE INSERT OR UPDATE ON run_projects
FOR EACH ROW
EXECUTE FUNCTION validate_project_snapshot();

-- ============================================================
-- 8. RUN CREATION PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE create_optimization_run(
    p_run_name VARCHAR,
    p_budget INTEGER,
    p_algorithm algorithm_type
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_run_id BIGINT;
    v_position INTEGER := 0;
    v_project RECORD;
BEGIN

    IF p_budget < 0 OR p_budget > 100000 THEN
        RAISE EXCEPTION
            'Budget must be between 0 and 100000.';
    END IF;

    IF p_run_name IS NULL OR length(trim(p_run_name)) = 0 THEN
        RAISE EXCEPTION 'Run name cannot be empty.';
    END IF;

    INSERT INTO optimization_runs (
        run_name,
        algorithm,
        available_budget
    )
    VALUES (
        p_run_name,
        p_algorithm,
        p_budget
    )
    RETURNING run_id INTO v_run_id;

    FOR v_project IN
        SELECT
            project_id,
            project_code,
            project_name,
            resource_cost,
            expected_value
        FROM projects
        WHERE status = 'APPROVED'
          AND resource_cost <= p_budget
        ORDER BY project_id
    LOOP

        v_position := v_position + 1;

        INSERT INTO run_projects (
            run_id,
            project_id,
            project_position,
            project_code,
            project_name,
            resource_cost,
            expected_value
        )
        VALUES (
            v_run_id,
            v_project.project_id,
            v_position,
            v_project.project_code,
            v_project.project_name,
            v_project.resource_cost,
            v_project.expected_value
        );

    END LOOP;

    RAISE NOTICE
        'Created optimization run % with % projects.',
        v_run_id,
        v_position;

END;
$$;

-- ============================================================
-- 9. TABULATION FUNCTION
--
-- The function computes every state.
--
-- It uses snapshots instead of reading mutable project values.
-- The transaction ensures that partial results are not exposed.
-- ============================================================

CREATE OR REPLACE FUNCTION execute_knapsack(
    p_run_id BIGINT
)
RETURNS TABLE (
    result_value BIGINT,
    result_cost INTEGER,
    selected_ids BIGINT[],
    computed_states BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_budget INTEGER;
    v_count INTEGER;
    v_index INTEGER;
    v_capacity INTEGER;

    v_project RECORD;

    v_exclude BIGINT;
    v_include BIGINT;

    v_exclude_ids BIGINT[];
    v_include_ids BIGINT[];

    v_best BIGINT;
    v_best_ids BIGINT[];

    v_total_cost INTEGER := 0;
    v_state_count BIGINT := 0;

BEGIN

    SELECT available_budget
    INTO v_budget
    FROM optimization_runs
    WHERE run_id = p_run_id
      AND execution_state IN ('PENDING', 'FAILED');

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Run does not exist or is not executable.';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM optimization_runs
        WHERE run_id = p_run_id
          AND execution_state = 'FAILED'
          AND error_message IS NOT NULL
    ) THEN
        -- Failed runs can be retried after clearing old state.
        NULL;
    END IF;

    UPDATE optimization_runs
    SET execution_state = 'RUNNING',
        error_message = NULL
    WHERE run_id = p_run_id;

    DELETE FROM dp_states
    WHERE run_id = p_run_id;

    DELETE FROM selected_projects
    WHERE run_id = p_run_id;

    SELECT COUNT(*)::INTEGER
    INTO v_count
    FROM run_projects
    WHERE run_id = p_run_id;

    -- Base states: no projects produce zero value.
    FOR v_capacity IN 0..v_budget LOOP

        INSERT INTO dp_states (
            run_id,
            item_index,
            remaining_budget,
            maximum_value,
            selected_project_ids
        )
        VALUES (
            p_run_id,
            0,
            v_capacity,
            0,
            '{}'
        );

        v_state_count := v_state_count + 1;
    END LOOP;

    -- Process each project.
    FOR v_index IN 1..v_count LOOP

        SELECT *
        INTO v_project
        FROM run_projects
        WHERE run_id = p_run_id
          AND project_position = v_index;

        FOR v_capacity IN 0..v_budget LOOP

            SELECT
                maximum_value,
                selected_project_ids
            INTO
                v_exclude,
                v_exclude_ids
            FROM dp_states
            WHERE run_id = p_run_id
              AND item_index = v_index - 1
              AND remaining_budget = v_capacity;

            v_best := v_exclude;
            v_best_ids := v_exclude_ids;

            IF v_project.resource_cost <= v_capacity THEN

                SELECT
                    maximum_value,
                    selected_project_ids
                INTO
                    v_include,
                    v_include_ids
                FROM dp_states
                WHERE run_id = p_run_id
                  AND item_index = v_index - 1
                  AND remaining_budget =
                      v_capacity - v_project.resource_cost;

                v_include := v_include + v_project.expected_value;

                IF v_include > v_exclude THEN

                    v_best := v_include;

                    v_best_ids :=
                        array_append(
                            v_include_ids,
                            v_project.project_id
                        );

                END IF;
            END IF;

            INSERT INTO dp_states (
                run_id,
                item_index,
                remaining_budget,
                maximum_value,
                selected_project_ids
            )
            VALUES (
                p_run_id,
                v_index,
                v_capacity,
                v_best,
                v_best_ids
            );

            v_state_count := v_state_count + 1;

        END LOOP;
    END LOOP;

    -- Retrieve the optimal state.
    SELECT
        maximum_value,
        selected_project_ids
    INTO
        v_best,
        v_best_ids
    FROM dp_states
    WHERE run_id = p_run_id
      AND item_index = v_count
      AND remaining_budget = v_budget;

    -- Persist selected projects.
    INSERT INTO selected_projects (
        run_id,
        project_id,
        allocated_cost,
        realized_value
    )
    SELECT
        p_run_id,
        rp.project_id,
        rp.resource_cost,
        rp.expected_value
    FROM run_projects rp
    WHERE rp.run_id = p_run_id
      AND rp.project_id = ANY(v_best_ids);

    SELECT COALESCE(SUM(allocated_cost), 0)::INTEGER
    INTO v_total_cost
    FROM selected_projects
    WHERE run_id = p_run_id;

    IF v_total_cost > v_budget THEN
        RAISE EXCEPTION 'Optimization violated budget constraint.';
    END IF;

    UPDATE optimization_runs
    SET execution_state = 'COMPLETED',
        maximum_value = v_best,
        total_resource_cost = v_total_cost,
        states_computed = v_state_count,
        completed_at = CURRENT_TIMESTAMP
    WHERE run_id = p_run_id;

    RETURN QUERY
    SELECT
        v_best,
        v_total_cost,
        v_best_ids,
        v_state_count;

EXCEPTION
    WHEN OTHERS THEN

        UPDATE optimization_runs
        SET execution_state = 'FAILED',
            error_message = SQLERRM,
            completed_at = CURRENT_TIMESTAMP
        WHERE run_id = p_run_id;

        RAISE;
END;
$$;

-- ============================================================
-- 10. VIEWS
-- ============================================================

CREATE OR REPLACE VIEW v_project_portfolio AS
SELECT
    project_id,
    project_code,
    project_name,
    resource_cost,
    expected_value,
    status,
    ROUND(
        expected_value::NUMERIC
        / NULLIF(resource_cost, 0),
        2
    ) AS value_per_resource_unit
FROM projects;

CREATE OR REPLACE VIEW v_optimization_report AS
SELECT
    r.run_id,
    r.run_name,
    r.algorithm,
    r.available_budget,
    r.execution_state,
    r.maximum_value,
    r.total_resource_cost,
    r.states_computed,
    COUNT(s.project_id) AS selected_project_count,
    r.completed_at
FROM optimization_runs r
LEFT JOIN selected_projects s
    ON s.run_id = r.run_id
GROUP BY
    r.run_id,
    r.run_name,
    r.algorithm,
    r.available_budget,
    r.execution_state,
    r.maximum_value,
    r.total_resource_cost,
    r.states_computed,
    r.completed_at;

-- ============================================================
-- 11. SAMPLE DATA
-- ============================================================

INSERT INTO projects (
    project_code,
    project_name,
    resource_cost,
    expected_value,
    status
)
VALUES
    ('INFRA', 'Infrastructure Modernization', 5, 100, 'APPROVED'),
    ('SEC', 'Cybersecurity Upgrade', 3, 80, 'APPROVED'),
    ('MON', 'Monitoring Platform', 2, 50, 'APPROVED'),
    ('BACKUP', 'Backup Infrastructure', 6, 120, 'APPROVED'),
    ('AUTO', 'Process Automation', 2, 40, 'APPROVED'),
    ('ANALYTICS', 'Analytics Platform', 4, 75, 'APPROVED'),
    ('REJECTED', 'Unapproved Experimental Project', 1, 500, 'REJECTED'),
    ('PROPOSED', 'Proposed Cloud Migration', 3, 200, 'PROPOSED');

-- ============================================================
-- 12. CREATE OPTIMIZATION RUNS
-- ============================================================

CALL create_optimization_run(
    'Enterprise Portfolio - Memoization Reference',
    10,
    'MEMOIZATION'
);

CALL create_optimization_run(
    'Enterprise Portfolio - Tabulation',
    10,
    'TABULATION'
);

-- ============================================================
-- 13. EXECUTE ALGORITHMS
-- ============================================================

SELECT *
FROM execute_knapsack(1);

SELECT *
FROM execute_knapsack(2);

-- ============================================================
-- 14. RETRIEVAL QUERIES
-- ============================================================

-- Retrieve the complete approved project portfolio.
SELECT *
FROM v_project_portfolio
WHERE project_id IN (
    SELECT project_id
    FROM projects
    WHERE status = 'APPROVED'
)
ORDER BY value_per_resource_unit DESC;

-- Retrieve selected projects for each completed run.
SELECT
    r.run_name,
    p.project_code,
    p.project_name,
    s.allocated_cost,
    s.realized_value
FROM selected_projects s
JOIN optimization_runs r
    ON r.run_id = s.run_id
JOIN projects p
    ON p.project_id = s.project_id
ORDER BY r.run_id, p.project_code;

-- ============================================================
-- 15. VALIDATION QUERIES
-- ============================================================

-- Confirm that allocated resources do not exceed budget.
SELECT
    run_id,
    run_name,
    available_budget,
    total_resource_cost,
    total_resource_cost <= available_budget AS budget_valid
FROM optimization_runs
WHERE execution_state = 'COMPLETED';

-- Check that rejected and proposed projects were excluded.
SELECT
    r.run_id,
    p.project_code,
    p.status
FROM run_projects rp
JOIN optimization_runs r
    ON r.run_id = rp.run_id
JOIN projects p
    ON p.project_id = rp.project_id
WHERE p.status <> 'APPROVED';

-- Verify every selected project belongs to its input snapshot.
SELECT
    s.run_id,
    s.project_id
FROM selected_projects s
LEFT JOIN run_projects rp
    ON rp.run_id = s.run_id
   AND rp.project_id = s.project_id
WHERE rp.project_id IS NULL;

-- ============================================================
-- 16. AGGREGATION AND REPORTING
-- ============================================================

SELECT
    algorithm,
    COUNT(*) AS completed_runs,
    AVG(maximum_value) AS average_optimal_value,
    MAX(maximum_value) AS highest_optimal_value,
    AVG(states_computed) AS average_states
FROM optimization_runs
WHERE execution_state = 'COMPLETED'
GROUP BY algorithm;

-- Resource utilization percentage.
SELECT
    run_id,
    run_name,
    maximum_value,
    available_budget,
    total_resource_cost,
    ROUND(
        100.0 * total_resource_cost
        / NULLIF(available_budget, 0),
        2
    ) AS utilization_percentage
FROM optimization_runs
WHERE execution_state = 'COMPLETED';

-- ============================================================
-- 17. DP STATE INSPECTION
-- ============================================================

-- Inspect the recurrence table for the first run.
SELECT
    item_index,
    remaining_budget,
    maximum_value,
    selected_project_ids
FROM dp_states
WHERE run_id = 1
ORDER BY item_index, remaining_budget;

-- Identify the best state at each project stage.
WITH ranked_states AS (
    SELECT
        item_index,
        remaining_budget,
        maximum_value,
        ROW_NUMBER() OVER (
            PARTITION BY item_index
            ORDER BY maximum_value DESC, remaining_budget ASC
        ) AS ranking
    FROM dp_states
    WHERE run_id = 1
)
SELECT
    item_index,
    remaining_budget,
    maximum_value
FROM ranked_states
WHERE ranking = 1
ORDER BY item_index;

-- ============================================================
-- 18. CTE-BASED ELIGIBILITY DETERMINATION
-- ============================================================

WITH completed_runs AS (
    SELECT *
    FROM optimization_runs
    WHERE execution_state = 'COMPLETED'
),
eligibility AS (
    SELECT
        run_id,
        run_name,
        available_budget,
        total_resource_cost,
        maximum_value,
        CASE
            WHEN total_resource_cost <= available_budget
             AND maximum_value IS NOT NULL
            THEN 'ELIGIBLE'
            ELSE 'INELIGIBLE'
        END AS eligibility_status
    FROM completed_runs
)
SELECT *
FROM eligibility
ORDER BY run_id;

-- ============================================================
-- 19. FAILURE CASE: INVALID INPUT
--
-- The following statement is intentionally commented out.
-- It can be executed separately to test the constraint.
--
-- INSERT INTO projects (
--     project_code,
--     project_name,
--     resource_cost,
--     expected_value
-- )
-- VALUES ('INVALID', 'Invalid Cost', 0, 100);
--
-- Expected: CHECK constraint violation.
--
-- Another failure:
--
-- CALL create_optimization_run(
--     'Invalid Budget',
--     -10,
--     'TABULATION'
-- );
--
-- Expected: budget validation exception.
-- ============================================================

-- ============================================================
-- 20. TRANSACTIONAL CONSISTENCY
-- ============================================================

-- The caller can execute an additional optimization run
-- transactionally. If any statement fails, rollback prevents
-- partially committed application-level operations.

-- Example:
--
-- BEGIN;
--
-- CALL create_optimization_run(
--     'Transactional Validation Run',
--     8,
--     'TABULATION'
-- );
--
-- SELECT *
-- FROM execute_knapsack(3);
--
-- COMMIT;
--
-- For failure:
--
-- ROLLBACK;

-- ============================================================
-- 21. PERFORMANCE DIAGNOSTICS
-- ============================================================

EXPLAIN
SELECT
    run_id,
    item_index,
    remaining_budget,
    maximum_value
FROM dp_states
WHERE run_id = 1
  AND item_index = 3
ORDER BY remaining_budget;

-- ============================================================
-- 22. FINAL REPORT
-- ============================================================

SELECT *
FROM v_optimization_report
ORDER BY run_id;

COMMIT;
