DROP SCHEMA IF EXISTS heap_lab CASCADE;
CREATE SCHEMA heap_lab;
SET search_path = heap_lab;

CREATE TYPE repository_status AS ENUM ('ACTIVE', 'ARCHIVED');

CREATE TABLE repositories (
    repository_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_name TEXT NOT NULL UNIQUE,
    status repository_status NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE branches (
    branch_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    branch_name TEXT NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    is_protected BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (repository_id, branch_name)
);

CREATE TABLE heap_profiles (
    heap_profile_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    profile_name TEXT NOT NULL UNIQUE,
    heap_type TEXT NOT NULL CHECK (heap_type IN ('MIN', 'MAX')),
    description TEXT NOT NULL
);

CREATE TABLE heap_operations (
    operation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    heap_profile_id BIGINT NOT NULL
        REFERENCES heap_profiles(heap_profile_id)
        ON DELETE CASCADE,
    operation_name TEXT NOT NULL CHECK (
        operation_name IN (
            'INSERT',
            'PEEK',
            'EXTRACT',
            'HEAPIFY',
            'REPLACE_ROOT'
        )
    ),
    value BIGINT NOT NULL,
    sequence_no BIGINT NOT NULL,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (heap_profile_id, sequence_no)
);

CREATE TABLE priority_jobs (
    job_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    job_name TEXT NOT NULL,
    priority INTEGER NOT NULL CHECK (priority >= 0),
    duration_seconds INTEGER NOT NULL CHECK (duration_seconds > 0),
    state TEXT NOT NULL DEFAULT 'QUEUED' CHECK (
        state IN ('QUEUED', 'RUNNING', 'COMPLETED', 'FAILED')
    ),
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_priority_jobs_queue
    ON priority_jobs (repository_id, state, priority, submitted_at);

CREATE INDEX idx_heap_operations_profile_sequence
    ON heap_operations (heap_profile_id, sequence_no);

CREATE TABLE heap_metrics (
    metric_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    heap_profile_id BIGINT NOT NULL
        REFERENCES heap_profiles(heap_profile_id)
        ON DELETE CASCADE,
    operation_count BIGINT NOT NULL CHECK (operation_count >= 0),
    total_value BIGINT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE OR REPLACE FUNCTION validate_job_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.state = 'COMPLETED'
       AND NEW.state <> 'COMPLETED' THEN
        RAISE EXCEPTION
            'completed job % cannot transition to %',
            OLD.job_id,
            NEW.state;
    END IF;

    IF NEW.state = 'COMPLETED'
       AND NEW.completed_at IS NULL THEN
        NEW.completed_at := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_job_transition
BEFORE UPDATE ON priority_jobs
FOR EACH ROW
EXECUTE FUNCTION validate_job_transition();

CREATE OR REPLACE FUNCTION extract_min_job(
    p_repository_id BIGINT
)
RETURNS TABLE (
    job_id BIGINT,
    job_name TEXT,
    priority INTEGER,
    duration_seconds INTEGER
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH selected AS (
        SELECT j.job_id
        FROM priority_jobs AS j
        WHERE j.repository_id = p_repository_id
          AND j.state = 'QUEUED'
        ORDER BY j.priority ASC, j.submitted_at ASC, j.job_id ASC
        FOR UPDATE SKIP LOCKED
        LIMIT 1
    )
    UPDATE priority_jobs AS j
    SET state = 'RUNNING'
    FROM selected
    WHERE j.job_id = selected.job_id
    RETURNING
        j.job_id,
        j.job_name,
        j.priority,
        j.duration_seconds;
END;
$$;

INSERT INTO repositories (repository_name)
VALUES
    ('platform-services'),
    ('security-analytics');

INSERT INTO branches (
    repository_id,
    branch_name,
    is_default,
    is_protected
)
SELECT
    repository_id,
    'main',
    TRUE,
    TRUE
FROM repositories;

INSERT INTO branches (
    repository_id,
    branch_name,
    is_default,
    is_protected
)
SELECT
    repository_id,
    'develop',
    FALSE,
    FALSE
FROM repositories;

INSERT INTO heap_profiles (
    profile_name,
    heap_type,
    description
)
VALUES
    (
        'incident-min-heap',
        'MIN',
        'Lowest-priority-number incident is extracted first'
    ),
    (
        'capacity-max-heap',
        'MAX',
        'Largest capacity score is extracted first'
    );

INSERT INTO heap_operations (
    heap_profile_id,
    operation_name,
    value,
    sequence_no
)
SELECT
    hp.heap_profile_id,
    x.operation_name,
    x.value,
    x.sequence_no
FROM heap_profiles AS hp
CROSS JOIN (
    VALUES
        ('INSERT', 42, 1),
        ('INSERT', 17, 2),
        ('INSERT', 8, 3),
        ('HEAPIFY', 8, 4),
        ('PEEK', 8, 5),
        ('EXTRACT', 8, 6),
        ('EXTRACT', 17, 7),
        ('REPLACE_ROOT', 12, 8)
) AS x(operation_name, value, sequence_no)
WHERE hp.profile_name = 'incident-min-heap';

INSERT INTO heap_operations (
    heap_profile_id,
    operation_name,
    value,
    sequence_no
)
SELECT
    hp.heap_profile_id,
    x.operation_name,
    x.value,
    x.sequence_no
FROM heap_profiles AS hp
CROSS JOIN (
    VALUES
        ('INSERT', 25, 1),
        ('INSERT', 70, 2),
        ('INSERT', 45, 3),
        ('HEAPIFY', 70, 4),
        ('PEEK', 70, 5),
        ('EXTRACT', 70, 6)
) AS x(operation_name, value, sequence_no)
WHERE hp.profile_name = 'capacity-max-heap';

INSERT INTO priority_jobs (
    repository_id,
    job_name,
    priority,
    duration_seconds
)
SELECT
    r.repository_id,
    x.job_name,
    x.priority,
    x.duration_seconds
FROM repositories AS r
CROSS JOIN (
    VALUES
        ('security-alert', 0, 5),
        ('incident-analysis', 1, 30),
        ('database-backup', 2, 45),
        ('report-generation', 3, 20),
        ('cache-refresh', 2, 10)
) AS x(job_name, priority, duration_seconds)
WHERE r.repository_name = 'platform-services';

INSERT INTO heap_metrics (
    heap_profile_id,
    operation_count,
    total_value
)
SELECT
    hp.heap_profile_id,
    COUNT(ho.operation_id),
    COALESCE(SUM(ho.value), 0)
FROM heap_profiles AS hp
LEFT JOIN heap_operations AS ho
    ON ho.heap_profile_id = hp.heap_profile_id
GROUP BY hp.heap_profile_id;

CREATE VIEW heap_operation_report AS
SELECT
    hp.profile_name,
    hp.heap_type,
    COUNT(ho.operation_id) AS operation_count,
    MIN(ho.value) AS minimum_value,
    MAX(ho.value) AS maximum_value,
    AVG(ho.value)::NUMERIC(12, 2) AS average_value
FROM heap_profiles AS hp
LEFT JOIN heap_operations AS ho
    ON ho.heap_profile_id = hp.heap_profile_id
GROUP BY
    hp.profile_name,
    hp.heap_type;

CREATE VIEW queued_job_report AS
SELECT
    r.repository_name,
    COUNT(*) AS queued_jobs,
    MIN(j.priority) AS next_priority,
    SUM(j.duration_seconds) AS total_queued_duration
FROM priority_jobs AS j
JOIN repositories AS r
    ON r.repository_id = j.repository_id
WHERE j.state = 'QUEUED'
GROUP BY r.repository_name;

CREATE VIEW priority_execution_order AS
SELECT
    j.job_id,
    r.repository_name,
    j.job_name,
    j.priority,
    j.duration_seconds,
    ROW_NUMBER() OVER (
        PARTITION BY j.repository_id
        ORDER BY
            j.priority ASC,
            j.submitted_at ASC,
            j.job_id ASC
    ) AS execution_position
FROM priority_jobs AS j
JOIN repositories AS r
    ON r.repository_id = j.repository_id
WHERE j.state = 'QUEUED';

-- Heap-profile reporting.
SELECT *
FROM heap_operation_report
ORDER BY profile_name;

-- Priority-queue inspection.
SELECT *
FROM priority_execution_order
ORDER BY repository_name, execution_position;

-- Queue aggregation.
SELECT *
FROM queued_job_report
ORDER BY repository_name;

-- CTE-based extraction candidate.
WITH next_job AS (
    SELECT
        j.job_id,
        j.repository_id,
        j.job_name,
        j.priority,
        j.duration_seconds
    FROM priority_jobs AS j
    WHERE j.state = 'QUEUED'
    ORDER BY
        j.priority ASC,
        j.submitted_at ASC,
        j.job_id ASC
    LIMIT 1
)
SELECT
    next_job.*,
    r.repository_name
FROM next_job
JOIN repositories AS r
    ON r.repository_id = next_job.repository_id;

-- Validation of heap operation sequences.
SELECT
    hp.profile_name,
    ho.sequence_no,
    ho.operation_name,
    ho.value,
    CASE
        WHEN ho.value >= 0 THEN 'VALID'
        ELSE 'INVALID'
    END AS validation_state
FROM heap_operations AS ho
JOIN heap_profiles AS hp
    ON hp.heap_profile_id = ho.heap_profile_id
ORDER BY hp.profile_name, ho.sequence_no;

-- Transactional priority extraction.
BEGIN;

SELECT *
FROM extract_min_job(
    (
        SELECT repository_id
        FROM repositories
        WHERE repository_name = 'platform-services'
    )
);

COMMIT;

-- Mark the selected running job as completed.
BEGIN;

UPDATE priority_jobs
SET state = 'COMPLETED'
WHERE job_id = (
    SELECT job_id
    FROM priority_jobs
    WHERE state = 'RUNNING'
    ORDER BY submitted_at, job_id
    LIMIT 1
);

COMMIT;

-- Final queue state.
SELECT
    r.repository_name,
    j.job_name,
    j.priority,
    j.state,
    j.submitted_at,
    j.completed_at
FROM priority_jobs AS j
JOIN repositories AS r
    ON r.repository_id = j.repository_id
ORDER BY
    r.repository_name,
    j.priority,
    j.submitted_at;
