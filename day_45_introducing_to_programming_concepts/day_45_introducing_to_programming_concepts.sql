-- Introduction to Programming Concepts
-- PostgreSQL 15+
--
-- Case study: a training platform stores programming exercises, submitted
-- source files, execution attempts, and test results.
--
-- The schema distinguishes source validity, runtime completion, and test
-- correctness because these are separate properties of a program.
--
-- Run in a disposable PostgreSQL database. The transaction makes the
-- demonstration repeatable by removing only this example schema.

BEGIN;

DROP SCHEMA IF EXISTS programming_lab CASCADE;
CREATE SCHEMA programming_lab;
SET LOCAL search_path = programming_lab, public;

CREATE TYPE language_kind AS ENUM (
    'python',
    'javascript',
    'cpp',
    'java'
);

CREATE TYPE execution_state AS ENUM (
    'submitted',
    'syntax_error',
    'compiled',
    'runtime_error',
    'completed'
);

CREATE TABLE learners (
    learner_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    display_name text NOT NULL CHECK (length(trim(display_name)) > 0),
    email text NOT NULL UNIQUE CHECK (position('@' IN email) > 1),
    enrolled_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE exercises (
    exercise_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title text NOT NULL UNIQUE CHECK (length(trim(title)) > 0),
    concept text NOT NULL CHECK (
        concept IN (
            'syntax',
            'semantics',
            'variables',
            'data_types',
            'expressions',
            'compilation'
        )
    ),
    expected_output text NOT NULL,
    description text NOT NULL CHECK (length(trim(description)) > 0)
);

CREATE TABLE submissions (
    submission_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    learner_id bigint NOT NULL REFERENCES learners(learner_id),
    exercise_id bigint NOT NULL REFERENCES exercises(exercise_id),
    language language_kind NOT NULL,
    source_code text NOT NULL CHECK (length(trim(source_code)) > 0),
    submitted_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT submission_source_size
        CHECK (octet_length(source_code) <= 100000)
);

CREATE TABLE execution_attempts (
    attempt_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    submission_id bigint NOT NULL REFERENCES submissions(submission_id),
    attempt_number integer NOT NULL CHECK (attempt_number > 0),
    state execution_state NOT NULL DEFAULT 'submitted',
    compiler_or_runtime text NOT NULL CHECK (length(trim(compiler_or_runtime)) > 0),
    error_category text,
    error_message text,
    started_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    CONSTRAINT unique_attempt_number UNIQUE (submission_id, attempt_number),
    CONSTRAINT finish_after_start CHECK (
        finished_at IS NULL OR finished_at >= started_at
    ),
    CONSTRAINT error_details_consistent CHECK (
        (state IN ('syntax_error', 'runtime_error'))
        OR (error_category IS NULL AND error_message IS NULL)
    )
);

CREATE TABLE test_results (
    test_result_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    attempt_id bigint NOT NULL REFERENCES execution_attempts(attempt_id),
    test_name text NOT NULL CHECK (length(trim(test_name)) > 0),
    expected_value text NOT NULL,
    actual_value text,
    passed boolean NOT NULL,
    executed_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT unique_test_per_attempt UNIQUE (attempt_id, test_name),
    CONSTRAINT actual_value_for_pass CHECK (
        NOT passed OR actual_value IS NOT NULL
    )
);

CREATE INDEX submissions_learner_recent_idx
    ON submissions (learner_id, submitted_at DESC);

CREATE INDEX execution_attempts_submission_state_idx
    ON execution_attempts (submission_id, state);

CREATE INDEX test_results_failed_idx
    ON test_results (attempt_id, executed_at)
    WHERE passed = false;

-- A trigger rejects impossible execution transitions. Syntax errors and
-- runtime errors are terminal outcomes for an individual attempt; a new
-- attempt records a corrected source submission or a separate rerun.
CREATE FUNCTION enforce_attempt_transition()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.state <> 'submitted' THEN
            RAISE EXCEPTION
                'New execution attempts must begin in submitted state';
        END IF;
        RETURN NEW;
    END IF;

    IF NEW.submission_id <> OLD.submission_id
       OR NEW.attempt_number <> OLD.attempt_number THEN
        RAISE EXCEPTION
            'Attempt identity and parent submission are immutable';
    END IF;

    IF OLD.state IN ('syntax_error', 'runtime_error', 'completed')
       AND NEW.state <> OLD.state THEN
        RAISE EXCEPTION 'Terminal execution state cannot be changed';
    END IF;

    IF OLD.state = 'submitted'
       AND NEW.state NOT IN (
           'submitted', 'syntax_error', 'compiled', 'runtime_error', 'completed'
       ) THEN
        RAISE EXCEPTION 'Invalid transition from submitted';
    END IF;

    IF OLD.state = 'compiled'
       AND NEW.state NOT IN ('compiled', 'runtime_error', 'completed') THEN
        RAISE EXCEPTION 'Invalid transition from compiled';
    END IF;

    IF NEW.state IN ('syntax_error', 'runtime_error')
       AND (
           NEW.error_category IS NULL
           OR NEW.error_message IS NULL
           OR NEW.finished_at IS NULL
       ) THEN
        RAISE EXCEPTION
            'Failure states require an error category, message, and finish time';
    END IF;

    IF NEW.state = 'completed' AND NEW.finished_at IS NULL THEN
        RAISE EXCEPTION 'Completed execution requires a finish time';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER execution_attempt_transition_trigger
BEFORE INSERT OR UPDATE ON execution_attempts
FOR EACH ROW EXECUTE FUNCTION enforce_attempt_transition();

INSERT INTO learners (display_name, email) VALUES
    ('Asha Rao', 'asha@example.edu'),
    ('Kabir Sen', 'kabir@example.edu'),
    ('Leena Das', 'leena@example.edu');

INSERT INTO exercises (title, concept, expected_output, description) VALUES
    (
        'Expression precedence',
        'expressions',
        '14',
        'Evaluate 2 + 3 * 4 using multiplication precedence.'
    ),
    (
        'Variable binding',
        'variables',
        '42',
        'Assign 42 to a variable and return its value.'
    ),
    (
        'Syntax validation',
        'syntax',
        'valid',
        'Identify a missing operand before program execution.'
    ),
    (
        'Compilation and execution',
        'compilation',
        'Hello',
        'Compile or interpret a program and compare its output.'
    ),
    (
        'Type conversion',
        'data_types',
        '15',
        'Convert numeric text to a number before arithmetic.'
    );

INSERT INTO submissions (
    learner_id, exercise_id, language, source_code, submitted_at
)
SELECT l.learner_id, e.exercise_id, 'python',
       'print(2 + 3 * 4)',
       '2026-10-15 08:00:00+05:30'
FROM learners l
CROSS JOIN exercises e
WHERE l.email = 'asha@example.edu'
  AND e.title = 'Expression precedence';

INSERT INTO submissions (
    learner_id, exercise_id, language, source_code, submitted_at
)
SELECT l.learner_id, e.exercise_id, 'cpp',
       'int result = 2 + ;',
       '2026-10-15 08:01:00+05:30'
FROM learners l
CROSS JOIN exercises e
WHERE l.email = 'kabir@example.edu'
  AND e.title = 'Syntax validation';

INSERT INTO submissions (
    learner_id, exercise_id, language, source_code, submitted_at
)
SELECT l.learner_id, e.exercise_id, 'javascript',
       'const answer = 40 + 2; console.log(answer);',
       '2026-10-15 08:02:00+05:30'
FROM learners l
CROSS JOIN exercises e
WHERE l.email = 'leena@example.edu'
  AND e.title = 'Variable binding';

INSERT INTO execution_attempts (
    submission_id, attempt_number, state, compiler_or_runtime,
    started_at, finished_at
)
SELECT submission_id, 1, 'completed', 'CPython 3.13',
       '2026-10-15 08:00:01+05:30',
       '2026-10-15 08:00:01.020+05:30'
FROM submissions
WHERE source_code = 'print(2 + 3 * 4)';

INSERT INTO execution_attempts (
    submission_id, attempt_number, state, compiler_or_runtime,
    error_category, error_message, started_at, finished_at
)
SELECT submission_id, 1, 'syntax_error', 'GCC 15',
       'syntax',
       'Expected an expression after the plus operator',
       '2026-10-15 08:01:01+05:30',
       '2026-10-15 08:01:01.010+05:30'
FROM submissions
WHERE source_code = 'int result = 2 + ;';

INSERT INTO execution_attempts (
    submission_id, attempt_number, state, compiler_or_runtime,
    started_at, finished_at
)
SELECT submission_id, 1, 'completed', 'Node.js 22',
       '2026-10-15 08:02:01+05:30',
       '2026-10-15 08:02:01.030+05:30'
FROM submissions
WHERE source_code = 'const answer = 40 + 2; console.log(answer);';

INSERT INTO test_results (
    attempt_id, test_name, expected_value, actual_value, passed
)
SELECT a.attempt_id, 'precedence-example', '14', '14', true
FROM execution_attempts a
JOIN submissions s USING (submission_id)
WHERE s.source_code = 'print(2 + 3 * 4)';

INSERT INTO test_results (
    attempt_id, test_name, expected_value, actual_value, passed
)
SELECT a.attempt_id, 'variable-value', '42', '42', true
FROM execution_attempts a
JOIN submissions s USING (submission_id)
WHERE s.source_code = 'const answer = 40 + 2; console.log(answer);';

-- Report submission state separately from execution state and test correctness.
SELECT
    s.submission_id,
    l.display_name AS learner,
    e.title AS exercise,
    s.language,
    a.state AS execution_state,
    COALESCE(bool_and(t.passed), false) AS all_recorded_tests_passed,
    count(t.test_result_id) AS recorded_test_count,
    a.error_category,
    a.error_message
FROM submissions s
JOIN learners l ON l.learner_id = s.learner_id
JOIN exercises e ON e.exercise_id = s.exercise_id
LEFT JOIN execution_attempts a ON a.submission_id = s.submission_id
LEFT JOIN test_results t ON t.attempt_id = a.attempt_id
GROUP BY
    s.submission_id, l.display_name, e.title, s.language,
    a.state, a.error_category, a.error_message
ORDER BY s.submission_id;

-- Compare learner activity and successful recorded tests by programming language.
SELECT
    s.language,
    count(DISTINCT s.submission_id) AS submissions,
    count(DISTINCT s.learner_id) AS participating_learners,
    count(t.test_result_id) FILTER (WHERE t.passed) AS passing_tests,
    count(t.test_result_id) FILTER (WHERE NOT t.passed) AS failing_tests
FROM submissions s
LEFT JOIN execution_attempts a ON a.submission_id = s.submission_id
LEFT JOIN test_results t ON t.attempt_id = a.attempt_id
GROUP BY s.language
ORDER BY s.language;

-- This view describes learning outcomes without conflating execution completion
-- with semantic correctness.
CREATE VIEW exercise_outcomes AS
SELECT
    e.exercise_id,
    e.title,
    e.concept,
    count(DISTINCT s.submission_id) AS submission_count,
    count(DISTINCT a.attempt_id)
        FILTER (WHERE a.state = 'syntax_error') AS syntax_failures,
    count(DISTINCT a.attempt_id)
        FILTER (WHERE a.state = 'runtime_error') AS runtime_failures,
    count(DISTINCT a.attempt_id)
        FILTER (WHERE a.state = 'completed') AS completed_attempts,
    count(t.test_result_id) FILTER (WHERE t.passed) AS passing_tests,
    count(t.test_result_id) FILTER (WHERE NOT t.passed) AS failing_tests
FROM exercises e
LEFT JOIN submissions s ON s.exercise_id = e.exercise_id
LEFT JOIN execution_attempts a ON a.submission_id = s.submission_id
LEFT JOIN test_results t ON t.attempt_id = a.attempt_id
GROUP BY e.exercise_id, e.title, e.concept;

SELECT * FROM exercise_outcomes ORDER BY concept, title;

-- Demonstrate an invalid transition inside a savepoint. The expected trigger
-- error is caught by rolling back to the savepoint so the rest of the script
-- can continue in the same transaction.
SAVEPOINT invalid_transition_demo;

DO $$
DECLARE
    completed_attempt_id bigint;
BEGIN
    SELECT a.attempt_id
    INTO completed_attempt_id
    FROM execution_attempts a
    JOIN submissions s USING (submission_id)
    WHERE s.source_code = 'print(2 + 3 * 4)';

    BEGIN
        UPDATE execution_attempts
        SET state = 'runtime_error',
            error_category = 'runtime',
            error_message = 'Attempt to overwrite completed result',
            finished_at = now()
        WHERE attempt_id = completed_attempt_id;
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Invalid transition rejected: %', SQLERRM;
    END;
END;
$$;

ROLLBACK TO SAVEPOINT invalid_transition_demo;
RELEASE SAVEPOINT invalid_transition_demo;

-- The transaction preserves all demonstration data while releasing locks.
COMMIT;
