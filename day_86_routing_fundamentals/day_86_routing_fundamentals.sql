/*
===============================================================================
ROUTING FUNDAMENTALS
Static Routing, Dynamic Routing, Routing Tables and Routing Algorithms
PostgreSQL 14+

Domain model:
Network
  -> Routers
  -> Interfaces
  -> Links
  -> Routing Protocols
  -> Routing Tables
  -> Routes
  -> Routing Decisions
  -> Link Events
  -> Route Recalculation

This script creates an executable routing-management database,
inserts realistic sample data, evaluates routes, and demonstrates
static and dynamic routing calculations.
===============================================================================
*/

BEGIN;

CREATE SCHEMA IF NOT EXISTS routing;

SET search_path TO routing, public;

-- ============================================================================
-- 1. ENUMERATIONS
-- ============================================================================

CREATE TYPE router_status AS ENUM (
    'ACTIVE',
    'MAINTENANCE',
    'INACTIVE'
);

CREATE TYPE link_status AS ENUM (
    'UP',
    'DOWN',
    'DEGRADED'
);

CREATE TYPE routing_protocol AS ENUM (
    'STATIC',
    'RIP',
    'OSPF'
);

CREATE TYPE route_status AS ENUM (
    'ACTIVE',
    'INACTIVE',
    'WITHDRAWN'
);

CREATE TYPE routing_algorithm AS ENUM (
    'DIJKSTRA',
    'BELLMAN_FORD',
    'STATIC_LOOKUP'
);

-- ============================================================================
-- 2. NETWORK AND ROUTER MANAGEMENT
-- ============================================================================

CREATE TABLE networks (
    network_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    network_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE routers (
    router_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    network_id BIGINT NOT NULL
        REFERENCES networks(network_id) ON DELETE CASCADE,
    router_name VARCHAR(32) NOT NULL,
    management_ip INET NOT NULL,
    router_status router_status NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(network_id, router_name),
    UNIQUE(network_id, management_ip),

    CHECK (family(management_ip) = 4)
);

CREATE TABLE interfaces (
    interface_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    router_id BIGINT NOT NULL
        REFERENCES routers(router_id) ON DELETE CASCADE,
    interface_name VARCHAR(32) NOT NULL,
    ip_address INET NOT NULL,
    subnet CIDR NOT NULL,
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    bandwidth_mbps NUMERIC(12,2) NOT NULL DEFAULT 1000,

    UNIQUE(router_id, interface_name),
    UNIQUE(router_id, ip_address),

    CHECK (family(ip_address) = 4),
    CHECK (family(subnet) = 4),
    CHECK (ip_address <<= subnet),
    CHECK (bandwidth_mbps > 0)
);

-- ============================================================================
-- 3. NETWORK LINKS
-- ============================================================================

CREATE TABLE network_links (
    link_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    source_router_id BIGINT NOT NULL
        REFERENCES routers(router_id),

    destination_router_id BIGINT NOT NULL
        REFERENCES routers(router_id),

    source_interface_id BIGINT NOT NULL
        REFERENCES interfaces(interface_id),

    destination_interface_id BIGINT NOT NULL
        REFERENCES interfaces(interface_id),

    cost NUMERIC(12,3) NOT NULL,
    status link_status NOT NULL DEFAULT 'UP',
    bidirectional BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (source_router_id <> destination_router_id),
    CHECK (cost >= 0),
    CHECK (source_interface_id <> destination_interface_id)
);

CREATE INDEX idx_links_source
    ON network_links(source_router_id, status);

CREATE INDEX idx_links_destination
    ON network_links(destination_router_id, status);

-- ============================================================================
-- 4. ROUTING PROTOCOL CONFIGURATION
-- ============================================================================

CREATE TABLE routing_protocols (
    protocol_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    router_id BIGINT NOT NULL
        REFERENCES routers(router_id) ON DELETE CASCADE,

    protocol routing_protocol NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    administrative_distance INTEGER NOT NULL,

    update_interval_seconds INTEGER,
    hold_down_seconds INTEGER,
    max_hops INTEGER,

    UNIQUE(router_id, protocol),

    CHECK (administrative_distance >= 0),
    CHECK (
        update_interval_seconds IS NULL OR
        update_interval_seconds > 0
    ),
    CHECK (
        hold_down_seconds IS NULL OR
        hold_down_seconds >= 0
    ),
    CHECK (
        max_hops IS NULL OR
        max_hops BETWEEN 1 AND 255
    ),
    CHECK (
        (protocol = 'STATIC' AND update_interval_seconds IS NULL)
        OR protocol <> 'STATIC'
    )
);

-- ============================================================================
-- 5. ROUTING TABLES
-- ============================================================================

CREATE TABLE routing_tables (
    table_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    router_id BIGINT NOT NULL
        REFERENCES routers(router_id) ON DELETE CASCADE,

    table_name VARCHAR(64) NOT NULL DEFAULT 'main',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(router_id, table_name)
);

CREATE TABLE routes (
    route_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    table_id BIGINT NOT NULL
        REFERENCES routing_tables(table_id) ON DELETE CASCADE,

    destination_network CIDR NOT NULL,

    next_hop INET,
    outgoing_interface_id BIGINT
        REFERENCES interfaces(interface_id),

    protocol routing_protocol NOT NULL,
    metric NUMERIC(12,3) NOT NULL DEFAULT 0,
    administrative_distance INTEGER NOT NULL,

    status route_status NOT NULL DEFAULT 'ACTIVE',

    is_default_route BOOLEAN GENERATED ALWAYS AS (
        destination_network = '0.0.0.0/0'::CIDR
    ) STORED,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (family(destination_network) = 4),
    CHECK (next_hop IS NULL OR family(next_hop) = 4),
    CHECK (metric >= 0),
    CHECK (administrative_distance >= 0),

    CHECK (
        next_hop IS NOT NULL OR
        outgoing_interface_id IS NOT NULL
    )
);

CREATE INDEX idx_routes_table_status
    ON routes(table_id, status);

CREATE INDEX idx_routes_destination
    ON routes USING GIST(destination_network inet_ops);

CREATE INDEX idx_routes_protocol
    ON routes(protocol, administrative_distance, metric);

CREATE INDEX idx_routes_active_prefix
    ON routes(table_id, masklen(destination_network) DESC)
    WHERE status = 'ACTIVE';

-- ============================================================================
-- 6. ROUTING EVENTS AND FORWARDING DECISIONS
-- ============================================================================

CREATE TABLE routing_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    link_id BIGINT REFERENCES network_links(link_id),
    router_id BIGINT REFERENCES routers(router_id),
    previous_status link_status,
    current_status link_status NOT NULL,
    event_description TEXT,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE forwarding_decisions (
    decision_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    router_id BIGINT NOT NULL
        REFERENCES routers(router_id),

    destination_ip INET NOT NULL,
    selected_route_id BIGINT REFERENCES routes(route_id),

    next_hop INET,
    outgoing_interface_id BIGINT REFERENCES interfaces(interface_id),

    decision_status VARCHAR(20) NOT NULL,
    decision_reason TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (family(destination_ip) = 4),
    CHECK (
        decision_status IN (
            'FORWARDED',
            'NO_ROUTE',
            'REJECTED'
        )
    )
);

CREATE INDEX idx_forwarding_router_time
    ON forwarding_decisions(router_id, created_at DESC);

-- ============================================================================
-- 7. ROUTE INTEGRITY TRIGGER
-- ============================================================================

CREATE OR REPLACE FUNCTION validate_route_configuration()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    route_router_id BIGINT;
    interface_router_id BIGINT;
BEGIN
    SELECT router_id
    INTO route_router_id
    FROM routing_tables
    WHERE table_id = NEW.table_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Routing table does not exist';
    END IF;

    IF NEW.outgoing_interface_id IS NOT NULL THEN

        SELECT router_id
        INTO interface_router_id
        FROM interfaces
        WHERE interface_id = NEW.outgoing_interface_id;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'Outgoing interface does not exist';
        END IF;

        IF interface_router_id <> route_router_id THEN
            RAISE EXCEPTION
                'Outgoing interface must belong to the route owner';
        END IF;
    END IF;

    IF NEW.next_hop IS NOT NULL AND
       NOT EXISTS (
           SELECT 1
           FROM interfaces i
           WHERE i.router_id = route_router_id
             AND i.is_enabled = TRUE
             AND NEW.next_hop <<= i.subnet
       ) THEN

        RAISE EXCEPTION
            'Next hop must be reachable through an enabled local interface';
    END IF;

    NEW.updated_at = CURRENT_TIMESTAMP;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_route
BEFORE INSERT OR UPDATE ON routes
FOR EACH ROW
EXECUTE FUNCTION validate_route_configuration();

-- ============================================================================
-- 8. LINK STATE EVENT TRIGGER
-- ============================================================================

CREATE OR REPLACE FUNCTION record_link_state_change()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO routing_events (
            link_id,
            router_id,
            previous_status,
            current_status,
            event_description
        )
        VALUES (
            NEW.link_id,
            NEW.source_router_id,
            OLD.status,
            NEW.status,
            'Network link state changed'
        );

        NEW.updated_at = CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_link_state_change
BEFORE UPDATE OF status ON network_links
FOR EACH ROW
EXECUTE FUNCTION record_link_state_change();

-- ============================================================================
-- 9. LONGEST PREFIX MATCHING
-- ============================================================================

CREATE OR REPLACE FUNCTION lookup_route(
    p_router_id BIGINT,
    p_destination INET
)
RETURNS TABLE (
    route_id BIGINT,
    destination_network CIDR,
    next_hop INET,
    interface_id BIGINT,
    protocol routing_protocol,
    metric NUMERIC,
    administrative_distance INTEGER
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        r.route_id,
        r.destination_network,
        r.next_hop,
        r.outgoing_interface_id,
        r.protocol,
        r.metric,
        r.administrative_distance
    FROM routing_tables rt
    JOIN routes r ON r.table_id = rt.table_id
    WHERE rt.router_id = p_router_id
      AND r.status = 'ACTIVE'
      AND p_destination <<= r.destination_network
    ORDER BY
        masklen(r.destination_network) DESC,
        r.administrative_distance ASC,
        r.metric ASC
    LIMIT 1;
$$;

-- ============================================================================
-- 10. DIJKSTRA SHORTEST-PATH FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION calculate_dijkstra(
    p_source_router BIGINT
)
RETURNS TABLE (
    destination_router BIGINT,
    total_cost NUMERIC,
    next_hop_router BIGINT
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    current_router BIGINT;
    current_cost NUMERIC;
    edge RECORD;
    candidate_cost NUMERIC;
    candidate_hop BIGINT;
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM routers
        WHERE router_id = p_source_router
          AND router_status = 'ACTIVE'
    ) THEN
        RAISE EXCEPTION 'Source router is not active';
    END IF;

    CREATE TEMP TABLE IF NOT EXISTS dijkstra_work (
        router_id BIGINT PRIMARY KEY,
        distance NUMERIC NOT NULL,
        next_hop BIGINT,
        visited BOOLEAN NOT NULL DEFAULT FALSE
    ) ON COMMIT DROP;

    TRUNCATE dijkstra_work;

    INSERT INTO dijkstra_work(router_id, distance)
    SELECT router_id, 1000000000000000
    FROM routers
    WHERE router_status = 'ACTIVE';

    UPDATE dijkstra_work
    SET distance = 0
    WHERE router_id = p_source_router;

    LOOP
        SELECT router_id, distance
        INTO current_router, current_cost
        FROM dijkstra_work
        WHERE visited = FALSE
          AND distance < 1000000000000000
        ORDER BY distance, router_id
        LIMIT 1;

        EXIT WHEN NOT FOUND;

        UPDATE dijkstra_work
        SET visited = TRUE
        WHERE router_id = current_router;

        FOR edge IN
            SELECT
                nl.destination_router_id,
                nl.cost
            FROM network_links nl
            JOIN routers destination
                ON destination.router_id =
                   nl.destination_router_id
            WHERE nl.source_router_id = current_router
              AND nl.status = 'UP'
              AND destination.router_status = 'ACTIVE'

            UNION ALL

            SELECT
                nl.source_router_id,
                nl.cost
            FROM network_links nl
            JOIN routers source
                ON source.router_id = nl.source_router_id
            WHERE nl.destination_router_id = current_router
              AND nl.status = 'UP'
              AND nl.bidirectional = TRUE
              AND source.router_status = 'ACTIVE'
        LOOP
            candidate_cost := current_cost + edge.cost;

            candidate_hop :=
                CASE
                    WHEN current_router = p_source_router
                    THEN edge.destination_router_id
                    ELSE (
                        SELECT w.next_hop
                        FROM dijkstra_work w
                        WHERE w.router_id = current_router
                    )
                END;

            UPDATE dijkstra_work
            SET
                distance = candidate_cost,
                next_hop = candidate_hop
            WHERE router_id = edge.destination_router_id
              AND visited = FALSE
              AND candidate_cost < distance;
        END LOOP;
    END LOOP;

    RETURN QUERY
    SELECT
        w.router_id,
        w.distance,
        w.next_hop
    FROM dijkstra_work w
    ORDER BY w.router_id;
END;
$$;

-- ============================================================================
-- 11. DISTANCE-VECTOR RELAXATION
-- ============================================================================

CREATE OR REPLACE FUNCTION calculate_distance_vector(
    p_source_router BIGINT
)
RETURNS TABLE (
    destination_router BIGINT,
    total_cost NUMERIC,
    next_hop_router BIGINT
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    iteration_count INTEGER;
    changed_count BIGINT;
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM routers
        WHERE router_id = p_source_router
          AND router_status = 'ACTIVE'
    ) THEN
        RAISE EXCEPTION 'Source router is not active';
    END IF;

    CREATE TEMP TABLE IF NOT EXISTS dv_work (
        router_id BIGINT PRIMARY KEY,
        distance NUMERIC NOT NULL,
        next_hop BIGINT
    ) ON COMMIT DROP;

    CREATE TEMP TABLE IF NOT EXISTS dv_snapshot (
        router_id BIGINT PRIMARY KEY,
        distance NUMERIC NOT NULL,
        next_hop BIGINT
    ) ON COMMIT DROP;

    TRUNCATE dv_work, dv_snapshot;

    INSERT INTO dv_work(router_id, distance)
    SELECT router_id, 1000000000000000
    FROM routers
    WHERE router_status = 'ACTIVE';

    UPDATE dv_work
    SET distance = 0
    WHERE router_id = p_source_router;

    FOR iteration_count IN 1..(
        SELECT GREATEST(COUNT(*)::INTEGER - 1, 1)
        FROM routers
        WHERE router_status = 'ACTIVE'
    )
    LOOP
        TRUNCATE dv_snapshot;

        INSERT INTO dv_snapshot
        SELECT * FROM dv_work;

        WITH edges AS (
            SELECT
                source_router_id AS source_id,
                destination_router_id AS destination_id,
                cost
            FROM network_links
            WHERE status = 'UP'

            UNION ALL

            SELECT
                destination_router_id,
                source_router_id,
                cost
            FROM network_links
            WHERE status = 'UP'
              AND bidirectional = TRUE
        ),
        candidates AS (
            SELECT
                e.destination_id,
                s.distance + e.cost AS candidate_cost,
                CASE
                    WHEN s.router_id = p_source_router
                    THEN e.destination_id
                    ELSE s.next_hop
                END AS candidate_hop
            FROM edges e
            JOIN dv_snapshot s
                ON s.router_id = e.source_id
            WHERE s.distance < 1000000000000000
        ),
        best AS (
            SELECT DISTINCT ON (destination_id)
                destination_id,
                candidate_cost,
                candidate_hop
            FROM candidates
            ORDER BY
                destination_id,
                candidate_cost,
                candidate_hop
        )
        UPDATE dv_work target
        SET
            distance = best.candidate_cost,
            next_hop = best.candidate_hop
        FROM best
        WHERE target.router_id = best.destination_id
          AND best.candidate_cost < target.distance;

        GET DIAGNOSTICS changed_count = ROW_COUNT;

        EXIT WHEN changed_count = 0;
    END LOOP;

    RETURN QUERY
    SELECT
        router_id,
        distance,
        next_hop
    FROM dv_work
    ORDER BY router_id;
END;
$$;

-- ============================================================================
-- 12. ROUTING ELIGIBILITY REPORT
-- ============================================================================

CREATE OR REPLACE VIEW active_routing_summary AS
SELECT
    r.router_id,
    r.router_name,
    rt.table_name,
    COUNT(routes.route_id) AS total_routes,
    COUNT(*) FILTER (
        WHERE routes.status = 'ACTIVE'
    ) AS active_routes,
    COUNT(*) FILTER (
        WHERE routes.protocol = 'STATIC'
          AND routes.status = 'ACTIVE'
    ) AS static_routes,
    COUNT(*) FILTER (
        WHERE routes.protocol = 'OSPF'
          AND routes.status = 'ACTIVE'
    ) AS ospf_routes,
    COUNT(*) FILTER (
        WHERE routes.protocol = 'RIP'
          AND routes.status = 'ACTIVE'
    ) AS rip_routes
FROM routers r
JOIN routing_tables rt
    ON rt.router_id = r.router_id
LEFT JOIN routes
    ON routes.table_id = rt.table_id
GROUP BY
    r.router_id,
    r.router_name,
    rt.table_name;

-- ============================================================================
-- 13. SAMPLE NETWORK
-- ============================================================================

INSERT INTO networks(network_name, description)
VALUES (
    'ENTERPRISE_NETWORK',
    'Four-router enterprise network for routing evaluation'
);

INSERT INTO routers(
    network_id,
    router_name,
    management_ip
)
SELECT
    network_id,
    data.router_name,
    data.management_ip::INET
FROM networks
CROSS JOIN (
    VALUES
        ('R1', '10.255.0.1'),
        ('R2', '10.255.0.2'),
        ('R3', '10.255.0.3'),
        ('R4', '10.255.0.4')
) AS data(router_name, management_ip)
WHERE network_name = 'ENTERPRISE_NETWORK';

-- ============================================================================
-- 14. INTERFACES
-- ============================================================================

INSERT INTO interfaces(
    router_id,
    interface_name,
    ip_address,
    subnet,
    bandwidth_mbps
)
SELECT
    r.router_id,
    data.interface_name,
    data.ip_address::INET,
    data.subnet::CIDR,
    data.bandwidth
FROM routers r
JOIN (
    VALUES
        ('R1', 'eth0', '10.0.12.1', '10.0.12.0/24', 1000::NUMERIC),
        ('R1', 'eth1', '10.0.13.1', '10.0.13.0/24', 1000::NUMERIC),
        ('R1', 'lan0', '192.168.1.1', '192.168.1.0/24', 1000::NUMERIC),

        ('R2', 'eth0', '10.0.12.2', '10.0.12.0/24', 1000::NUMERIC),
        ('R2', 'eth1', '10.0.23.1', '10.0.23.0/24', 1000::NUMERIC),
        ('R2', 'eth2', '10.0.24.1', '10.0.24.0/24', 1000::NUMERIC),

        ('R3', 'eth0', '10.0.13.2', '10.0.13.0/24', 1000::NUMERIC),
        ('R3', 'eth1', '10.0.23.2', '10.0.23.0/24', 1000::NUMERIC),
        ('R3', 'eth2', '10.0.34.1', '10.0.34.0/24', 1000::NUMERIC),

        ('R4', 'eth0', '10.0.24.2', '10.0.24.0/24', 1000::NUMERIC),
        ('R4', 'eth1', '10.0.34.2', '10.0.34.0/24', 1000::NUMERIC),
        ('R4', 'lan0', '192.168.4.1', '192.168.4.0/24', 1000::NUMERIC)
) AS data(
    router_name,
    interface_name,
    ip_address,
    subnet,
    bandwidth
)
ON data.router_name = r.router_name;

-- ============================================================================
-- 15. ROUTER LINKS
-- ============================================================================

INSERT INTO network_links(
    source_router_id,
    destination_router_id,
    source_interface_id,
    destination_interface_id,
    cost,
    status,
    bidirectional
)
SELECT
    source.router_id,
    destination.router_id,
    source_interface.interface_id,
    destination_interface.interface_id,
    data.cost,
    'UP',
    TRUE
FROM (
    VALUES
        ('R1', 'R2', 'eth0', 'eth0', 2::NUMERIC),
        ('R1', 'R3', 'eth1', 'eth0', 5::NUMERIC),
        ('R2', 'R3', 'eth1', 'eth1', 1::NUMERIC),
        ('R2', 'R4', 'eth2', 'eth0', 7::NUMERIC),
        ('R3', 'R4', 'eth2', 'eth1', 2::NUMERIC)
) AS data(source_name, destination_name,
          source_if, destination_if, cost)

JOIN routers source
    ON source.router_name = data.source_name

JOIN routers destination
    ON destination.router_name = data.destination_name

JOIN interfaces source_interface
    ON source_interface.router_id = source.router_id
   AND source_interface.interface_name = data.source_if

JOIN interfaces destination_interface
    ON destination_interface.router_id = destination.router_id
   AND destination_interface.interface_name = data.destination_if;

-- ============================================================================
-- 16. ROUTING PROTOCOL CONFIGURATION
-- ============================================================================

INSERT INTO routing_protocols(
    router_id,
    protocol,
    enabled,
    administrative_distance,
    update_interval_seconds,
    hold_down_seconds,
    max_hops
)
SELECT
    r.router_id,
    p.protocol::routing_protocol,
    TRUE,
    p.distance,
    p.interval,
    p.hold_down,
    p.max_hops
FROM routers r
CROSS JOIN (
    VALUES
        ('STATIC', 1, NULL::INTEGER, NULL::INTEGER, NULL::INTEGER),
        ('OSPF', 110, 10, 30, NULL::INTEGER),
        ('RIP', 120, 30, 180, 15)
) AS p(protocol, distance, interval, hold_down, max_hops);

-- ============================================================================
-- 17. ROUTING TABLE CREATION
-- ============================================================================

INSERT INTO routing_tables(router_id, table_name)
SELECT router_id, 'main'
FROM routers;

-- ============================================================================
-- 18. STATIC ROUTE INSTALLATION
-- ============================================================================

INSERT INTO routes(
    table_id,
    destination_network,
    next_hop,
    outgoing_interface_id,
    protocol,
    metric,
    administrative_distance
)
SELECT
    rt.table_id,
    '172.16.0.0/16'::CIDR,
    '10.0.12.2'::INET,
    i.interface_id,
    'STATIC',
    1,
    1
FROM routing_tables rt
JOIN routers r
    ON r.router_id = rt.router_id
JOIN interfaces i
    ON i.router_id = r.router_id
   AND i.interface_name = 'eth0'
WHERE r.router_name = 'R1';

-- ============================================================================
-- 19. DYNAMIC ROUTE INSTALLATION FROM DIJKSTRA
-- ============================================================================

WITH source_router AS (
    SELECT router_id
    FROM routers
    WHERE router_name = 'R1'
),
paths AS (
    SELECT *
    FROM calculate_dijkstra(
        (SELECT router_id FROM source_router)
    )
),
destination_networks AS (
    SELECT *
    FROM (
        VALUES
            ('R2', '10.0.2.0/24'),
            ('R3', '10.0.3.0/24'),
            ('R4', '10.0.4.0/24')
    ) AS d(router_name, destination_network)
)
INSERT INTO routes(
    table_id,
    destination_network,
    next_hop,
    outgoing_interface_id,
    protocol,
    metric,
    administrative_distance
)
SELECT
    rt.table_id,
    d.destination_network::CIDR,
    nh.ip_address,
    outgoing.interface_id,
    'OSPF',
    paths.total_cost,
    110
FROM paths
JOIN routers destination
    ON destination.router_id = paths.destination_router
JOIN destination_networks d
    ON d.router_name = destination.router_name
JOIN routers source
    ON source.router_name = 'R1'
JOIN routing_tables rt
    ON rt.router_id = source.router_id
JOIN routers next_router
    ON next_router.router_id = paths.next_hop_router
JOIN interfaces nh
    ON nh.router_id = next_router.router_id
   AND nh.interface_name = 'eth0'
JOIN interfaces outgoing
    ON outgoing.router_id = source.router_id
   AND outgoing.interface_name = 'eth0'
WHERE paths.total_cost < 1000000000000000
  AND paths.next_hop_router IS NOT NULL;

-- ============================================================================
-- 20. ROUTE LOOKUP EXAMPLES
-- ============================================================================

-- Longest prefix match.
SELECT *
FROM lookup_route(
    (SELECT router_id FROM routers WHERE router_name = 'R1'),
    '192.168.1.25'::INET
);

-- Static route retrieval.
SELECT
    r.destination_network,
    r.next_hop,
    r.protocol,
    r.metric,
    r.administrative_distance
FROM routes r
JOIN routing_tables rt
    ON rt.table_id = r.table_id
JOIN routers router
    ON router.router_id = rt.router_id
WHERE router.router_name = 'R1'
  AND r.status = 'ACTIVE'
ORDER BY masklen(r.destination_network) DESC;

-- ============================================================================
-- 21. SHORTEST-PATH REPORT
-- ============================================================================

SELECT
    source.router_name AS source_router,
    destination.router_name AS destination_router,
    result.total_cost,
    next_router.router_name AS next_hop
FROM calculate_dijkstra(
    (SELECT router_id FROM routers WHERE router_name = 'R1')
) result
JOIN routers source
    ON source.router_name = 'R1'
JOIN routers destination
    ON destination.router_id = result.destination_router
LEFT JOIN routers next_router
    ON next_router.router_id = result.next_hop_router
ORDER BY result.total_cost;

-- ============================================================================
-- 22. DISTANCE-VECTOR REPORT
-- ============================================================================

SELECT
    destination.router_name,
    result.total_cost,
    next_router.router_name AS next_hop
FROM calculate_distance_vector(
    (SELECT router_id FROM routers WHERE router_name = 'R1')
) result
JOIN routers destination
    ON destination.router_id = result.destination_router
LEFT JOIN routers next_router
    ON next_router.router_id = result.next_hop_router
ORDER BY result.total_cost;

-- ============================================================================
-- 23. LINK FAILURE AND ROUTE RECALCULATION
-- ============================================================================

SAVEPOINT before_link_failure;

UPDATE network_links
SET status = 'DOWN'
WHERE source_router_id = (
    SELECT router_id FROM routers WHERE router_name = 'R2'
)
AND destination_router_id = (
    SELECT router_id FROM routers WHERE router_name = 'R3'
);

-- The following query recalculates paths using the changed topology.
SELECT
    destination.router_name,
    result.total_cost,
    next_router.router_name AS next_hop
FROM calculate_dijkstra(
    (SELECT router_id FROM routers WHERE router_name = 'R1')
) result
JOIN routers destination
    ON destination.router_id = result.destination_router
LEFT JOIN routers next_router
    ON next_router.router_id = result.next_hop_router
ORDER BY result.total_cost;

-- Restore the original topology for subsequent examples.
ROLLBACK TO SAVEPOINT before_link_failure;

-- ============================================================================
-- 24. PACKET FORWARDING DECISION
-- ============================================================================

CREATE OR REPLACE FUNCTION record_forwarding_decision(
    p_router_id BIGINT,
    p_destination INET
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    selected routes%ROWTYPE;
    new_decision_id BIGINT;
BEGIN
    SELECT r.*
    INTO selected
    FROM routing_tables rt
    JOIN routes r
        ON r.table_id = rt.table_id
    WHERE rt.router_id = p_router_id
      AND r.status = 'ACTIVE'
      AND p_destination <<= r.destination_network
    ORDER BY
        masklen(r.destination_network) DESC,
        r.administrative_distance,
        r.metric
    LIMIT 1;

    IF NOT FOUND THEN
        INSERT INTO forwarding_decisions(
            router_id,
            destination_ip,
            decision_status,
            decision_reason
        )
        VALUES (
            p_router_id,
            p_destination,
            'NO_ROUTE',
            'No matching active route'
        )
        RETURNING decision_id INTO new_decision_id;

        RETURN new_decision_id;
    END IF;

    INSERT INTO forwarding_decisions(
        router_id,
        destination_ip,
        selected_route_id,
        next_hop,
        outgoing_interface_id,
        decision_status,
        decision_reason
    )
    VALUES (
        p_router_id,
        p_destination,
        selected.route_id,
        selected.next_hop,
        selected.outgoing_interface_id,
        'FORWARDED',
        'Longest prefix and route preference selected'
    )
    RETURNING decision_id INTO new_decision_id;

    RETURN new_decision_id;
END;
$$;

-- Valid forwarding decision.
SELECT record_forwarding_decision(
    (SELECT router_id FROM routers WHERE router_name = 'R1'),
    '172.16.10.5'::INET
);

-- Unmatched destination.
SELECT record_forwarding_decision(
    (SELECT router_id FROM routers WHERE router_name = 'R1'),
    '203.0.113.10'::INET
);

-- ============================================================================
-- 25. REPORTING QUERIES
-- ============================================================================

-- Route count by router and protocol.
SELECT
    router.router_name,
    route.protocol,
    COUNT(*) AS route_count,
    AVG(route.metric) AS average_metric
FROM routes route
JOIN routing_tables rt
    ON rt.table_id = route.table_id
JOIN routers router
    ON router.router_id = rt.router_id
GROUP BY router.router_name, route.protocol
ORDER BY router.router_name, route.protocol;

-- Routing table summary.
SELECT *
FROM active_routing_summary
ORDER BY router_name;

-- Link availability report.
SELECT
    source.router_name AS source,
    destination.router_name AS destination,
    link.cost,
    link.status,
    link.bidirectional
FROM network_links link
JOIN routers source
    ON source.router_id = link.source_router_id
JOIN routers destination
    ON destination.router_id = link.destination_router_id
ORDER BY source.router_name, destination.router_name;

-- Protocol configuration report.
SELECT
    router.router_name,
    protocol.protocol,
    protocol.enabled,
    protocol.administrative_distance,
    protocol.update_interval_seconds,
    protocol.max_hops
FROM routing_protocols protocol
JOIN routers router
    ON router.router_id = protocol.router_id
ORDER BY router.router_name, protocol.protocol;

-- Forwarding history.
SELECT
    router.router_name,
    decision.destination_ip,
    decision.decision_status,
    decision.next_hop,
    decision.created_at
FROM forwarding_decisions decision
JOIN routers router
    ON router.router_id = decision.router_id
ORDER BY decision.created_at DESC;

-- ============================================================================
-- 26. VALIDATION QUERIES
-- ============================================================================

-- Routers without routing tables.
SELECT router_name
FROM routers r
WHERE NOT EXISTS (
    SELECT 1
    FROM routing_tables rt
    WHERE rt.router_id = r.router_id
);

-- Enabled protocols without an active routing configuration.
SELECT
    router.router_name,
    protocol.protocol
FROM routing_protocols protocol
JOIN routers router
    ON router.router_id = protocol.router_id
WHERE protocol.enabled = TRUE
  AND NOT EXISTS (
      SELECT 1
      FROM routing_tables rt
      JOIN routes route
          ON route.table_id = rt.table_id
      WHERE rt.router_id = protocol.router_id
        AND route.protocol = protocol.protocol
        AND route.status = 'ACTIVE'
  );

-- Routes pointing to disabled interfaces.
SELECT
    router.router_name,
    route.destination_network,
    interface.interface_name
FROM routes route
JOIN routing_tables rt
    ON rt.table_id = route.table_id
JOIN routers router
    ON router.router_id = rt.router_id
JOIN interfaces interface
    ON interface.interface_id = route.outgoing_interface_id
WHERE route.status = 'ACTIVE'
  AND interface.is_enabled = FALSE;

-- ============================================================================
-- 27. TRANSACTION DEMONSTRATION
-- ============================================================================

-- A configuration change can be rolled back if validation fails.
SAVEPOINT configuration_test;

UPDATE routes
SET status = 'INACTIVE'
WHERE protocol = 'OSPF'
  AND destination_network = '10.0.4.0/24'::CIDR;

SELECT
    destination_network,
    status
FROM routes
WHERE protocol = 'OSPF';

ROLLBACK TO SAVEPOINT configuration_test;

-- ============================================================================
-- 28. FINAL DATA INTEGRITY CHECK
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM routers WHERE router_name = 'R1'
    ) THEN
        RAISE EXCEPTION 'Sample router R1 missing';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM routing_tables
    ) THEN
        RAISE EXCEPTION 'Routing tables were not created';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM routes
    ) THEN
        RAISE EXCEPTION 'Routes were not installed';
    END IF;

    RAISE NOTICE 'Routing database validation successful';
END;
$$;

COMMIT;
