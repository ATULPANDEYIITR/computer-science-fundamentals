/*
    TRANSPORT LAYER DATABASE MODEL
    PostgreSQL 14+

    Domains:
      1. Network endpoints and port assignments.
      2. TCP and UDP transport protocols.
      3. TCP connection lifecycle.
      4. TCP sequence numbers and acknowledgements.
      5. Sliding-window flow control.
      6. UDP datagram telemetry.
      7. Transport policy enforcement.
      8. Operational reporting.

    The schema stores transport telemetry and modeled network
    operations. It does not implement a kernel TCP/IP stack.
*/

BEGIN;

CREATE SCHEMA IF NOT EXISTS transport_lab;

SET search_path TO transport_lab, public;

-- ============================================================
-- 1. DOMAIN TYPES
-- ============================================================

CREATE TYPE transport_protocol AS ENUM (
    'TCP',
    'UDP'
);

CREATE TYPE connection_state AS ENUM (
    'CLOSED',
    'LISTEN',
    'SYN_SENT',
    'SYN_RECEIVED',
    'ESTABLISHED',
    'FIN_WAIT',
    'CLOSE_WAIT',
    'TIME_WAIT'
);

CREATE TYPE connection_event AS ENUM (
    'CREATED',
    'SYN',
    'SYN_ACK',
    'ACK',
    'DATA',
    'WINDOW_UPDATE',
    'FIN',
    'RESET',
    'CLOSED'
);

CREATE TYPE port_status AS ENUM (
    'ACTIVE',
    'DISABLED',
    'RELEASED'
);

-- ============================================================
-- 2. REPOSITORY OF NETWORK DEVICES
-- ============================================================

CREATE TABLE network_devices (
    device_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    device_name VARCHAR(100) NOT NULL UNIQUE,

    ipv4_address INET NOT NULL UNIQUE,

    device_role VARCHAR(30) NOT NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_device_role CHECK (
        device_role IN (
            'CLIENT',
            'SERVER',
            'GATEWAY',
            'DNS_SERVER',
            'APPLICATION_SERVER'
        )
    ),

    CONSTRAINT valid_ipv4 CHECK (
        family(ipv4_address) = 4
    )
);

-- ============================================================
-- 3. PORT REGISTRY
-- ============================================================

CREATE TABLE port_assignments (
    port_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    device_id BIGINT NOT NULL
        REFERENCES network_devices(device_id),

    protocol transport_protocol NOT NULL,

    port_number INTEGER NOT NULL,

    service_name VARCHAR(100) NOT NULL,

    status port_status NOT NULL DEFAULT 'ACTIVE',

    registered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_port CHECK (
        port_number BETWEEN 1 AND 65535
    ),

    CONSTRAINT unique_endpoint_protocol
        UNIQUE(device_id, protocol, port_number)
);

CREATE INDEX idx_port_assignments_lookup
ON port_assignments(device_id, protocol, port_number)
WHERE status = 'ACTIVE';

CREATE INDEX idx_port_assignments_service
ON port_assignments(service_name);

-- ============================================================
-- 4. CONNECTIONS
-- ============================================================

CREATE TABLE transport_connections (
    connection_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    source_device_id BIGINT NOT NULL
        REFERENCES network_devices(device_id),

    destination_device_id BIGINT NOT NULL
        REFERENCES network_devices(device_id),

    source_port INTEGER NOT NULL,

    destination_port INTEGER NOT NULL,

    protocol transport_protocol NOT NULL,

    state connection_state NOT NULL DEFAULT 'CLOSED',

    send_sequence BIGINT NOT NULL DEFAULT 0,

    receive_sequence BIGINT NOT NULL DEFAULT 0,

    bytes_sent BIGINT NOT NULL DEFAULT 0,

    bytes_received BIGINT NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    established_at TIMESTAMPTZ,

    closed_at TIMESTAMPTZ,

    CONSTRAINT valid_source_port CHECK (
        source_port BETWEEN 1 AND 65535
    ),

    CONSTRAINT valid_destination_port CHECK (
        destination_port BETWEEN 1 AND 65535
    ),

    CONSTRAINT nonnegative_sequence CHECK (
        send_sequence >= 0 AND receive_sequence >= 0
    ),

    CONSTRAINT nonnegative_byte_counts CHECK (
        bytes_sent >= 0 AND bytes_received >= 0
    ),

    CONSTRAINT valid_connection_protocol CHECK (
        protocol = 'TCP' OR state IN ('CLOSED', 'ESTABLISHED')
    )
);

CREATE INDEX idx_connections_source
ON transport_connections(source_device_id, created_at DESC);

CREATE INDEX idx_connections_destination
ON transport_connections(destination_device_id, created_at DESC);

CREATE INDEX idx_connections_active
ON transport_connections(state, protocol)
WHERE state = 'ESTABLISHED';

-- ============================================================
-- 5. CONNECTION EVENT HISTORY
-- ============================================================

CREATE TABLE connection_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    connection_id BIGINT NOT NULL
        REFERENCES transport_connections(connection_id)
        ON DELETE CASCADE,

    event_type connection_event NOT NULL,

    previous_state connection_state,

    new_state connection_state,

    event_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    description TEXT,

    CONSTRAINT valid_event_description CHECK (
        description IS NULL OR length(description) <= 2000
    )
);

CREATE INDEX idx_connection_events_history
ON connection_events(connection_id, event_timestamp DESC);

-- ============================================================
-- 6. TCP FLOW CONTROL
-- ============================================================

CREATE TABLE tcp_flow_control (
    flow_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    connection_id BIGINT NOT NULL UNIQUE
        REFERENCES transport_connections(connection_id)
        ON DELETE CASCADE,

    send_window INTEGER NOT NULL DEFAULT 65535,

    receive_window INTEGER NOT NULL DEFAULT 65535,

    congestion_window INTEGER NOT NULL DEFAULT 65535,

    outstanding_bytes BIGINT NOT NULL DEFAULT 0,

    next_sequence BIGINT NOT NULL DEFAULT 0,

    acknowledged_sequence BIGINT NOT NULL DEFAULT 0,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_send_window CHECK (
        send_window BETWEEN 0 AND 65535
    ),

    CONSTRAINT valid_receive_window CHECK (
        receive_window BETWEEN 0 AND 65535
    ),

    CONSTRAINT valid_congestion_window CHECK (
        congestion_window BETWEEN 0 AND 2147483647
    ),

    CONSTRAINT valid_outstanding_bytes CHECK (
        outstanding_bytes >= 0
    ),

    CONSTRAINT valid_sequence_numbers CHECK (
        next_sequence >= acknowledged_sequence
        AND acknowledged_sequence >= 0
    )
);

CREATE INDEX idx_flow_window_monitoring
ON tcp_flow_control(receive_window, outstanding_bytes);

-- ============================================================
-- 7. TRANSMITTED TCP SEGMENTS
-- ============================================================

CREATE TABLE tcp_segments (
    segment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    connection_id BIGINT NOT NULL
        REFERENCES transport_connections(connection_id)
        ON DELETE CASCADE,

    sequence_number BIGINT NOT NULL,

    acknowledgement_number BIGINT NOT NULL,

    payload_bytes INTEGER NOT NULL,

    acknowledged BOOLEAN NOT NULL DEFAULT FALSE,

    retransmission_count INTEGER NOT NULL DEFAULT 0,

    transmitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    acknowledged_at TIMESTAMPTZ,

    CONSTRAINT valid_segment_sequence CHECK (
        sequence_number >= 0 AND acknowledgement_number >= 0
    ),

    CONSTRAINT valid_payload_length CHECK (
        payload_bytes BETWEEN 0 AND 65535
    ),

    CONSTRAINT valid_retransmissions CHECK (
        retransmission_count >= 0
    )
);

CREATE INDEX idx_tcp_segments_unacknowledged
ON tcp_segments(connection_id, sequence_number)
WHERE acknowledged = FALSE;

-- ============================================================
-- 8. UDP DATAGRAM TELEMETRY
-- ============================================================

CREATE TABLE udp_datagrams (
    datagram_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    source_device_id BIGINT NOT NULL
        REFERENCES network_devices(device_id),

    destination_device_id BIGINT NOT NULL
        REFERENCES network_devices(device_id),

    source_port INTEGER NOT NULL,

    destination_port INTEGER NOT NULL,

    payload_bytes INTEGER NOT NULL,

    checksum_valid BOOLEAN NOT NULL DEFAULT TRUE,

    received BOOLEAN NOT NULL DEFAULT FALSE,

    transmitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    received_at TIMESTAMPTZ,

    CONSTRAINT valid_udp_source_port CHECK (
        source_port BETWEEN 1 AND 65535
    ),

    CONSTRAINT valid_udp_destination_port CHECK (
        destination_port BETWEEN 1 AND 65535
    ),

    CONSTRAINT valid_udp_payload CHECK (
        payload_bytes BETWEEN 0 AND 65507
    ),

    CONSTRAINT valid_udp_receive_time CHECK (
        received = FALSE OR received_at IS NOT NULL
    )
);

CREATE INDEX idx_udp_datagram_destination
ON udp_datagrams(destination_device_id, transmitted_at DESC);

-- ============================================================
-- 9. TRANSPORT SECURITY AND CONFIGURATION POLICIES
-- ============================================================

CREATE TABLE transport_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    policy_name VARCHAR(120) NOT NULL UNIQUE,

    protocol transport_protocol NOT NULL,

    minimum_port INTEGER NOT NULL DEFAULT 1,

    maximum_port INTEGER NOT NULL DEFAULT 65535,

    maximum_payload_bytes INTEGER NOT NULL DEFAULT 65507,

    require_registered_port BOOLEAN NOT NULL DEFAULT TRUE,

    allow_udp BOOLEAN NOT NULL DEFAULT TRUE,

    allow_tcp BOOLEAN NOT NULL DEFAULT TRUE,

    maximum_connections INTEGER NOT NULL DEFAULT 1000,

    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_policy_port_range CHECK (
        minimum_port >= 1
        AND maximum_port <= 65535
        AND minimum_port <= maximum_port
    ),

    CONSTRAINT valid_policy_payload CHECK (
        maximum_payload_bytes BETWEEN 1 AND 65507
    ),

    CONSTRAINT valid_maximum_connections CHECK (
        maximum_connections > 0
    )
);

-- ============================================================
-- 10. AUTOMATIC CONNECTION EVENT LOGGING
-- ============================================================

CREATE OR REPLACE FUNCTION log_connection_state()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.state IS DISTINCT FROM OLD.state THEN

        INSERT INTO connection_events (
            connection_id,
            event_type,
            previous_state,
            new_state,
            description
        )
        VALUES (
            NEW.connection_id,

            CASE NEW.state
                WHEN 'SYN_SENT' THEN 'SYN'
                WHEN 'SYN_RECEIVED' THEN 'SYN_ACK'
                WHEN 'ESTABLISHED' THEN 'ACK'
                WHEN 'FIN_WAIT' THEN 'FIN'
                WHEN 'CLOSED' THEN 'CLOSED'
                ELSE 'CREATED'
            END,

            OLD.state,
            NEW.state,

            'Automatic connection state transition'
        );

        IF NEW.state = 'ESTABLISHED'
           AND NEW.established_at IS NULL THEN

            NEW.established_at := NOW();

        END IF;

        IF NEW.state = 'CLOSED'
           AND OLD.state <> 'CLOSED' THEN

            NEW.closed_at := NOW();

        END IF;

    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_connection_state_history
BEFORE UPDATE OF state
ON transport_connections
FOR EACH ROW
EXECUTE FUNCTION log_connection_state();

-- ============================================================
-- 11. FLOW CONTROL VALIDATION
-- ============================================================

CREATE OR REPLACE FUNCTION validate_flow_control()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.connection_id IS NOT NULL
       AND NOT EXISTS (
           SELECT 1
           FROM transport_connections c
           WHERE c.connection_id = NEW.connection_id
             AND c.protocol = 'TCP'
       ) THEN

        RAISE EXCEPTION
            'Flow control requires a TCP connection';
    END IF;

    IF NEW.acknowledged_sequence > NEW.next_sequence THEN
        RAISE EXCEPTION
            'Acknowledgement exceeds transmitted sequence';
    END IF;

    IF NEW.outstanding_bytes > NEW.receive_window THEN
        RAISE EXCEPTION
            'Outstanding bytes exceed receive window';
    END IF;

    NEW.updated_at := NOW();

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_flow_control
BEFORE INSERT OR UPDATE
ON tcp_flow_control
FOR EACH ROW
EXECUTE FUNCTION validate_flow_control();

-- ============================================================
-- 12. CONNECTION CREATION FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION create_tcp_connection(
    p_source BIGINT,
    p_destination BIGINT,
    p_source_port INTEGER,
    p_destination_port INTEGER
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_connection_id BIGINT;
BEGIN
    IF p_source = p_destination THEN
        RAISE EXCEPTION
            'Source and destination devices must differ';
    END IF;

    IF p_source_port NOT BETWEEN 1 AND 65535
       OR p_destination_port NOT BETWEEN 1 AND 65535 THEN

        RAISE EXCEPTION 'Invalid TCP port';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM network_devices
        WHERE device_id = p_source
          AND is_active
    ) THEN

        RAISE EXCEPTION 'Source device is inactive or missing';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM network_devices
        WHERE device_id = p_destination
          AND is_active
    ) THEN

        RAISE EXCEPTION
            'Destination device is inactive or missing';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM port_assignments
        WHERE device_id = p_destination
          AND protocol = 'TCP'
          AND port_number = p_destination_port
          AND status = 'ACTIVE'
    ) THEN

        RAISE EXCEPTION
            'Destination TCP port is not registered';
    END IF;

    INSERT INTO transport_connections (
        source_device_id,
        destination_device_id,
        source_port,
        destination_port,
        protocol,
        state
    )
    VALUES (
        p_source,
        p_destination,
        p_source_port,
        p_destination_port,
        'TCP',
        'SYN_SENT'
    )
    RETURNING connection_id INTO v_connection_id;

    INSERT INTO tcp_flow_control (
        connection_id,
        send_window,
        receive_window,
        congestion_window
    )
    VALUES (
        v_connection_id,
        65535,
        65535,
        65535
    );

    RETURN v_connection_id;
END;
$$;

-- ============================================================
-- 13. CUMULATIVE ACKNOWLEDGEMENT FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION acknowledge_tcp_data(
    p_connection_id BIGINT,
    p_acknowledgement BIGINT
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_next BIGINT;
    v_previous BIGINT;
    v_removed INTEGER;
BEGIN
    SELECT
        next_sequence,
        acknowledged_sequence
    INTO
        v_next,
        v_previous
    FROM tcp_flow_control
    WHERE connection_id = p_connection_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'TCP flow-control record does not exist';
    END IF;

    IF p_acknowledgement < v_previous
       OR p_acknowledgement > v_next THEN

        RAISE EXCEPTION 'Invalid cumulative ACK';
    END IF;

    UPDATE tcp_segments
    SET
        acknowledged = TRUE,
        acknowledged_at = NOW()
    WHERE connection_id = p_connection_id
      AND sequence_number + payload_bytes <= p_acknowledgement
      AND acknowledged = FALSE;

    GET DIAGNOSTICS v_removed = ROW_COUNT;

    UPDATE tcp_flow_control
    SET
        acknowledged_sequence = p_acknowledgement,
        outstanding_bytes = GREATEST(
            0,
            next_sequence - p_acknowledgement
        )
    WHERE connection_id = p_connection_id;

    RETURN v_removed;
END;
$$;

-- ============================================================
-- 14. RECEIVE WINDOW UPDATE FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION update_receive_window(
    p_connection_id BIGINT,
    p_new_window INTEGER
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_new_window NOT BETWEEN 0 AND 65535 THEN
        RAISE EXCEPTION 'Invalid TCP receive window';
    END IF;

    UPDATE tcp_flow_control
    SET receive_window = p_new_window
    WHERE connection_id = p_connection_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'TCP flow-control record not found';
    END IF;
END;
$$;

-- ============================================================
-- 15. SAMPLE DEVICES
-- ============================================================

INSERT INTO network_devices (
    device_name,
    ipv4_address,
    device_role
)
VALUES
    ('Development Client', '192.168.1.10', 'CLIENT'),
    ('Application Server', '192.168.1.20', 'APPLICATION_SERVER'),
    ('DNS Server', '192.168.1.53', 'DNS_SERVER'),
    ('Network Gateway', '192.168.1.1', 'GATEWAY')
ON CONFLICT DO NOTHING;

-- ============================================================
-- 16. SAMPLE PORT ASSIGNMENTS
-- ============================================================

INSERT INTO port_assignments (
    device_id,
    protocol,
    port_number,
    service_name
)
SELECT
    d.device_id,
    p.protocol::transport_protocol,
    p.port_number,
    p.service_name
FROM network_devices d
CROSS JOIN (
    VALUES
        ('TCP', 443, 'HTTPS'),
        ('TCP', 8080, 'Application API'),
        ('UDP', 53, 'DNS')
) AS p(protocol, port_number, service_name)
WHERE
    (d.device_name = 'Application Server'
     AND p.protocol = 'TCP')
    OR
    (d.device_name = 'DNS Server'
     AND p.protocol = 'UDP')
ON CONFLICT DO NOTHING;

-- ============================================================
-- 17. SAMPLE TRANSPORT POLICIES
-- ============================================================

INSERT INTO transport_policies (
    policy_name,
    protocol,
    minimum_port,
    maximum_port,
    maximum_payload_bytes,
    require_registered_port,
    allow_udp,
    allow_tcp,
    maximum_connections
)
VALUES
    (
        'Enterprise HTTPS Policy',
        'TCP',
        443,
        443,
        65535,
        TRUE,
        FALSE,
        TRUE,
        5000
    ),
    (
        'Enterprise DNS Policy',
        'UDP',
        53,
        53,
        1200,
        TRUE,
        TRUE,
        FALSE,
        2000
    )
ON CONFLICT DO NOTHING;

-- ============================================================
-- 18. SAMPLE TCP CONNECTION
-- ============================================================

DO $$
DECLARE
    v_client BIGINT;
    v_server BIGINT;
    v_connection BIGINT;
BEGIN
    SELECT device_id
    INTO v_client
    FROM network_devices
    WHERE device_name = 'Development Client';

    SELECT device_id
    INTO v_server
    FROM network_devices
    WHERE device_name = 'Application Server';

    v_connection := create_tcp_connection(
        v_client,
        v_server,
        52000,
        443
    );

    UPDATE transport_connections
    SET state = 'ESTABLISHED',
        send_sequence = 1000,
        receive_sequence = 1000,
        bytes_sent = 1000
    WHERE connection_id = v_connection;

    UPDATE tcp_flow_control
    SET
        next_sequence = 1000,
        outstanding_bytes = 1000
    WHERE connection_id = v_connection;

    INSERT INTO tcp_segments (
        connection_id,
        sequence_number,
        acknowledgement_number,
        payload_bytes
    )
    VALUES (
        v_connection,
        0,
        0,
        1000
    );

    PERFORM update_receive_window(v_connection, 12000);

    RAISE NOTICE
        'Sample TCP connection created: %',
        v_connection;
END;
$$;

-- ============================================================
-- 19. SAMPLE UDP DATAGRAMS
-- ============================================================

INSERT INTO udp_datagrams (
    source_device_id,
    destination_device_id,
    source_port,
    destination_port,
    payload_bytes,
    checksum_valid,
    received,
    received_at
)
SELECT
    source.device_id,
    destination.device_id,
    53000,
    53,
    128,
    TRUE,
    TRUE,
    NOW()
FROM network_devices source
CROSS JOIN network_devices destination
WHERE source.device_name = 'Development Client'
  AND destination.device_name = 'DNS Server';

INSERT INTO udp_datagrams (
    source_device_id,
    destination_device_id,
    source_port,
    destination_port,
    payload_bytes,
    checksum_valid,
    received
)
SELECT
    source.device_id,
    destination.device_id,
    53001,
    53,
    256,
    FALSE,
    FALSE
FROM network_devices source
CROSS JOIN network_devices destination
WHERE source.device_name = 'Development Client'
  AND destination.device_name = 'DNS Server';

-- ============================================================
-- 20. SAMPLE FAILURE AND EVENT RECORDS
-- ============================================================

INSERT INTO connection_events (
    connection_id,
    event_type,
    description
)
SELECT
    connection_id,
    'DATA',
    'Application payload transmitted successfully'
FROM transport_connections
WHERE state = 'ESTABLISHED';

-- ============================================================
-- 21. CONNECTION RETRIEVAL VIEW
-- ============================================================

CREATE OR REPLACE VIEW v_connection_inventory AS
SELECT
    c.connection_id,
    source.device_name AS source_device,
    destination.device_name AS destination_device,
    c.source_port,
    c.destination_port,
    c.protocol,
    c.state,
    c.bytes_sent,
    c.bytes_received,
    c.created_at,
    c.established_at
FROM transport_connections c
JOIN network_devices source
    ON source.device_id = c.source_device_id
JOIN network_devices destination
    ON destination.device_id = c.destination_device_id;

-- ============================================================
-- 22. FLOW CONTROL MONITORING VIEW
-- ============================================================

CREATE OR REPLACE VIEW v_tcp_flow_monitor AS
SELECT
    c.connection_id,
    source.device_name AS source_device,
    destination.device_name AS destination_device,
    f.send_window,
    f.receive_window,
    f.congestion_window,
    f.outstanding_bytes,
    f.next_sequence,
    f.acknowledged_sequence,
    GREATEST(
        0,
        f.receive_window - f.outstanding_bytes
    ) AS available_receive_window,

    CASE
        WHEN f.receive_window = 0
            THEN 'ZERO_WINDOW'
        WHEN f.outstanding_bytes >= f.receive_window
            THEN 'WINDOW_FULL'
        ELSE 'TRANSMISSION_AVAILABLE'
    END AS flow_status

FROM tcp_flow_control f
JOIN transport_connections c
    ON c.connection_id = f.connection_id
JOIN network_devices source
    ON source.device_id = c.source_device_id
JOIN network_devices destination
    ON destination.device_id = c.destination_device_id;

-- ============================================================
-- 23. TRANSPORT PERFORMANCE REPORT
-- ============================================================

CREATE OR REPLACE VIEW v_transport_performance AS
SELECT
    protocol,
    COUNT(*) AS total_connections,
    COUNT(*) FILTER (
        WHERE state = 'ESTABLISHED'
    ) AS established_connections,
    SUM(bytes_sent) AS total_bytes_sent,
    SUM(bytes_received) AS total_bytes_received,
    AVG(bytes_sent) AS average_bytes_sent
FROM transport_connections
GROUP BY protocol;

-- ============================================================
-- 24. UDP DELIVERY REPORT
-- ============================================================

CREATE OR REPLACE VIEW v_udp_delivery_report AS
SELECT
    COUNT(*) AS total_datagrams,

    COUNT(*) FILTER (
        WHERE received
    ) AS received_datagrams,

    COUNT(*) FILTER (
        WHERE NOT received
    ) AS undelivered_datagrams,

    COUNT(*) FILTER (
        WHERE NOT checksum_valid
    ) AS invalid_checksum_datagrams,

    COALESCE(
        ROUND(
            100.0 * COUNT(*) FILTER (WHERE received)
            / NULLIF(COUNT(*), 0),
            2
        ),
        0
    ) AS delivery_percentage

FROM udp_datagrams;

-- ============================================================
-- 25. PORT ELIGIBILITY QUERY
-- ============================================================

SELECT
    d.device_name,
    p.protocol,
    p.port_number,
    p.service_name,
    p.status,
    CASE
        WHEN p.status = 'ACTIVE'
         AND d.is_active
            THEN 'ELIGIBLE'
        ELSE 'NOT_ELIGIBLE'
    END AS endpoint_status
FROM port_assignments p
JOIN network_devices d
    ON d.device_id = p.device_id
ORDER BY d.device_name, p.port_number;

-- ============================================================
-- 26. TCP CONNECTION REPORT
-- ============================================================

SELECT *
FROM v_connection_inventory
ORDER BY created_at DESC;

-- ============================================================
-- 27. FLOW CONTROL REPORT
-- ============================================================

SELECT *
FROM v_tcp_flow_monitor;

-- ============================================================
-- 28. UDP DELIVERY REPORT
-- ============================================================

SELECT *
FROM v_udp_delivery_report;

-- ============================================================
-- 29. TRANSPORT AGGREGATION
-- ============================================================

SELECT *
FROM v_transport_performance;

-- ============================================================
-- 30. CUMULATIVE ACKNOWLEDGEMENT DEMONSTRATION
-- ============================================================

DO $$
DECLARE
    v_connection BIGINT;
BEGIN
    SELECT connection_id
    INTO v_connection
    FROM transport_connections
    WHERE protocol = 'TCP'
      AND state = 'ESTABLISHED'
    ORDER BY connection_id
    LIMIT 1;

    IF v_connection IS NOT NULL THEN

        PERFORM acknowledge_tcp_data(
            v_connection,
            1000
        );

        RAISE NOTICE
            'Cumulative acknowledgement processed for connection %',
            v_connection;

    END IF;
END;
$$;

-- ============================================================
-- 31. VALIDATION QUERIES
-- ============================================================

-- Connections using unregistered destination ports.
SELECT
    c.connection_id,
    c.destination_port,
    c.protocol
FROM transport_connections c
WHERE NOT EXISTS (
    SELECT 1
    FROM port_assignments p
    WHERE p.device_id = c.destination_device_id
      AND p.port_number = c.destination_port
      AND p.protocol = c.protocol
      AND p.status = 'ACTIVE'
);

-- UDP datagrams with invalid checksums or missing delivery.
SELECT
    datagram_id,
    payload_bytes,
    checksum_valid,
    received
FROM udp_datagrams
WHERE NOT checksum_valid
   OR NOT received;

-- Outstanding TCP segments.
SELECT
    connection_id,
    COUNT(*) AS outstanding_segments,
    SUM(payload_bytes) AS outstanding_bytes
FROM tcp_segments
WHERE NOT acknowledged
GROUP BY connection_id;

-- ============================================================
-- 32. TRANSACTIONAL CONNECTION CLOSURE
-- ============================================================

DO $$
DECLARE
    v_connection BIGINT;
BEGIN
    SELECT connection_id
    INTO v_connection
    FROM transport_connections
    WHERE state = 'ESTABLISHED'
    ORDER BY connection_id
    LIMIT 1;

    IF v_connection IS NOT NULL THEN

        UPDATE transport_connections
        SET state = 'FIN_WAIT'
        WHERE connection_id = v_connection;

        UPDATE transport_connections
        SET state = 'TIME_WAIT'
        WHERE connection_id = v_connection;

        UPDATE transport_connections
        SET state = 'CLOSED'
        WHERE connection_id = v_connection;

    END IF;
END;
$$;

COMMIT;
