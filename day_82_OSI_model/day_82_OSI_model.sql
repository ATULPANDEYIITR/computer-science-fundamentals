-- ============================================================
-- OSI MODEL: RELATIONAL NETWORK MANAGEMENT AND DIAGNOSTICS
-- PostgreSQL 15+
--
-- Models:
-- 1. Seven OSI layers.
-- 2. Network devices and interfaces.
-- 3. Physical and logical connections.
-- 4. Application and transport protocols.
-- 5. Communication sessions.
-- 6. Encapsulation and decapsulation events.
-- 7. Network flows and packet observations.
-- 8. Layer-specific failures.
-- 9. Network diagnostics and reporting.
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS osi_network;

SET search_path TO osi_network, public;

-- ------------------------------------------------------------
-- 1. OSI layer reference data
-- ------------------------------------------------------------

CREATE TABLE osi_layers (
    layer_number SMALLINT PRIMARY KEY,
    layer_name VARCHAR(30) NOT NULL UNIQUE,
    responsibilities TEXT NOT NULL,
    pdu_name VARCHAR(30) NOT NULL,
    CONSTRAINT valid_layer_number
        CHECK (layer_number BETWEEN 1 AND 7)
);

INSERT INTO osi_layers
    (layer_number, layer_name, responsibilities, pdu_name)
VALUES
    (1, 'Physical',
     'Transmission of raw bits through physical media',
     'Bits'),

    (2, 'Data Link',
     'Framing, MAC addressing and link-level error detection',
     'Frame'),

    (3, 'Network',
     'Logical addressing, routing and packet forwarding',
     'Packet'),

    (4, 'Transport',
     'End-to-end delivery, segmentation, reliability and ports',
     'Segment or Datagram'),

    (5, 'Session',
     'Establishment, management and termination of sessions',
     'Data'),

    (6, 'Presentation',
     'Encoding, serialization, compression and encryption',
     'Data'),

    (7, 'Application',
     'Application-level network services and protocols',
     'Data');

-- ------------------------------------------------------------
-- 2. Protocol definitions
-- ------------------------------------------------------------

CREATE TABLE protocols (
    protocol_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    protocol_name VARCHAR(30) NOT NULL UNIQUE,
    layer_number SMALLINT NOT NULL REFERENCES osi_layers(layer_number),
    protocol_category VARCHAR(20) NOT NULL,
    default_port INTEGER,
    description TEXT NOT NULL,

    CONSTRAINT valid_protocol_category
        CHECK (
            protocol_category IN (
                'APPLICATION',
                'TRANSPORT',
                'NETWORK',
                'DATA_LINK',
                'PHYSICAL'
            )
        ),

    CONSTRAINT valid_default_port
        CHECK (
            default_port IS NULL
            OR default_port BETWEEN 1 AND 65535
        )
);

INSERT INTO protocols
    (protocol_name, layer_number, protocol_category,
     default_port, description)
VALUES
    ('HTTP', 7, 'APPLICATION', 80,
     'Hypertext Transfer Protocol'),

    ('HTTPS', 7, 'APPLICATION', 443,
     'HTTP protected by TLS'),

    ('DNS', 7, 'APPLICATION', 53,
     'Domain Name System'),

    ('SSH', 7, 'APPLICATION', 22,
     'Secure Shell'),

    ('TCP', 4, 'TRANSPORT', NULL,
     'Connection-oriented reliable transport'),

    ('UDP', 4, 'TRANSPORT', NULL,
     'Connectionless datagram transport'),

    ('IPv4', 3, 'NETWORK', NULL,
     'Internet Protocol version 4'),

    ('IPv6', 3, 'NETWORK', NULL,
     'Internet Protocol version 6'),

    ('ARP', 2, 'DATA_LINK', NULL,
     'IPv4 address-to-MAC resolution'),

    ('Ethernet', 2, 'DATA_LINK', NULL,
     'Ethernet framing'),

    ('WiFi', 2, 'DATA_LINK', NULL,
     'IEEE 802.11 wireless networking'),

    ('Fiber Optic', 1, 'PHYSICAL', NULL,
     'Optical physical transmission');

-- ------------------------------------------------------------
-- 3. Network devices
-- ------------------------------------------------------------

CREATE TABLE network_devices (
    device_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    hostname VARCHAR(100) NOT NULL UNIQUE,
    device_type VARCHAR(30) NOT NULL,
    vendor VARCHAR(100),
    management_ip INET,
    operational_status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_device_type
        CHECK (
            device_type IN (
                'ROUTER',
                'SWITCH',
                'HOST',
                'SERVER',
                'FIREWALL',
                'ACCESS_POINT'
            )
        ),

    CONSTRAINT valid_device_status
        CHECK (
            operational_status IN (
                'ACTIVE',
                'INACTIVE',
                'MAINTENANCE',
                'FAILED'
            )
        )
);

INSERT INTO network_devices
    (hostname, device_type, vendor, management_ip)
VALUES
    ('router-01', 'ROUTER', 'Cisco', '192.168.1.1'),
    ('switch-01', 'SWITCH', 'Aruba', '192.168.1.2'),
    ('workstation-01', 'HOST', 'Dell', '192.168.1.10'),
    ('server-01', 'SERVER', 'Dell', '192.168.1.20'),
    ('firewall-01', 'FIREWALL', 'Fortinet', '192.168.1.254');

-- ------------------------------------------------------------
-- 4. Network interfaces
-- ------------------------------------------------------------

CREATE TABLE network_interfaces (
    interface_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    device_id BIGINT NOT NULL
        REFERENCES network_devices(device_id),

    interface_name VARCHAR(40) NOT NULL,
    mac_address MACADDR NOT NULL,
    ip_address INET,
    interface_status VARCHAR(20) NOT NULL DEFAULT 'UP',
    mtu INTEGER NOT NULL DEFAULT 1500,
    speed_mbps INTEGER,

    CONSTRAINT unique_device_interface
        UNIQUE (device_id, interface_name),

    CONSTRAINT unique_mac_address
        UNIQUE (mac_address),

    CONSTRAINT valid_interface_status
        CHECK (interface_status IN ('UP', 'DOWN', 'DISABLED')),

    CONSTRAINT valid_mtu
        CHECK (mtu BETWEEN 576 AND 9216),

    CONSTRAINT valid_speed
        CHECK (speed_mbps IS NULL OR speed_mbps > 0),

    CONSTRAINT valid_interface_ip
        CHECK (
            ip_address IS NULL
            OR family(ip_address) IN (4, 6)
        )
);

INSERT INTO network_interfaces
    (device_id, interface_name, mac_address,
     ip_address, mtu, speed_mbps)
SELECT
    d.device_id,
    x.interface_name,
    x.mac_address::MACADDR,
    x.ip_address::INET,
    1500,
    x.speed_mbps
FROM network_devices d
JOIN (
    VALUES
        ('router-01', 'GigabitEthernet0/0',
         '00:11:22:33:44:01', '192.168.1.1', 1000),

        ('switch-01', 'Ethernet1',
         '00:11:22:33:44:02', '192.168.1.2', 1000),

        ('workstation-01', 'Ethernet0',
         '00:11:22:33:44:10', '192.168.1.10', 1000),

        ('server-01', 'Ethernet0',
         '00:11:22:33:44:20', '192.168.1.20', 1000),

        ('firewall-01', 'Ethernet0',
         '00:11:22:33:44:FE', '192.168.1.254', 1000)
) AS x(hostname, interface_name, mac_address, ip_address, speed_mbps)
ON d.hostname = x.hostname;

CREATE INDEX idx_interfaces_ip
ON network_interfaces(ip_address);

CREATE INDEX idx_interfaces_device_status
ON network_interfaces(device_id, interface_status);

-- ------------------------------------------------------------
-- 5. Physical and logical links
-- ------------------------------------------------------------

CREATE TABLE network_links (
    link_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    source_interface_id BIGINT NOT NULL
        REFERENCES network_interfaces(interface_id),

    destination_interface_id BIGINT NOT NULL
        REFERENCES network_interfaces(interface_id),

    link_type VARCHAR(20) NOT NULL,
    bandwidth_mbps INTEGER NOT NULL,
    link_status VARCHAR(20) NOT NULL DEFAULT 'UP',
    latency_ms NUMERIC(10,3) NOT NULL DEFAULT 0,

    CONSTRAINT unique_link
        UNIQUE (source_interface_id, destination_interface_id),

    CONSTRAINT different_link_endpoints
        CHECK (source_interface_id <> destination_interface_id),

    CONSTRAINT valid_link_type
        CHECK (
            link_type IN (
                'ETHERNET',
                'FIBER',
                'WIRELESS',
                'VIRTUAL'
            )
        ),

    CONSTRAINT valid_bandwidth
        CHECK (bandwidth_mbps > 0),

    CONSTRAINT valid_link_status
        CHECK (link_status IN ('UP', 'DOWN', 'DEGRADED')),

    CONSTRAINT valid_latency
        CHECK (latency_ms >= 0)
);

INSERT INTO network_links (
    source_interface_id,
    destination_interface_id,
    link_type,
    bandwidth_mbps,
    latency_ms
)
SELECT
    a.interface_id,
    b.interface_id,
    'ETHERNET',
    1000,
    0.500
FROM network_interfaces a
JOIN network_interfaces b
    ON a.device_id <> b.device_id
JOIN network_devices da
    ON da.device_id = a.device_id
JOIN network_devices db
    ON db.device_id = b.device_id
WHERE da.hostname = 'switch-01'
  AND db.hostname = 'workstation-01';

-- ------------------------------------------------------------
-- 6. Communication sessions
-- ------------------------------------------------------------

CREATE TABLE communication_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    source_interface_id BIGINT NOT NULL
        REFERENCES network_interfaces(interface_id),

    destination_interface_id BIGINT NOT NULL
        REFERENCES network_interfaces(interface_id),

    transport_protocol VARCHAR(10) NOT NULL,
    application_protocol VARCHAR(30) NOT NULL,

    source_port INTEGER NOT NULL,
    destination_port INTEGER NOT NULL,

    session_state VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',

    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMPTZ,

    CONSTRAINT valid_transport
        CHECK (transport_protocol IN ('TCP', 'UDP')),

    CONSTRAINT valid_session_ports
        CHECK (
            source_port BETWEEN 1 AND 65535
            AND destination_port BETWEEN 1 AND 65535
        ),

    CONSTRAINT valid_session_state
        CHECK (
            session_state IN (
                'ACTIVE',
                'ESTABLISHED',
                'CLOSED',
                'FAILED',
                'TIMEOUT'
            )
        ),

    CONSTRAINT valid_session_end
        CHECK (
            ended_at IS NULL
            OR ended_at >= started_at
        )
);

CREATE INDEX idx_sessions_active
ON communication_sessions(started_at)
WHERE session_state IN ('ACTIVE', 'ESTABLISHED');

CREATE INDEX idx_sessions_protocol
ON communication_sessions(
    transport_protocol,
    application_protocol
);

-- ------------------------------------------------------------
-- 7. Communication session sample data
-- ------------------------------------------------------------

INSERT INTO communication_sessions (
    source_interface_id,
    destination_interface_id,
    transport_protocol,
    application_protocol,
    source_port,
    destination_port,
    session_state
)
SELECT
    source.interface_id,
    destination.interface_id,
    'TCP',
    'HTTPS',
    52000,
    443,
    'ESTABLISHED'
FROM network_interfaces source
CROSS JOIN network_interfaces destination
JOIN network_devices source_device
    ON source_device.device_id = source.device_id
JOIN network_devices destination_device
    ON destination_device.device_id = destination.device_id
WHERE source_device.hostname = 'workstation-01'
  AND destination_device.hostname = 'server-01';

INSERT INTO communication_sessions (
    source_interface_id,
    destination_interface_id,
    transport_protocol,
    application_protocol,
    source_port,
    destination_port,
    session_state
)
SELECT
    source.interface_id,
    destination.interface_id,
    'UDP',
    'DNS',
    53000,
    53,
    'CLOSED'
FROM network_interfaces source
CROSS JOIN network_interfaces destination
JOIN network_devices source_device
    ON source_device.device_id = source.device_id
JOIN network_devices destination_device
    ON destination_device.device_id = destination.device_id
WHERE source_device.hostname = 'workstation-01'
  AND destination_device.hostname = 'router-01';

-- ------------------------------------------------------------
-- 8. Packet and encapsulation observations
-- ------------------------------------------------------------

CREATE TABLE packet_observations (
    observation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    session_id UUID NOT NULL
        REFERENCES communication_sessions(session_id),

    layer_number SMALLINT NOT NULL
        REFERENCES osi_layers(layer_number),

    protocol_id BIGINT NOT NULL
        REFERENCES protocols(protocol_id),

    pdu_size_bytes INTEGER NOT NULL,

    direction VARCHAR(20) NOT NULL,

    observation_status VARCHAR(20) NOT NULL DEFAULT 'SUCCESS',

    observed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_pdu_size
        CHECK (pdu_size_bytes >= 0),

    CONSTRAINT valid_observation_direction
        CHECK (direction IN ('OUTBOUND', 'INBOUND')),

    CONSTRAINT valid_observation_status
        CHECK (
            observation_status IN (
                'SUCCESS',
                'FAILED',
                'DROPPED',
                'CORRUPTED'
            )
        )
);

CREATE INDEX idx_observations_session
ON packet_observations(session_id, observed_at);

CREATE INDEX idx_observations_layer_status
ON packet_observations(layer_number, observation_status);

CREATE INDEX idx_observations_time
ON packet_observations(observed_at DESC);

-- ------------------------------------------------------------
-- 9. Layer-specific diagnostic events
-- ------------------------------------------------------------

CREATE TABLE diagnostic_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    session_id UUID
        REFERENCES communication_sessions(session_id),

    layer_number SMALLINT NOT NULL
        REFERENCES osi_layers(layer_number),

    severity VARCHAR(15) NOT NULL,

    event_code VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_severity
        CHECK (
            severity IN (
                'INFO',
                'WARNING',
                'ERROR',
                'CRITICAL'
            )
        )
);

CREATE INDEX idx_diagnostics_layer_time
ON diagnostic_events(layer_number, created_at DESC);

CREATE INDEX idx_diagnostics_severity
ON diagnostic_events(severity, created_at DESC);

-- ------------------------------------------------------------
-- 10. Insert observations for a sample session
-- ------------------------------------------------------------

INSERT INTO packet_observations (
    session_id,
    layer_number,
    protocol_id,
    pdu_size_bytes,
    direction,
    observation_status
)
SELECT
    s.session_id,
    p.layer_number,
    p.protocol_id,
    CASE p.layer_number
        WHEN 1 THEN 128
        WHEN 2 THEN 128
        WHEN 3 THEN 114
        WHEN 4 THEN 94
        ELSE 80
    END,
    'OUTBOUND',
    'SUCCESS'
FROM communication_sessions s
CROSS JOIN protocols p
WHERE s.application_protocol = 'HTTPS'
  AND s.session_state = 'ESTABLISHED'
  AND p.protocol_name IN (
      'HTTP',
      'TCP',
      'IPv4',
      'Ethernet',
      'Fiber Optic'
  );

-- ------------------------------------------------------------
-- 11. Trigger: prevent observations for closed sessions
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_observation_session()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    current_state VARCHAR(20);
BEGIN
    SELECT session_state
    INTO current_state
    FROM communication_sessions
    WHERE session_id = NEW.session_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Communication session does not exist';
    END IF;

    IF current_state NOT IN ('ACTIVE', 'ESTABLISHED') THEN
        RAISE EXCEPTION
            'Cannot record observations for session state %',
            current_state;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_observation_session
BEFORE INSERT OR UPDATE ON packet_observations
FOR EACH ROW
EXECUTE FUNCTION validate_observation_session();

-- ------------------------------------------------------------
-- 12. Function: evaluate session readiness
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION evaluate_session(
    requested_session UUID
)
RETURNS TABLE (
    session_id UUID,
    session_state VARCHAR,
    observations BIGINT,
    failed_observations BIGINT,
    successful_layers BIGINT,
    missing_layers BIGINT,
    eligible BOOLEAN
)
LANGUAGE SQL
STABLE
AS $$
    WITH session_data AS (
        SELECT
            s.session_id,
            s.session_state
        FROM communication_sessions s
        WHERE s.session_id = requested_session
    ),
    observation_data AS (
        SELECT
            COUNT(*) AS total_observations,

            COUNT(*) FILTER (
                WHERE o.observation_status <> 'SUCCESS'
            ) AS failed_observations,

            COUNT(DISTINCT o.layer_number) FILTER (
                WHERE o.observation_status = 'SUCCESS'
            ) AS successful_layers

        FROM packet_observations o
        WHERE o.session_id = requested_session
    )
    SELECT
        sd.session_id,
        sd.session_state,
        od.total_observations,
        od.failed_observations,
        od.successful_layers,
        7 - od.successful_layers,
        (
            sd.session_state = 'ESTABLISHED'
            AND od.failed_observations = 0
            AND od.successful_layers = 7
        )
    FROM session_data sd
    CROSS JOIN observation_data od;
$$;

-- ------------------------------------------------------------
-- 13. Function: terminate a session
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION terminate_session(
    requested_session UUID
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    current_state VARCHAR(20);
BEGIN
    SELECT session_state
    INTO current_state
    FROM communication_sessions
    WHERE session_id = requested_session
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Unknown session: %', requested_session;
    END IF;

    IF current_state NOT IN ('ACTIVE', 'ESTABLISHED') THEN
        RETURN FALSE;
    END IF;

    UPDATE communication_sessions
    SET
        session_state = 'CLOSED',
        ended_at = CURRENT_TIMESTAMP
    WHERE session_id = requested_session;

    RETURN TRUE;
END;
$$;

-- ------------------------------------------------------------
-- 14. View: device and interface inventory
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW device_interface_inventory AS
SELECT
    d.hostname,
    d.device_type,
    d.operational_status AS device_status,
    i.interface_name,
    i.mac_address,
    i.ip_address,
    i.interface_status,
    i.mtu,
    i.speed_mbps
FROM network_devices d
JOIN network_interfaces i
    ON i.device_id = d.device_id;

-- ------------------------------------------------------------
-- 15. View: network session report
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW network_session_report AS
SELECT
    s.session_id,
    source_device.hostname AS source_device,
    destination_device.hostname AS destination_device,
    s.transport_protocol,
    s.application_protocol,
    s.source_port,
    s.destination_port,
    s.session_state,
    s.started_at,
    s.ended_at
FROM communication_sessions s
JOIN network_interfaces source_interface
    ON source_interface.interface_id = s.source_interface_id
JOIN network_devices source_device
    ON source_device.device_id = source_interface.device_id
JOIN network_interfaces destination_interface
    ON destination_interface.interface_id = s.destination_interface_id
JOIN network_devices destination_device
    ON destination_device.device_id = destination_interface.device_id;

-- ------------------------------------------------------------
-- 16. Retrieval query
-- ------------------------------------------------------------

SELECT *
FROM device_interface_inventory
ORDER BY hostname, interface_name;

SELECT *
FROM network_session_report
ORDER BY started_at DESC;

-- ------------------------------------------------------------
-- 17. Aggregation: protocol usage
-- ------------------------------------------------------------

SELECT
    transport_protocol,
    application_protocol,
    session_state,
    COUNT(*) AS session_count
FROM communication_sessions
GROUP BY
    transport_protocol,
    application_protocol,
    session_state
ORDER BY session_count DESC;

-- ------------------------------------------------------------
-- 18. Aggregation: layer-level processing results
-- ------------------------------------------------------------

SELECT
    l.layer_number,
    l.layer_name,
    COUNT(o.observation_id) AS total_observations,

    COUNT(*) FILTER (
        WHERE o.observation_status = 'SUCCESS'
    ) AS successful_observations,

    COUNT(*) FILTER (
        WHERE o.observation_status <> 'SUCCESS'
    ) AS failed_observations

FROM osi_layers l
LEFT JOIN packet_observations o
    ON o.layer_number = l.layer_number

GROUP BY l.layer_number, l.layer_name
ORDER BY l.layer_number;

-- ------------------------------------------------------------
-- 19. CTE: identify incomplete layer coverage
-- ------------------------------------------------------------

WITH required_layers AS (
    SELECT layer_number
    FROM osi_layers
),
session_coverage AS (
    SELECT
        s.session_id,
        s.session_state,
        COUNT(DISTINCT o.layer_number) FILTER (
            WHERE o.observation_status = 'SUCCESS'
        ) AS covered_layers
    FROM communication_sessions s
    LEFT JOIN packet_observations o
        ON o.session_id = s.session_id
    GROUP BY s.session_id, s.session_state
)
SELECT
    session_id,
    session_state,
    covered_layers,
    7 - covered_layers AS missing_layers
FROM session_coverage
WHERE covered_layers < (
    SELECT COUNT(*) FROM required_layers
)
ORDER BY missing_layers DESC;

-- ------------------------------------------------------------
-- 20. Evaluation: individual session eligibility
-- ------------------------------------------------------------

SELECT *
FROM evaluate_session(
    (
        SELECT session_id
        FROM communication_sessions
        WHERE application_protocol = 'HTTPS'
        ORDER BY started_at
        LIMIT 1
    )
);

-- ------------------------------------------------------------
-- 21. Diagnostic reporting
-- ------------------------------------------------------------

SELECT
    l.layer_name,
    d.severity,
    d.event_code,
    d.description,
    d.created_at
FROM diagnostic_events d
JOIN osi_layers l
    ON l.layer_number = d.layer_number
ORDER BY d.created_at DESC;

-- ------------------------------------------------------------
-- 22. Demonstrate a recorded failure
-- ------------------------------------------------------------

INSERT INTO diagnostic_events (
    session_id,
    layer_number,
    severity,
    event_code,
    description
)
SELECT
    session_id,
    3,
    'ERROR',
    'TTL_EXPIRED',
    'Packet discarded because its IPv4 TTL expired'
FROM communication_sessions
WHERE application_protocol = 'HTTPS'
LIMIT 1;

-- ------------------------------------------------------------
-- 23. Demonstrate a transactional session closure
-- ------------------------------------------------------------

SAVEPOINT before_session_closure;

SELECT terminate_session(session_id)
FROM communication_sessions
WHERE application_protocol = 'DNS'
  AND session_state = 'CLOSED';

-- The function returns FALSE for an already closed session.
-- This operation is intentionally non-destructive.

RELEASE SAVEPOINT before_session_closure;

-- ------------------------------------------------------------
-- 24. Network link health
-- ------------------------------------------------------------

SELECT
    source_device.hostname AS source_device,
    source_interface.interface_name AS source_interface,
    destination_device.hostname AS destination_device,
    destination_interface.interface_name AS destination_interface,
    link.link_type,
    link.bandwidth_mbps,
    link.latency_ms,
    link.link_status
FROM network_links link
JOIN network_interfaces source_interface
    ON source_interface.interface_id = link.source_interface_id
JOIN network_devices source_device
    ON source_device.device_id = source_interface.device_id
JOIN network_interfaces destination_interface
    ON destination_interface.interface_id =
       link.destination_interface_id
JOIN network_devices destination_device
    ON destination_device.device_id = destination_interface.device_id;

-- ------------------------------------------------------------
-- 25. Layer-specific troubleshooting query
-- ------------------------------------------------------------

SELECT
    l.layer_number,
    l.layer_name,
    COUNT(d.event_id) AS event_count,

    COUNT(d.event_id) FILTER (
        WHERE d.severity IN ('ERROR', 'CRITICAL')
    ) AS critical_or_error_count

FROM osi_layers l
LEFT JOIN diagnostic_events d
    ON d.layer_number = l.layer_number

GROUP BY l.layer_number, l.layer_name
ORDER BY critical_or_error_count DESC, l.layer_number;

-- ------------------------------------------------------------
-- 26. Demonstrate constraint validation
-- ------------------------------------------------------------

DO $$
BEGIN
    BEGIN
        INSERT INTO network_interfaces (
            device_id,
            interface_name,
            mac_address,
            interface_status,
            mtu
        )
        SELECT
            device_id,
            'INVALID-MTU',
            '00:00:00:00:00:99'::MACADDR,
            'UP',
            100
        FROM network_devices
        WHERE hostname = 'server-01';

        RAISE EXCEPTION
            'Expected MTU validation to reject invalid input';

    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'Expected validation succeeded: invalid MTU rejected';
    END;
END;
$$;

-- ------------------------------------------------------------
-- 27. Operational performance indexes
-- ------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_devices_operational_status
ON network_devices(operational_status);

CREATE INDEX IF NOT EXISTS idx_diagnostics_session
ON diagnostic_events(session_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_links_status
ON network_links(link_status);

-- ------------------------------------------------------------
-- 28. Final operational report
-- ------------------------------------------------------------

SELECT
    (SELECT COUNT(*) FROM network_devices) AS devices,
    (SELECT COUNT(*) FROM network_interfaces) AS interfaces,
    (SELECT COUNT(*) FROM network_links) AS links,
    (SELECT COUNT(*) FROM communication_sessions) AS sessions,
    (SELECT COUNT(*) FROM packet_observations) AS observations,
    (SELECT COUNT(*) FROM diagnostic_events) AS diagnostics;

COMMIT;
