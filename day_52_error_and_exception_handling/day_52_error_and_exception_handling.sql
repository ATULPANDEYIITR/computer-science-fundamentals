DROP SCHEMA IF EXISTS exception_handling_demo CASCADE;
CREATE SCHEMA exception_handling_demo;
SET search_path TO exception_handling_demo;

-- The database model distinguishes validation failures from operational
-- failures so that application code can react to them differently.

CREATE TYPE repository_state AS ENUM ('active', 'archived');

CREATE TABLE repositories (
    repository_id BIGSERIAL PRIMARY KEY,
    repository_name TEXT NOT NULL,
    owner_name TEXT NOT NULL,
    default_branch TEXT NOT NULL DEFAULT 'main',
    state repository_state NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT repositories_name_format
        CHECK (repository_name ~ '^[a-z0-9][a-z0-9._-]*$'),
    CONSTRAINT repositories_owner_nonempty
        CHECK (length(trim(owner_name)) > 0),
    CONSTRAINT repositories_branch_nonempty
        CHECK (length(trim(default_branch)) > 0),
    CONSTRAINT repositories_unique_name
        UNIQUE (repository_name)
);

CREATE TABLE deployment_attempts (
    deployment_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id),
    attempt_number INTEGER NOT NULL,
    status TEXT NOT NULL,
    error_code TEXT,
    error_message TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    finished_at TIMESTAMPTZ,
    CONSTRAINT deployment_attempt_number_positive
        CHECK (attempt_number > 0),
    CONSTRAINT deployment_status_valid
        CHECK (status IN ('started', 'succeeded', 'failed', 'rolled_back')),
    CONSTRAINT deployment_error_consistency
        CHECK (
            (status IN ('failed', 'rolled_back')
                AND error_code IS NOT NULL)
            OR
            (status IN ('started', 'succeeded')
                AND error_code IS NULL
                AND error_message IS NULL)
        )
);

CREATE TABLE error_events (
    error_event_id BIGSERIAL PRIMARY KEY,
    deployment_id BIGINT
        REFERENCES deployment_attempts(deployment_id),
    error_code TEXT NOT NULL,
    error_class TEXT NOT NULL,
    message TEXT NOT NULL,
    is_transient BOOLEAN NOT NULL DEFAULT FALSE,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT error_code_nonempty
        CHECK (length(trim(error_code)) > 0),
    CONSTRAINT error_class_nonempty
        CHECK (length(trim(error_class)) > 0)
);

CREATE INDEX deployment_attempts_repository_idx
    ON deployment_attempts(repository_id, started_at DESC);

CREATE INDEX error_events_code_idx
    ON error_events(error_code, occurred_at DESC);

CREATE OR REPLACE FUNCTION validate_repository_name()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.repository_name IS NULL
       OR length(trim(NEW.repository_name)) = 0 THEN
        RAISE EXCEPTION
            USING
                ERRCODE = '23514',
                MESSAGE = 'Repository name cannot be empty.';
    END IF;

    IF NEW.state = 'archived'
       AND TG_OP = 'INSERT' THEN
        RAISE EXCEPTION
            USING
                ERRCODE = '23514',
                MESSAGE = 'A newly created repository must be active.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER repositories_validate_before_write
BEFORE INSERT OR UPDATE ON repositories
FOR EACH ROW
EXECUTE FUNCTION validate_repository_name();

CREATE OR REPLACE FUNCTION archive_repository(
    p_repository_id BIGINT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    current_state repository_state;
BEGIN
    SELECT state
    INTO current_state
    FROM repositories
    WHERE repository_id = p_repository_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            USING
                ERRCODE = 'P0002',
                MESSAGE = 'Repository does not exist.';
    END IF;

    IF current_state = 'archived' THEN
        RAISE EXCEPTION
            USING
                ERRCODE = 'P0001',
                MESSAGE = 'Repository is already archived.';
    END IF;

    UPDATE repositories
    SET state = 'archived'
    WHERE repository_id = p_repository_id;
END;
$$;

CREATE OR REPLACE FUNCTION register_deployment_failure(
    p_repository_id BIGINT,
    p_attempt_number INTEGER,
    p_error_code TEXT,
    p_error_class TEXT,
    p_message TEXT,
    p_is_transient BOOLEAN
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_deployment_id BIGINT;
BEGIN
    IF p_attempt_number <= 0 THEN
        RAISE EXCEPTION
            USING
                ERRCODE = '22023',
                MESSAGE = 'Attempt number must be positive.';
    END IF;

    IF p_error_code IS NULL OR length(trim(p_error_code)) = 0 THEN
        RAISE EXCEPTION
            USING
                ERRCODE = '22023',
                MESSAGE = 'Error code is required.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM repositories
        WHERE repository_id = p_repository_id
    ) THEN
        RAISE EXCEPTION
            USING
                ERRCODE = 'P0002',
                MESSAGE = 'Cannot record an error for an unknown repository.';
    END IF;

    INSERT INTO deployment_attempts (
        repository_id,
        attempt_number,
        status,
        error_code,
        error_message,
        finished_at
    )
    VALUES (
        p_repository_id,
        p_attempt_number,
        'failed',
        p_error_code,
        p_message,
        clock_timestamp()
    )
    RETURNING deployment_id
    INTO v_deployment_id;

    INSERT INTO error_events (
        deployment_id,
        error_code,
        error_class,
        message,
        is_transient
    )
    VALUES (
        v_deployment_id,
        p_error_code,
        p_error_class,
        p_message,
        p_is_transient
    );

    RETURN v_deployment_id;
END;
$$;

INSERT INTO repositories (
    repository_name,
    owner_name,
    default_branch
)
VALUES
    ('billing-service', 'platform-team', 'main'),
    ('analytics-service', 'data-team', 'main'),
    ('legacy-service', 'maintenance-team', 'release');

INSERT INTO deployment_attempts (
    repository_id,
    attempt_number,
    status
)
SELECT repository_id, 1, 'started'
FROM repositories
WHERE repository_name = 'billing-service';

UPDATE deployment_attempts
SET status = 'succeeded',
    finished_at = clock_timestamp()
WHERE repository_id = (
    SELECT repository_id
    FROM repositories
    WHERE repository_name = 'billing-service'
)
AND attempt_number = 1;

SELECT register_deployment_failure(
    (
        SELECT repository_id
        FROM repositories
        WHERE repository_name = 'analytics-service'
    ),
    1,
    'STORAGE_TIMEOUT',
    'TransientStorageError',
    'Temporary object-storage timeout.',
    TRUE
);

SELECT register_deployment_failure(
    (
        SELECT repository_id
        FROM repositories
        WHERE repository_name = 'legacy-service'
    ),
    1,
    'CONFIG_INVALID',
    'ConfigurationError',
    'Deployment environment is invalid.',
    FALSE
);

-- CTE-based reporting separates transient failures from permanent failures.
WITH latest_errors AS (
    SELECT DISTINCT ON (repository_id)
        d.repository_id,
        d.deployment_id,
        d.error_code,
        e.error_class,
        e.is_transient,
        d.started_at
    FROM deployment_attempts d
    JOIN error_events e
      ON e.deployment_id = d.deployment_id
    WHERE d.status = 'failed'
    ORDER BY d.repository_id, d.started_at DESC
)
SELECT
    r.repository_name,
    latest_errors.error_code,
    latest_errors.error_class,
    latest_errors.is_transient,
    latest_errors.started_at
FROM repositories r
JOIN latest_errors
  ON latest_errors.repository_id = r.repository_id
ORDER BY r.repository_name;

CREATE OR REPLACE VIEW repository_error_summary AS
SELECT
    r.repository_name,
    count(e.error_event_id) AS error_count,
    count(*) FILTER (
        WHERE e.is_transient
    ) AS transient_error_count,
    count(*) FILTER (
        WHERE NOT e.is_transient
    ) AS permanent_error_count
FROM repositories r
LEFT JOIN deployment_attempts d
    ON d.repository_id = r.repository_id
LEFT JOIN error_events e
    ON e.deployment_id = d.deployment_id
GROUP BY r.repository_id, r.repository_name;

SELECT *
FROM repository_error_summary
ORDER BY repository_name;

-- Transactional state transition: either the archive operation succeeds
-- completely or PostgreSQL rolls the change back.
BEGIN;

SELECT archive_repository(
    (
        SELECT repository_id
        FROM repositories
        WHERE repository_name = 'legacy-service'
    )
);

COMMIT;

-- Demonstrate database-level integrity enforcement without leaving
-- invalid data behind.
BEGIN;

DO $$
BEGIN
    BEGIN
        INSERT INTO repositories (
            repository_name,
            owner_name,
            default_branch
        )
        VALUES ('INVALID NAME', 'platform-team', 'main');
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'Expected validation failure was caught.';
    END;
END;
$$;

ROLLBACK;

SELECT
    repository_name,
    state
FROM repositories
ORDER BY repository_name;
