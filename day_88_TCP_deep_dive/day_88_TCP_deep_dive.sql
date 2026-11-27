-- ============================================================
-- TCP DEEP DIVE
-- PostgreSQL transport telemetry and reliability model
--
-- Models:
-- 1. TCP connections and endpoint states
-- 2. Three-way handshake
-- 3. Sequence and acknowledgment tracking
-- 4. TCP segments and retransmissions
-- 5. RTT and retransmission timeout estimation
-- 6. Congestion-control observations
-- 7. Receiver flow control
-- 8. Connection termination
-- 9. Network monitoring and reliability reporting
--
-- PostgreSQL 15+
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS tcp_lab;

SET search_path TO tcp_lab, public;

-- ------------------------------------------------------------
-- ENUMERATED DOMAIN TYPES
-- ------------------------------------------------------------

CREATE TYPE connection_state AS ENUM (
    'CLOSED',
    'LISTEN',
    'SYN_SENT',
    'SYN_RECEIVED',
    'ESTABLISHED',
    'FIN_WAIT_1',
    'FIN_WAIT_2',
    'CLOSE_WAIT',
    'LAST_ACK',
    'TIME_WAIT'
);

CREATE TYPE segment_type AS ENUM (
    'SYN',
    'SYN_ACK',
    'ACK',
    'DATA',
    'FIN',
    'RST'
);

CREATE TYPE congestion_state AS ENUM (
    'SLOW_START',
    'CONGESTION_AVOIDANCE',
    'FAST_RECOVERY'
);

CREATE TYPE transmission_status AS ENUM (
    'SENT',
    'ACKNOWLEDGED',
    'LOST',
    'RETRANSMITTED',
    'OUT_OF_ORDER'
);

CREATE TYPE endpoint_role AS ENUM (
    'CLIENT',
    'SERVER'
);

-- ------------------------------------------------------------
-- REPOSITORY OF NETWORK ENDPOINTS
-- ------------------------------------------------------------

CREATE TABLE endpoints (
    endpoint_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    hostname VARCHAR(150) NOT NULL UNIQUE,

    ip_address INET NOT NULL,

    operating_system VARCHAR(100),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_hostname
        CHECK (length(trim(hostname)) > 0)
);

-- ------------------------------------------------------------
-- TCP CONNECTIONS
-- ------------------------------------------------------------

CREATE TABLE tcp_connections (
    connection_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    client_endpoint_id BIGINT NOT NULL
        REFERENCES endpoints(endpoint_id),

    server_endpoint_id BIGINT NOT NULL
        REFERENCES endpoints(endpoint_id),

    client_port INTEGER NOT NULL,

    server_port INTEGER NOT NULL,

    state connection_state NOT NULL DEFAULT 'CLOSED',

    client_iss BIGINT NOT NULL,

    server_iss BIGINT,

    snd_una BIGINT NOT NULL,

    snd_nxt BIGINT NOT NULL,

    rcv_nxt BIGINT NOT NULL DEFAULT 0,

    mss INTEGER NOT NULL DEFAULT 1460,

    receiver_window INTEGER NOT NULL DEFAULT 65535,

    opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    established_at TIMESTAMPTZ,

    closed_at TIMESTAMPTZ,

    CONSTRAINT valid_client_port
        CHECK (client_port BETWEEN 1 AND 65535),

    CONSTRAINT valid_server_port
        CHECK (server_port BETWEEN 1 AND 65535),

    CONSTRAINT valid_sequence_numbers
        CHECK (
            client_iss >= 0
            AND snd_una >= 0
            AND snd_nxt >= snd_una
            AND rcv_nxt >= 0
        ),

    CONSTRAINT valid_mss
        CHECK (mss BETWEEN 1 AND 65535),

    CONSTRAINT valid_receive_window
        CHECK (receiver_window BETWEEN 0 AND 65535),

    CONSTRAINT different_endpoints
        CHECK (client_endpoint_id <> server_endpoint_id)
);

CREATE INDEX idx_connections_state
    ON tcp_connections(state);

CREATE INDEX idx_connections_opened
    ON tcp_connections(opened_at DESC);

CREATE INDEX idx_connections_client
    ON tcp_connections(client_endpoint_id, opened_at DESC);

CREATE INDEX idx_connections_server
    ON tcp_connections(server_endpoint_id, opened_at DESC);

-- ------------------------------------------------------------
-- TCP SEGMENT TELEMETRY
-- ------------------------------------------------------------

CREATE TABLE tcp_segments (
    segment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    connection_id BIGINT NOT NULL
        REFERENCES tcp_connections(connection_id)
        ON DELETE CASCADE,

    sequence_number BIGINT NOT NULL,

    acknowledgment_number BIGINT NOT NULL DEFAULT 0,

    payload_bytes INTEGER NOT NULL DEFAULT 0,

    segment_kind segment_type NOT NULL,

    status transmission_status NOT NULL DEFAULT 'SENT',

    retransmission_number INTEGER NOT NULL DEFAULT 0,

    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    acknowledged_at TIMESTAMPTZ,

    rtt_ms NUMERIC(12, 4),

    CONSTRAINT valid_segment_sequence
        CHECK (sequence_number >= 0),

    CONSTRAINT valid_ack_number
        CHECK (acknowledgment_number >= 0),

    CONSTRAINT valid_payload
        CHECK (payload_bytes >= 0),

    CONSTRAINT valid_retransmission_number
        CHECK (retransmission_number >= 0),

    CONSTRAINT valid_rtt
        CHECK (rtt_ms IS NULL OR rtt_ms > 0),

    CONSTRAINT acknowledgment_after_send
        CHECK (
            acknowledged_at IS NULL
            OR acknowledged_at >= sent_at
        )
);

CREATE INDEX idx_segments_connection_sequence
    ON tcp_segments(connection_id, sequence_number);

CREATE INDEX idx_segments_status
    ON tcp_segments(status, sent_at DESC);

CREATE INDEX idx_segments_retransmissions
    ON tcp_segments(connection_id, retransmission_number)
    WHERE retransmission_number > 0;

CREATE INDEX idx_segments_acknowledgment
    ON tcp_segments(connection_id, acknowledgment_number);

-- ------------------------------------------------------------
-- CONGESTION CONTROL OBSERVATIONS
-- ------------------------------------------------------------

CREATE TABLE congestion_observations (
    observation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    connection_id BIGINT NOT NULL
        REFERENCES tcp_connections(connection_id)
        ON DELETE CASCADE,

    congestion_window NUMERIC(14, 4) NOT NULL,

    slow_start_threshold NUMERIC(14, 4) NOT NULL,

    congestion_phase congestion_state NOT NULL,

    receiver_window INTEGER NOT NULL,

    measured_rtt_ms NUMERIC(12, 4),

    retransmission_timeout_ms NUMERIC(12, 4) NOT NULL,

    observed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT positive_congestion_window
        CHECK (congestion_window > 0),

    CONSTRAINT valid_threshold
        CHECK (slow_start_threshold > 0),

    CONSTRAINT valid_observed_window
        CHECK (receiver_window BETWEEN 0 AND 65535),

    CONSTRAINT valid_measured_rtt
        CHECK (
            measured_rtt_ms IS NULL
            OR measured_rtt_ms > 0
        ),

    CONSTRAINT valid_timeout
        CHECK (retransmission_timeout_ms > 0)
);

CREATE INDEX idx_congestion_connection_time
    ON congestion_observations(connection_id, observed_at DESC);

CREATE INDEX idx_congestion_phase
    ON congestion_observations(congestion_phase);

-- ------------------------------------------------------------
-- CONNECTION EVENTS
-- ------------------------------------------------------------

CREATE TABLE connection_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    connection_id BIGINT NOT NULL
        REFERENCES tcp_connections(connection_id)
        ON DELETE CASCADE,

    event_type VARCHAR(60) NOT NULL,

    old_state connection_state,

    new_state connection_state,

    description TEXT NOT NULL,

    event_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_event_type
        CHECK (length(trim(event_type)) > 0)
);

CREATE INDEX idx_connection_events_history
    ON connection_events(connection_id, event_time DESC);

-- ------------------------------------------------------------
-- CONNECTION STATE VALIDATION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_tcp_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.state NOT IN ('CLOSED', 'LISTEN') THEN
            RAISE EXCEPTION
                'New TCP connections must begin CLOSED or LISTEN';
        END IF;

        RETURN NEW;
    END IF;

    IF NEW.state = OLD.state THEN
        RETURN NEW;
    END IF;

    IF NOT (
        (OLD.state = 'CLOSED'
            AND NEW.state IN ('LISTEN', 'SYN_SENT'))

        OR (OLD.state = 'LISTEN'
            AND NEW.state IN ('SYN_RECEIVED', 'CLOSED'))

        OR (OLD.state = 'SYN_SENT'
            AND NEW.state IN ('ESTABLISHED', 'CLOSED'))

        OR (OLD.state = 'SYN_RECEIVED'
            AND NEW.state IN ('ESTABLISHED', 'CLOSED'))

        OR (OLD.state = 'ESTABLISHED'
            AND NEW.state IN ('FIN_WAIT_1', 'CLOSE_WAIT', 'CLOSED'))

        OR (OLD.state = 'FIN_WAIT_1'
            AND NEW.state IN ('FIN_WAIT_2', 'CLOSING', 'TIME_WAIT'))

        OR (OLD.state = 'FIN_WAIT_2'
            AND NEW.state = 'TIME_WAIT')

        OR (OLD.state = 'CLOSE_WAIT'
            AND NEW.state IN ('LAST_ACK', 'CLOSED'))

        OR (OLD.state = 'LAST_ACK'
            AND NEW.state = 'CLOSED')

        OR (OLD.state = 'TIME_WAIT'
            AND NEW.state = 'CLOSED')
    ) THEN
        RAISE EXCEPTION
            'Invalid TCP state transition: % -> %',
            OLD.state,
            NEW.state;
    END IF;

    IF NEW.state = 'ESTABLISHED'
       AND NEW.established_at IS NULL THEN
        NEW.established_at := NOW();
    END IF;

    IF NEW.state = 'CLOSED'
       AND OLD.state <> 'CLOSED' THEN
        NEW.closed_at := NOW();
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_tcp_transition
BEFORE INSERT OR UPDATE OF state
ON tcp_connections
FOR EACH ROW
EXECUTE FUNCTION validate_tcp_transition();

-- ------------------------------------------------------------
-- AUTOMATIC CONNECTION EVENT AUDITING
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION audit_tcp_state_change()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.state IS DISTINCT FROM NEW.state THEN

        INSERT INTO connection_events (
            connection_id,
            event_type,
            old_state,
            new_state,
            description
        )
        VALUES (
            NEW.connection_id,
            'STATE_TRANSITION',
            OLD.state,
            NEW.state,
            format(
                'TCP state changed from %s to %s',
                OLD.state,
                NEW.state
            )
        );

    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_audit_tcp_state
AFTER UPDATE OF state
ON tcp_connections
FOR EACH ROW
EXECUTE FUNCTION audit_tcp_state_change();

-- ------------------------------------------------------------
-- CONNECTION CREATION PROCEDURE
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE create_tcp_connection(
    p_client_endpoint BIGINT,
    p_server_endpoint BIGINT,
    p_client_port INTEGER,
    p_server_port INTEGER,
    p_client_iss BIGINT,
    p_mss INTEGER,
    p_receiver_window INTEGER
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM endpoints
        WHERE endpoint_id = p_client_endpoint
    ) THEN
        RAISE EXCEPTION 'Client endpoint does not exist';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM endpoints
        WHERE endpoint_id = p_server_endpoint
    ) THEN
        RAISE EXCEPTION 'Server endpoint does not exist';
    END IF;

    INSERT INTO tcp_connections (
        client_endpoint_id,
        server_endpoint_id,
        client_port,
        server_port,
        state,
        client_iss,
        snd_una,
        snd_nxt,
        mss,
        receiver_window
    )
    VALUES (
        p_client_endpoint,
        p_server_endpoint,
        p_client_port,
        p_server_port,
        'CLOSED',
        p_client_iss,
        p_client_iss,
        p_client_iss,
        p_mss,
        p_receiver_window
    );
END;
$$;

-- ------------------------------------------------------------
-- HANDSHAKE PROCESSING
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE establish_tcp_connection(
    p_connection_id BIGINT,
    p_server_iss BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_connection tcp_connections%ROWTYPE;
BEGIN
    SELECT *
    INTO v_connection
    FROM tcp_connections
    WHERE connection_id = p_connection_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Connection not found';
    END IF;

    IF v_connection.state <> 'CLOSED' THEN
        RAISE EXCEPTION
            'Connection must be CLOSED before handshake';
    END IF;

    IF p_server_iss < 0 THEN
        RAISE EXCEPTION 'Invalid server sequence number';
    END IF;

    -- SYN: client sends its initial sequence number.
    UPDATE tcp_connections
    SET
        state = 'SYN_SENT',
        snd_nxt = client_iss + 1
    WHERE connection_id = p_connection_id;

    INSERT INTO tcp_segments (
        connection_id,
        sequence_number,
        segment_kind
    )
    VALUES (
        p_connection_id,
        v_connection.client_iss,
        'SYN'
    );

    -- SYN-ACK: server acknowledges the client SYN.
    UPDATE tcp_connections
    SET
        state = 'SYN_RECEIVED',
        server_iss = p_server_iss,
        rcv_nxt = p_server_iss + 1
    WHERE connection_id = p_connection_id;

    INSERT INTO tcp_segments (
        connection_id,
        sequence_number,
        acknowledgment_number,
        segment_kind
    )
    VALUES (
        p_connection_id,
        p_server_iss,
        v_connection.client_iss + 1,
        'SYN_ACK'
    );

    -- ACK: client acknowledges the server SYN.
    UPDATE tcp_connections
    SET
        state = 'ESTABLISHED',
        snd_una = snd_nxt,
        rcv_nxt = p_server_iss + 1
    WHERE connection_id = p_connection_id;

    INSERT INTO tcp_segments (
        connection_id,
        sequence_number,
        acknowledgment_number,
        segment_kind,
        status
    )
    VALUES (
        p_connection_id,
        v_connection.client_iss + 1,
        p_server_iss + 1,
        'ACK',
        'ACKNOWLEDGED'
    );

END;
$$;

-- ------------------------------------------------------------
-- RECORD DATA TRANSMISSION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION record_tcp_data(
    p_connection_id BIGINT,
    p_payload_bytes INTEGER
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_connection tcp_connections%ROWTYPE;
    v_sequence BIGINT;
    v_in_flight BIGINT;
    v_effective_window INTEGER;
BEGIN
    IF p_payload_bytes <= 0 THEN
        RAISE EXCEPTION 'Payload must be positive';
    END IF;

    SELECT *
    INTO v_connection
    FROM tcp_connections
    WHERE connection_id = p_connection_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Unknown connection';
    END IF;

    IF v_connection.state <> 'ESTABLISHED' THEN
        RAISE EXCEPTION
            'Data transmission requires ESTABLISHED state';
    END IF;

    v_in_flight :=
        v_connection.snd_nxt - v_connection.snd_una;

    -- The example uses the current receive window as a
    -- conservative transmission limit. Congestion-window
    -- limits are evaluated separately from observations.
    v_effective_window := v_connection.receiver_window;

    IF v_in_flight >= v_effective_window THEN
        RAISE EXCEPTION 'Receiver window is exhausted';
    END IF;

    IF p_payload_bytes > v_connection.mss THEN
        RAISE EXCEPTION 'Payload exceeds MSS';
    END IF;

    IF p_payload_bytes >
        v_effective_window - v_in_flight THEN
        RAISE EXCEPTION 'Payload exceeds available send window';
    END IF;

    v_sequence := v_connection.snd_nxt;

    INSERT INTO tcp_segments (
        connection_id,
        sequence_number,
        acknowledgment_number,
        payload_bytes,
        segment_kind,
        status
    )
    VALUES (
        p_connection_id,
        v_sequence,
        v_connection.rcv_nxt,
        p_payload_bytes,
        'DATA',
        'SENT'
    );

    UPDATE tcp_connections
    SET snd_nxt = snd_nxt + p_payload_bytes
    WHERE connection_id = p_connection_id;

    RETURN v_sequence;
END;
$$;

-- ------------------------------------------------------------
-- CUMULATIVE ACKNOWLEDGMENT PROCESSING
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE acknowledge_tcp_data(
    p_connection_id BIGINT,
    p_acknowledgment BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_connection tcp_connections%ROWTYPE;
BEGIN
    SELECT *
    INTO v_connection
    FROM tcp_connections
    WHERE connection_id = p_connection_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Connection not found';
    END IF;

    IF p_acknowledgment > v_connection.snd_nxt THEN
        RAISE EXCEPTION
            'ACK cannot acknowledge unsent sequence numbers';
    END IF;

    IF p_acknowledgment < v_connection.snd_una THEN
        RAISE EXCEPTION 'Stale acknowledgment';
    END IF;

    IF p_acknowledgment = v_connection.snd_una THEN

        INSERT INTO connection_events (
            connection_id,
            event_type,
            description
        )
        VALUES (
            p_connection_id,
            'DUPLICATE_ACK',
            'Duplicate cumulative acknowledgment observed'
        );

        RETURN;
    END IF;

    UPDATE tcp_segments
    SET
        status = 'ACKNOWLEDGED',
        acknowledged_at = NOW()
    WHERE connection_id = p_connection_id
      AND segment_kind = 'DATA'
      AND status IN ('SENT', 'RETRANSMITTED')
      AND sequence_number + payload_bytes <= p_acknowledgment;

    UPDATE tcp_connections
    SET snd_una = p_acknowledgment
    WHERE connection_id = p_connection_id;

END;
$$;

-- ------------------------------------------------------------
-- RECORD RTT AND CONGESTION STATE
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE record_congestion_observation(
    p_connection_id BIGINT,
    p_cwnd NUMERIC,
    p_ssthresh NUMERIC,
    p_phase congestion_state,
    p_rwnd INTEGER,
    p_rtt NUMERIC,
    p_rto NUMERIC
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM tcp_connections
        WHERE connection_id = p_connection_id
          AND state = 'ESTABLISHED'
    ) THEN
        RAISE EXCEPTION
            'Congestion observation requires an established connection';
    END IF;

    INSERT INTO congestion_observations (
        connection_id,
        congestion_window,
        slow_start_threshold,
        congestion_phase,
        receiver_window,
        measured_rtt_ms,
        retransmission_timeout_ms
    )
    VALUES (
        p_connection_id,
        p_cwnd,
        p_ssthresh,
        p_phase,
        p_rwnd,
        p_rtt,
        p_rto
    );
END;
$$;

-- ------------------------------------------------------------
-- RECORD RETRANSMISSION
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE mark_segment_retransmitted(
    p_segment_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_connection_id BIGINT;
BEGIN
    SELECT connection_id
    INTO v_connection_id
    FROM tcp_segments
    WHERE segment_id = p_segment_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Segment not found';
    END IF;

    UPDATE tcp_segments
    SET
        status = 'RETRANSMITTED',
        retransmission_number = retransmission_number + 1,
        sent_at = NOW(),
        acknowledged_at = NULL
    WHERE segment_id = p_segment_id
      AND status IN ('SENT', 'LOST', 'RETRANSMITTED');

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Segment cannot be retransmitted in its current state';
    END IF;

    INSERT INTO connection_events (
        connection_id,
        event_type,
        description
    )
    VALUES (
        v_connection_id,
        'RETRANSMISSION',
        'Segment retransmitted after loss detection'
    );
END;
$$;

-- ------------------------------------------------------------
-- BRANCH-FREE CONNECTION RELIABILITY VIEW
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW connection_reliability AS
SELECT
    c.connection_id,
    client.hostname AS client_hostname,
    server.hostname AS server_hostname,
    c.state,

    COUNT(s.segment_id) AS total_segments,

    COUNT(s.segment_id) FILTER (
        WHERE s.segment_kind = 'DATA'
    ) AS data_segments,

    COUNT(s.segment_id) FILTER (
        WHERE s.status = 'ACKNOWLEDGED'
    ) AS acknowledged_segments,

    COUNT(s.segment_id) FILTER (
        WHERE s.status = 'LOST'
    ) AS lost_segments,

    COUNT(s.segment_id) FILTER (
        WHERE s.retransmission_number > 0
    ) AS retransmitted_segments,

    COALESCE(
        SUM(s.payload_bytes),
        0
    ) AS transmitted_payload_bytes,

    COALESCE(
        AVG(s.rtt_ms),
        0
    ) AS average_rtt_ms

FROM tcp_connections c

JOIN endpoints client
    ON client.endpoint_id = c.client_endpoint_id

JOIN endpoints server
    ON server.endpoint_id = c.server_endpoint_id

LEFT JOIN tcp_segments s
    ON s.connection_id = c.connection_id

GROUP BY
    c.connection_id,
    client.hostname,
    server.hostname,
    c.state;

-- ------------------------------------------------------------
-- CONGESTION REPORTING VIEW
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW congestion_report AS
SELECT
    c.connection_id,

    c.state,

    COUNT(o.observation_id) AS observations,

    ROUND(
        AVG(o.congestion_window),
        3
    ) AS average_cwnd,

    ROUND(
        MAX(o.congestion_window),
        3
    ) AS maximum_cwnd,

    ROUND(
        AVG(o.measured_rtt_ms),
        3
    ) AS average_rtt_ms,

    ROUND(
        MAX(o.retransmission_timeout_ms),
        3
    ) AS maximum_rto_ms,

    COUNT(o.observation_id) FILTER (
        WHERE o.congestion_phase = 'SLOW_START'
    ) AS slow_start_samples,

    COUNT(o.observation_id) FILTER (
        WHERE o.congestion_phase = 'CONGESTION_AVOIDANCE'
    ) AS avoidance_samples,

    COUNT(o.observation_id) FILTER (
        WHERE o.congestion_phase = 'FAST_RECOVERY'
    ) AS fast_recovery_samples

FROM tcp_connections c

LEFT JOIN congestion_observations o
    ON o.connection_id = c.connection_id

GROUP BY
    c.connection_id,
    c.state;

-- ------------------------------------------------------------
-- SAMPLE NETWORK ENDPOINTS
-- ------------------------------------------------------------

INSERT INTO endpoints (
    hostname,
    ip_address,
    operating_system
)
VALUES
    ('client-alpha', '192.168.1.10', 'Linux'),
    ('server-alpha', '10.0.0.10', 'Linux'),
    ('client-beta', '192.168.1.20', 'Windows'),
    ('server-beta', '10.0.0.20', 'Linux');

-- ------------------------------------------------------------
-- CREATE CONNECTIONS
-- ------------------------------------------------------------

CALL create_tcp_connection(
    1, 2, 51000, 443,
    1000, 1460, 65535
);

CALL create_tcp_connection(
    3, 4, 52000, 443,
    5000, 1460, 32000
);

-- ------------------------------------------------------------
-- TRANSACTIONAL THREE-WAY HANDSHAKES
-- ------------------------------------------------------------

CALL establish_tcp_connection(1, 5000);
CALL establish_tcp_connection(2, 9000);

-- ------------------------------------------------------------
-- RECORD DATA TRANSMISSION
-- ------------------------------------------------------------

DO $$
DECLARE
    v_sequence BIGINT;
BEGIN
    v_sequence := record_tcp_data(1, 1000);

    RAISE NOTICE 'Connection 1 transmitted at sequence %',
        v_sequence;

    v_sequence := record_tcp_data(1, 500);

    RAISE NOTICE 'Connection 1 transmitted at sequence %',
        v_sequence;
END;
$$;

-- ------------------------------------------------------------
-- ACKNOWLEDGMENT PROCESSING
-- ------------------------------------------------------------

CALL acknowledge_tcp_data(
    1,
    2501
);

-- ------------------------------------------------------------
-- CONGESTION CONTROL OBSERVATIONS
-- ------------------------------------------------------------

CALL record_congestion_observation(
    1,
    1.0,
    16.0,
    'SLOW_START',
    65535,
    120.0,
    600.0
);

CALL record_congestion_observation(
    1,
    2.0,
    16.0,
    'SLOW_START',
    65535,
    135.0,
    650.0
);

CALL record_congestion_observation(
    1,
    4.0,
    8.0,
    'CONGESTION_AVOIDANCE',
    65535,
    150.0,
    700.0
);

CALL record_congestion_observation(
    1,
    5.0,
    8.0,
    'FAST_RECOVERY',
    65535,
    180.0,
    900.0
);

-- ------------------------------------------------------------
-- FAILURE SCENARIO: MARK A TRANSMITTED SEGMENT AS LOST
-- ------------------------------------------------------------

INSERT INTO tcp_segments (
    connection_id,
    sequence_number,
    acknowledgment_number,
    payload_bytes,
    segment_kind,
    status
)
VALUES (
    2,
    9001,
    5001,
    1200,
    'DATA',
    'LOST'
);

-- Demonstrate retransmission with a real segment identifier.
SELECT mark_segment_retransmitted(
    (
        SELECT segment_id
        FROM tcp_segments
        WHERE connection_id = 2
          AND status = 'LOST'
        ORDER BY segment_id DESC
        LIMIT 1
    )
);

-- ------------------------------------------------------------
-- CONNECTION RETRIEVAL
-- ------------------------------------------------------------

SELECT
    connection_id,
    state,
    client_port,
    server_port,
    snd_una,
    snd_nxt,
    rcv_nxt,
    mss,
    receiver_window
FROM tcp_connections
ORDER BY connection_id;

-- ------------------------------------------------------------
-- SEGMENT RETRIEVAL
-- ------------------------------------------------------------

SELECT
    segment_id,
    connection_id,
    sequence_number,
    acknowledgment_number,
    payload_bytes,
    segment_kind,
    status,
    retransmission_number,
    sent_at
FROM tcp_segments
ORDER BY connection_id, sequence_number, segment_id;

-- ------------------------------------------------------------
-- RELIABILITY AGGREGATION
-- ------------------------------------------------------------

SELECT *
FROM connection_reliability
ORDER BY connection_id;

-- ------------------------------------------------------------
-- CONGESTION CONTROL REPORT
-- ------------------------------------------------------------

SELECT *
FROM congestion_report
ORDER BY connection_id;

-- ------------------------------------------------------------
-- LOSS AND RETRANSMISSION ANALYSIS
-- ------------------------------------------------------------

SELECT
    connection_id,

    COUNT(*) AS total_data_segments,

    COUNT(*) FILTER (
        WHERE status = 'LOST'
    ) AS lost_segments,

    COUNT(*) FILTER (
        WHERE retransmission_number > 0
    ) AS retransmitted_segments,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE status = 'LOST'
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS loss_percentage

FROM tcp_segments

WHERE segment_kind = 'DATA'

GROUP BY connection_id
ORDER BY connection_id;

-- ------------------------------------------------------------
-- CONNECTION EVENT HISTORY
-- ------------------------------------------------------------

SELECT
    connection_id,
    event_type,
    old_state,
    new_state,
    description,
    event_time
FROM connection_events
ORDER BY connection_id, event_time;

-- ------------------------------------------------------------
-- ELIGIBILITY: CAN A CONNECTION TRANSMIT APPLICATION DATA?
-- ------------------------------------------------------------

SELECT
    connection_id,
    state,

    CASE
        WHEN state <> 'ESTABLISHED'
            THEN 'NOT_ELIGIBLE'

        WHEN receiver_window = 0
            THEN 'ZERO_WINDOW'

        WHEN snd_nxt - snd_una >= receiver_window
            THEN 'WINDOW_EXHAUSTED'

        ELSE 'ELIGIBLE'
    END AS transmission_eligibility

FROM tcp_connections
ORDER BY connection_id;

-- ------------------------------------------------------------
-- VALIDATION: CHECK INVALID ACKS WITHOUT ABORTING SCRIPT
-- ------------------------------------------------------------

DO $$
BEGIN
    BEGIN
        CALL acknowledge_tcp_data(
            1,
            999999999
        );

    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE
                'Expected ACK validation failure: %',
                SQLERRM;
    END;
END;
$$;

-- ------------------------------------------------------------
-- CONNECTION TERMINATION
-- ------------------------------------------------------------

UPDATE tcp_connections
SET state = 'FIN_WAIT_1'
WHERE connection_id = 1
  AND state = 'ESTABLISHED';

UPDATE tcp_connections
SET state = 'FIN_WAIT_2'
WHERE connection_id = 1
  AND state = 'FIN_WAIT_1';

UPDATE tcp_connections
SET state = 'TIME_WAIT'
WHERE connection_id = 1
  AND state = 'FIN_WAIT_2';

-- ------------------------------------------------------------
-- FINAL CONNECTION AUDIT
-- ------------------------------------------------------------

SELECT
    connection_id,
    state,
    opened_at,
    established_at,
    closed_at
FROM tcp_connections
ORDER BY connection_id;

COMMIT;

-- ============================================================
-- OPERATIONAL NOTES
--
-- 1. Sequence and acknowledgment values use BIGINT for
--    analytical simplicity. Real TCP sequence numbers are
--    32-bit values with serial-number arithmetic and wraparound.
--
-- 2. Congestion observations are historical measurements.
--    The database does not independently implement a TCP stack.
--
-- 3. RTT estimation and congestion-control algorithms execute
--    at the transport endpoint, not inside the relational engine.
--
-- 4. A production collector should use authenticated ingestion,
--    restricted database roles, retention policies, and
--    partitioning for high-volume segment telemetry.
--
-- 5. TCP checksum verification and cryptographic protection
--    require packet-processing or transport-layer components.
--
-- 6. Database state-transition validation is a monitoring
--    integrity mechanism, not a replacement for TCP protocol
--    state-machine enforcement.
-- ============================================================
