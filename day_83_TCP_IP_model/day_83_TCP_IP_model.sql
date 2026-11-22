/*
===============================================================================
TCP/IP MODEL: NETWORK ARCHITECTURE AND PROTOCOL INTERACTION
PostgreSQL 15+

Relational model for:
- TCP/IP layers
- Application protocols
- Network interfaces
- IPv4 addresses and subnets
- Transport endpoints
- TCP connections and state transitions
- UDP datagrams
- IP packets
- Routers and routing tables
- Ethernet frames
- Packet forwarding
- Network diagnostics
- DNS records and TTL
- Network performance monitoring

The database models network operations and telemetry.
It does not implement a physical TCP/IP protocol stack.
===============================================================================
*/

-- ============================================================================
-- 1. SCHEMA
-- ============================================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS tcpip;

SET search_path TO tcpip, public;

-- ============================================================================
-- 2. ENUMERATIONS
-- ============================================================================

CREATE TYPE network_layer AS ENUM (
    'APPLICATION',
    'TRANSPORT',
    'INTERNET',
    'NETWORK_ACCESS'
);

CREATE TYPE transport_protocol AS ENUM (
    'TCP',
    'UDP',
    'ICMP'
);

CREATE TYPE connection_state AS ENUM (
    'CLOSED',
    'LISTEN',
    'SYN_SENT',
    'SYN_RECEIVED',
    'ESTABLISHED',
    'FIN_WAIT',
    'TIME_WAIT',
    'RESET'
);

CREATE TYPE packet_status AS ENUM (
    'CREATED',
    'TRANSMITTED',
    'FORWARDED',
    'DELIVERED',
    'DROPPED'
);

CREATE TYPE diagnostic_status AS ENUM (
    'PASS',
    'FAIL',
    'WARNING'
);

-- ============================================================================
-- 3. TCP/IP LAYER DEFINITIONS
-- ============================================================================

CREATE TABLE protocol_layers (
    layer_id SMALLINT PRIMARY KEY,
    layer_name VARCHAR(40) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    responsibilities TEXT NOT NULL,

    CHECK (layer_id BETWEEN 1 AND 4)
);

INSERT INTO protocol_layers VALUES
(
    4,
    'APPLICATION',
    'Provides network services to applications.',
    'HTTP, HTTPS, DNS, DHCP, SMTP and application data exchange.'
),
(
    3,
    'TRANSPORT',
    'Provides process-to-process communication.',
    'TCP, UDP, ports, segmentation, reliability and flow control.'
),
(
    2,
    'INTERNET',
    'Provides logical addressing and packet routing.',
    'IPv4, ICMP, routing, forwarding and TTL.'
),
(
    1,
    'NETWORK_ACCESS',
    'Provides access to the local transmission medium.',
    'Ethernet, MAC addressing, framing and physical transmission.'
);

-- ============================================================================
-- 4. PROTOCOL REGISTRY
-- ============================================================================

CREATE TABLE protocols (
    protocol_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    protocol_name VARCHAR(30) NOT NULL UNIQUE,

    layer_id SMALLINT NOT NULL
        REFERENCES protocol_layers(layer_id),

    protocol_number SMALLINT,

    default_port INTEGER,

    description TEXT NOT NULL,

    CHECK (
        protocol_number IS NULL OR
        protocol_number BETWEEN 0 AND 255
    ),

    CHECK (
        default_port IS NULL OR
        default_port BETWEEN 1 AND 65535
    )
);

INSERT INTO protocols (
    protocol_name,
    layer_id,
    protocol_number,
    default_port,
    description
)
VALUES
('HTTP', 4, NULL, 80, 'Hypertext Transfer Protocol'),
('HTTPS', 4, NULL, 443, 'HTTP over TLS'),
('DNS', 4, NULL, 53, 'Domain Name System'),
('DHCP', 4, NULL, 67, 'Dynamic Host Configuration Protocol'),
('TCP', 3, 6, NULL, 'Transmission Control Protocol'),
('UDP', 3, 17, NULL, 'User Datagram Protocol'),
('ICMP', 2, 1, NULL, 'Internet Control Message Protocol'),
('IPv4', 2, 4, NULL, 'Internet Protocol version 4'),
('ETHERNET', 1, NULL, NULL, 'Ethernet framing');

-- ============================================================================
-- 5. NETWORK DEVICES
-- ============================================================================

CREATE TABLE network_devices (
    device_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    hostname VARCHAR(100) NOT NULL UNIQUE,

    device_type VARCHAR(30) NOT NULL,

    operating_status BOOLEAN NOT NULL DEFAULT TRUE,

    management_address INET,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        device_type IN (
            'HOST',
            'ROUTER',
            'SWITCH',
            'SERVER',
            'FIREWALL'
        )
    ),

    CHECK (
        management_address IS NULL OR
        family(management_address) = 4
    )
);

INSERT INTO network_devices (
    hostname,
    device_type,
    management_address
)
VALUES
('CLIENT-01', 'HOST', '192.168.1.10'),
('SERVER-01', 'SERVER', '203.0.113.20'),
('ROUTER-01', 'ROUTER', '192.168.1.1'),
('DNS-01', 'SERVER', '192.168.1.53'),
('FIREWALL-01', 'FIREWALL', '192.168.1.254');

-- ============================================================================
-- 6. NETWORK INTERFACES
-- ============================================================================

CREATE TABLE network_interfaces (
    interface_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    device_id BIGINT NOT NULL
        REFERENCES network_devices(device_id),

    interface_name VARCHAR(40) NOT NULL,

    mac_address MACADDR NOT NULL,

    mtu INTEGER NOT NULL DEFAULT 1500,

    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    UNIQUE (device_id, interface_name),

    UNIQUE (mac_address),

    CHECK (mtu BETWEEN 576 AND 65535)
);

INSERT INTO network_interfaces (
    device_id,
    interface_name,
    mac_address,
    mtu
)
SELECT
    device_id,
    'eth0',
    CASE hostname
        WHEN 'CLIENT-01' THEN '02:00:00:00:00:01'
        WHEN 'SERVER-01' THEN '02:00:00:00:00:02'
        WHEN 'ROUTER-01' THEN '02:00:00:00:00:03'
        WHEN 'DNS-01' THEN '02:00:00:00:00:04'
        ELSE '02:00:00:00:00:05'
    END::MACADDR,
    1500
FROM network_devices;

-- ============================================================================
-- 7. IP ADDRESS ASSIGNMENTS
-- ============================================================================

CREATE TABLE ip_assignments (
    assignment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    interface_id BIGINT NOT NULL
        REFERENCES network_interfaces(interface_id),

    ip_address INET NOT NULL,

    subnet_prefix SMALLINT NOT NULL,

    is_primary BOOLEAN NOT NULL DEFAULT TRUE,

    assigned_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (interface_id, ip_address),

    CHECK (family(ip_address) = 4),

    CHECK (subnet_prefix BETWEEN 0 AND 32)
);

INSERT INTO ip_assignments (
    interface_id,
    ip_address,
    subnet_prefix
)
SELECT
    ni.interface_id,
    nd.management_address,
    24
FROM network_interfaces ni
JOIN network_devices nd
    ON nd.device_id = ni.device_id
WHERE nd.management_address IS NOT NULL;

CREATE INDEX idx_ip_assignments_address
ON ip_assignments USING HASH (ip_address);

CREATE INDEX idx_ip_assignments_network
ON ip_assignments (
    ((network(ip_address, subnet_prefix)))
);

-- ============================================================================
-- 8. TRANSPORT ENDPOINTS
-- ============================================================================

CREATE TABLE transport_endpoints (
    endpoint_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    device_id BIGINT NOT NULL
        REFERENCES network_devices(device_id),

    ip_address INET NOT NULL,

    port INTEGER NOT NULL,

    protocol_id BIGINT NOT NULL
        REFERENCES protocols(protocol_id),

    service_name VARCHAR(100),

    listening BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (family(ip_address) = 4),

    CHECK (port BETWEEN 1 AND 65535)
);

INSERT INTO transport_endpoints (
    device_id,
    ip_address,
    port,
    protocol_id,
    service_name
)
SELECT
    nd.device_id,
    nd.management_address,
    service.port,
    p.protocol_id,
    service.service_name
FROM (
    VALUES
        ('CLIENT-01', 50000, 'TCP', 'Client ephemeral endpoint'),
        ('SERVER-01', 443, 'TCP', 'HTTPS service'),
        ('DNS-01', 53, 'UDP', 'DNS service'),
        ('DNS-01', 53, 'TCP', 'DNS reliable transport')
) AS service(hostname, port, protocol_name, service_name)
JOIN network_devices nd
    ON nd.hostname = service.hostname
JOIN protocols p
    ON p.protocol_name = service.protocol_name;

CREATE INDEX idx_transport_lookup
ON transport_endpoints (
    ip_address,
    port,
    protocol_id
);

-- ============================================================================
-- 9. TCP CONNECTIONS
-- ============================================================================

CREATE TABLE tcp_connections (
    connection_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    source_endpoint BIGINT NOT NULL
        REFERENCES transport_endpoints(endpoint_id),

    destination_endpoint BIGINT NOT NULL
        REFERENCES transport_endpoints(endpoint_id),

    source_sequence BIGINT NOT NULL DEFAULT 1000,

    destination_sequence BIGINT NOT NULL DEFAULT 2000,

    state connection_state NOT NULL DEFAULT 'CLOSED',

    opened_at TIMESTAMPTZ,

    closed_at TIMESTAMPTZ,

    CHECK (source_sequence >= 0),

    CHECK (destination_sequence >= 0),

    CHECK (source_endpoint <> destination_endpoint),

    CHECK (
        closed_at IS NULL OR
        opened_at IS NULL OR
        closed_at >= opened_at
    )
);

CREATE INDEX idx_tcp_connections_state
ON tcp_connections(state);

-- ============================================================================
-- 10. TCP STATE TRANSITION HISTORY
-- ============================================================================

CREATE TABLE tcp_state_history (
    history_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    connection_id BIGINT NOT NULL
        REFERENCES tcp_connections(connection_id),

    previous_state connection_state NOT NULL,

    next_state connection_state NOT NULL,

    event_description TEXT NOT NULL,

    occurred_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 11. TCP CONNECTION VALIDATION TRIGGER
-- ============================================================================

CREATE OR REPLACE FUNCTION validate_tcp_state_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    valid_transition BOOLEAN;
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.state NOT IN ('CLOSED', 'LISTEN') THEN
            RAISE EXCEPTION
                'New TCP connections must start CLOSED or LISTEN';
        END IF;

        RETURN NEW;
    END IF;

    IF OLD.state = NEW.state THEN
        RETURN NEW;
    END IF;

    valid_transition := CASE OLD.state
        WHEN 'CLOSED' THEN
            NEW.state IN ('LISTEN', 'SYN_SENT')

        WHEN 'LISTEN' THEN
            NEW.state IN ('SYN_RECEIVED', 'CLOSED')

        WHEN 'SYN_SENT' THEN
            NEW.state IN ('ESTABLISHED', 'CLOSED', 'RESET')

        WHEN 'SYN_RECEIVED' THEN
            NEW.state IN ('ESTABLISHED', 'CLOSED', 'RESET')

        WHEN 'ESTABLISHED' THEN
            NEW.state IN ('FIN_WAIT', 'RESET')

        WHEN 'FIN_WAIT' THEN
            NEW.state IN ('TIME_WAIT', 'CLOSED', 'RESET')

        WHEN 'TIME_WAIT' THEN
            NEW.state IN ('CLOSED', 'RESET')

        WHEN 'RESET' THEN
            NEW.state = 'CLOSED'

        ELSE FALSE
    END;

    IF NOT valid_transition THEN
        RAISE EXCEPTION
            'Invalid TCP state transition: % -> %',
            OLD.state,
            NEW.state;
    END IF;

    INSERT INTO tcp_state_history (
        connection_id,
        previous_state,
        next_state,
        event_description
    )
    VALUES (
        OLD.connection_id,
        OLD.state,
        NEW.state,
        'TCP connection state transition'
    );

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_tcp_state_transition
BEFORE INSERT OR UPDATE OF state
ON tcp_connections
FOR EACH ROW
EXECUTE FUNCTION validate_tcp_state_transition();

-- ============================================================================
-- 12. UDP DATAGRAMS
-- ============================================================================

CREATE TABLE udp_datagrams (
    datagram_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    source_endpoint BIGINT NOT NULL
        REFERENCES transport_endpoints(endpoint_id),

    destination_endpoint BIGINT NOT NULL
        REFERENCES transport_endpoints(endpoint_id),

    payload_size INTEGER NOT NULL,

    received BOOLEAN NOT NULL DEFAULT FALSE,

    transmitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (payload_size BETWEEN 0 AND 65507)
);

-- ============================================================================
-- 13. ROUTERS AND ROUTING TABLES
-- ============================================================================

CREATE TABLE routing_entries (
    route_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    router_id BIGINT NOT NULL
        REFERENCES network_devices(device_id),

    destination_network CIDR NOT NULL,

    next_hop INET NOT NULL,

    interface_id BIGINT NOT NULL
        REFERENCES network_interfaces(interface_id),

    metric INTEGER NOT NULL DEFAULT 1,

    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (family(next_hop) = 4),

    CHECK (metric >= 0),

    UNIQUE (
        router_id,
        destination_network,
        next_hop,
        interface_id
    )
);

INSERT INTO routing_entries (
    router_id,
    destination_network,
    next_hop,
    interface_id,
    metric
)
SELECT
    router.device_id,
    route.destination_network::CIDR,
    route.next_hop::INET,
    ni.interface_id,
    route.metric
FROM (
    VALUES
        ('ROUTER-01', '203.0.113.0/24', '192.168.1.1', 'eth0', 1),
        ('ROUTER-01', '0.0.0.0/0', '192.168.1.254', 'eth0', 10)
) AS route(
    hostname,
    destination_network,
    next_hop,
    interface_name,
    metric
)
JOIN network_devices router
    ON router.hostname = route.hostname
JOIN network_interfaces ni
    ON ni.device_id = router.device_id
   AND ni.interface_name = route.interface_name;

CREATE INDEX idx_routing_active
ON routing_entries (
    router_id,
    active,
    metric
);

-- ============================================================================
-- 14. IPV4 PACKETS
-- ============================================================================

CREATE TABLE ip_packets (
    packet_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    source_ip INET NOT NULL,

    destination_ip INET NOT NULL,

    protocol_number SMALLINT NOT NULL,

    ttl SMALLINT NOT NULL DEFAULT 64,

    identification INTEGER NOT NULL DEFAULT 1,

    packet_length INTEGER NOT NULL,

    status packet_status NOT NULL DEFAULT 'CREATED',

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (family(source_ip) = 4),

    CHECK (family(destination_ip) = 4),

    CHECK (protocol_number BETWEEN 0 AND 255),

    CHECK (ttl BETWEEN 1 AND 255),

    CHECK (identification BETWEEN 0 AND 65535),

    CHECK (packet_length BETWEEN 20 AND 65535)
);

CREATE INDEX idx_ip_packets_destination
ON ip_packets(destination_ip);

CREATE INDEX idx_ip_packets_status_time
ON ip_packets(status, created_at DESC);

-- ============================================================================
-- 15. PACKET FORWARDING HISTORY
-- ============================================================================

CREATE TABLE packet_forwarding (
    forwarding_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    packet_id BIGINT NOT NULL
        REFERENCES ip_packets(packet_id),

    route_id BIGINT
        REFERENCES routing_entries(route_id),

    router_id BIGINT NOT NULL
        REFERENCES network_devices(device_id),

    incoming_ttl SMALLINT NOT NULL,

    outgoing_ttl SMALLINT,

    forwarding_status packet_status NOT NULL,

    failure_reason TEXT,

    forwarded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (incoming_ttl BETWEEN 1 AND 255),

    CHECK (
        outgoing_ttl IS NULL OR
        outgoing_ttl BETWEEN 1 AND 255
    ),

    CHECK (
        (forwarding_status = 'DROPPED'
            AND failure_reason IS NOT NULL)
        OR
        (forwarding_status <> 'DROPPED')
    )
);

-- ============================================================================
-- 16. ROUTE LOOKUP FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION find_best_route(
    p_router_id BIGINT,
    p_destination INET
)
RETURNS TABLE (
    selected_route_id BIGINT,
    destination_network CIDR,
    next_hop INET,
    interface_name VARCHAR,
    route_metric INTEGER
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        r.route_id,
        r.destination_network,
        r.next_hop,
        ni.interface_name,
        r.metric
    FROM routing_entries r
    JOIN network_interfaces ni
        ON ni.interface_id = r.interface_id
    WHERE r.router_id = p_router_id
      AND r.active = TRUE
      AND p_destination <<= r.destination_network
    ORDER BY
        masklen(r.destination_network) DESC,
        r.metric ASC
    LIMIT 1;
$$;

-- ============================================================================
-- 17. PACKET FORWARDING PROCEDURE
-- ============================================================================

CREATE OR REPLACE PROCEDURE forward_ip_packet(
    p_packet_id BIGINT,
    p_router_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    packet_record ip_packets%ROWTYPE;
    route_record RECORD;
    new_ttl SMALLINT;
BEGIN
    SELECT *
    INTO packet_record
    FROM ip_packets
    WHERE packet_id = p_packet_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Packet % does not exist', p_packet_id;
    END IF;

    IF packet_record.status IN ('DROPPED', 'DELIVERED') THEN
        RAISE EXCEPTION
            'Packet is already in terminal state: %',
            packet_record.status;
    END IF;

    SELECT *
    INTO route_record
    FROM find_best_route(
        p_router_id,
        packet_record.destination_ip
    );

    IF NOT FOUND THEN
        INSERT INTO packet_forwarding (
            packet_id,
            router_id,
            incoming_ttl,
            forwarding_status,
            failure_reason
        )
        VALUES (
            p_packet_id,
            p_router_id,
            packet_record.ttl,
            'DROPPED',
            'No matching routing entry'
        );

        UPDATE ip_packets
        SET status = 'DROPPED'
        WHERE packet_id = p_packet_id;

        RETURN;
    END IF;

    IF packet_record.ttl <= 1 THEN
        INSERT INTO packet_forwarding (
            packet_id,
            route_id,
            router_id,
            incoming_ttl,
            forwarding_status,
            failure_reason
        )
        VALUES (
            p_packet_id,
            route_record.selected_route_id,
            p_router_id,
            packet_record.ttl,
            'DROPPED',
            'TTL expired'
        );

        UPDATE ip_packets
        SET status = 'DROPPED'
        WHERE packet_id = p_packet_id;

        RETURN;
    END IF;

    new_ttl := packet_record.ttl - 1;

    INSERT INTO packet_forwarding (
        packet_id,
        route_id,
        router_id,
        incoming_ttl,
        outgoing_ttl,
        forwarding_status
    )
    VALUES (
        p_packet_id,
        route_record.selected_route_id,
        p_router_id,
        packet_record.ttl,
        new_ttl,
        'FORWARDED'
    );

    UPDATE ip_packets
    SET ttl = new_ttl,
        status = 'FORWARDED'
    WHERE packet_id = p_packet_id;
END;
$$;

-- ============================================================================
-- 18. ETHERNET FRAMES
-- ============================================================================

CREATE TABLE ethernet_frames (
    frame_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    interface_id BIGINT NOT NULL
        REFERENCES network_interfaces(interface_id),

    source_mac MACADDR NOT NULL,

    destination_mac MACADDR NOT NULL,

    ether_type INTEGER NOT NULL DEFAULT 2048,

    payload_length INTEGER NOT NULL,

    packet_id BIGINT
        REFERENCES ip_packets(packet_id),

    transmitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (ether_type BETWEEN 0 AND 65535),

    CHECK (payload_length BETWEEN 0 AND 1500)
);

CREATE INDEX idx_ethernet_frame_packet
ON ethernet_frames(packet_id);

-- ============================================================================
-- 19. DNS RECORDS
-- ============================================================================

CREATE TABLE dns_records (
    dns_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    domain_name VARCHAR(253) NOT NULL,

    record_type VARCHAR(10) NOT NULL DEFAULT 'A',

    ip_address INET NOT NULL,

    ttl_seconds INTEGER NOT NULL DEFAULT 300,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    expires_at TIMESTAMPTZ GENERATED ALWAYS AS (
        created_at + ttl_seconds * INTERVAL '1 second'
    ) STORED,

    CHECK (record_type = 'A'),

    CHECK (family(ip_address) = 4),

    CHECK (ttl_seconds > 0),

    UNIQUE (domain_name, record_type, ip_address)
);

INSERT INTO dns_records (
    domain_name,
    ip_address,
    ttl_seconds
)
VALUES
('example.com', '93.184.216.34', 300),
('internal.example.com', '192.168.1.53', 120);

CREATE INDEX idx_dns_domain
ON dns_records(domain_name, record_type);

CREATE INDEX idx_dns_expiry
ON dns_records(expires_at);

-- ============================================================================
-- 20. NETWORK DIAGNOSTICS
-- ============================================================================

CREATE TABLE network_diagnostics (
    diagnostic_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    device_id BIGINT NOT NULL
        REFERENCES network_devices(device_id),

    component VARCHAR(60) NOT NULL,

    status diagnostic_status NOT NULL,

    diagnostic_message TEXT NOT NULL,

    measured_value NUMERIC(14, 4),

    measured_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_diagnostics_device_time
ON network_diagnostics(device_id, measured_at DESC);

INSERT INTO network_diagnostics (
    device_id,
    component,
    status,
    diagnostic_message,
    measured_value
)
SELECT
    device_id,
    'INTERFACE_MTU',
    'PASS',
    'Interface MTU is within supported configuration',
    1500
FROM network_devices
WHERE hostname = 'CLIENT-01';

-- ============================================================================
-- 21. NETWORK PERFORMANCE METRICS
-- ============================================================================

CREATE TABLE network_metrics (
    metric_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    device_id BIGINT NOT NULL
        REFERENCES network_devices(device_id),

    bytes_sent BIGINT NOT NULL DEFAULT 0,

    bytes_received BIGINT NOT NULL DEFAULT 0,

    packets_sent BIGINT NOT NULL DEFAULT 0,

    packets_received BIGINT NOT NULL DEFAULT 0,

    packets_dropped BIGINT NOT NULL DEFAULT 0,

    latency_ms NUMERIC(12, 4),

    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (bytes_sent >= 0),

    CHECK (bytes_received >= 0),

    CHECK (packets_sent >= 0),

    CHECK (packets_received >= 0),

    CHECK (packets_dropped >= 0),

    CHECK (latency_ms IS NULL OR latency_ms >= 0)
);

CREATE INDEX idx_network_metrics_device_time
ON network_metrics(device_id, recorded_at DESC);

-- ============================================================================
-- 22. SAMPLE TCP CONNECTION
-- ============================================================================

INSERT INTO tcp_connections (
    source_endpoint,
    destination_endpoint,
    source_sequence,
    destination_sequence,
    state,
    opened_at
)
SELECT
    source.endpoint_id,
    destination.endpoint_id,
    1000,
    2000,
    'CLOSED',
    CURRENT_TIMESTAMP
FROM transport_endpoints source
JOIN network_devices source_device
    ON source_device.device_id = source.device_id
JOIN transport_endpoints destination
    ON destination.port = 443
JOIN network_devices destination_device
    ON destination_device.device_id = destination.device_id
WHERE source_device.hostname = 'CLIENT-01'
  AND source.port = 50000
  AND destination_device.hostname = 'SERVER-01'
  AND destination.protocol_id = (
      SELECT protocol_id
      FROM protocols
      WHERE protocol_name = 'TCP'
  );

-- ============================================================================
-- 23. SAMPLE UDP DATAGRAM
-- ============================================================================

INSERT INTO udp_datagrams (
    source_endpoint,
    destination_endpoint,
    payload_size
)
SELECT
    source.endpoint_id,
    destination.endpoint_id,
    64
FROM transport_endpoints source
JOIN network_devices source_device
    ON source_device.device_id = source.device_id
JOIN transport_endpoints destination
    ON destination.port = 53
JOIN network_devices destination_device
    ON destination_device.device_id = destination.device_id
JOIN protocols udp
    ON udp.protocol_id = destination.protocol_id
WHERE source_device.hostname = 'CLIENT-01'
  AND source.port = 50000
  AND destination_device.hostname = 'DNS-01'
  AND udp.protocol_name = 'UDP'
LIMIT 1;

-- ============================================================================
-- 24. SAMPLE IP PACKETS
-- ============================================================================

INSERT INTO ip_packets (
    source_ip,
    destination_ip,
    protocol_number,
    ttl,
    identification,
    packet_length
)
VALUES
(
    '192.168.1.10',
    '203.0.113.20',
    6,
    64,
    100,
    500
),
(
    '192.168.1.10',
    '203.0.113.99',
    17,
    1,
    101,
    200
),
(
    '192.168.1.10',
    '198.51.100.20',
    6,
    64,
    102,
    800
);

-- ============================================================================
-- 25. PACKET FORWARDING TRANSACTION
-- ============================================================================

DO $$
DECLARE
    packet_id_value BIGINT;
    router_id_value BIGINT;
BEGIN
    SELECT device_id
    INTO router_id_value
    FROM network_devices
    WHERE hostname = 'ROUTER-01';

    FOR packet_id_value IN
        SELECT packet_id
        FROM ip_packets
        WHERE status = 'CREATED'
        ORDER BY packet_id
    LOOP
        CALL forward_ip_packet(
            packet_id_value,
            router_id_value
        );
    END LOOP;
END;
$$;

-- ============================================================================
-- 26. TCP HANDSHAKE AND TERMINATION
-- ============================================================================

UPDATE tcp_connections
SET state = 'SYN_SENT'
WHERE state = 'CLOSED';

UPDATE tcp_connections
SET state = 'ESTABLISHED'
WHERE state = 'SYN_SENT';

UPDATE tcp_connections
SET state = 'FIN_WAIT',
    closed_at = CURRENT_TIMESTAMP
WHERE state = 'ESTABLISHED';

UPDATE tcp_connections
SET state = 'TIME_WAIT'
WHERE state = 'FIN_WAIT';

UPDATE tcp_connections
SET state = 'CLOSED'
WHERE state = 'TIME_WAIT';

-- ============================================================================
-- 27. VIEWS
-- ============================================================================

CREATE VIEW v_protocol_architecture AS
SELECT
    l.layer_id,
    l.layer_name,
    p.protocol_name,
    p.protocol_number,
    p.default_port,
    p.description
FROM protocol_layers l
LEFT JOIN protocols p
    ON p.layer_id = l.layer_id
ORDER BY l.layer_id DESC, p.protocol_name;

CREATE VIEW v_network_inventory AS
SELECT
    d.hostname,
    d.device_type,
    ni.interface_name,
    ni.mac_address,
    ni.mtu,
    ia.ip_address,
    ia.subnet_prefix
FROM network_devices d
JOIN network_interfaces ni
    ON ni.device_id = d.device_id
LEFT JOIN ip_assignments ia
    ON ia.interface_id = ni.interface_id;

CREATE VIEW v_tcp_connection_report AS
SELECT
    c.connection_id,
    c.state,
    c.source_sequence,
    c.destination_sequence,
    se.ip_address AS source_ip,
    se.port AS source_port,
    de.ip_address AS destination_ip,
    de.port AS destination_port,
    c.opened_at,
    c.closed_at
FROM tcp_connections c
JOIN transport_endpoints se
    ON se.endpoint_id = c.source_endpoint
JOIN transport_endpoints de
    ON de.endpoint_id = c.destination_endpoint;

CREATE VIEW v_packet_forwarding_report AS
SELECT
    p.packet_id,
    p.source_ip,
    p.destination_ip,
    p.protocol_number,
    p.ttl,
    p.status,
    f.incoming_ttl,
    f.outgoing_ttl,
    f.failure_reason,
    d.hostname AS router_name,
    f.forwarded_at
FROM ip_packets p
LEFT JOIN packet_forwarding f
    ON f.packet_id = p.packet_id
LEFT JOIN network_devices d
    ON d.device_id = f.router_id;

CREATE VIEW v_device_performance AS
SELECT
    d.hostname,
    COUNT(m.metric_id) AS measurement_count,
    SUM(m.bytes_sent) AS total_bytes_sent,
    SUM(m.bytes_received) AS total_bytes_received,
    SUM(m.packets_dropped) AS total_dropped,
    ROUND(AVG(m.latency_ms), 2) AS average_latency_ms
FROM network_devices d
LEFT JOIN network_metrics m
    ON m.device_id = d.device_id
GROUP BY d.device_id, d.hostname;

-- ============================================================================
-- 28. ROUTE ELIGIBILITY QUERY
-- ============================================================================

SELECT *
FROM find_best_route(
    (
        SELECT device_id
        FROM network_devices
        WHERE hostname = 'ROUTER-01'
    ),
    '203.0.113.20'::INET
);

-- ============================================================================
-- 29. PACKET VALIDATION QUERY
-- ============================================================================

SELECT
    packet_id,
    source_ip,
    destination_ip,
    ttl,
    packet_length,
    CASE
        WHEN ttl = 1 THEN 'TTL_AT_LAST_HOP'
        WHEN packet_length > 1500 THEN 'MTU_EXCEEDED'
        ELSE 'VALID'
    END AS validation_result
FROM ip_packets
ORDER BY packet_id;

-- ============================================================================
-- 30. NETWORK PERFORMANCE AGGREGATION
-- ============================================================================

SELECT
    d.hostname,
    COUNT(*) AS measurement_count,
    SUM(m.packets_sent) AS total_packets_sent,
    SUM(m.packets_received) AS total_packets_received,
    SUM(m.packets_dropped) AS total_packets_dropped,
    ROUND(AVG(m.latency_ms), 2) AS average_latency
FROM network_metrics m
JOIN network_devices d
    ON d.device_id = m.device_id
GROUP BY d.hostname
ORDER BY total_packets_dropped DESC;

-- ============================================================================
-- 31. DNS ELIGIBILITY
-- ============================================================================

SELECT
    domain_name,
    record_type,
    ip_address,
    ttl_seconds,
    expires_at,
    CASE
        WHEN expires_at > CURRENT_TIMESTAMP THEN 'VALID'
        ELSE 'EXPIRED'
    END AS cache_status
FROM dns_records
ORDER BY domain_name;

-- ============================================================================
-- 32. NETWORK DIAGNOSTIC REPORT
-- ============================================================================

SELECT
    d.hostname,
    nd.component,
    nd.status,
    nd.diagnostic_message,
    nd.measured_value,
    nd.measured_at
FROM network_diagnostics nd
JOIN network_devices d
    ON d.device_id = nd.device_id
ORDER BY nd.measured_at DESC;

-- ============================================================================
-- 33. ROUTING TABLE REPORT
-- ============================================================================

SELECT
    d.hostname AS router,
    r.destination_network,
    r.next_hop,
    ni.interface_name,
    r.metric,
    r.active
FROM routing_entries r
JOIN network_devices d
    ON d.device_id = r.router_id
JOIN network_interfaces ni
    ON ni.interface_id = r.interface_id
ORDER BY
    d.hostname,
    masklen(r.destination_network) DESC,
    r.metric;

-- ============================================================================
-- 34. FAILURE ANALYSIS
-- ============================================================================

SELECT
    status,
    COUNT(*) AS packet_count
FROM ip_packets
GROUP BY status
ORDER BY packet_count DESC;

SELECT
    failure_reason,
    COUNT(*) AS occurrences
FROM packet_forwarding
WHERE forwarding_status = 'DROPPED'
GROUP BY failure_reason;

-- ============================================================================
-- 35. TCP STATE TRANSITION REPORT
-- ============================================================================

SELECT
    connection_id,
    previous_state,
    next_state,
    event_description,
    occurred_at
FROM tcp_state_history
ORDER BY connection_id, occurred_at;

-- ============================================================================
-- 36. DATA INTEGRITY TESTS
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM protocol_layers
        WHERE layer_name = 'APPLICATION'
    ) THEN
        RAISE EXCEPTION 'Application layer missing.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM protocols
        WHERE protocol_name = 'TCP'
          AND protocol_number = 6
    ) THEN
        RAISE EXCEPTION 'TCP registry validation failed.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM protocols
        WHERE protocol_name = 'UDP'
          AND protocol_number = 17
    ) THEN
        RAISE EXCEPTION 'UDP registry validation failed.';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM ip_packets
        WHERE ttl < 1 OR ttl > 255
    ) THEN
        RAISE EXCEPTION 'Invalid packet TTL detected.';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM ip_packets
        WHERE packet_length < 20
    ) THEN
        RAISE EXCEPTION 'Invalid IP packet length detected.';
    END IF;

    RAISE NOTICE 'All network integrity tests passed.';
END;
$$;

COMMIT;

-- ============================================================================
-- 37. OPERATIONAL QUERIES
-- ============================================================================

-- A. Complete protocol architecture.
SELECT * FROM v_protocol_architecture;

-- B. Device and interface inventory.
SELECT * FROM v_network_inventory;

-- C. TCP connection status.
SELECT * FROM v_tcp_connection_report;

-- D. Packet forwarding decisions.
SELECT * FROM v_packet_forwarding_report;

-- E. Device performance.
SELECT * FROM v_device_performance;

-- F. Active routing entries.
SELECT *
FROM routing_entries
WHERE active = TRUE;

-- G. Expired DNS records.
SELECT *
FROM dns_records
WHERE expires_at <= CURRENT_TIMESTAMP;

-- H. Dropped packet investigation.
SELECT *
FROM packet_forwarding
WHERE forwarding_status = 'DROPPED'
ORDER BY forwarded_at DESC;
