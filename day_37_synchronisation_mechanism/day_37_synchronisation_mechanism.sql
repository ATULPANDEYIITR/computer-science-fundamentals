-- PostgreSQL 14+ compatible synchronization laboratory.
--
-- The database model demonstrates database-level equivalents and supporting
-- mechanisms for mutex-like exclusion, semaphore-like capacity control,
-- row locks, advisory locks, and condition-style state transitions.
--
-- Database locks are not identical to in-memory thread primitives:
-- PostgreSQL coordinates concurrent database sessions and transactions.
-- SELECT ... FOR UPDATE provides row-level mutual exclusion, while
-- pg_advisory_xact_lock provides application-defined transactional exclusion.
-- A permit table can model a bounded semaphore by locking and consuming rows.

DROP SCHEMA IF EXISTS synchronization_lab CASCADE;
CREATE SCHEMA synchronization_lab;
SET search_path = synchronization_lab;

CREATE TABLE worker_pool (
    pool_id         BIGSERIAL PRIMARY KEY,
    pool_name       TEXT NOT NULL UNIQUE,
    capacity        INTEGER NOT NULL CHECK (capacity > 0)
);

CREATE TABLE worker_permit (
    permit_id       BIGSERIAL PRIMARY KEY,
    pool_id         BIGINT NOT NULL
        REFERENCES worker_pool(pool_id)
        ON DELETE CASCADE,
    permit_number   INTEGER NOT NULL,
    holder_task_id  BIGINT,
    acquired_at     TIMESTAMPTZ,
    UNIQUE (pool_id, permit_number)
);

CREATE TABLE synchronization_task (
    task_id         BIGSERIAL PRIMARY KEY,
    pool_id         BIGINT NOT NULL
        REFERENCES worker_pool(pool_id),
    task_name       TEXT NOT NULL,
    state           TEXT NOT NULL DEFAULT 'WAITING',
    priority        INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ,
    CHECK (
        state IN (
            'WAITING',
            'RUNNING',
            'SUCCEEDED',
            'FAILED',
            'CANCELLED'
        )
    ),
    CHECK (
        finished_at IS NULL
        OR state IN ('SUCCEEDED', 'FAILED', 'CANCELLED')
    )
);

CREATE TABLE synchronization_event (
    event_id        BIGSERIAL PRIMARY KEY,
    task_id         BIGINT NOT NULL
        REFERENCES synchronization_task(task_id)
        ON DELETE CASCADE,
    event_type      TEXT NOT NULL,
    event_message   TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE lock_audit (
    audit_id        BIGSERIAL PRIMARY KEY,
    task_id         BIGINT REFERENCES synchronization_task(task_id),
    mechanism       TEXT NOT NULL,
    action          TEXT NOT NULL,
    session_pid     INTEGER NOT NULL DEFAULT pg_backend_pid(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX idx_task_pool_state_priority
    ON synchronization_task(pool_id, state, priority DESC, created_at);

CREATE INDEX idx_event_task_time
    ON synchronization_event(task_id, created_at DESC);

CREATE INDEX idx_permit_pool_holder
    ON worker_permit(pool_id, holder_task_id);

INSERT INTO worker_pool(pool_name, capacity)
VALUES ('compiler-workers', 2);

INSERT INTO worker_permit(pool_id, permit_number)
SELECT pool_id, number
FROM worker_pool
CROSS JOIN generate_series(1, capacity) AS number;

INSERT INTO synchronization_task(
    pool_id,
    task_name,
    state,
    priority
)
SELECT
    pool_id,
    task_name,
    state,
    priority
FROM worker_pool
CROSS JOIN (
    VALUES
        ('compile-inventory-main', 'WAITING', 10),
        ('compile-payments-main', 'WAITING', 20),
        ('compile-inventory-cache', 'WAITING', 30),
        ('compile-payments-api', 'WAITING', 15),
        ('compile-reporting', 'WAITING', 5)
) AS tasks(task_name, state, priority)
WHERE pool_name = 'compiler-workers';

-- -------------------------------------------------------------------------
-- Mutex-like row protection
-- -------------------------------------------------------------------------
--
-- SELECT FOR UPDATE locks the selected task rows until the transaction ends.
-- A second session attempting to update the same row must wait.
--
-- The UPDATE is deliberately state-oriented. Synchronization correctness
-- should be based on a transactionally protected predicate, not on the
-- assumption that a previously observed value is still current.

BEGIN;

SELECT task_id, task_name, state
FROM synchronization_task
WHERE task_name = 'compile-payments-main'
FOR UPDATE;

UPDATE synchronization_task
SET state = 'RUNNING',
    started_at = clock_timestamp()
WHERE task_name = 'compile-payments-main'
  AND state = 'WAITING';

INSERT INTO synchronization_event(
    task_id,
    event_type,
    event_message
)
SELECT
    task_id,
    'STATE_CHANGE',
    'Task transitioned from WAITING to RUNNING under row lock'
FROM synchronization_task
WHERE task_name = 'compile-payments-main';

INSERT INTO lock_audit(task_id, mechanism, action)
SELECT
    task_id,
    'ROW_LOCK',
    'SELECT FOR UPDATE acquired'
FROM synchronization_task
WHERE task_name = 'compile-payments-main';

COMMIT;

-- -------------------------------------------------------------------------
-- Semaphore-like permit acquisition
-- -------------------------------------------------------------------------
--
-- Each permit row represents one available unit of concurrency.
-- The transaction locks one currently-free permit and assigns it to a task.
-- SKIP LOCKED allows independent workers to find different permits without
-- waiting behind a permit already being processed by another worker.
--
-- The UPDATE is atomic with respect to the row locks established by the CTE.

BEGIN;

WITH available_permit AS (
    SELECT permit_id
    FROM worker_permit
    WHERE pool_id = (
        SELECT pool_id
        FROM worker_pool
        WHERE pool_name = 'compiler-workers'
    )
    AND holder_task_id IS NULL
    ORDER BY permit_number
    FOR UPDATE SKIP LOCKED
    LIMIT 1
)
UPDATE worker_permit AS permit
SET holder_task_id = (
        SELECT task_id
        FROM synchronization_task
        WHERE task_name = 'compile-inventory-main'
    ),
    acquired_at = clock_timestamp()
FROM available_permit
WHERE permit.permit_id = available_permit.permit_id
RETURNING permit.permit_id, permit.permit_number, permit.holder_task_id;

INSERT INTO lock_audit(
    task_id,
    mechanism,
    action
)
SELECT
    task_id,
    'PERMIT_ROW_LOCK',
    'Semaphore permit acquired'
FROM synchronization_task
WHERE task_name = 'compile-inventory-main';

COMMIT;

-- -------------------------------------------------------------------------
-- Condition-style state predicate
-- -------------------------------------------------------------------------
--
-- PostgreSQL has no direct SQL equivalent of a thread condition variable.
-- Instead, a transaction waits on or repeatedly evaluates a database state
-- predicate. FOR UPDATE and transaction isolation provide the synchronization
-- boundary while the application can poll, LISTEN/NOTIFY, or retry.
--
-- This query exposes tasks whose prerequisite state is now satisfied.

SELECT
    task_id,
    task_name,
    state,
    priority
FROM synchronization_task
WHERE state = 'WAITING'
ORDER BY priority DESC, created_at
FOR UPDATE SKIP LOCKED;

-- -------------------------------------------------------------------------
-- Monitor-like transactional operation
-- -------------------------------------------------------------------------
--
-- The following transaction encapsulates state, locking, validation, and
-- transition in one database operation. This is conceptually monitor-like:
-- callers do not need to coordinate individual field updates themselves.

BEGIN;

WITH candidate AS (
    SELECT task_id
    FROM synchronization_task
    WHERE state = 'WAITING'
    ORDER BY priority DESC, created_at
    FOR UPDATE SKIP LOCKED
    LIMIT 1
)
UPDATE synchronization_task AS task
SET state = 'RUNNING',
    started_at = clock_timestamp()
FROM candidate
WHERE task.task_id = candidate.task_id
RETURNING task.task_id, task.task_name, task.state;

INSERT INTO synchronization_event(
    task_id,
    event_type,
    event_message
)
SELECT
    task_id,
    'WORK_ACQUIRED',
    'Worker atomically claimed a waiting task'
FROM synchronization_task
WHERE state = 'RUNNING'
  AND started_at >= clock_timestamp() - INTERVAL '5 seconds';

COMMIT;

-- -------------------------------------------------------------------------
-- Advisory lock: application-defined mutex-like coordination
-- -------------------------------------------------------------------------
--
-- Advisory locks are not tied to a table row. An application can assign a
-- stable integer key to a logical resource such as "repository 42".
-- Transaction-scoped advisory locks automatically disappear at COMMIT or
-- ROLLBACK.

BEGIN;

SELECT pg_advisory_xact_lock(4242);

INSERT INTO lock_audit(
    mechanism,
    action
)
VALUES (
    'TRANSACTION_ADVISORY_LOCK',
    'Logical resource 4242 exclusively locked'
);

COMMIT;

-- -------------------------------------------------------------------------
-- Finish a task and release its semaphore permit in one transaction
-- -------------------------------------------------------------------------

BEGIN;

WITH selected_task AS (
    SELECT task_id
    FROM synchronization_task
    WHERE task_name = 'compile-inventory-main'
      AND state = 'RUNNING'
    FOR UPDATE
)
UPDATE synchronization_task AS task
SET state = 'SUCCEEDED',
    finished_at = clock_timestamp()
FROM selected_task
WHERE task.task_id = selected_task.task_id
RETURNING task.task_id, task.task_name, task.state;

UPDATE worker_permit
SET holder_task_id = NULL,
    acquired_at = NULL
WHERE holder_task_id = (
    SELECT task_id
    FROM synchronization_task
    WHERE task_name = 'compile-inventory-main'
);

INSERT INTO synchronization_event(
    task_id,
    event_type,
    event_message
)
SELECT
    task_id,
    'WORK_RELEASED',
    'Task completed and concurrency permit was released'
FROM synchronization_task
WHERE task_name = 'compile-inventory-main';

COMMIT;

-- -------------------------------------------------------------------------
-- Detect inconsistent semaphore state
-- -------------------------------------------------------------------------

SELECT
    pool.pool_name,
    pool.capacity,
    COUNT(permit.permit_id) AS total_permits,
    COUNT(permit.holder_task_id) AS occupied_permits,
    pool.capacity - COUNT(permit.holder_task_id) AS available_permits
FROM worker_pool AS pool
LEFT JOIN worker_permit AS permit
    ON permit.pool_id = pool.pool_id
GROUP BY pool.pool_id, pool.pool_name, pool.capacity;

-- -------------------------------------------------------------------------
-- Detect invalid or suspicious task states
-- -------------------------------------------------------------------------

SELECT
    task_id,
    task_name,
    state,
    started_at,
    finished_at
FROM synchronization_task
WHERE
    (state = 'RUNNING' AND started_at IS NULL)
    OR
    (state IN ('SUCCEEDED', 'FAILED', 'CANCELLED')
     AND finished_at IS NULL);

-- -------------------------------------------------------------------------
-- Demonstrate PostgreSQL's transactional isolation semantics
-- -------------------------------------------------------------------------
--
-- This transaction shows a serialization-oriented operation. SERIALIZABLE
-- does not make application code magically race-free. It detects conflicts
-- that violate serial execution and can require a retry.

BEGIN TRANSACTION ISOLATION LEVEL SERIALIZABLE;

SELECT
    pool_id,
    pool_name,
    capacity
FROM worker_pool
WHERE pool_name = 'compiler-workers';

INSERT INTO lock_audit(
    mechanism,
    action
)
VALUES (
    'SERIALIZABLE_TRANSACTION',
    'Protected capacity decision from serialization anomalies'
);

COMMIT;

-- -------------------------------------------------------------------------
-- Operational view
-- -------------------------------------------------------------------------

CREATE VIEW synchronization_status AS
SELECT
    pool.pool_name,
    pool.capacity,
    COUNT(permit.permit_id) AS total_permits,
    COUNT(permit.holder_task_id) AS busy_permits,
    COUNT(permit.permit_id)
        - COUNT(permit.holder_task_id) AS free_permits,
    COUNT(task.task_id)
        FILTER (WHERE task.state = 'WAITING') AS waiting_tasks,
    COUNT(task.task_id)
        FILTER (WHERE task.state = 'RUNNING') AS running_tasks,
    COUNT(task.task_id)
        FILTER (WHERE task.state = 'SUCCEEDED') AS succeeded_tasks,
    COUNT(task.task_id)
        FILTER (WHERE task.state = 'FAILED') AS failed_tasks
FROM worker_pool AS pool
LEFT JOIN worker_permit AS permit
    ON permit.pool_id = pool.pool_id
LEFT JOIN synchronization_task AS task
    ON task.pool_id = pool.pool_id
GROUP BY
    pool.pool_id,
    pool.pool_name,
    pool.capacity;

SELECT *
FROM synchronization_status;

-- -------------------------------------------------------------------------
-- Final audit query
-- -------------------------------------------------------------------------

SELECT
    audit_id,
    task_id,
    mechanism,
    action,
    session_pid,
    created_at
FROM lock_audit
ORDER BY audit_id;
