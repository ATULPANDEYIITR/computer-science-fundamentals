-- PostgreSQL-compatible deadlock laboratory.
--
-- The schema models resource-allocation deadlocks rather than relying on
-- PostgreSQL's own lock manager. It stores processes, resources, allocations,
-- waiting requests, wait-for relationships, detection results, and recovery
-- actions so that the mechanisms can be inspected as relational data.
--
-- PostgreSQL's native transaction locking is intentionally distinct from this
-- teaching model. The tables below represent a logical resource-governance
-- layer that an application could use to reason about deadlock risk.

DROP SCHEMA IF EXISTS deadlock_lab CASCADE;
CREATE SCHEMA deadlock_lab;

SET search_path TO deadlock_lab;

CREATE TABLE resources (
    resource_id BIGSERIAL PRIMARY KEY,
    resource_name TEXT NOT NULL UNIQUE,
    capacity INTEGER NOT NULL CHECK (capacity > 0)
);

CREATE TABLE processes (
    process_id BIGSERIAL PRIMARY KEY,
    process_name TEXT NOT NULL UNIQUE,
    state TEXT NOT NULL DEFAULT 'READY',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (
        state IN ('READY', 'RUNNING', 'WAITING', 'COMPLETED', 'ABORTED')
    )
);

CREATE TABLE maximum_claims (
    process_id BIGINT NOT NULL REFERENCES processes(process_id)
        ON DELETE CASCADE,
    resource_id BIGINT NOT NULL REFERENCES resources(resource_id)
        ON DELETE CASCADE,
    maximum_units INTEGER NOT NULL CHECK (maximum_units >= 0),
    PRIMARY KEY (process_id, resource_id)
);

CREATE TABLE allocations (
    process_id BIGINT NOT NULL REFERENCES processes(process_id)
        ON DELETE CASCADE,
    resource_id BIGINT NOT NULL REFERENCES resources(resource_id)
        ON DELETE CASCADE,
    allocated_units INTEGER NOT NULL CHECK (allocated_units >= 0),
    PRIMARY KEY (process_id, resource_id)
);

CREATE TABLE resource_requests (
    request_id BIGSERIAL PRIMARY KEY,
    process_id BIGINT NOT NULL REFERENCES processes(process_id)
        ON DELETE CASCADE,
    resource_id BIGINT NOT NULL REFERENCES resources(resource_id)
        ON DELETE CASCADE,
    requested_units INTEGER NOT NULL CHECK (requested_units > 0),
    status TEXT NOT NULL DEFAULT 'WAITING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (status IN ('WAITING', 'GRANTED', 'CANCELLED'))
);

CREATE TABLE wait_for_edges (
    waiting_process_id BIGINT NOT NULL REFERENCES processes(process_id)
        ON DELETE CASCADE,
    holding_process_id BIGINT NOT NULL REFERENCES processes(process_id)
        ON DELETE CASCADE,
    resource_id BIGINT NOT NULL REFERENCES resources(resource_id)
        ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (
        waiting_process_id,
        holding_process_id,
        resource_id
    ),
    CHECK (waiting_process_id <> holding_process_id)
);

CREATE TABLE deadlock_events (
    deadlock_event_id BIGSERIAL PRIMARY KEY,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    detection_method TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'OPEN',
    CHECK (status IN ('OPEN', 'RECOVERED', 'IGNORED'))
);

CREATE TABLE recovery_actions (
    recovery_action_id BIGSERIAL PRIMARY KEY,
    deadlock_event_id BIGINT NOT NULL
        REFERENCES deadlock_events(deadlock_event_id)
        ON DELETE CASCADE,
    victim_process_id BIGINT NOT NULL
        REFERENCES processes(process_id),
    action TEXT NOT NULL,
    resources_released BOOLEAN NOT NULL DEFAULT FALSE,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes support the two common access paths in the logical deadlock model:
-- finding requests by process and finding holders/waiters by resource.
CREATE INDEX idx_requests_process
    ON resource_requests(process_id, status);

CREATE INDEX idx_requests_resource
    ON resource_requests(resource_id, status);

CREATE INDEX idx_allocations_resource
    ON allocations(resource_id);

CREATE INDEX idx_wait_for_waiting
    ON wait_for_edges(waiting_process_id);

CREATE INDEX idx_wait_for_holding
    ON wait_for_edges(holding_process_id);

INSERT INTO resources (resource_name, capacity)
VALUES
    ('DatabaseConnection', 1),
    ('AuditLock', 1),
    ('WorkerSlot', 2);

INSERT INTO processes (process_name, state)
VALUES
    ('BillingTransaction', 'RUNNING'),
    ('AuditTransaction', 'RUNNING'),
    ('ReportingWorker', 'RUNNING');

INSERT INTO maximum_claims (process_id, resource_id, maximum_units)
SELECT p.process_id, r.resource_id, v.maximum_units
FROM (
    VALUES
        ('BillingTransaction', 'DatabaseConnection', 1),
        ('BillingTransaction', 'AuditLock', 1),
        ('AuditTransaction', 'DatabaseConnection', 1),
        ('AuditTransaction', 'AuditLock', 1),
        ('ReportingWorker', 'WorkerSlot', 2)
) AS v(process_name, resource_name, maximum_units)
JOIN processes p ON p.process_name = v.process_name
JOIN resources r ON r.resource_name = v.resource_name;

INSERT INTO allocations (process_id, resource_id, allocated_units)
SELECT p.process_id, r.resource_id, v.allocated_units
FROM (
    VALUES
        ('BillingTransaction', 'DatabaseConnection', 1),
        ('BillingTransaction', 'AuditLock', 0),
        ('AuditTransaction', 'DatabaseConnection', 0),
        ('AuditTransaction', 'AuditLock', 1),
        ('ReportingWorker', 'WorkerSlot', 1)
) AS v(process_name, resource_name, allocated_units)
JOIN processes p ON p.process_name = v.process_name
JOIN resources r ON r.resource_name = v.resource_name;

INSERT INTO resource_requests (
    process_id,
    resource_id,
    requested_units,
    status
)
SELECT p.process_id, r.resource_id, v.requested_units, 'WAITING'
FROM (
    VALUES
        ('BillingTransaction', 'AuditLock', 1),
        ('AuditTransaction', 'DatabaseConnection', 1)
) AS v(process_name, resource_name, requested_units)
JOIN processes p ON p.process_name = v.process_name
JOIN resources r ON r.resource_name = v.resource_name;

-- The two wait-for edges describe:
-- BillingTransaction -> AuditTransaction because AuditTransaction owns AuditLock.
-- AuditTransaction -> BillingTransaction because BillingTransaction owns
-- DatabaseConnection.
INSERT INTO wait_for_edges (
    waiting_process_id,
    holding_process_id,
    resource_id
)
SELECT waiting.process_id,
       holding.process_id,
       resource.resource_id
FROM (
    VALUES
        ('BillingTransaction', 'AuditTransaction', 'AuditLock'),
        ('AuditTransaction', 'BillingTransaction', 'DatabaseConnection')
) AS edge(waiting_name, holding_name, resource_name)
JOIN processes waiting
    ON waiting.process_name = edge.waiting_name
JOIN processes holding
    ON holding.process_name = edge.holding_name
JOIN resources resource
    ON resource.resource_name = edge.resource_name;

-- Available resources are capacity minus active allocations.
CREATE VIEW available_resources AS
SELECT
    r.resource_id,
    r.resource_name,
    r.capacity,
    r.capacity - COALESCE(SUM(
        CASE
            WHEN p.state <> 'ABORTED' THEN a.allocated_units
            ELSE 0
        END
    ), 0) AS available_units
FROM resources r
LEFT JOIN allocations a
    ON a.resource_id = r.resource_id
LEFT JOIN processes p
    ON p.process_id = a.process_id
GROUP BY
    r.resource_id,
    r.resource_name,
    r.capacity;

-- Remaining need is maximum claim minus current allocation.
CREATE VIEW remaining_need AS
SELECT
    p.process_id,
    p.process_name,
    r.resource_id,
    r.resource_name,
    mc.maximum_units,
    COALESCE(a.allocated_units, 0) AS allocated_units,
    mc.maximum_units - COALESCE(a.allocated_units, 0) AS remaining_units
FROM maximum_claims mc
JOIN processes p
    ON p.process_id = mc.process_id
JOIN resources r
    ON r.resource_id = mc.resource_id
LEFT JOIN allocations a
    ON a.process_id = mc.process_id
   AND a.resource_id = mc.resource_id;

-- This query identifies processes that are waiting for a resource currently
-- unavailable to them.
SELECT
    p.process_name AS waiting_process,
    r.resource_name,
    rr.requested_units,
    ar.available_units
FROM resource_requests rr
JOIN processes p
    ON p.process_id = rr.process_id
JOIN resources r
    ON r.resource_id = rr.resource_id
JOIN available_resources ar
    ON ar.resource_id = rr.resource_id
WHERE rr.status = 'WAITING'
  AND rr.requested_units > ar.available_units
ORDER BY p.process_name;

-- A direct relational representation of the wait-for graph.
SELECT
    waiting.process_name AS waiting_process,
    holding.process_name AS holding_process,
    resource.resource_name
FROM wait_for_edges edge
JOIN processes waiting
    ON waiting.process_id = edge.waiting_process_id
JOIN processes holding
    ON holding.process_id = edge.holding_process_id
JOIN resources resource
    ON resource.resource_id = edge.resource_id
ORDER BY waiting.process_name, holding.process_name;

-- Recursive traversal searches for cycles in the wait-for graph.
-- PostgreSQL arrays preserve the path, allowing the query to reject a path
-- when a process is encountered again.
WITH RECURSIVE wait_graph AS (
    SELECT
        waiting_process_id AS start_process,
        waiting_process_id AS current_process,
        holding_process_id AS next_process,
        ARRAY[
            waiting_process_id,
            holding_process_id
        ]::BIGINT[] AS path
    FROM wait_for_edges

    UNION ALL

    SELECT
        wg.start_process,
        wg.next_process AS current_process,
        edge.holding_process_id AS next_process,
        wg.path || edge.holding_process_id
    FROM wait_graph wg
    JOIN wait_for_edges edge
        ON edge.waiting_process_id = wg.next_process
    WHERE NOT edge.holding_process_id = ANY(wg.path)
)
SELECT DISTINCT
    p_start.process_name AS cycle_start,
    p_next.process_name AS cycle_reaches
FROM wait_graph wg
JOIN processes p_start
    ON p_start.process_id = wg.start_process
JOIN processes p_next
    ON p_next.process_id = wg.next_process
WHERE EXISTS (
    SELECT 1
    FROM wait_for_edges edge
    WHERE edge.waiting_process_id = wg.next_process
      AND edge.holding_process_id = wg.start_process
);

-- Record a detection event only after the application or detection service
-- confirms that the wait-for graph contains a cycle.
INSERT INTO deadlock_events (
    detection_method,
    status
)
VALUES (
    'WAIT_FOR_GRAPH_CYCLE',
    'OPEN'
);

-- The following transaction demonstrates recovery at the logical model layer.
-- It selects a victim, releases its allocations, marks the process aborted,
-- and records the recovery decision atomically.
BEGIN;

WITH victim AS (
    SELECT process_id
    FROM processes
    WHERE process_name = 'BillingTransaction'
      AND state = 'RUNNING'
    FOR UPDATE
)
UPDATE allocations a
SET allocated_units = 0
FROM victim v
WHERE a.process_id = v.process_id;

WITH victim AS (
    SELECT process_id
    FROM processes
    WHERE process_name = 'BillingTransaction'
      AND state = 'RUNNING'
    FOR UPDATE
)
UPDATE processes p
SET state = 'ABORTED'
FROM victim v
WHERE p.process_id = v.process_id;

WITH latest_event AS (
    SELECT deadlock_event_id
    FROM deadlock_events
    WHERE status = 'OPEN'
    ORDER BY deadlock_event_id DESC
    LIMIT 1
),
victim AS (
    SELECT process_id
    FROM processes
    WHERE process_name = 'BillingTransaction'
)
INSERT INTO recovery_actions (
    deadlock_event_id,
    victim_process_id,
    action,
    resources_released
)
SELECT
    latest_event.deadlock_event_id,
    victim.process_id,
    'ABORT_PROCESS',
    TRUE
FROM latest_event
CROSS JOIN victim;

UPDATE deadlock_events
SET status = 'RECOVERED'
WHERE deadlock_event_id = (
    SELECT deadlock_event_id
    FROM deadlock_events
    WHERE status = 'OPEN'
    ORDER BY deadlock_event_id DESC
    LIMIT 1
);

DELETE FROM wait_for_edges
WHERE waiting_process_id = (
    SELECT process_id
    FROM processes
    WHERE process_name = 'BillingTransaction'
)
OR holding_process_id = (
    SELECT process_id
    FROM processes
    WHERE process_name = 'BillingTransaction'
);

COMMIT;

-- Post-recovery availability demonstrates that releasing the victim's
-- allocation restores a resource for other work.
SELECT *
FROM available_resources
ORDER BY resource_name;

-- The remaining waiting request is now exposed as potentially grantable.
SELECT
    p.process_name,
    r.resource_name,
    rr.requested_units,
    ar.available_units,
    CASE
        WHEN rr.requested_units <= ar.available_units
        THEN 'GRANTABLE'
        ELSE 'STILL_WAITING'
    END AS request_status
FROM resource_requests rr
JOIN processes p
    ON p.process_id = rr.process_id
JOIN resources r
    ON r.resource_id = rr.resource_id
JOIN available_resources ar
    ON ar.resource_id = rr.resource_id
WHERE rr.status = 'WAITING'
ORDER BY p.process_name;

-- A database constraint prevents negative allocations directly.
-- This intentionally invalid statement is commented out so the complete
-- script remains executable:
--
-- INSERT INTO allocations (process_id, resource_id, allocated_units)
-- VALUES (1, 1, -1);
--
-- The CHECK constraint would reject it.

-- A practical policy query identifies processes that have both outstanding
-- claims and allocations, which are the candidates relevant to safety
-- analysis and hold-and-wait investigation.
SELECT
    p.process_name,
    SUM(rn.allocated_units) AS units_held,
    SUM(rn.remaining_units) AS units_still_needed
FROM remaining_need rn
JOIN processes p
    ON p.process_id = rn.process_id
WHERE p.state IN ('READY', 'RUNNING', 'WAITING')
GROUP BY p.process_id, p.process_name
HAVING SUM(rn.allocated_units) > 0
   AND SUM(rn.remaining_units) > 0
ORDER BY p.process_name;
