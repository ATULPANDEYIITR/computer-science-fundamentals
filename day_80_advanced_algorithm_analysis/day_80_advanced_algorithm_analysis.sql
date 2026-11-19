/*
    ADVANCED ALGORITHM ANALYSIS
    PostgreSQL 14+

    Subject areas:
    1. Amortized analysis
    2. Randomized algorithms
    3. Probabilistic analysis

    Database components:
    - Algorithm experiment registry
    - Algorithm execution records
    - Individual trial observations
    - Complexity classifications
    - Statistical summaries
    - Validation constraints
    - Aggregate analysis
    - Experiment processing procedures
    - Automatic consistency checks
*/

BEGIN;

CREATE SCHEMA IF NOT EXISTS algorithm_lab;

SET search_path TO algorithm_lab, public;


/* =========================================================
   1. DOMAIN TYPES
   ========================================================= */

DO $$
BEGIN
    CREATE TYPE algorithm_category AS ENUM (
        'AMORTIZED',
        'RANDOMIZED',
        'PROBABILISTIC'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END;
$$;


DO $$
BEGIN
    CREATE TYPE complexity_class AS ENUM (
        'O_1',
        'O_LOG_N',
        'O_N',
        'O_N_LOG_N',
        'O_N_SQUARED',
        'O_ALPHA_N',
        'O_EXPONENTIAL'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END;
$$;


DO $$
BEGIN
    CREATE TYPE experiment_status AS ENUM (
        'PENDING',
        'RUNNING',
        'COMPLETED',
        'FAILED'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END;
$$;


/* =========================================================
   2. ALGORITHM CATALOG
   ========================================================= */

CREATE TABLE IF NOT EXISTS algorithms (
    algorithm_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    algorithm_name VARCHAR(150) NOT NULL UNIQUE,

    category algorithm_category NOT NULL,

    best_case complexity_class NOT NULL,

    average_case complexity_class NOT NULL,

    worst_case complexity_class NOT NULL,

    amortized_complexity complexity_class,

    description TEXT NOT NULL,

    deterministic BOOLEAN NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT algorithm_description_nonempty
        CHECK (LENGTH(TRIM(description)) > 0)
);


/* =========================================================
   3. EXPERIMENT REGISTRY
   ========================================================= */

CREATE TABLE IF NOT EXISTS experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    algorithm_id BIGINT NOT NULL
        REFERENCES algorithms(algorithm_id),

    experiment_name VARCHAR(200) NOT NULL,

    input_size INTEGER NOT NULL,

    trial_count INTEGER NOT NULL,

    random_seed BIGINT,

    status experiment_status NOT NULL DEFAULT 'PENDING',

    expected_mean NUMERIC(20, 6),

    observed_mean NUMERIC(20, 6),

    standard_deviation NUMERIC(20, 6),

    minimum_observed NUMERIC(20, 6),

    maximum_observed NUMERIC(20, 6),

    execution_started_at TIMESTAMPTZ,

    execution_finished_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT positive_input_size
        CHECK (input_size > 0),

    CONSTRAINT positive_trial_count
        CHECK (trial_count > 0),

    CONSTRAINT nonnegative_statistics
        CHECK (
            (expected_mean IS NULL OR expected_mean >= 0)
            AND
            (observed_mean IS NULL OR observed_mean >= 0)
            AND
            (standard_deviation IS NULL OR standard_deviation >= 0)
            AND
            (minimum_observed IS NULL OR minimum_observed >= 0)
            AND
            (maximum_observed IS NULL OR maximum_observed >= 0)
        ),

    CONSTRAINT valid_execution_period
        CHECK (
            execution_finished_at IS NULL
            OR execution_started_at IS NULL
            OR execution_finished_at >= execution_started_at
        ),

    CONSTRAINT valid_observed_range
        CHECK (
            minimum_observed IS NULL
            OR maximum_observed IS NULL
            OR maximum_observed >= minimum_observed
        ),

    CONSTRAINT completed_experiment_has_results
        CHECK (
            status <> 'COMPLETED'
            OR (
                observed_mean IS NOT NULL
                AND standard_deviation IS NOT NULL
                AND minimum_observed IS NOT NULL
                AND maximum_observed IS NOT NULL
            )
        )
);


/* =========================================================
   4. INDIVIDUAL TRIAL OBSERVATIONS
   ========================================================= */

CREATE TABLE IF NOT EXISTS trial_observations (
    observation_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,

    trial_number INTEGER NOT NULL,

    observed_cost NUMERIC(20, 6) NOT NULL,

    comparison_count BIGINT,

    swap_count BIGINT,

    elapsed_microseconds BIGINT,

    random_seed BIGINT,

    successful BOOLEAN NOT NULL DEFAULT TRUE,

    error_message TEXT,

    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_trial_number
        UNIQUE (experiment_id, trial_number),

    CONSTRAINT positive_trial_number
        CHECK (trial_number > 0),

    CONSTRAINT nonnegative_observed_cost
        CHECK (observed_cost >= 0),

    CONSTRAINT nonnegative_counters
        CHECK (
            (comparison_count IS NULL OR comparison_count >= 0)
            AND
            (swap_count IS NULL OR swap_count >= 0)
            AND
            (elapsed_microseconds IS NULL OR elapsed_microseconds >= 0)
        ),

    CONSTRAINT failed_trial_has_reason
        CHECK (
            successful = TRUE
            OR NULLIF(TRIM(error_message), '') IS NOT NULL
        )
);


/* =========================================================
   5. AMORTIZED OPERATION ACCOUNTING
   ========================================================= */

CREATE TABLE IF NOT EXISTS amortized_operations (
    operation_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,

    operation_number INTEGER NOT NULL,

    operation_type VARCHAR(80) NOT NULL,

    actual_cost NUMERIC(20, 6) NOT NULL,

    potential_before NUMERIC(20, 6) NOT NULL,

    potential_after NUMERIC(20, 6) NOT NULL,

    amortized_cost NUMERIC(20, 6)
        GENERATED ALWAYS AS (
            actual_cost + potential_after - potential_before
        ) STORED,

    CONSTRAINT unique_operation_number
        UNIQUE (experiment_id, operation_number),

    CONSTRAINT positive_operation_number
        CHECK (operation_number > 0),

    CONSTRAINT valid_costs
        CHECK (
            actual_cost >= 0
            AND potential_before >= 0
            AND potential_after >= 0
        ),

    CONSTRAINT nonempty_operation_type
        CHECK (LENGTH(TRIM(operation_type)) > 0)
);


/* =========================================================
   6. PERFORMANCE INDEXES
   ========================================================= */

CREATE INDEX IF NOT EXISTS idx_experiments_algorithm_status
    ON experiments(algorithm_id, status);

CREATE INDEX IF NOT EXISTS idx_experiments_created
    ON experiments(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_observations_experiment
    ON trial_observations(experiment_id, trial_number);

CREATE INDEX IF NOT EXISTS idx_successful_observations
    ON trial_observations(experiment_id)
    WHERE successful = TRUE;

CREATE INDEX IF NOT EXISTS idx_amortized_experiment
    ON amortized_operations(experiment_id, operation_number);


/* =========================================================
   7. ALGORITHM CATALOG DATA
   ========================================================= */

INSERT INTO algorithms (
    algorithm_name,
    category,
    best_case,
    average_case,
    worst_case,
    amortized_complexity,
    description,
    deterministic
)
VALUES
(
    'Dynamic Array Doubling',
    'AMORTIZED',
    'O_1',
    'O_1',
    'O_N',
    'O_1',
    'Dynamic array insertion with geometric capacity expansion.',
    TRUE
),
(
    'Two Stack Queue',
    'AMORTIZED',
    'O_1',
    'O_1',
    'O_N',
    'O_1',
    'Queue using two stacks with each element transferred at most once.',
    TRUE
),
(
    'Randomized Quicksort',
    'RANDOMIZED',
    'O_N_LOG_N',
    'O_N_LOG_N',
    'O_N_SQUARED',
    NULL,
    'Sorting algorithm using randomly selected partition pivots.',
    FALSE
),
(
    'Coupon Collector',
    'PROBABILISTIC',
    'O_N',
    'O_N_LOG_N',
    'O_EXPONENTIAL',
    NULL,
    'Random sampling process requiring all distinct coupon types.',
    FALSE
),
(
    'Disjoint Set Union',
    'AMORTIZED',
    'O_1',
    'O_ALPHA_N',
    'O_LOG_N',
    'O_ALPHA_N',
    'Union by rank and path compression.',
    TRUE
)
ON CONFLICT (algorithm_name) DO NOTHING;


/* =========================================================
   8. HARMONIC NUMBER FUNCTION
   ========================================================= */

CREATE OR REPLACE FUNCTION harmonic_number(
    p_n INTEGER
)
RETURNS NUMERIC
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
DECLARE
    result NUMERIC := 0;
    i INTEGER;
BEGIN
    IF p_n < 0 THEN
        RAISE EXCEPTION
            'Harmonic number input cannot be negative.';
    END IF;

    IF p_n > 1000000 THEN
        RAISE EXCEPTION
            'Input exceeds configured computational limit.';
    END IF;

    FOR i IN 1..p_n LOOP
        result := result + 1.0 / i;
    END LOOP;

    RETURN result;
END;
$$;


/* =========================================================
   9. THEORETICAL EXPECTED QUICKSORT COMPARISONS
   ========================================================= */

CREATE OR REPLACE FUNCTION expected_quicksort_comparisons(
    p_n INTEGER
)
RETURNS NUMERIC
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
BEGIN
    IF p_n < 0 THEN
        RAISE EXCEPTION 'Input size cannot be negative.';
    END IF;

    IF p_n <= 1 THEN
        RETURN 0;
    END IF;

    RETURN 2.0 * (p_n + 1) * harmonic_number(p_n)
           - 4.0 * p_n;
END;
$$;


/* =========================================================
   10. EXPERIMENT STATE VALIDATION
   ========================================================= */

CREATE OR REPLACE FUNCTION validate_experiment_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN

        IF OLD.status = 'COMPLETED'
           AND NEW.status <> 'COMPLETED' THEN
            RAISE EXCEPTION
                'Completed experiments cannot be reopened.';
        END IF;

        IF OLD.status = 'FAILED'
           AND NEW.status NOT IN ('FAILED', 'RUNNING') THEN
            RAISE EXCEPTION
                'Invalid transition from FAILED.';
        END IF;

        IF OLD.status = 'RUNNING'
           AND NEW.status NOT IN ('RUNNING', 'COMPLETED', 'FAILED') THEN
            RAISE EXCEPTION
                'Invalid transition from RUNNING.';
        END IF;

        IF OLD.status = 'PENDING'
           AND NEW.status NOT IN ('PENDING', 'RUNNING', 'FAILED') THEN
            RAISE EXCEPTION
                'Invalid transition from PENDING.';
        END IF;

    END IF;

    IF NEW.status = 'RUNNING'
       AND NEW.execution_started_at IS NULL THEN
        NEW.execution_started_at := CURRENT_TIMESTAMP;
    END IF;

    IF NEW.status IN ('COMPLETED', 'FAILED')
       AND NEW.execution_finished_at IS NULL THEN
        NEW.execution_finished_at := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$;


DROP TRIGGER IF EXISTS trg_experiment_transition
    ON experiments;

CREATE TRIGGER trg_experiment_transition
BEFORE UPDATE ON experiments
FOR EACH ROW
EXECUTE FUNCTION validate_experiment_transition();


/* =========================================================
   11. OBSERVATION VALIDATION
   ========================================================= */

CREATE OR REPLACE FUNCTION validate_observation_status()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    current_status experiment_status;
BEGIN
    SELECT status
    INTO current_status
    FROM experiments
    WHERE experiment_id = NEW.experiment_id
    FOR UPDATE;

    IF current_status IS NULL THEN
        RAISE EXCEPTION 'Experiment does not exist.';
    END IF;

    IF current_status <> 'RUNNING' THEN
        RAISE EXCEPTION
            'Observations can only be recorded for running experiments.';
    END IF;

    RETURN NEW;
END;
$$;


DROP TRIGGER IF EXISTS trg_observation_validation
    ON trial_observations;

CREATE TRIGGER trg_observation_validation
BEFORE INSERT ON trial_observations
FOR EACH ROW
EXECUTE FUNCTION validate_observation_status();


/* =========================================================
   12. EXPERIMENT AGGREGATION
   ========================================================= */

CREATE OR REPLACE FUNCTION finalize_experiment(
    p_experiment_id BIGINT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_expected INTEGER;
    v_recorded INTEGER;
    v_mean NUMERIC;
    v_stddev NUMERIC;
    v_min NUMERIC;
    v_max NUMERIC;
    v_status experiment_status;
BEGIN
    SELECT trial_count, status
    INTO v_expected, v_status
    FROM experiments
    WHERE experiment_id = p_experiment_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Experiment not found.';
    END IF;

    IF v_status <> 'RUNNING' THEN
        RAISE EXCEPTION 'Experiment is not running.';
    END IF;

    SELECT
        COUNT(*),
        AVG(observed_cost),
        STDDEV_POP(observed_cost),
        MIN(observed_cost),
        MAX(observed_cost)
    INTO
        v_recorded,
        v_mean,
        v_stddev,
        v_min,
        v_max
    FROM trial_observations
    WHERE experiment_id = p_experiment_id
      AND successful = TRUE;

    IF v_recorded <> v_expected THEN
        RAISE EXCEPTION
            'Expected % successful trials, received %.',
            v_expected,
            v_recorded;
    END IF;

    UPDATE experiments
    SET
        observed_mean = v_mean,
        standard_deviation = v_stddev,
        minimum_observed = v_min,
        maximum_observed = v_max,
        status = 'COMPLETED',
        execution_finished_at = CURRENT_TIMESTAMP
    WHERE experiment_id = p_experiment_id;
END;
$$;


/* =========================================================
   13. EXPERIMENT EXECUTION PROCEDURE
   ========================================================= */

CREATE OR REPLACE PROCEDURE start_experiment(
    p_experiment_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_status experiment_status;
BEGIN
    SELECT status
    INTO v_status
    FROM experiments
    WHERE experiment_id = p_experiment_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Experiment does not exist.';
    END IF;

    IF v_status NOT IN ('PENDING', 'FAILED') THEN
        RAISE EXCEPTION
            'Experiment cannot start from state %.',
            v_status;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM trial_observations
        WHERE experiment_id = p_experiment_id
    ) THEN
        RAISE EXCEPTION
            'Experiment already contains observations.';
    END IF;

    UPDATE experiments
    SET
        status = 'RUNNING',
        execution_started_at = CURRENT_TIMESTAMP,
        execution_finished_at = NULL
    WHERE experiment_id = p_experiment_id;
END;
$$;


/* =========================================================
   14. EXPERIMENT SAMPLE RECORDS
   ========================================================= */

INSERT INTO experiments (
    algorithm_id,
    experiment_name,
    input_size,
    trial_count,
    random_seed,
    expected_mean
)
SELECT
    algorithm_id,
    'Dynamic Array Insertion Benchmark',
    1000,
    1,
    2026,
    2999
FROM algorithms
WHERE algorithm_name = 'Dynamic Array Doubling';


INSERT INTO experiments (
    algorithm_id,
    experiment_name,
    input_size,
    trial_count,
    random_seed,
    expected_mean
)
SELECT
    algorithm_id,
    'Randomized Quicksort Comparison Study',
    100,
    5,
    2026,
    expected_quicksort_comparisons(100)
FROM algorithms
WHERE algorithm_name = 'Randomized Quicksort';


INSERT INTO experiments (
    algorithm_id,
    experiment_name,
    input_size,
    trial_count,
    random_seed,
    expected_mean
)
SELECT
    algorithm_id,
    'Coupon Collector Simulation',
    20,
    5,
    12345,
    20 * harmonic_number(20)
FROM algorithms
WHERE algorithm_name = 'Coupon Collector';


/* =========================================================
   15. RUNNING EXPERIMENTS
   ========================================================= */

DO $$
DECLARE
    experiment_record RECORD;
    i INTEGER;
    generated_cost NUMERIC;
BEGIN
    FOR experiment_record IN
        SELECT *
        FROM experiments
        ORDER BY experiment_id
    LOOP

        CALL start_experiment(
            experiment_record.experiment_id
        );

        FOR i IN 1..experiment_record.trial_count LOOP

            IF experiment_record.experiment_name
               LIKE 'Dynamic Array%' THEN

                generated_cost := 2 * experiment_record.input_size + 1;

            ELSIF experiment_record.experiment_name
                  LIKE 'Randomized Quicksort%' THEN

                generated_cost :=
                    expected_quicksort_comparisons(
                        experiment_record.input_size
                    ) * (0.90 + i * 0.025);

            ELSE

                generated_cost :=
                    experiment_record.input_size
                    * harmonic_number(experiment_record.input_size)
                    * (0.85 + i * 0.05);

            END IF;

            INSERT INTO trial_observations (
                experiment_id,
                trial_number,
                observed_cost,
                comparison_count,
                swap_count,
                elapsed_microseconds,
                random_seed
            )
            VALUES (
                experiment_record.experiment_id,
                i,
                generated_cost,
                CASE
                    WHEN experiment_record.experiment_name
                         LIKE 'Randomized Quicksort%'
                    THEN ROUND(generated_cost)::BIGINT
                    ELSE NULL
                END,
                NULL,
                1000 + i * 100,
                experiment_record.random_seed + i
            );

        END LOOP;

        PERFORM finalize_experiment(
            experiment_record.experiment_id
        );

    END LOOP;
END;
$$;


/* =========================================================
   16. AMORTIZED OPERATION EXAMPLE
   ========================================================= */

INSERT INTO amortized_operations (
    experiment_id,
    operation_number,
    operation_type,
    actual_cost,
    potential_before,
    potential_after
)
SELECT
    experiment_id,
    1,
    'APPEND',
    1,
    0,
    1
FROM experiments
WHERE experiment_name = 'Dynamic Array Insertion Benchmark';

INSERT INTO amortized_operations (
    experiment_id,
    operation_number,
    operation_type,
    actual_cost,
    potential_before,
    potential_after
)
SELECT
    experiment_id,
    2,
    'APPEND_WITH_RESIZE',
    3,
    1,
    0
FROM experiments
WHERE experiment_name = 'Dynamic Array Insertion Benchmark';


/* =========================================================
   17. EXPERIMENT SUMMARY VIEW
   ========================================================= */

CREATE OR REPLACE VIEW experiment_summary AS
SELECT
    e.experiment_id,
    e.experiment_name,
    a.algorithm_name,
    a.category,
    a.average_case,
    a.worst_case,
    a.amortized_complexity,
    e.input_size,
    e.trial_count,
    e.status,
    e.expected_mean,
    e.observed_mean,
    e.standard_deviation,
    e.minimum_observed,
    e.maximum_observed,
    CASE
        WHEN e.expected_mean IS NULL
             OR e.expected_mean = 0
        THEN NULL
        ELSE ROUND(
            (
                (e.observed_mean - e.expected_mean)
                / e.expected_mean
            ) * 100,
            2
        )
    END AS percentage_deviation,
    e.execution_started_at,
    e.execution_finished_at
FROM experiments e
JOIN algorithms a
    ON a.algorithm_id = e.algorithm_id;


/* =========================================================
   18. AMORTIZED ANALYSIS REPORT
   ========================================================= */

CREATE OR REPLACE VIEW amortized_analysis_report AS
SELECT
    e.experiment_name,
    COUNT(o.operation_id) AS operation_count,
    SUM(o.actual_cost) AS aggregate_actual_cost,
    SUM(o.amortized_cost) AS aggregate_amortized_cost,
    AVG(o.actual_cost) AS average_actual_cost,
    AVG(o.amortized_cost) AS average_amortized_cost,
    MAX(o.actual_cost) AS maximum_individual_cost
FROM experiments e
JOIN amortized_operations o
    ON o.experiment_id = e.experiment_id
GROUP BY e.experiment_id, e.experiment_name;


/* =========================================================
   19. PROBABILISTIC ANALYSIS REPORT
   ========================================================= */

CREATE OR REPLACE VIEW probabilistic_analysis_report AS
SELECT
    e.experiment_name,
    e.input_size,
    COUNT(t.observation_id) AS successful_trials,
    AVG(t.observed_cost) AS empirical_mean,
    STDDEV_POP(t.observed_cost) AS empirical_standard_deviation,
    MIN(t.observed_cost) AS minimum_observed,
    MAX(t.observed_cost) AS maximum_observed
FROM experiments e
JOIN trial_observations t
    ON t.experiment_id = e.experiment_id
WHERE t.successful = TRUE
GROUP BY e.experiment_id, e.experiment_name, e.input_size;


/* =========================================================
   20. ELIGIBILITY AND VALIDATION REPORT
   ========================================================= */

CREATE OR REPLACE VIEW experiment_validation AS
SELECT
    e.experiment_id,
    e.experiment_name,
    e.status,
    e.trial_count AS required_trials,
    COUNT(t.observation_id)
        FILTER (WHERE t.successful) AS successful_trials,
    COUNT(t.observation_id)
        FILTER (WHERE NOT t.successful) AS failed_trials,
    CASE
        WHEN e.status = 'COMPLETED'
         AND COUNT(t.observation_id)
             FILTER (WHERE t.successful) = e.trial_count
        THEN TRUE
        ELSE FALSE
    END AS valid_completed_experiment
FROM experiments e
LEFT JOIN trial_observations t
    ON t.experiment_id = e.experiment_id
GROUP BY
    e.experiment_id,
    e.experiment_name,
    e.status,
    e.trial_count;


/* =========================================================
   21. RETRIEVAL QUERIES
   ========================================================= */

-- Algorithm catalog.
SELECT
    algorithm_name,
    category,
    best_case,
    average_case,
    worst_case,
    amortized_complexity
FROM algorithms
ORDER BY category, algorithm_name;


-- Experiment details.
SELECT *
FROM experiment_summary
ORDER BY experiment_id;


-- Individual execution observations.
SELECT
    e.experiment_name,
    t.trial_number,
    t.observed_cost,
    t.comparison_count,
    t.elapsed_microseconds,
    t.successful
FROM trial_observations t
JOIN experiments e
    ON e.experiment_id = t.experiment_id
ORDER BY e.experiment_id, t.trial_number;


/* =========================================================
   22. AGGREGATION QUERIES
   ========================================================= */

-- Mean observed cost by algorithm category.
SELECT
    category,
    COUNT(*) AS experiments,
    AVG(observed_mean) AS category_mean,
    AVG(standard_deviation) AS average_standard_deviation
FROM experiment_summary
WHERE status = 'COMPLETED'
GROUP BY category
ORDER BY category;


-- Empirical variation across trials.
SELECT *
FROM probabilistic_analysis_report
ORDER BY empirical_mean DESC;


-- Amortized operation costs.
SELECT *
FROM amortized_analysis_report;


/* =========================================================
   23. THEORETICAL EVALUATION QUERIES
   ========================================================= */

SELECT
    n,
    harmonic_number(n) AS harmonic_value,
    expected_quicksort_comparisons(n) AS expected_comparisons
FROM (
    VALUES (10), (50), (100), (500), (1000)
) AS input_sizes(n);


-- Compare empirical and theoretical measurements.
SELECT
    experiment_name,
    expected_mean,
    observed_mean,
    percentage_deviation
FROM experiment_summary
WHERE status = 'COMPLETED';


/* =========================================================
   24. WORKFLOW VALIDATION
   ========================================================= */

SELECT *
FROM experiment_validation
WHERE valid_completed_experiment = FALSE;


/* =========================================================
   25. FAILURE CASE DEMONSTRATION
   ========================================================= */

DO $$
BEGIN
    BEGIN
        INSERT INTO experiments (
            algorithm_id,
            experiment_name,
            input_size,
            trial_count
        )
        SELECT
            algorithm_id,
            'Invalid Zero Size Experiment',
            0,
            10
        FROM algorithms
        WHERE algorithm_name = 'Dynamic Array Doubling';

    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'Expected failure: zero input size rejected.';
    END;

    BEGIN
        PERFORM harmonic_number(-5);

    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE
                'Expected failure: negative harmonic input rejected.';
    END;
END;
$$;


/* =========================================================
   26. TRANSACTION AND CONSISTENCY DEMONSTRATION
   ========================================================= */

SAVEPOINT analysis_consistency_checkpoint;

DO $$
DECLARE
    invalid_count BIGINT;
BEGIN
    SELECT COUNT(*)
    INTO invalid_count
    FROM experiments e
    WHERE e.status = 'COMPLETED'
      AND (
          e.observed_mean IS NULL
          OR e.standard_deviation IS NULL
      );

    IF invalid_count > 0 THEN
        RAISE EXCEPTION
            'Completed experiments contain missing statistics.';
    END IF;
END;
$$;

RELEASE SAVEPOINT analysis_consistency_checkpoint;

COMMIT;
