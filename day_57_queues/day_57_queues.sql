DROP SCHEMA IF EXISTS queue_lab CASCADE;
CREATE SCHEMA queue_lab;

SET search_path TO queue_lab, public;

-- A queue is modeled as ordered work. Circular queues add bounded capacity,
-- deques add two-sided operations, and priority queues change service order.

CREATE TYPE queue_kind AS ENUM (
    'FIFO',
    'CIRCULAR',
    'DEQUE',
    'PRIORITY'
);

CREATE TYPE item_state AS ENUM (
    'WAITING',
    'READY',
    'RUNNING',
    'COMPLETED',
    'FAILED',
    'CANCELLED'
);

CREATE TYPE priority_level AS ENUM (
    'CRITICAL',
    'HIGH',
    'NORMAL',
    'LOW'
);

CREATE TABLE queue (
    queue_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    queue_name TEXT NOT NULL UNIQUE,
    queue_kind queue_kind NOT NULL,
    capacity INTEGER,
    priority_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT queue_capacity_valid
        CHECK (
            (queue_kind = 'CIRCULAR' AND capacity IS NOT NULL AND capacity > 0)
            OR
            (queue_kind <> 'CIRCULAR' AND capacity IS NULL)
        ),
    CONSTRAINT priority_kind_valid
        CHECK (
            priority_enabled = FALSE
            OR queue_kind = 'PRIORITY'
        )
);

CREATE TABLE queue_item (
    item_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    queue_id BIGINT NOT NULL REFERENCES queue(queue_id) ON DELETE CASCADE,
    external_key TEXT NOT NULL,
    payload TEXT NOT NULL,
    priority priority_level NOT NULL DEFAULT 'NORMAL',
    sequence_no BIGINT NOT NULL,
    state item_state NOT NULL DEFAULT 'WAITING',
    enqueued_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    CONSTRAINT queue_item_unique_key
        UNIQUE (queue_id, external_key),
    CONSTRAINT queue_item_sequence_unique
        UNIQUE (queue_id, sequence_no),
    CONSTRAINT queue_item_time_order
        CHECK (
            completed_at IS NULL
            OR started_at IS NULL
            OR completed_at >= started_at
        )
);

CREATE TABLE queue_event (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    queue_id BIGINT NOT NULL REFERENCES queue(queue_id) ON DELETE CASCADE,
    item_id BIGINT REFERENCES queue_item(item_id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    event_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT event_type_valid
        CHECK (
            event_type IN (
                'ENQUEUED',
                'DEQUEUED',
                'FRONT_INSERT',
                'BACK_INSERT',
                'PEEK',
                'STARTED',
                'COMPLETED',
                'FAILED',
                'CANCELLED'
            )
        )
);

CREATE INDEX queue_item_fifo_idx
    ON queue_item(queue_id, sequence_no)
    WHERE state IN ('WAITING', 'READY');

CREATE INDEX queue_item_priority_idx
    ON queue_item(queue_id, priority, sequence_no)
    WHERE state IN ('WAITING', 'READY');

CREATE INDEX queue_event_queue_time_idx
    ON queue_event(queue_id, created_at DESC);

-- Only one active item with the same external key may exist in a queue.
CREATE UNIQUE INDEX queue_item_active_key_idx
    ON queue_item(queue_id, external_key)
    WHERE state IN ('WAITING', 'READY', 'RUNNING');

CREATE OR REPLACE FUNCTION validate_queue_item()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    q_kind queue_kind;
    q_capacity INTEGER;
    current_count INTEGER;
BEGIN
    SELECT queue_kind, capacity
    INTO q_kind, q_capacity
    FROM queue
    WHERE queue_id = NEW.queue_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'queue % does not exist', NEW.queue_id;
    END IF;

    IF NEW.sequence_no <= 0 THEN
        RAISE EXCEPTION 'sequence_no must be positive';
    END IF;

    IF q_kind = 'CIRCULAR'
       AND NEW.state IN ('WAITING', 'READY', 'RUNNING')
    THEN
        SELECT COUNT(*)
        INTO current_count
        FROM queue_item
        WHERE queue_id = NEW.queue_id
          AND state IN ('WAITING', 'READY', 'RUNNING')
          AND item_id <> COALESCE(NEW.item_id, -1);

        IF current_count >= q_capacity THEN
            RAISE EXCEPTION
                'circular queue % is full: capacity %',
                NEW.queue_id,
                q_capacity;
        END IF;
    END IF;

    IF q_kind <> 'PRIORITY' AND NEW.priority <> 'NORMAL' THEN
        RAISE EXCEPTION
            'non-priority queue % cannot assign priority %',
            NEW.queue_id,
            NEW.priority;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER queue_item_validation_trigger
BEFORE INSERT OR UPDATE OF queue_id, priority, state
ON queue_item
FOR EACH ROW
EXECUTE FUNCTION validate_queue_item();

CREATE OR REPLACE FUNCTION record_queue_event()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    event_name TEXT;
BEGIN
    IF TG_OP = 'INSERT' THEN
        event_name := CASE
            WHEN NEW.state = 'WAITING' THEN 'ENQUEUED'
            ELSE 'STARTED'
        END;

        INSERT INTO queue_event(queue_id, item_id, event_type, event_data)
        VALUES (
            NEW.queue_id,
            NEW.item_id,
            event_name,
            jsonb_build_object(
                'external_key', NEW.external_key,
                'priority', NEW.priority,
                'sequence_no', NEW.sequence_no
            )
        );

        RETURN NEW;
    END IF;

    IF TG_OP = 'UPDATE' AND NEW.state IS DISTINCT FROM OLD.state THEN
        event_name := CASE NEW.state
            WHEN 'RUNNING' THEN 'STARTED'
            WHEN 'COMPLETED' THEN 'COMPLETED'
            WHEN 'FAILED' THEN 'FAILED'
            WHEN 'CANCELLED' THEN 'CANCELLED'
            ELSE 'DEQUEUED'
        END;

        INSERT INTO queue_event(queue_id, item_id, event_type, event_data)
        VALUES (
            NEW.queue_id,
            NEW.item_id,
            event_name,
            jsonb_build_object(
                'from_state', OLD.state,
                'to_state', NEW.state
            )
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER queue_event_trigger
AFTER INSERT OR UPDATE OF state
ON queue_item
FOR EACH ROW
EXECUTE FUNCTION record_queue_event();

CREATE OR REPLACE FUNCTION set_item_timestamps()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.state = 'RUNNING' AND OLD.state IS DISTINCT FROM 'RUNNING' THEN
        NEW.started_at := COALESCE(NEW.started_at, CURRENT_TIMESTAMP);
    END IF;

    IF NEW.state IN ('COMPLETED', 'FAILED', 'CANCELLED')
       AND OLD.state IS DISTINCT FROM NEW.state
    THEN
        NEW.completed_at := COALESCE(NEW.completed_at, CURRENT_TIMESTAMP);
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER queue_item_timestamp_trigger
BEFORE UPDATE OF state
ON queue_item
FOR EACH ROW
EXECUTE FUNCTION set_item_timestamps();

CREATE OR REPLACE FUNCTION dequeue_fifo(
    target_queue BIGINT
)
RETURNS TABLE (
    item_id BIGINT,
    external_key TEXT,
    payload TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH candidate AS (
        SELECT qi.item_id
        FROM queue_item qi
        JOIN queue q ON q.queue_id = qi.queue_id
        WHERE qi.queue_id = target_queue
          AND qi.state IN ('WAITING', 'READY')
          AND q.queue_kind IN ('FIFO', 'CIRCULAR')
        ORDER BY qi.sequence_no
        LIMIT 1
        FOR UPDATE OF qi SKIP LOCKED
    ),
    changed AS (
        UPDATE queue_item qi
        SET state = 'RUNNING'
        FROM candidate c
        WHERE qi.item_id = c.item_id
        RETURNING qi.item_id, qi.external_key, qi.payload
    )
    SELECT * FROM changed;
END;
$$;

CREATE OR REPLACE FUNCTION dequeue_priority(
    target_queue BIGINT
)
RETURNS TABLE (
    item_id BIGINT,
    external_key TEXT,
    payload TEXT,
    priority priority_level
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH candidate AS (
        SELECT qi.item_id
        FROM queue_item qi
        JOIN queue q ON q.queue_id = qi.queue_id
        WHERE qi.queue_id = target_queue
          AND qi.state IN ('WAITING', 'READY')
          AND q.queue_kind = 'PRIORITY'
        ORDER BY
            CASE qi.priority
                WHEN 'CRITICAL' THEN 1
                WHEN 'HIGH' THEN 2
                WHEN 'NORMAL' THEN 3
                WHEN 'LOW' THEN 4
            END,
            qi.sequence_no
        LIMIT 1
        FOR UPDATE OF qi SKIP LOCKED
    ),
    changed AS (
        UPDATE queue_item qi
        SET state = 'RUNNING'
        FROM candidate c
        WHERE qi.item_id = c.item_id
        RETURNING qi.item_id, qi.external_key, qi.payload, qi.priority
    )
    SELECT * FROM changed;
END;
$$;

CREATE OR REPLACE VIEW queue_status AS
SELECT
    q.queue_id,
    q.queue_name,
    q.queue_kind,
    q.capacity,
    q.priority_enabled,
    COUNT(qi.item_id) FILTER (
        WHERE qi.state IN ('WAITING', 'READY')
    ) AS pending_items,
    COUNT(qi.item_id) FILTER (
        WHERE qi.state = 'RUNNING'
    ) AS running_items,
    COUNT(qi.item_id) FILTER (
        WHERE qi.state = 'COMPLETED'
    ) AS completed_items,
    COUNT(qi.item_id) FILTER (
        WHERE qi.state = 'FAILED'
    ) AS failed_items
FROM queue q
LEFT JOIN queue_item qi ON qi.queue_id = q.queue_id
GROUP BY
    q.queue_id,
    q.queue_name,
    q.queue_kind,
    q.capacity,
    q.priority_enabled;

CREATE OR REPLACE VIEW next_dispatch AS
WITH ranked AS (
    SELECT
        qi.*,
        q.queue_kind,
        ROW_NUMBER() OVER (
            PARTITION BY qi.queue_id
            ORDER BY
                CASE
                    WHEN q.queue_kind = 'PRIORITY'
                    THEN CASE qi.priority
                        WHEN 'CRITICAL' THEN 1
                        WHEN 'HIGH' THEN 2
                        WHEN 'NORMAL' THEN 3
                        WHEN 'LOW' THEN 4
                    END
                    ELSE 0
                END,
                qi.sequence_no
        ) AS dispatch_rank
    FROM queue_item qi
    JOIN queue q ON q.queue_id = qi.queue_id
    WHERE qi.state IN ('WAITING', 'READY')
)
SELECT
    queue_id,
    queue_kind,
    item_id,
    external_key,
    payload,
    priority,
    sequence_no
FROM ranked
WHERE dispatch_rank = 1;

-- Queue definitions.
INSERT INTO queue(queue_name, queue_kind, capacity, priority_enabled)
VALUES
    ('commit-fifo', 'FIFO', NULL, FALSE),
    ('network-ring', 'CIRCULAR', 3, FALSE),
    ('review-deque', 'DEQUE', NULL, FALSE),
    ('incident-priority', 'PRIORITY', NULL, TRUE);

-- FIFO records.
INSERT INTO queue_item(
    queue_id, external_key, payload, priority, sequence_no, state
)
SELECT
    queue_id,
    'commit-001',
    'compile source tree',
    'NORMAL',
    1,
    'WAITING'
FROM queue
WHERE queue_name = 'commit-fifo';

INSERT INTO queue_item(
    queue_id, external_key, payload, priority, sequence_no, state
)
SELECT
    queue_id,
    'commit-002',
    'run unit tests',
    'NORMAL',
    2,
    'WAITING'
FROM queue
WHERE queue_name = 'commit-fifo';

-- Circular queue deliberately reaches its configured capacity.
INSERT INTO queue_item(
    queue_id, external_key, payload, priority, sequence_no, state
)
SELECT
    queue_id,
    item_key,
    payload,
    'NORMAL',
    sequence_no,
    'READY'
FROM (
    VALUES
        ('ring-001', 'network packet A', 1),
        ('ring-002', 'network packet B', 2),
        ('ring-003', 'network packet C', 3)
) AS v(item_key, payload, sequence_no)
CROSS JOIN (
    SELECT queue_id
    FROM queue
    WHERE queue_name = 'network-ring'
) q;

-- Deque items use the same relational storage but the application decides
-- whether insertion/removal occurs at the front or back.
INSERT INTO queue_item(
    queue_id, external_key, payload, priority, sequence_no, state
)
SELECT
    queue_id,
    'review-front',
    'security review',
    'NORMAL',
    1,
    'READY'
FROM queue
WHERE queue_name = 'review-deque';

INSERT INTO queue_item(
    queue_id, external_key, payload, priority, sequence_no, state
)
SELECT
    queue_id,
    'review-back',
    'documentation review',
    'NORMAL',
    2,
    'READY'
FROM queue
WHERE queue_name = 'review-deque';

-- Priority queue records demonstrate service ordering independent of arrival.
INSERT INTO queue_item(
    queue_id, external_key, payload, priority, sequence_no, state
)
SELECT
    q.queue_id,
    v.external_key,
    v.payload,
    v.priority,
    v.sequence_no,
    'READY'
FROM (
    VALUES
        ('incident-normal', 'normal incident', 'NORMAL'::priority_level, 1),
        ('incident-critical', 'production outage', 'CRITICAL'::priority_level, 2),
        ('incident-high', 'security alert', 'HIGH'::priority_level, 3),
        ('incident-low', 'maintenance task', 'LOW'::priority_level, 4)
) AS v(external_key, payload, priority, sequence_no)
CROSS JOIN (
    SELECT queue_id
    FROM queue
    WHERE queue_name = 'incident-priority'
) q;

-- Retrieval and queue state reporting.
SELECT *
FROM queue_status
ORDER BY queue_id;

SELECT *
FROM next_dispatch
ORDER BY queue_id;

-- FIFO dispatch is based on sequence number.
SELECT *
FROM dequeue_fifo(
    (SELECT queue_id FROM queue WHERE queue_name = 'commit-fifo')
);

-- Priority dispatch selects CRITICAL before HIGH, NORMAL, and LOW.
SELECT *
FROM dequeue_priority(
    (SELECT queue_id FROM queue WHERE queue_name = 'incident-priority')
);

-- Mark a completed item. The trigger records completion time and event.
UPDATE queue_item
SET state = 'COMPLETED'
WHERE external_key = 'commit-001';

-- Mark a failed item. Failure is distinct from normal completion.
UPDATE queue_item
SET state = 'FAILED'
WHERE external_key = 'incident-critical';

-- Aggregation by queue and priority.
SELECT
    q.queue_name,
    qi.priority,
    COUNT(*) AS item_count
FROM queue q
JOIN queue_item qi ON qi.queue_id = q.queue_id
GROUP BY q.queue_name, qi.priority
ORDER BY q.queue_name, qi.priority;

-- Event audit trail.
SELECT
    q.queue_name,
    qe.event_type,
    qe.event_data,
    qe.created_at
FROM queue_event qe
JOIN queue q ON q.queue_id = qe.queue_id
ORDER BY qe.created_at, qe.event_id;

-- Transactional example: reserve one priority item and complete it atomically.
BEGIN;

WITH candidate AS (
    SELECT qi.item_id
    FROM queue_item qi
    JOIN queue q ON q.queue_id = qi.queue_id
    WHERE q.queue_name = 'incident-priority'
      AND qi.state IN ('WAITING', 'READY')
    ORDER BY
        CASE qi.priority
            WHEN 'CRITICAL' THEN 1
            WHEN 'HIGH' THEN 2
            WHEN 'NORMAL' THEN 3
            WHEN 'LOW' THEN 4
        END,
        qi.sequence_no
    LIMIT 1
    FOR UPDATE SKIP LOCKED
)
UPDATE queue_item qi
SET state = 'RUNNING'
FROM candidate c
WHERE qi.item_id = c.item_id;

WITH running_item AS (
    SELECT item_id
    FROM queue_item
    WHERE queue_id = (
        SELECT queue_id
        FROM queue
        WHERE queue_name = 'incident-priority'
    )
      AND state = 'RUNNING'
    ORDER BY started_at DESC NULLS LAST, item_id DESC
    LIMIT 1
)
UPDATE queue_item qi
SET state = 'COMPLETED'
FROM running_item ri
WHERE qi.item_id = ri.item_id;

COMMIT;

-- Failure validation: duplicate active external keys are rejected by the
-- partial unique index. The following query exposes the existing rule.
SELECT
    queue_name,
    COUNT(*) AS active_items
FROM queue_status
GROUP BY queue_name
ORDER BY queue_name;

-- CTE report showing average processing duration for completed work.
WITH durations AS (
    SELECT
        q.queue_name,
        qi.item_id,
        qi.completed_at - qi.started_at AS duration
    FROM queue_item qi
    JOIN queue q ON q.queue_id = qi.queue_id
    WHERE qi.state = 'COMPLETED'
      AND qi.started_at IS NOT NULL
      AND qi.completed_at IS NOT NULL
)
SELECT
    queue_name,
    COUNT(*) AS completed_count,
    AVG(duration) AS average_duration
FROM durations
GROUP BY queue_name
ORDER BY queue_name;
