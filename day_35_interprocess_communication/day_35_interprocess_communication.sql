-- PostgreSQL 15+ compatible IPC learning schema
--
-- The database represents an operating-system-adjacent IPC service that
-- receives work through pipes or queues, maintains shared-memory-style
-- processing state in the service layer, and exposes socket endpoints.
--
-- SQL does not implement operating-system pipes or shared memory itself.
-- Instead, this database models the durable control plane around an IPC
-- service: endpoints, messages, consumers, deliveries, retries, failures,
-- and socket connections.

DROP SCHEMA IF EXISTS ipc_lab CASCADE;
CREATE SCHEMA ipc_lab;

SET search_path = ipc_lab, public;

CREATE TYPE transport_kind AS ENUM (
    'PIPE',
    'MESSAGE_QUEUE',
    'SHARED_MEMORY',
    'SOCKET'
);

CREATE TYPE endpoint_scope AS ENUM (
    'LOCAL_PROCESS',
    'LOCAL_HOST',
    'NETWORK'
);

CREATE TYPE message_state AS ENUM (
    'QUEUED',
    'DELIVERED',
    'PROCESSING',
    'COMPLETED',
    'FAILED',
    'DEAD_LETTERED'
);

CREATE TYPE socket_protocol AS ENUM (
    'UNIX_STREAM',
    'TCP_STREAM',
    'UDP_DATAGRAM'
);

CREATE TABLE ipc_service (
    service_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service_name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE ipc_endpoint (
    endpoint_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service_id BIGINT NOT NULL REFERENCES ipc_service(service_id)
        ON DELETE CASCADE,
    endpoint_name TEXT NOT NULL,
    transport transport_kind NOT NULL,
    scope endpoint_scope NOT NULL,
    capacity_messages INTEGER,
    endpoint_path TEXT,
    active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT endpoint_capacity_valid
        CHECK (
            capacity_messages IS NULL
            OR capacity_messages > 0
        ),

    CONSTRAINT endpoint_path_required_for_local
        CHECK (
            scope <> 'LOCAL_HOST'
            OR endpoint_path IS NOT NULL
        ),

    CONSTRAINT endpoint_name_unique
        UNIQUE (service_id, endpoint_name)
);

CREATE TABLE socket_endpoint (
    endpoint_id BIGINT PRIMARY KEY
        REFERENCES ipc_endpoint(endpoint_id)
        ON DELETE CASCADE,

    protocol socket_protocol NOT NULL,
    host TEXT,
    port INTEGER,

    CONSTRAINT socket_port_valid
        CHECK (
            port IS NULL
            OR port BETWEEN 1 AND 65535
        ),

    CONSTRAINT unix_socket_has_path
        CHECK (
            protocol <> 'UNIX_STREAM'
            OR host IS NULL
        ),

    CONSTRAINT network_socket_has_host
        CHECK (
            protocol = 'UNIX_STREAM'
            OR host IS NOT NULL
        )
);

CREATE TABLE ipc_process (
    process_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service_id BIGINT NOT NULL REFERENCES ipc_service(service_id)
        ON DELETE CASCADE,
    process_name TEXT NOT NULL,
    operating_system_pid INTEGER,
    started_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    stopped_at TIMESTAMPTZ,

    CONSTRAINT pid_positive
        CHECK (
            operating_system_pid IS NULL
            OR operating_system_pid > 0
        ),

    CONSTRAINT process_times_valid
        CHECK (
            stopped_at IS NULL
            OR stopped_at >= started_at
        ),

    CONSTRAINT process_name_unique
        UNIQUE (service_id, process_name)
);

CREATE TABLE ipc_message (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    endpoint_id BIGINT NOT NULL REFERENCES ipc_endpoint(endpoint_id),
    producer_process_id BIGINT REFERENCES ipc_process(process_id),
    correlation_id UUID NOT NULL DEFAULT gen_random_uuid(),
    message_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    state message_state NOT NULL DEFAULT 'QUEUED',
    priority SMALLINT NOT NULL DEFAULT 0,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    available_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    completed_at TIMESTAMPTZ,

    CONSTRAINT message_type_not_blank
        CHECK (length(trim(message_type)) > 0),

    CONSTRAINT message_priority_valid
        CHECK (priority BETWEEN -100 AND 100),

    CONSTRAINT message_attempts_valid
        CHECK (attempt_count >= 0),

    CONSTRAINT completion_time_consistent
        CHECK (
            (state IN ('COMPLETED', 'FAILED', 'DEAD_LETTERED')
             AND completed_at IS NOT NULL)
            OR
            (state NOT IN ('COMPLETED', 'FAILED', 'DEAD_LETTERED')
             AND completed_at IS NULL)
        )
);

CREATE TABLE message_consumer (
    consumer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    endpoint_id BIGINT NOT NULL REFERENCES ipc_endpoint(endpoint_id)
        ON DELETE CASCADE,
    process_id BIGINT REFERENCES ipc_process(process_id),
    consumer_name TEXT NOT NULL,
    max_attempts INTEGER NOT NULL DEFAULT 5,
    active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT consumer_max_attempts_valid
        CHECK (max_attempts BETWEEN 1 AND 100),

    CONSTRAINT consumer_name_unique
        UNIQUE (endpoint_id, consumer_name)
);

CREATE TABLE message_delivery (
    delivery_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    message_id UUID NOT NULL REFERENCES ipc_message(message_id)
        ON DELETE CASCADE,
    consumer_id BIGINT NOT NULL REFERENCES message_consumer(consumer_id),
    delivered_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    processing_started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    success BOOLEAN,
    failure_reason TEXT,

    CONSTRAINT delivery_result_consistent
        CHECK (
            success IS NULL
            OR finished_at IS NOT NULL
        ),

    CONSTRAINT delivery_failure_reason_consistent
        CHECK (
            success IS NOT FALSE
            OR length(trim(coalesce(failure_reason, ''))) > 0
        )
);

CREATE TABLE shared_memory_segment (
    segment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service_id BIGINT NOT NULL REFERENCES ipc_service(service_id)
        ON DELETE CASCADE,
    segment_name TEXT NOT NULL,
    size_bytes BIGINT NOT NULL,
    permissions TEXT NOT NULL,
    synchronization_strategy TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT shared_memory_size_valid
        CHECK (size_bytes > 0),

    CONSTRAINT shared_memory_permissions_valid
        CHECK (permissions IN ('OWNER_ONLY', 'OWNER_GROUP', 'CUSTOM')),

    CONSTRAINT segment_name_unique
        UNIQUE (service_id, segment_name)
);

CREATE TABLE shared_memory_attachment (
    segment_id BIGINT NOT NULL REFERENCES shared_memory_segment(segment_id)
        ON DELETE CASCADE,
    process_id BIGINT NOT NULL REFERENCES ipc_process(process_id)
        ON DELETE CASCADE,
    attached_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    detached_at TIMESTAMPTZ,

    PRIMARY KEY (segment_id, process_id),

    CONSTRAINT attachment_times_valid
        CHECK (
            detached_at IS NULL
            OR detached_at >= attached_at
        )
);

CREATE TABLE ipc_failure (
    failure_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    message_id UUID REFERENCES ipc_message(message_id)
        ON DELETE SET NULL,
    process_id BIGINT REFERENCES ipc_process(process_id)
        ON DELETE SET NULL,
    transport transport_kind NOT NULL,
    failure_code TEXT NOT NULL,
    failure_detail TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    retryable BOOLEAN NOT NULL,

    CONSTRAINT failure_code_not_blank
        CHECK (length(trim(failure_code)) > 0)
);

CREATE INDEX idx_messages_ready
    ON ipc_message (endpoint_id, priority DESC, available_at, created_at)
    WHERE state = 'QUEUED';

CREATE INDEX idx_messages_correlation
    ON ipc_message (correlation_id);

CREATE INDEX idx_deliveries_message
    ON message_delivery (message_id, delivered_at DESC);

CREATE INDEX idx_failures_transport_time
    ON ipc_failure (transport, occurred_at DESC);

CREATE INDEX idx_process_service_active
    ON ipc_process (service_id, active)
    WHERE stopped_at IS NULL;

INSERT INTO ipc_service (service_name, description)
VALUES
    (
        'telemetry-ingestion',
        'Processes sensor messages using multiple local IPC transports'
    ),
    (
        'document-worker',
        'Consumes document-processing jobs from a bounded message queue'
    );

INSERT INTO ipc_endpoint (
    service_id,
    endpoint_name,
    transport,
    scope,
    capacity_messages,
    endpoint_path
)
SELECT
    service_id,
    'sensor-pipe',
    'PIPE',
    'LOCAL_PROCESS',
    NULL,
    NULL
FROM ipc_service
WHERE service_name = 'telemetry-ingestion';

INSERT INTO ipc_endpoint (
    service_id,
    endpoint_name,
    transport,
    scope,
    capacity_messages,
    endpoint_path
)
SELECT
    service_id,
    'sensor-queue',
    'MESSAGE_QUEUE',
    'LOCAL_HOST',
    1000,
    '/run/telemetry/sensor.queue'
FROM ipc_service
WHERE service_name = 'telemetry-ingestion';

INSERT INTO ipc_endpoint (
    service_id,
    endpoint_name,
    transport,
    scope,
    capacity_messages,
    endpoint_path
)
SELECT
    service_id,
    'admin-socket',
    'SOCKET',
    'LOCAL_HOST',
    NULL,
    '/run/telemetry/admin.sock'
FROM ipc_service
WHERE service_name = 'telemetry-ingestion';

INSERT INTO ipc_endpoint (
    service_id,
    endpoint_name,
    transport,
    scope,
    capacity_messages,
    endpoint_path
)
SELECT
    service_id,
    'document-queue',
    'MESSAGE_QUEUE',
    'LOCAL_HOST',
    500,
    '/run/document-worker/jobs.queue'
FROM ipc_service
WHERE service_name = 'document-worker';

INSERT INTO socket_endpoint (
    endpoint_id,
    protocol
)
SELECT endpoint_id, 'UNIX_STREAM'
FROM ipc_endpoint
WHERE endpoint_name = 'admin-socket';

INSERT INTO ipc_process (
    service_id,
    process_name,
    operating_system_pid
)
SELECT
    service_id,
    'telemetry-producer',
    42101
FROM ipc_service
WHERE service_name = 'telemetry-ingestion';

INSERT INTO ipc_process (
    service_id,
    process_name,
    operating_system_pid
)
SELECT
    service_id,
    'telemetry-consumer',
    42102
FROM ipc_service
WHERE service_name = 'telemetry-ingestion';

INSERT INTO ipc_process (
    service_id,
    process_name,
    operating_system_pid
)
SELECT
    service_id,
    'document-consumer',
    42103
FROM ipc_service
WHERE service_name = 'document-worker';

INSERT INTO shared_memory_segment (
    service_id,
    segment_name,
    size_bytes,
    permissions,
    synchronization_strategy
)
SELECT
    service_id,
    'telemetry-counters',
    4096,
    'OWNER_ONLY',
    'atomic counters with process-shared synchronization'
FROM ipc_service
WHERE service_name = 'telemetry-ingestion';

INSERT INTO shared_memory_attachment (
    segment_id,
    process_id
)
SELECT
    segment.segment_id,
    process.process_id
FROM shared_memory_segment segment
JOIN ipc_process process
    ON process.service_id = segment.service_id
WHERE segment.segment_name = 'telemetry-counters'
  AND process.process_name IN (
      'telemetry-producer',
      'telemetry-consumer'
  );

INSERT INTO message_consumer (
    endpoint_id,
    process_id,
    consumer_name,
    max_attempts
)
SELECT
    endpoint.endpoint_id,
    process.process_id,
    'telemetry-consumer-main',
    4
FROM ipc_endpoint endpoint
JOIN ipc_process process
    ON process.process_name = 'telemetry-consumer'
WHERE endpoint.endpoint_name = 'sensor-queue';

INSERT INTO message_consumer (
    endpoint_id,
    process_id,
    consumer_name,
    max_attempts
)
SELECT
    endpoint.endpoint_id,
    process.process_id,
    'document-worker-main',
    6
FROM ipc_endpoint endpoint
JOIN ipc_process process
    ON process.process_name = 'document-consumer'
WHERE endpoint.endpoint_name = 'document-queue';

INSERT INTO ipc_message (
    endpoint_id,
    producer_process_id,
    message_type,
    payload,
    priority
)
SELECT
    endpoint.endpoint_id,
    process.process_id,
    'SENSOR_READING',
    '{"sensor_id": 1001, "value": 23.4, "unit": "C"}',
    20
FROM ipc_endpoint endpoint
JOIN ipc_process process
    ON process.process_name = 'telemetry-producer'
WHERE endpoint.endpoint_name = 'sensor-queue';

INSERT INTO ipc_message (
    endpoint_id,
    producer_process_id,
    message_type,
    payload,
    priority
)
SELECT
    endpoint.endpoint_id,
    process.process_id,
    'SENSOR_READING',
    '{"sensor_id": 1002, "value": 91.0, "unit": "C"}',
    10
FROM ipc_endpoint endpoint
JOIN ipc_process process
    ON process.process_name = 'telemetry-producer'
WHERE endpoint.endpoint_name = 'sensor-queue';

INSERT INTO ipc_message (
    endpoint_id,
    producer_process_id,
    message_type,
    payload,
    priority,
    state
)
SELECT
    endpoint.endpoint_id,
    process.process_id,
    'DOCUMENT_JOB',
    '{"document": "annual-report.pdf", "pages": 42}',
    30,
    'FAILED'
FROM ipc_endpoint endpoint
JOIN ipc_process process
    ON process.process_name = 'document-consumer'
WHERE endpoint.endpoint_name = 'document-queue';

UPDATE ipc_message
SET completed_at = clock_timestamp()
WHERE message_type = 'DOCUMENT_JOB'
  AND state = 'FAILED';

INSERT INTO message_delivery (
    message_id,
    consumer_id,
    processing_started_at,
    finished_at,
    success
)
SELECT
    message.message_id,
    consumer.consumer_id,
    clock_timestamp() - INTERVAL '2 seconds',
    clock_timestamp(),
    TRUE
FROM ipc_message message
JOIN message_consumer consumer
    ON consumer.consumer_name = 'telemetry-consumer-main'
WHERE message.message_type = 'SENSOR_READING'
  AND message.state = 'QUEUED'
  AND message.payload->>'sensor_id' = '1001';

INSERT INTO ipc_failure (
    message_id,
    process_id,
    transport,
    failure_code,
    failure_detail,
    retryable
)
SELECT
    message.message_id,
    process.process_id,
    'MESSAGE_QUEUE',
    'VALIDATION_ERROR',
    'Sensor value exceeded the configured operating range',
    FALSE
FROM ipc_message message
JOIN ipc_process process
    ON process.process_name = 'document-consumer'
WHERE message.message_type = 'DOCUMENT_JOB'
  AND message.state = 'FAILED';

-- A queue consumer can atomically claim one available message.
-- FOR UPDATE SKIP LOCKED prevents competing consumers from blocking one
-- another on already claimed rows.
BEGIN;

WITH next_message AS (
    SELECT message_id
    FROM ipc_message
    WHERE state = 'QUEUED'
      AND available_at <= clock_timestamp()
    ORDER BY priority DESC, created_at
    FOR UPDATE SKIP LOCKED
    LIMIT 1
)
UPDATE ipc_message message
SET
    state = 'PROCESSING',
    attempt_count = attempt_count + 1
FROM next_message
WHERE message.message_id = next_message.message_id
RETURNING
    message.message_id,
    message.message_type,
    message.attempt_count,
    message.payload;

COMMIT;

-- Identify messages whose attempt count has reached the consumer policy.
SELECT
    message.message_id,
    message.message_type,
    message.attempt_count,
    consumer.max_attempts,
    CASE
        WHEN message.attempt_count >= consumer.max_attempts
            THEN 'DEAD_LETTER_CANDIDATE'
        ELSE 'RETRYABLE'
    END AS delivery_decision
FROM ipc_message message
JOIN message_consumer consumer
    ON consumer.endpoint_id = message.endpoint_id
WHERE message.state IN ('FAILED', 'PROCESSING')
ORDER BY message.created_at;

-- Inspect transport-level message volume.
SELECT
    endpoint.endpoint_name,
    endpoint.transport,
    message.state,
    count(*) AS message_count
FROM ipc_endpoint endpoint
LEFT JOIN ipc_message message
    ON message.endpoint_id = endpoint.endpoint_id
GROUP BY
    endpoint.endpoint_name,
    endpoint.transport,
    message.state
ORDER BY
    endpoint.endpoint_name,
    message.state;

-- Socket endpoints are distinct from message queues because they expose a
-- connection-oriented transport rather than a durable work-item abstraction.
SELECT
    service.service_name,
    endpoint.endpoint_name,
    socket.protocol,
    endpoint.endpoint_path,
    endpoint.active
FROM ipc_service service
JOIN ipc_endpoint endpoint
    ON endpoint.service_id = service.service_id
JOIN socket_endpoint socket
    ON socket.endpoint_id = endpoint.endpoint_id
WHERE endpoint.transport = 'SOCKET';

-- Detect shared-memory segments attached to processes that have stopped.
SELECT
    segment.segment_name,
    process.process_name,
    process.stopped_at,
    attachment.attached_at,
    attachment.detached_at
FROM shared_memory_segment segment
JOIN shared_memory_attachment attachment
    ON attachment.segment_id = segment.segment_id
JOIN ipc_process process
    ON process.process_id = attachment.process_id
WHERE process.stopped_at IS NOT NULL
  AND attachment.detached_at IS NULL;

-- Demonstrate a transactional completion update. The state transition and
-- delivery outcome are committed together, preventing durable state from
-- saying COMPLETED while its delivery record still says unresolved.
BEGIN;

WITH selected AS (
    SELECT message_id
    FROM ipc_message
    WHERE state = 'PROCESSING'
    ORDER BY created_at
    FOR UPDATE SKIP LOCKED
    LIMIT 1
)
UPDATE ipc_message message
SET
    state = 'COMPLETED',
    completed_at = clock_timestamp()
FROM selected
WHERE message.message_id = selected.message_id
RETURNING message.message_id, message.state, message.completed_at;

COMMIT;

-- Operational query: identify messages that have remained available long
-- enough to indicate consumer starvation or a broken producer/consumer path.
SELECT
    message.message_id,
    endpoint.endpoint_name,
    message.priority,
    message.created_at,
    age(clock_timestamp(), message.created_at) AS queue_age
FROM ipc_message message
JOIN ipc_endpoint endpoint
    ON endpoint.endpoint_id = message.endpoint_id
WHERE message.state = 'QUEUED'
ORDER BY message.created_at;

-- IPC design comparison represented as queryable metadata.
SELECT
    transport,
    count(*) AS configured_endpoints,
    string_agg(DISTINCT scope::text, ', ' ORDER BY scope::text) AS scopes
FROM ipc_endpoint
GROUP BY transport
ORDER BY transport;
