-- ============================================================
-- INTRODUCTION TO COMPUTER NETWORKS
-- PostgreSQL 14+
--
-- Relational network inventory and packet-switching workflow.
--
-- Covers:
-- Networks, LAN, WAN, devices, interfaces, IP addressing,
-- subnets, links, packets, routes, packet transmissions,
-- OSI/TCP-IP models, monitoring and network performance.
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS computer_networks;

SET search_path TO computer_networks, public;

-- ============================================================
-- 1. NETWORK MODEL REFERENCE TABLES
-- ============================================================

CREATE TABLE network_models (
    model_id SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    model_name VARCHAR(30) NOT NULL UNIQUE,
    description TEXT NOT NULL
);

CREATE TABLE network_layers (
    layer_id SMALLINT PRIMARY KEY,
    model_id SMALLINT NOT NULL
        REFERENCES network_models(model_id),
    layer_number SMALLINT NOT NULL,
    layer_name VARCHAR(40) NOT NULL,
    responsibility TEXT NOT NULL,
    UNIQUE (model_id, layer_number)
);

CREATE TABLE layer_protocols (
    protocol_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    layer_id SMALLINT NOT NULL
        REFERENCES network_layers(layer_id),
    protocol_name VARCHAR(40) NOT NULL UNIQUE,
    description TEXT NOT NULL
);

INSERT INTO network_models (model_name, description)
VALUES
(
    'OSI',
    'Seven-layer reference model for network communication'
),
(
    'TCP/IP',
    'Four-layer Internet communication model'
);

-- OSI layers.
INSERT INTO network_layers (
    layer_id, model_id, layer_number, layer_name, responsibility
)
SELECT
    layer_number,
    (SELECT model_id FROM network_models WHERE model_name = 'OSI'),
    layer_number,
    layer_name,
    responsibility
FROM (
    VALUES
    (1, 'Physical', 'Transmission of raw bits'),
    (2, 'Data Link', 'Frames and MAC addressing'),
    (3, 'Network', 'IP addressing and routing'),
    (4, 'Transport', 'End-to-end transport'),
    (5, 'Session', 'Session management'),
    (6, 'Presentation', 'Data representation and encryption'),
    (7, 'Application', 'Application-level network services')
) AS layers(layer_number, layer_name, responsibility);

-- TCP/IP layers are maintained separately.
INSERT INTO network_layers (
    layer_id, model_id, layer_number, layer_name, responsibility
)
SELECT
    layer_number + 10,
    (SELECT model_id FROM network_models WHERE model_name = 'TCP/IP'),
    layer_number,
    layer_name,
    responsibility
FROM (
    VALUES
    (1, 'Network Access', 'Physical transmission and local delivery'),
    (2, 'Internet', 'Logical addressing and routing'),
    (3, 'Transport', 'End-to-end communication'),
    (4, 'Application', 'Application protocols and services')
) AS layers(layer_number, layer_name, responsibility);

INSERT INTO layer_protocols (layer_id, protocol_name, description)
VALUES
(1, 'Ethernet', 'Wired local area network technology'),
(1, 'Wi-Fi', 'Wireless local area network technology'),
(2, 'IP', 'Internet Protocol'),
(2, 'ICMP', 'Internet Control Message Protocol'),
(3, 'TCP', 'Reliable connection-oriented transport'),
(3, 'UDP', 'Connectionless transport'),
(4, 'HTTP', 'Hypertext Transfer Protocol'),
(4, 'DNS', 'Domain Name System'),
(4, 'DHCP', 'Dynamic Host Configuration Protocol');

-- ============================================================
-- 2. NETWORKS AND SUBNETS
-- ============================================================

CREATE TABLE networks (
    network_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    network_name VARCHAR(100) NOT NULL UNIQUE,

    network_type VARCHAR(10) NOT NULL
        CHECK (network_type IN ('LAN', 'WAN')),

    description TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE subnets (
    subnet_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    network_id BIGINT NOT NULL
        REFERENCES networks(network_id),

    network_address INET NOT NULL,

    prefix_length SMALLINT NOT NULL
        CHECK (prefix_length BETWEEN 0 AND 32),

    gateway_address INET,

    CHECK (family(network_address) = 4),
    CHECK (masklen(network_address) = prefix_length),
    CHECK (
        gateway_address IS NULL OR
        (
            family(gateway_address) = 4
            AND gateway_address << network_address
        )
    ),

    UNIQUE (network_id, network_address, prefix_length)
);

CREATE INDEX idx_subnets_network
ON subnets(network_id);

-- ============================================================
-- 3. NETWORK DEVICES
-- ============================================================

CREATE TABLE devices (
    device_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    device_name VARCHAR(100) NOT NULL UNIQUE,

    device_type VARCHAR(20) NOT NULL
        CHECK (
            device_type IN ('HOST', 'SWITCH', 'ROUTER', 'FIREWALL')
        ),

    manufacturer VARCHAR(100),

    location VARCHAR(150),

    operational_status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'
        CHECK (
            operational_status IN (
                'ACTIVE', 'INACTIVE', 'MAINTENANCE', 'FAILED'
            )
        ),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE network_interfaces (
    interface_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    device_id BIGINT NOT NULL
        REFERENCES devices(device_id),

    interface_name VARCHAR(50) NOT NULL,

    subnet_id BIGINT NOT NULL
        REFERENCES subnets(subnet_id),

    ip_address INET NOT NULL,

    mac_address MACADDR NOT NULL,

    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,

    CHECK (family(ip_address) = 4),

    UNIQUE (device_id, interface_name),
    UNIQUE (ip_address),
    UNIQUE (mac_address)
);

CREATE INDEX idx_interfaces_device
ON network_interfaces(device_id);

CREATE INDEX idx_interfaces_subnet
ON network_interfaces(subnet_id);

CREATE INDEX idx_interfaces_ip
ON network_interfaces USING HASH(ip_address);

-- Enforce that interface addresses belong to their assigned subnet.
CREATE OR REPLACE FUNCTION validate_interface_subnet()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    subnet_record subnets%ROWTYPE;
BEGIN
    SELECT *
    INTO subnet_record
    FROM subnets
    WHERE subnet_id = NEW.subnet_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Subnet does not exist';
    END IF;

    IF NOT (NEW.ip_address << subnet_record.network_address) THEN
        RAISE EXCEPTION
            'Interface IP % is outside subnet %',
            NEW.ip_address,
            subnet_record.network_address;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_interface_subnet
BEFORE INSERT OR UPDATE OF ip_address, subnet_id
ON network_interfaces
FOR EACH ROW
EXECUTE FUNCTION validate_interface_subnet();

-- ============================================================
-- 4. NETWORK LINKS
-- ============================================================

CREATE TABLE network_links (
    link_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    source_device_id BIGINT NOT NULL
        REFERENCES devices(device_id),

    destination_device_id BIGINT NOT NULL
        REFERENCES devices(device_id),

    network_type VARCHAR(10) NOT NULL
        CHECK (network_type IN ('LAN', 'WAN')),

    bandwidth_mbps NUMERIC(12, 2) NOT NULL
        CHECK (bandwidth_mbps > 0),

    latency_ms NUMERIC(12, 3) NOT NULL
        CHECK (latency_ms >= 0),

    link_status VARCHAR(15) NOT NULL DEFAULT 'UP'
        CHECK (link_status IN ('UP', 'DOWN', 'MAINTENANCE')),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (source_device_id <> destination_device_id),

    UNIQUE (source_device_id, destination_device_id)
);

CREATE INDEX idx_links_source_status
ON network_links(source_device_id, link_status);

CREATE INDEX idx_links_destination
ON network_links(destination_device_id);

-- ============================================================
-- 5. ROUTING TABLES
-- ============================================================

CREATE TABLE routing_entries (
    route_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    router_device_id BIGINT NOT NULL
        REFERENCES devices(device_id),

    destination_network CIDR NOT NULL,

    next_hop INET,

    outgoing_interface_id BIGINT
        REFERENCES network_interfaces(interface_id),

    metric INTEGER NOT NULL DEFAULT 1
        CHECK (metric >= 0),

    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (next_hop IS NOT NULL OR outgoing_interface_id IS NOT NULL)
);

CREATE INDEX idx_routes_router
ON routing_entries(router_device_id, is_enabled);

CREATE INDEX idx_routes_destination
ON routing_entries USING GIST(destination_network inet_ops);

-- Longest-prefix matching.
CREATE OR REPLACE FUNCTION find_next_hop(
    p_router_id BIGINT,
    p_destination INET
)
RETURNS TABLE (
    selected_route_id BIGINT,
    selected_network CIDR,
    selected_next_hop INET,
    selected_metric INTEGER
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        route_id,
        destination_network,
        next_hop,
        metric
    FROM routing_entries
    WHERE router_device_id = p_router_id
      AND is_enabled
      AND p_destination <<= destination_network
    ORDER BY
        masklen(destination_network) DESC,
        metric ASC
    LIMIT 1;
$$;

-- ============================================================
-- 6. PACKET RECORDS
-- ============================================================

CREATE TABLE packets (
    packet_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    source_ip INET NOT NULL,
    destination_ip INET NOT NULL,

    transport_protocol VARCHAR(10) NOT NULL
        CHECK (
            transport_protocol IN ('TCP', 'UDP', 'ICMP')
        ),

    source_port INTEGER,
    destination_port INTEGER,

    payload_size_bytes INTEGER NOT NULL
        CHECK (payload_size_bytes BETWEEN 0 AND 65507),

    ttl SMALLINT NOT NULL DEFAULT 64
        CHECK (ttl BETWEEN 1 AND 255),

    packet_status VARCHAR(15) NOT NULL DEFAULT 'CREATED'
        CHECK (
            packet_status IN (
                'CREATED', 'FORWARDED', 'DELIVERED', 'DROPPED'
            )
        ),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (family(source_ip) = 4),
    CHECK (family(destination_ip) = 4),

    CHECK (
        source_port IS NULL OR
        source_port BETWEEN 1 AND 65535
    ),

    CHECK (
        destination_port IS NULL OR
        destination_port BETWEEN 1 AND 65535
    )
);

CREATE INDEX idx_packets_created
ON packets(created_at DESC);

CREATE INDEX idx_packets_status
ON packets(packet_status, created_at DESC);

CREATE INDEX idx_packets_destination
ON packets(destination_ip);

-- ============================================================
-- 7. PACKET TRANSMISSION HISTORY
-- ============================================================

CREATE TABLE packet_transmissions (
    transmission_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    packet_id BIGINT NOT NULL
        REFERENCES packets(packet_id),

    link_id BIGINT NOT NULL
        REFERENCES network_links(link_id),

    hop_number SMALLINT NOT NULL
        CHECK (hop_number > 0),

    latency_ms NUMERIC(12, 3)
        CHECK (latency_ms >= 0),

    transmission_status VARCHAR(15) NOT NULL
        CHECK (
            transmission_status IN (
                'FORWARDED', 'DELIVERED', 'DROPPED'
            )
        ),

    transmitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (packet_id, hop_number)
);

CREATE INDEX idx_transmissions_packet
ON packet_transmissions(packet_id, hop_number);

CREATE INDEX idx_transmissions_time
ON packet_transmissions(transmitted_at DESC);

-- ============================================================
-- 8. NETWORK MONITORING
-- ============================================================

CREATE TABLE network_metrics (
    metric_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    device_id BIGINT NOT NULL
        REFERENCES devices(device_id),

    bandwidth_utilization NUMERIC(5, 2)
        CHECK (bandwidth_utilization BETWEEN 0 AND 100),

    latency_ms NUMERIC(12, 3)
        CHECK (latency_ms >= 0),

    packet_loss_percent NUMERIC(5, 2)
        CHECK (packet_loss_percent BETWEEN 0 AND 100),

    measured_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_metrics_device_time
ON network_metrics(device_id, measured_at DESC);

-- ============================================================
-- 9. SAMPLE NETWORK INFRASTRUCTURE
-- ============================================================

INSERT INTO networks (network_name, network_type, description)
VALUES
(
    'Head Office LAN',
    'LAN',
    'Internal development and application network'
),
(
    'Enterprise WAN',
    'WAN',
    'Connectivity between head office and remote office'
),
(
    'Remote Office LAN',
    'LAN',
    'Remote server and workstation network'
);

INSERT INTO subnets (
    network_id,
    network_address,
    prefix_length,
    gateway_address
)
VALUES
(
    (SELECT network_id FROM networks
     WHERE network_name = 'Head Office LAN'),
    '192.168.1.0/24',
    24,
    '192.168.1.1'
),
(
    (SELECT network_id FROM networks
     WHERE network_name = 'Remote Office LAN'),
    '10.0.0.0/24',
    24,
    '10.0.0.1'
);

INSERT INTO devices (
    device_name,
    device_type,
    manufacturer,
    location
)
VALUES
('PC1', 'HOST', 'Dell', 'Head Office'),
('SW1', 'SWITCH', 'Cisco', 'Head Office'),
('R1', 'ROUTER', 'Cisco', 'Head Office'),
('R2', 'ROUTER', 'Cisco', 'Remote Office'),
('SW2', 'SWITCH', 'Cisco', 'Remote Office'),
('SRV1', 'HOST', 'HPE', 'Remote Office'),
('FW1', 'FIREWALL', 'Fortinet', 'Head Office');

INSERT INTO network_interfaces (
    device_id,
    interface_name,
    subnet_id,
    ip_address,
    mac_address
)
VALUES
(
    (SELECT device_id FROM devices WHERE device_name = 'PC1'),
    'eth0',
    (SELECT subnet_id FROM subnets
     WHERE network_address = '192.168.1.0/24'),
    '192.168.1.10',
    '02:00:00:00:00:01'
),
(
    (SELECT device_id FROM devices WHERE device_name = 'R1'),
    'eth0',
    (SELECT subnet_id FROM subnets
     WHERE network_address = '192.168.1.0/24'),
    '192.168.1.1',
    '02:00:00:00:00:02'
),
(
    (SELECT device_id FROM devices WHERE device_name = 'SRV1'),
    'eth0',
    (SELECT subnet_id FROM subnets
     WHERE network_address = '10.0.0.0/24'),
    '10.0.0.10',
    '02:00:00:00:00:03'
),
(
    (SELECT device_id FROM devices WHERE device_name = 'R2'),
    'eth0',
    (SELECT subnet_id FROM subnets
     WHERE network_address = '10.0.0.0/24'),
    '10.0.0.1',
    '02:00:00:00:00:04'
);

INSERT INTO network_links (
    source_device_id,
    destination_device_id,
    network_type,
    bandwidth_mbps,
    latency_ms
)
VALUES
(
    (SELECT device_id FROM devices WHERE device_name = 'PC1'),
    (SELECT device_id FROM devices WHERE device_name = 'SW1'),
    'LAN', 1000, 0.1
),
(
    (SELECT device_id FROM devices WHERE device_name = 'SW1'),
    (SELECT device_id FROM devices WHERE device_name = 'R1'),
    'LAN', 1000, 0.2
),
(
    (SELECT device_id FROM devices WHERE device_name = 'R1'),
    (SELECT device_id FROM devices WHERE device_name = 'R2'),
    'WAN', 100, 20
),
(
    (SELECT device_id FROM devices WHERE device_name = 'R2'),
    (SELECT device_id FROM devices WHERE device_name = 'SW2'),
    'LAN', 1000, 0.2
),
(
    (SELECT device_id FROM devices WHERE device_name = 'SW2'),
    (SELECT device_id FROM devices WHERE device_name = 'SRV1'),
    'LAN', 1000, 0.1
);

INSERT INTO routing_entries (
    router_device_id,
    destination_network,
    next_hop,
    metric
)
VALUES
(
    (SELECT device_id FROM devices WHERE device_name = 'R1'),
    '10.0.0.0/8',
    '192.168.1.1',
    10
),
(
    (SELECT device_id FROM devices WHERE device_name = 'R1'),
    '10.0.0.0/24',
    '192.168.1.1',
    5
);

-- ============================================================
-- 10. PACKET PROCESSING FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION process_packet(
    p_source INET,
    p_destination INET,
    p_protocol VARCHAR,
    p_payload_size INTEGER,
    p_ttl INTEGER DEFAULT 64
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    new_packet_id BIGINT;
BEGIN
    IF family(p_source) <> 4 OR family(p_destination) <> 4 THEN
        RAISE EXCEPTION 'Only IPv4 packets are supported';
    END IF;

    IF p_protocol NOT IN ('TCP', 'UDP', 'ICMP') THEN
        RAISE EXCEPTION 'Unsupported protocol: %', p_protocol;
    END IF;

    IF p_payload_size < 0 OR p_payload_size > 65507 THEN
        RAISE EXCEPTION 'Invalid payload size';
    END IF;

    IF p_ttl < 1 OR p_ttl > 255 THEN
        RAISE EXCEPTION 'Invalid TTL';
    END IF;

    INSERT INTO packets (
        source_ip,
        destination_ip,
        transport_protocol,
        payload_size_bytes,
        ttl,
        packet_status
    )
    VALUES (
        p_source,
        p_destination,
        p_protocol,
        p_payload_size,
        p_ttl,
        'CREATED'
    )
    RETURNING packet_id INTO new_packet_id;

    RETURN new_packet_id;
END;
$$;

-- ============================================================
-- 11. PACKET STATE TRANSITION VALIDATION
-- ============================================================

CREATE OR REPLACE FUNCTION validate_packet_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.packet_status = OLD.packet_status THEN
        RETURN NEW;
    END IF;

    IF OLD.packet_status = 'CREATED'
       AND NEW.packet_status NOT IN ('FORWARDED', 'DROPPED') THEN
        RAISE EXCEPTION 'Invalid CREATED transition';
    END IF;

    IF OLD.packet_status = 'FORWARDED'
       AND NEW.packet_status NOT IN ('FORWARDED', 'DELIVERED', 'DROPPED') THEN
        RAISE EXCEPTION 'Invalid FORWARDED transition';
    END IF;

    IF OLD.packet_status IN ('DELIVERED', 'DROPPED') THEN
        RAISE EXCEPTION 'Terminal packet state cannot be changed';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_packet_transition
BEFORE UPDATE OF packet_status
ON packets
FOR EACH ROW
EXECUTE FUNCTION validate_packet_transition();

-- ============================================================
-- 12. PACKET TRANSMISSION PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE record_transmission(
    p_packet_id BIGINT,
    p_link_id BIGINT,
    p_hop_number SMALLINT,
    p_latency NUMERIC,
    p_status VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    current_status VARCHAR(15);
    current_ttl SMALLINT;
BEGIN
    SELECT packet_status, ttl
    INTO current_status, current_ttl
    FROM packets
    WHERE packet_id = p_packet_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Packet not found';
    END IF;

    IF current_status IN ('DELIVERED', 'DROPPED') THEN
        RAISE EXCEPTION 'Packet is already in terminal state';
    END IF;

    IF current_ttl <= 1 AND p_status = 'FORWARDED' THEN
        UPDATE packets
        SET packet_status = 'DROPPED'
        WHERE packet_id = p_packet_id;

        RAISE EXCEPTION 'Packet TTL expired';
    END IF;

    IF p_status = 'FORWARDED' THEN
        UPDATE packets
        SET
            packet_status = 'FORWARDED',
            ttl = ttl - 1
        WHERE packet_id = p_packet_id;

    ELSIF p_status IN ('DELIVERED', 'DROPPED') THEN
        UPDATE packets
        SET packet_status = p_status
        WHERE packet_id = p_packet_id;

    ELSE
        RAISE EXCEPTION 'Unsupported transmission status';
    END IF;

    INSERT INTO packet_transmissions (
        packet_id,
        link_id,
        hop_number,
        latency_ms,
        transmission_status
    )
    VALUES (
        p_packet_id,
        p_link_id,
        p_hop_number,
        p_latency,
        p_status
    );
END;
$$;

-- ============================================================
-- 13. NETWORK REPORTING VIEWS
-- ============================================================

CREATE OR REPLACE VIEW network_inventory AS
SELECT
    d.device_id,
    d.device_name,
    d.device_type,
    d.operational_status,
    ni.interface_name,
    ni.ip_address,
    ni.mac_address,
    s.network_address,
    n.network_name,
    n.network_type
FROM devices d
LEFT JOIN network_interfaces ni
    ON ni.device_id = d.device_id
LEFT JOIN subnets s
    ON s.subnet_id = ni.subnet_id
LEFT JOIN networks n
    ON n.network_id = s.network_id;

CREATE OR REPLACE VIEW packet_delivery_report AS
SELECT
    packet_status,
    transport_protocol,
    COUNT(*) AS packet_count,
    SUM(payload_size_bytes) AS total_payload_bytes,
    AVG(ttl) AS average_remaining_ttl
FROM packets
GROUP BY packet_status, transport_protocol;

CREATE OR REPLACE VIEW link_performance_report AS
SELECT
    nl.link_id,
    source.device_name AS source_device,
    destination.device_name AS destination_device,
    nl.network_type,
    nl.bandwidth_mbps,
    nl.latency_ms,
    nl.link_status,
    COUNT(pt.transmission_id) AS transmission_count
FROM network_links nl
JOIN devices source
    ON source.device_id = nl.source_device_id
JOIN devices destination
    ON destination.device_id = nl.destination_device_id
LEFT JOIN packet_transmissions pt
    ON pt.link_id = nl.link_id
GROUP BY
    nl.link_id,
    source.device_name,
    destination.device_name;

-- ============================================================
-- 14. PACKET AND NETWORK SAMPLE DATA
-- ============================================================

INSERT INTO packets (
    source_ip,
    destination_ip,
    transport_protocol,
    source_port,
    destination_port,
    payload_size_bytes,
    ttl,
    packet_status
)
VALUES
(
    '192.168.1.10',
    '10.0.0.10',
    'TCP',
    50000,
    443,
    1024,
    64,
    'DELIVERED'
),
(
    '192.168.1.10',
    '10.0.0.10',
    'UDP',
    50001,
    53,
    512,
    64,
    'FORWARDED'
),
(
    '10.0.0.10',
    '192.168.1.10',
    'ICMP',
    NULL,
    NULL,
    64,
    1,
    'DROPPED'
);

INSERT INTO network_metrics (
    device_id,
    bandwidth_utilization,
    latency_ms,
    packet_loss_percent
)
VALUES
(
    (SELECT device_id FROM devices WHERE device_name = 'R1'),
    65.5, 20.1, 0.2
),
(
    (SELECT device_id FROM devices WHERE device_name = 'R2'),
    72.0, 22.5, 1.5
),
(
    (SELECT device_id FROM devices WHERE device_name = 'SW1'),
    35.0, 0.3, 0
);

-- ============================================================
-- 15. ROUTING AND ELIGIBILITY QUERIES
-- ============================================================

-- Longest-prefix routing lookup.
SELECT *
FROM find_next_hop(
    (SELECT device_id FROM devices WHERE device_name = 'R1'),
    '10.0.0.10'
);

-- Device eligibility for active network communication.
SELECT
    d.device_name,
    d.device_type,
    d.operational_status,
    COUNT(ni.interface_id) AS enabled_interfaces,
    CASE
        WHEN d.operational_status = 'ACTIVE'
         AND COUNT(ni.interface_id) FILTER (
             WHERE ni.is_enabled
         ) > 0
        THEN 'ELIGIBLE'
        ELSE 'NOT ELIGIBLE'
    END AS communication_eligibility
FROM devices d
LEFT JOIN network_interfaces ni
    ON ni.device_id = d.device_id
GROUP BY
    d.device_id,
    d.device_name,
    d.device_type,
    d.operational_status
ORDER BY d.device_name;

-- ============================================================
-- 16. RETRIEVAL AND AGGREGATION QUERIES
-- ============================================================

SELECT *
FROM network_inventory
ORDER BY device_name;

SELECT *
FROM packet_delivery_report
ORDER BY packet_status;

SELECT *
FROM link_performance_report
ORDER BY link_id;

-- Average network performance per device.
SELECT
    d.device_name,
    ROUND(AVG(m.bandwidth_utilization), 2)
        AS average_utilization,
    ROUND(AVG(m.latency_ms), 2)
        AS average_latency,
    ROUND(AVG(m.packet_loss_percent), 2)
        AS average_packet_loss
FROM network_metrics m
JOIN devices d
    ON d.device_id = m.device_id
GROUP BY d.device_name
ORDER BY average_latency DESC;

-- CTE-based network transmission analysis.
WITH packet_summary AS (
    SELECT
        packet_id,
        COUNT(*) AS hop_count,
        SUM(latency_ms) AS total_latency,
        BOOL_AND(
            transmission_status IN ('DELIVERED', 'FORWARDED')
        ) AS transmission_success
    FROM packet_transmissions
    GROUP BY packet_id
)
SELECT
    p.packet_id,
    p.source_ip,
    p.destination_ip,
    p.packet_status,
    COALESCE(ps.hop_count, 0) AS hop_count,
    COALESCE(ps.total_latency, 0) AS total_latency_ms,
    ps.transmission_success
FROM packets p
LEFT JOIN packet_summary ps
    ON ps.packet_id = p.packet_id
ORDER BY p.packet_id;

-- ============================================================
-- 17. TRANSACTIONAL PACKET WORKFLOW
-- ============================================================

DO $$
DECLARE
    new_packet BIGINT;
    first_link BIGINT;
    second_link BIGINT;
BEGIN
    new_packet := process_packet(
        '192.168.1.10',
        '10.0.0.10',
        'TCP',
        256,
        64
    );

    SELECT link_id INTO first_link
    FROM network_links
    WHERE source_device_id = (
        SELECT device_id FROM devices WHERE device_name = 'PC1'
    )
    AND destination_device_id = (
        SELECT device_id FROM devices WHERE device_name = 'SW1'
    );

    SELECT link_id INTO second_link
    FROM network_links
    WHERE source_device_id = (
        SELECT device_id FROM devices WHERE device_name = 'R1'
    )
    AND destination_device_id = (
        SELECT device_id FROM devices WHERE device_name = 'R2'
    );

    CALL record_transmission(
        new_packet,
        first_link,
        1,
        0.1,
        'FORWARDED'
    );

    CALL record_transmission(
        new_packet,
        second_link,
        2,
        20.0,
        'DELIVERED'
    );

    RAISE NOTICE 'Packet % processed successfully', new_packet;
END;
$$;

-- ============================================================
-- 18. FAILURE AND VALIDATION EXAMPLES
-- ============================================================

-- Invalid IP assignments, duplicate addresses and invalid link
-- parameters are rejected by constraints or triggers.
--
-- The following query identifies unhealthy links.

SELECT
    link_id,
    network_type,
    bandwidth_mbps,
    latency_ms,
    link_status,
    CASE
        WHEN link_status <> 'UP' THEN 'UNAVAILABLE'
        WHEN latency_ms > 50 THEN 'HIGH LATENCY'
        ELSE 'NORMAL'
    END AS health_status
FROM network_links
ORDER BY link_id;

-- Find dropped packets.
SELECT
    packet_id,
    source_ip,
    destination_ip,
    transport_protocol,
    ttl,
    created_at
FROM packets
WHERE packet_status = 'DROPPED'
ORDER BY created_at DESC;

-- ============================================================
-- 19. PERFORMANCE AND SECURITY NOTES
-- ============================================================

-- Production deployments should use:
-- 1. Separate database roles for monitoring and administration.
-- 2. Least-privilege GRANT permissions.
-- 3. TLS connections and encrypted backups.
-- 4. Retention policies for high-volume packet history.
-- 5. Partitioning for large time-series tables.
-- 6. Query monitoring and execution-plan analysis.
-- 7. Restricted access to IP and device inventory.
-- 8. Explicit authorization for network changes.
--
-- This schema models packet metadata and simulated forwarding.
-- It does not capture or transmit real network packets.

COMMIT;
