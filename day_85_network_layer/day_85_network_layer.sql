/*
===============================================================================
NETWORK LAYER ENGINEERING
PostgreSQL 15+

Domain:
    IP addressing
    IPv4 and IPv6
    CIDR and subnetting
    Network interfaces
    Static routing
    Longest-prefix matching
    Route metrics
    Interface availability
    Packet forwarding decisions
    Network utilization and reporting

PostgreSQL native inet and cidr types provide address-family-aware
storage and network operations.
===============================================================================
*/

BEGIN;

CREATE SCHEMA IF NOT EXISTS network_layer;

SET search_path TO network_layer, public;


/* ============================================================================
   ENUMERATED DOMAIN TYPES
   ============================================================================ */

CREATE TYPE interface_state AS ENUM (
    'UP',
    'DOWN',
    'MAINTENANCE'
);

CREATE TYPE route_state AS ENUM (
    'ACTIVE',
    'INACTIVE'
);

CREATE TYPE address_role AS ENUM (
    'PRIMARY',
    'SECONDARY',
    'LOOPBACK',
    'VIRTUAL'
);

CREATE TYPE packet_state AS ENUM (
    'FORWARDED',
    'NO_ROUTE',
    'INTERFACE_DOWN',
    'MTU_EXCEEDED',
    'INVALID_SOURCE'
);


/* ============================================================================
   REPOSITORY OF NETWORK DEVICES
   ============================================================================ */

CREATE TABLE routers (
    router_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    hostname VARCHAR(100) NOT NULL UNIQUE,

    location VARCHAR(150) NOT NULL,

    management_ip INET,

    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_hostname
        CHECK (hostname ~ '^[A-Za-z0-9][A-Za-z0-9.-]{0,98}$')
);


/* ============================================================================
   NETWORK INTERFACES
   ============================================================================ */

CREATE TABLE network_interfaces (
    interface_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    router_id BIGINT NOT NULL
        REFERENCES routers(router_id)
        ON DELETE CASCADE,

    interface_name VARCHAR(30) NOT NULL,

    state interface_state NOT NULL DEFAULT 'UP',

    mtu INTEGER NOT NULL DEFAULT 1500,

    mac_address MACADDR,

    description TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_router_interface
        UNIQUE (router_id, interface_name),

    CONSTRAINT valid_mtu
        CHECK (mtu BETWEEN 576 AND 65535)
);


/* ============================================================================
   INTERFACE IP ADDRESSES
   ============================================================================ */

CREATE TABLE interface_addresses (
    address_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    interface_id BIGINT NOT NULL
        REFERENCES network_interfaces(interface_id)
        ON DELETE CASCADE,

    address CIDR NOT NULL,

    role address_role NOT NULL DEFAULT 'PRIMARY',

    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_interface_address
        UNIQUE (interface_id, address),

    CONSTRAINT valid_address_prefix
        CHECK (
            family(address) = 4
            OR family(address) = 6
        )
);

CREATE INDEX idx_interface_addresses_network
    ON interface_addresses USING GIST(address inet_ops);


/* ============================================================================
   ROUTING TABLE
   ============================================================================ */

CREATE TABLE routes (
    route_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    router_id BIGINT NOT NULL
        REFERENCES routers(router_id)
        ON DELETE CASCADE,

    destination CIDR NOT NULL,

    interface_id BIGINT NOT NULL
        REFERENCES network_interfaces(interface_id),

    next_hop INET,

    metric INTEGER NOT NULL DEFAULT 100,

    state route_state NOT NULL DEFAULT 'ACTIVE',

    is_default BOOLEAN GENERATED ALWAYS AS (
        masklen(destination) = 0
    ) STORED,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_metric
        CHECK (metric >= 0),

    CONSTRAINT gateway_family_match
        CHECK (
            next_hop IS NULL
            OR family(next_hop) = family(destination)
        ),

    CONSTRAINT unique_router_route
        UNIQUE (
            router_id,
            destination,
            interface_id,
            metric
        )
);

CREATE INDEX idx_routes_router_state
    ON routes(router_id, state);

CREATE INDEX idx_routes_destination
    ON routes USING GIST(destination inet_ops);

CREATE INDEX idx_routes_longest_prefix
    ON routes(
        router_id,
        masklen(destination) DESC,
        metric ASC
    )
    WHERE state = 'ACTIVE';


/* ============================================================================
   NETWORK PACKET FORWARDING LOG
   ============================================================================ */

CREATE TABLE forwarding_logs (
    forwarding_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    router_id BIGINT NOT NULL
        REFERENCES routers(router_id),

    source_address INET NOT NULL,

    destination_address INET NOT NULL,

    matched_route_id BIGINT
        REFERENCES routes(route_id)
        ON DELETE SET NULL,

    outgoing_interface_id BIGINT
        REFERENCES network_interfaces(interface_id)
        ON DELETE SET NULL,

    packet_size INTEGER NOT NULL,

    state packet_state NOT NULL,

    error_message TEXT,

    forwarded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_packet_size
        CHECK (packet_size BETWEEN 0 AND 65535),

    CONSTRAINT matching_address_family
        CHECK (
            family(source_address) = family(destination_address)
        )
);

CREATE INDEX idx_forwarding_router_time
    ON forwarding_logs(router_id, forwarded_at DESC);

CREATE INDEX idx_forwarding_failures
    ON forwarding_logs(router_id, state)
    WHERE state <> 'FORWARDED';


/* ============================================================================
   ROUTE VALIDATION TRIGGER
   ============================================================================ */

CREATE OR REPLACE FUNCTION validate_route()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    interface_router BIGINT;
    interface_status interface_state;
    router_enabled BOOLEAN;
    gateway_reachable BOOLEAN;
BEGIN
    SELECT
        ni.router_id,
        ni.state,
        r.enabled
    INTO
        interface_router,
        interface_status,
        router_enabled
    FROM network_interfaces ni
    JOIN routers r
        ON r.router_id = ni.router_id
    WHERE ni.interface_id = NEW.interface_id
    FOR UPDATE OF ni;

    IF interface_router IS NULL THEN
        RAISE EXCEPTION 'Outgoing interface does not exist';
    END IF;

    IF interface_router <> NEW.router_id THEN
        RAISE EXCEPTION
            'Route interface must belong to the selected router';
    END IF;

    IF NOT router_enabled THEN
        RAISE EXCEPTION 'Router is disabled';
    END IF;

    IF interface_status <> 'UP' AND NEW.state = 'ACTIVE' THEN
        RAISE EXCEPTION
            'Cannot activate a route through a non-UP interface';
    END IF;

    IF NEW.next_hop IS NOT NULL THEN

        SELECT EXISTS (
            SELECT 1
            FROM interface_addresses ia
            WHERE ia.interface_id = NEW.interface_id
              AND ia.enabled
              AND family(ia.address) = family(NEW.next_hop)
              AND NEW.next_hop <<= network(ia.address)
        )
        INTO gateway_reachable;

        IF NOT gateway_reachable THEN
            RAISE EXCEPTION
                'Gateway % is not reachable through interface %',
                NEW.next_hop,
                NEW.interface_id;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_route
BEFORE INSERT OR UPDATE
ON routes
FOR EACH ROW
EXECUTE FUNCTION validate_route();


/* ============================================================================
   INTERFACE STATE CHANGE
   Deactivates routes when an interface becomes unavailable.
   ============================================================================ */

CREATE OR REPLACE FUNCTION synchronize_interface_routes()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.state <> 'UP' THEN
        UPDATE routes
        SET state = 'INACTIVE'
        WHERE interface_id = NEW.interface_id
          AND state = 'ACTIVE';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_interface_state
AFTER UPDATE OF state
ON network_interfaces
FOR EACH ROW
WHEN (OLD.state IS DISTINCT FROM NEW.state)
EXECUTE FUNCTION synchronize_interface_routes();


/* ============================================================================
   ROUTE LOOKUP FUNCTION
   Longest-prefix match, then lowest metric.
   ============================================================================ */

CREATE OR REPLACE FUNCTION lookup_route(
    p_router_id BIGINT,
    p_destination INET
)
RETURNS TABLE (
    selected_route_id BIGINT,
    selected_network CIDR,
    selected_gateway INET,
    selected_interface_id BIGINT,
    selected_metric INTEGER
)
LANGUAGE SQL
STABLE
AS $$
    SELECT
        rt.route_id,
        rt.destination,
        rt.next_hop,
        rt.interface_id,
        rt.metric
    FROM routes rt
    JOIN network_interfaces ni
        ON ni.interface_id = rt.interface_id
    JOIN routers r
        ON r.router_id = rt.router_id
    WHERE rt.router_id = p_router_id
      AND rt.state = 'ACTIVE'
      AND ni.state = 'UP'
      AND ni.router_id = p_router_id
      AND r.enabled
      AND family(rt.destination) = family(p_destination)
      AND p_destination <<= rt.destination
    ORDER BY
        masklen(rt.destination) DESC,
        rt.metric ASC,
        rt.route_id ASC
    LIMIT 1;
$$;


/* ============================================================================
   SUBNET INFORMATION VIEW
   ============================================================================ */

CREATE OR REPLACE VIEW subnet_inventory AS
SELECT
    r.hostname,
    ni.interface_name,
    ni.state AS interface_state,
    ia.address,
    family(ia.address) AS ip_version,
    masklen(ia.address) AS prefix_length,
    network(ia.address) AS network_address,
    broadcast(ia.address) AS broadcast_address,
    host(ia.address) AS interface_ip,
    ni.mtu
FROM interface_addresses ia
JOIN network_interfaces ni
    ON ni.interface_id = ia.interface_id
JOIN routers r
    ON r.router_id = ni.router_id
WHERE ia.enabled;


/* ============================================================================
   ROUTING TABLE VIEW
   ============================================================================ */

CREATE OR REPLACE VIEW active_routing_table AS
SELECT
    r.hostname,
    rt.route_id,
    rt.destination,
    rt.next_hop,
    ni.interface_name,
    rt.metric,
    rt.is_default
FROM routes rt
JOIN routers r
    ON r.router_id = rt.router_id
JOIN network_interfaces ni
    ON ni.interface_id = rt.interface_id
WHERE rt.state = 'ACTIVE'
  AND ni.state = 'UP'
  AND r.enabled;


/* ============================================================================
   PACKET FORWARDING PROCEDURE
   Records successful and unsuccessful forwarding attempts.
   ============================================================================ */

CREATE OR REPLACE PROCEDURE forward_packet(
    IN p_router_id BIGINT,
    IN p_source INET,
    IN p_destination INET,
    IN p_packet_size INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    route_record RECORD;
    interface_mtu INTEGER;
    source_valid BOOLEAN;
    result_state packet_state;
    failure_reason TEXT;
BEGIN
    IF family(p_source) <> family(p_destination) THEN
        RAISE EXCEPTION 'Source and destination families differ';
    END IF;

    IF p_packet_size < 0 OR p_packet_size > 65535 THEN
        RAISE EXCEPTION 'Invalid packet size';
    END IF;

    SELECT EXISTS (
        SELECT 1
        FROM network_interfaces ni
        JOIN interface_addresses ia
            ON ia.interface_id = ni.interface_id
        WHERE ni.router_id = p_router_id
          AND ni.state = 'UP'
          AND ia.enabled
          AND p_source = host(ia.address)::inet
    )
    INTO source_valid;

    IF NOT source_valid THEN
        result_state := 'INVALID_SOURCE';
        failure_reason := 'Source address is not configured on an active interface';

        INSERT INTO forwarding_logs (
            router_id,
            source_address,
            destination_address,
            packet_size,
            state,
            error_message
        )
        VALUES (
            p_router_id,
            p_source,
            p_destination,
            p_packet_size,
            result_state,
            failure_reason
        );

        RETURN;
    END IF;

    SELECT *
    INTO route_record
    FROM lookup_route(
        p_router_id,
        p_destination
    );

    IF route_record.selected_route_id IS NULL THEN
        result_state := 'NO_ROUTE';
        failure_reason := 'No matching active route';

        INSERT INTO forwarding_logs (
            router_id,
            source_address,
            destination_address,
            packet_size,
            state,
            error_message
        )
        VALUES (
            p_router_id,
            p_source,
            p_destination,
            p_packet_size,
            result_state,
            failure_reason
        );

        RETURN;
    END IF;

    SELECT mtu
    INTO interface_mtu
    FROM network_interfaces
    WHERE interface_id = route_record.selected_interface_id
      AND state = 'UP';

    IF interface_mtu IS NULL THEN
        result_state := 'INTERFACE_DOWN';
        failure_reason := 'Outgoing interface unavailable';

        INSERT INTO forwarding_logs (
            router_id,
            source_address,
            destination_address,
            matched_route_id,
            outgoing_interface_id,
            packet_size,
            state,
            error_message
        )
        VALUES (
            p_router_id,
            p_source,
            p_destination,
            route_record.selected_route_id,
            route_record.selected_interface_id,
            p_packet_size,
            result_state,
            failure_reason
        );

        RETURN;
    END IF;

    IF p_packet_size > interface_mtu THEN
        result_state := 'MTU_EXCEEDED';
        failure_reason := 'Packet exceeds outgoing interface MTU';

        INSERT INTO forwarding_logs (
            router_id,
            source_address,
            destination_address,
            matched_route_id,
            outgoing_interface_id,
            packet_size,
            state,
            error_message
        )
        VALUES (
            p_router_id,
            p_source,
            p_destination,
            route_record.selected_route_id,
            route_record.selected_interface_id,
            p_packet_size,
            result_state,
            failure_reason
        );

        RETURN;
    END IF;

    INSERT INTO forwarding_logs (
        router_id,
        source_address,
        destination_address,
        matched_route_id,
        outgoing_interface_id,
        packet_size,
        state
    )
    VALUES (
        p_router_id,
        p_source,
        p_destination,
        route_record.selected_route_id,
        route_record.selected_interface_id,
        p_packet_size,
        'FORWARDED'
    );

END;
$$;


/* ============================================================================
   REPORTING: ROUTE COUNTS
   ============================================================================ */

CREATE OR REPLACE VIEW router_route_statistics AS
SELECT
    r.router_id,
    r.hostname,
    COUNT(rt.route_id) AS total_routes,
    COUNT(rt.route_id) FILTER (
        WHERE rt.state = 'ACTIVE'
    ) AS active_routes,
    COUNT(rt.route_id) FILTER (
        WHERE rt.is_default
    ) AS default_routes,
    COUNT(rt.route_id) FILTER (
        WHERE family(rt.destination) = 4
    ) AS ipv4_routes,
    COUNT(rt.route_id) FILTER (
        WHERE family(rt.destination) = 6
    ) AS ipv6_routes
FROM routers r
LEFT JOIN routes rt
    ON rt.router_id = r.router_id
GROUP BY r.router_id, r.hostname;


/* ============================================================================
   SAMPLE DATA
   ============================================================================ */

INSERT INTO routers (
    hostname,
    location,
    management_ip
)
VALUES
    ('router-lucknow-01', 'Lucknow Data Center', '192.168.10.1'),
    ('router-delhi-01', 'Delhi Data Center', '10.10.10.1');


INSERT INTO network_interfaces (
    router_id,
    interface_name,
    state,
    mtu,
    mac_address
)
SELECT
    router_id,
    interface_name,
    'UP',
    mtu,
    mac
FROM (
    SELECT
        r.router_id,
        v.interface_name,
        v.mtu,
        v.mac
    FROM routers r
    CROSS JOIN (
        VALUES
            ('eth0', 1500, '02:00:00:00:00:01'::macaddr),
            ('eth1', 1500, '02:00:00:00:00:02'::macaddr),
            ('eth2', 9000, '02:00:00:00:00:03'::macaddr)
    ) AS v(interface_name, mtu, mac)
    WHERE r.hostname = 'router-lucknow-01'
) AS interfaces;


INSERT INTO interface_addresses (
    interface_id,
    address,
    role
)
SELECT
    ni.interface_id,
    v.address::cidr,
    v.role::address_role
FROM network_interfaces ni
JOIN routers r
    ON r.router_id = ni.router_id
JOIN (
    VALUES
        ('eth0', '192.168.10.1/24', 'PRIMARY'),
        ('eth1', '10.0.0.1/24', 'PRIMARY'),
        ('eth2', '2001:db8:1::1/64', 'PRIMARY')
) AS v(interface_name, address, role)
    ON v.interface_name = ni.interface_name
WHERE r.hostname = 'router-lucknow-01';


/* ============================================================================
   ROUTE RECORDS
   ============================================================================ */

INSERT INTO routes (
    router_id,
    destination,
    interface_id,
    next_hop,
    metric,
    state
)
SELECT
    r.router_id,
    v.destination::cidr,
    ni.interface_id,
    v.next_hop::inet,
    v.metric,
    'ACTIVE'
FROM routers r
JOIN (
    VALUES
        ('eth0', '192.168.10.0/24', NULL::text, 0),
        ('eth1', '10.0.0.0/24', NULL::text, 0),
        ('eth1', '172.16.0.0/16', '10.0.0.2', 50),
        ('eth1', '172.16.10.0/24', '10.0.0.3', 10),
        ('eth2', '2001:db8:1::/64', NULL::text, 0),
        ('eth2', '2001:db8:2::/64', '2001:db8:1::2', 100)
) AS v(interface_name, destination, next_hop, metric)
    ON TRUE
JOIN network_interfaces ni
    ON ni.router_id = r.router_id
   AND ni.interface_name = v.interface_name
WHERE r.hostname = 'router-lucknow-01';


/* ============================================================================
   SAMPLE PACKET PROCESSING
   ============================================================================ */

CALL forward_packet(
    (SELECT router_id FROM routers
     WHERE hostname = 'router-lucknow-01'),
    '192.168.10.20',
    '172.16.10.50',
    1200
);

CALL forward_packet(
    (SELECT router_id FROM routers
     WHERE hostname = 'router-lucknow-01'),
    '192.168.10.20',
    '203.0.113.10',
    1200
);

CALL forward_packet(
    (SELECT router_id FROM routers
     WHERE hostname = 'router-lucknow-01'),
    '192.168.10.20',
    '172.16.10.50',
    2000
);

CALL forward_packet(
    (SELECT router_id FROM routers
     WHERE hostname = 'router-lucknow-01'),
    '192.168.10.99',
    '172.16.10.50',
    1200
);

CALL forward_packet(
    (SELECT router_id FROM routers
     WHERE hostname = 'router-lucknow-01'),
    '2001:db8:1::10',
    '2001:db8:2::20',
    1200
);


/* ============================================================================
   RETRIEVAL QUERIES
   ============================================================================ */

-- Inspect configured interfaces and subnet information.
SELECT *
FROM subnet_inventory
ORDER BY hostname, interface_name;

-- Inspect active routes.
SELECT *
FROM active_routing_table
ORDER BY hostname, destination;

-- Inspect router statistics.
SELECT *
FROM router_route_statistics;


/* ============================================================================
   LONGEST-PREFIX MATCH EVALUATION
   ============================================================================ */

SELECT *
FROM lookup_route(
    (
        SELECT router_id
        FROM routers
        WHERE hostname = 'router-lucknow-01'
    ),
    '172.16.10.50'
);

-- Expected destination network: 172.16.10.0/24.
-- The /24 route takes precedence over the /16 route.


/* ============================================================================
   ADDRESS FAMILY REPORT
   ============================================================================ */

SELECT
    hostname,
    interface_name,
    address,
    CASE family(address)
        WHEN 4 THEN 'IPv4'
        WHEN 6 THEN 'IPv6'
    END AS address_family,
    masklen(address) AS prefix_length,
    network(address) AS subnet
FROM subnet_inventory
ORDER BY hostname, address_family;


/* ============================================================================
   FORWARDING PERFORMANCE REPORT
   ============================================================================ */

SELECT
    r.hostname,
    fl.state,
    COUNT(*) AS packet_count,
    AVG(fl.packet_size)::NUMERIC(12,2) AS average_packet_size,
    MAX(fl.forwarded_at) AS last_packet_time
FROM forwarding_logs fl
JOIN routers r
    ON r.router_id = fl.router_id
GROUP BY r.hostname, fl.state
ORDER BY r.hostname, fl.state;


/* ============================================================================
   ROUTE FAILURE INVESTIGATION
   ============================================================================ */

SELECT
    fl.forwarding_id,
    r.hostname,
    fl.source_address,
    fl.destination_address,
    fl.state,
    fl.error_message,
    fl.forwarded_at
FROM forwarding_logs fl
JOIN routers r
    ON r.router_id = fl.router_id
WHERE fl.state <> 'FORWARDED'
ORDER BY fl.forwarded_at DESC;


/* ============================================================================
   SUBNET CAPACITY REPORT
   ============================================================================ */

SELECT
    hostname,
    interface_name,
    address,
    network(address) AS network_address,
    broadcast(address) AS broadcast_address,
    family(address) AS ip_version,
    masklen(address) AS prefix_length,
    CASE
        WHEN family(address) = 4
             AND masklen(address) <= 30
        THEN power(2::NUMERIC, 32 - masklen(address)) - 2
        WHEN family(address) = 4
        THEN power(2::NUMERIC, 32 - masklen(address))
        ELSE power(2::NUMERIC, 128 - masklen(address))
    END AS theoretical_usable_addresses
FROM subnet_inventory;


/* ============================================================================
   TRANSACTIONAL ROUTE MANAGEMENT
   Example of an atomic route update.
   ============================================================================ */

SAVEPOINT before_route_change;

UPDATE routes
SET metric = 15
WHERE destination = '172.16.10.0/24'
  AND router_id = (
      SELECT router_id
      FROM routers
      WHERE hostname = 'router-lucknow-01'
  );

-- Verify the changed route.
SELECT
    destination,
    metric,
    state
FROM routes
WHERE destination = '172.16.10.0/24';

-- Release savepoint after successful verification.
RELEASE SAVEPOINT before_route_change;


/* ============================================================================
   FINAL DATABASE STATE
   ============================================================================ */

SELECT
    'ROUTERS' AS entity,
    COUNT(*) AS records
FROM routers

UNION ALL

SELECT
    'INTERFACES',
    COUNT(*)
FROM network_interfaces

UNION ALL

SELECT
    'ADDRESSES',
    COUNT(*)
FROM interface_addresses

UNION ALL

SELECT
    'ROUTES',
    COUNT(*)
FROM routes

UNION ALL

SELECT
    'FORWARDING LOGS',
    COUNT(*)
FROM forwarding_logs;


COMMIT;
