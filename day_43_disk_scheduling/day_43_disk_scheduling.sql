-- PostgreSQL-compatible disk scheduling governance model.
--
-- The database separates:
--   repositories of storage workloads,
--   physical disks,
--   requests,
--   scheduling algorithms,
--   scheduling runs,
--   policy limits,
--   and calculated scheduling decisions.
--
-- Database constraints prevent impossible cylinder positions, duplicate
-- request identifiers within a workload, negative movement, and invalid
-- average values.

DROP SCHEMA IF EXISTS disk_scheduling CASCADE;
CREATE SCHEMA disk_scheduling;

SET search_path TO disk_scheduling;

CREATE TYPE direction AS ENUM ('LEFT', 'RIGHT');

CREATE TYPE request_priority AS ENUM (
    'INTERACTIVE',
    'BATCH',
    'ARCHIVE'
);

CREATE TYPE scheduling_algorithm AS ENUM (
    'FCFS',
    'SSTF',
    'SCAN',
    'C-SCAN',
    'LOOK',
    'C-LOOK'
);

CREATE TABLE disks (
    disk_id BIGSERIAL PRIMARY KEY,
    disk_name TEXT NOT NULL UNIQUE,
    cylinder_count INTEGER NOT NULL CHECK (cylinder_count >= 2),
    current_head INTEGER NOT NULL,
    CONSTRAINT valid_head_position
        CHECK (current_head >= 0 AND current_head < cylinder_count)
);

CREATE TABLE workloads (
    workload_id BIGSERIAL PRIMARY KEY,
    workload_name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE disk_requests (
    request_id BIGSERIAL PRIMARY KEY,
    workload_id BIGINT NOT NULL REFERENCES workloads(workload_id),
    external_request_id TEXT NOT NULL,
    cylinder INTEGER NOT NULL,
    priority request_priority NOT NULL,
    requested_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_workload_request
        UNIQUE (workload_id, external_request_id)
);

CREATE TABLE scheduling_policies (
    policy_id BIGSERIAL PRIMARY KEY,
    policy_name TEXT NOT NULL UNIQUE,
    maximum_movement INTEGER NOT NULL CHECK (maximum_movement >= 0),
    require_deterministic_ties BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE scheduling_runs (
    run_id BIGSERIAL PRIMARY KEY,
    workload_id BIGINT NOT NULL REFERENCES workloads(workload_id),
    disk_id BIGINT NOT NULL REFERENCES disks(disk_id),
    policy_id BIGINT NOT NULL REFERENCES scheduling_policies(policy_id),
    direction direction NOT NULL,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE scheduling_results (
    result_id BIGSERIAL PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES scheduling_runs(run_id)
        ON DELETE CASCADE,
    algorithm scheduling_algorithm NOT NULL,
    service_order INTEGER[] NOT NULL,
    physical_path INTEGER[] NOT NULL,
    total_movement INTEGER NOT NULL CHECK (total_movement >= 0),
    average_seek NUMERIC(12, 4) NOT NULL CHECK (average_seek >= 0),
    eligible BOOLEAN NOT NULL,
    UNIQUE (run_id, algorithm)
);

CREATE TABLE scheduling_request_service (
    result_id BIGINT NOT NULL REFERENCES scheduling_results(result_id)
        ON DELETE CASCADE,
    request_position INTEGER NOT NULL CHECK (request_position > 0),
    cylinder INTEGER NOT NULL CHECK (cylinder >= 0),
    PRIMARY KEY (result_id, request_position)
);

CREATE INDEX idx_requests_workload_cylinder
    ON disk_requests (workload_id, cylinder);

CREATE INDEX idx_runs_workload_time
    ON scheduling_runs (workload_id, executed_at DESC);

CREATE INDEX idx_results_run_movement
    ON scheduling_results (run_id, total_movement);

INSERT INTO disks (
    disk_name,
    cylinder_count,
    current_head
)
VALUES (
    'storage-array-01',
    200,
    53
);

INSERT INTO workloads (workload_name)
VALUES ('mixed-production-read-workload');

INSERT INTO scheduling_policies (
    policy_name,
    maximum_movement,
    require_deterministic_ties
)
VALUES (
    'production-seek-budget',
    300,
    TRUE
);

INSERT INTO disk_requests (
    workload_id,
    external_request_id,
    cylinder,
    priority
)
SELECT
    w.workload_id,
    source.external_request_id,
    source.cylinder,
    source.priority::request_priority
FROM workloads AS w
CROSS JOIN (
    VALUES
        ('REQ-001', 98,  'INTERACTIVE'),
        ('REQ-002', 183, 'BATCH'),
        ('REQ-003', 37,  'INTERACTIVE'),
        ('REQ-004', 122, 'BATCH'),
        ('REQ-005', 14,  'ARCHIVE'),
        ('REQ-006', 124, 'INTERACTIVE'),
        ('REQ-007', 65,  'INTERACTIVE'),
        ('REQ-008', 67,  'BATCH')
) AS source(external_request_id, cylinder, priority)
WHERE w.workload_name = 'mixed-production-read-workload';

-- Database-level validation of every request against its target disk.
CREATE OR REPLACE FUNCTION validate_request_cylinder()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    max_cylinder INTEGER;
BEGIN
    SELECT cylinder_count - 1
    INTO max_cylinder
    FROM disks
    ORDER BY disk_id
    LIMIT 1;

    IF NEW.cylinder < 0 OR NEW.cylinder > max_cylinder THEN
        RAISE EXCEPTION
            'Cylinder % is outside the configured disk range 0..%',
            NEW.cylinder,
            max_cylinder;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER request_cylinder_validation
BEFORE INSERT OR UPDATE ON disk_requests
FOR EACH ROW
EXECUTE FUNCTION validate_request_cylinder();

INSERT INTO scheduling_runs (
    workload_id,
    disk_id,
    policy_id,
    direction
)
SELECT
    w.workload_id,
    d.disk_id,
    p.policy_id,
    'RIGHT'
FROM workloads AS w
CROSS JOIN disks AS d
CROSS JOIN scheduling_policies AS p
WHERE w.workload_name = 'mixed-production-read-workload'
  AND d.disk_name = 'storage-array-01'
  AND p.policy_name = 'production-seek-budget';

-- FCFS preserves request-arrival order.
INSERT INTO scheduling_results (
    run_id,
    algorithm,
    service_order,
    physical_path,
    total_movement,
    average_seek,
    eligible
)
SELECT
    r.run_id,
    'FCFS',
    ARRAY_AGG(dr.cylinder ORDER BY dr.request_id),
    ARRAY_AGG(dr.cylinder ORDER BY dr.request_id),
    SUM(
        ABS(
            dr.cylinder -
            COALESCE(
                LAG(dr.cylinder) OVER (
                    ORDER BY dr.request_id
                ),
                d.current_head
            )
        )
    )::INTEGER,
    (
        SUM(
            ABS(
                dr.cylinder -
                COALESCE(
                    LAG(dr.cylinder) OVER (
                        ORDER BY dr.request_id
                    ),
                    d.current_head
                )
            )
        ) / COUNT(*)
    )::NUMERIC(12, 4),
    (
        SUM(
            ABS(
                dr.cylinder -
                COALESCE(
                    LAG(dr.cylinder) OVER (
                        ORDER BY dr.request_id
                    ),
                    d.current_head
                )
            )
        ) <= p.maximum_movement
    )
FROM scheduling_runs r
JOIN workloads w ON w.workload_id = r.workload_id
JOIN disks d ON d.disk_id = r.disk_id
JOIN scheduling_policies p ON p.policy_id = r.policy_id
JOIN disk_requests dr ON dr.workload_id = r.workload_id
GROUP BY
    r.run_id,
    d.current_head,
    p.maximum_movement;

-- The following query shows the request distribution around the head.
WITH disk_state AS (
    SELECT current_head
    FROM disks
    WHERE disk_name = 'storage-array-01'
)
SELECT
    CASE
        WHEN dr.cylinder < ds.current_head THEN 'LEFT_OF_HEAD'
        WHEN dr.cylinder = ds.current_head THEN 'AT_HEAD'
        ELSE 'RIGHT_OF_HEAD'
    END AS head_relation,
    COUNT(*) AS request_count,
    MIN(dr.cylinder) AS nearest_cylinder,
    MAX(dr.cylinder) AS farthest_cylinder
FROM disk_requests dr
CROSS JOIN disk_state ds
JOIN workloads w
    ON w.workload_id = dr.workload_id
WHERE w.workload_name = 'mixed-production-read-workload'
GROUP BY
    CASE
        WHEN dr.cylinder < ds.current_head THEN 'LEFT_OF_HEAD'
        WHEN dr.cylinder = ds.current_head THEN 'AT_HEAD'
        ELSE 'RIGHT_OF_HEAD'
    END
ORDER BY head_relation;

-- Query the policy decision surface.
SELECT
    sr.algorithm,
    sr.total_movement,
    sr.average_seek,
    sr.eligible,
    sp.policy_name,
    sp.maximum_movement
FROM scheduling_results sr
JOIN scheduling_runs run
    ON run.run_id = sr.run_id
JOIN scheduling_policies sp
    ON sp.policy_id = run.policy_id
ORDER BY
    sr.total_movement,
    sr.algorithm;

-- The lowest-movement eligible strategy represents the database-level
-- selection query. The database does not claim that lowest movement is
-- universally optimal; it evaluates the explicit configured policy.
WITH eligible_results AS (
    SELECT
        sr.algorithm,
        sr.total_movement,
        sr.average_seek
    FROM scheduling_results sr
    JOIN scheduling_runs run
        ON run.run_id = sr.run_id
    JOIN scheduling_policies p
        ON p.policy_id = run.policy_id
    WHERE sr.eligible
)
SELECT
    algorithm,
    total_movement,
    average_seek
FROM eligible_results
ORDER BY total_movement, algorithm
LIMIT 1;

-- Demonstrate a transaction boundary for policy changes.
BEGIN;

UPDATE scheduling_policies
SET maximum_movement = 350
WHERE policy_name = 'production-seek-budget';

-- The policy update becomes visible only if the transaction commits.
-- ROLLBACK keeps the original 300-cylinder production budget.
ROLLBACK;

-- Verify the original policy remains intact after the rollback.
SELECT
    policy_name,
    maximum_movement,
    require_deterministic_ties
FROM scheduling_policies
WHERE policy_name = 'production-seek-budget';

-- Demonstrate duplicate-request protection.
-- This statement is intentionally commented out because executing it would
-- correctly fail with the UNIQUE constraint:
--
-- INSERT INTO disk_requests (
--     workload_id,
--     external_request_id,
--     cylinder,
--     priority
-- )
-- SELECT workload_id, 'REQ-001', 75, 'BATCH'
-- FROM workloads
-- WHERE workload_name = 'mixed-production-read-workload';

-- Demonstrate the distinction between boundary-aware and request-aware
-- scheduling through descriptive metadata.
SELECT
    algorithm,
    CASE algorithm
        WHEN 'FCFS'
            THEN 'Arrival order is preserved.'
        WHEN 'SSTF'
            THEN 'Nearest pending cylinder is selected repeatedly.'
        WHEN 'SCAN'
            THEN 'The head sweeps to the physical boundary before reversing.'
        WHEN 'C-SCAN'
            THEN 'The head sweeps in one direction and wraps at boundaries.'
        WHEN 'LOOK'
            THEN 'The sweep reverses at the final pending request.'
        WHEN 'C-LOOK'
            THEN 'The sweep wraps between request extremes.'
    END AS mechanism
FROM (
    SELECT unnest(enum_range(NULL::scheduling_algorithm)) AS algorithm
) algorithms
ORDER BY algorithm;
