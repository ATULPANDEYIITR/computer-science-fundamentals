/*
===============================================================================
PHYSICAL AND DATA LINK LAYER
PostgreSQL 15+

Domain:
    Physical signals
    Network devices
    Interfaces
    MAC addresses
    Ethernet frames
    CRC-32/FCS
    Ethernet switching
    MAC address learning
    Forwarding decisions
    MAC aging
    Network statistics

The database models Ethernet switching and records frame-processing
decisions. It does not simulate electrical waveforms or replace a
hardware Ethernet controller.
===============================================================================
*/

BEGIN;

CREATE SCHEMA IF NOT EXISTS network_lab;

SET search_path TO network_lab, public;

-- ============================================================================
-- 1. ENUMERATED DOMAIN TYPES
-- ============================================================================

CREATE TYPE device_type AS ENUM (
    'SWITCH',
    'HOST',
    'ROUTER',
    'ACCESS_POINT'
);

CREATE TYPE interface_status AS ENUM (
    'UP',
    'DOWN',
    'ADMIN_DISABLED'
);

CREATE TYPE encoding_type AS ENUM (
    'NRZ',
    'MANCHESTER',
    'PAM4',
    'OTHER'
);

CREATE TYPE frame_status AS ENUM (
    'RECEIVED',
    'VALIDATED',
    'CORRUPTED',
    'DROPPED',
    'FORWARDED'
);

CREATE TYPE forwarding_action AS ENUM (
    'UNICAST',
    'FLOOD',
    'BROADCAST',
    'MULTICAST',
    'DROP',
    'FILTERED'
);

-- ============================================================================
-- 2. NETWORK DEVICES
-- ============================================================================

CREATE TABLE network_devices (
    device_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    device_name VARCHAR(100) NOT NULL UNIQUE,

    device_type device_type NOT NULL,

    management_ip INET,

    location VARCHAR(150),

    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 3. NETWORK INTERFACES
-- ============================================================================

CREATE TABLE network_interfaces (
    interface_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    device_id BIGINT NOT NULL
        REFERENCES network_devices(device_id)
        ON DELETE CASCADE,

    interface_name VARCHAR(50) NOT NULL,

    mac_address MACADDR NOT NULL,

    status interface_status NOT NULL DEFAULT 'UP',

    speed_mbps INTEGER NOT NULL DEFAULT 1000
        CHECK (speed_mbps > 0),

    mtu INTEGER NOT NULL DEFAULT 1500
        CHECK (mtu BETWEEN 46 AND 9000),

    duplex_mode VARCHAR(10) NOT NULL DEFAULT 'FULL'
        CHECK (duplex_mode IN ('FULL', 'HALF')),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(device_id, interface_name),

    UNIQUE(device_id, mac_address)
);

CREATE INDEX idx_interfaces_mac
    ON network_interfaces(mac_address);

CREATE INDEX idx_interfaces_device_status
    ON network_interfaces(device_id, status);

-- ============================================================================
-- 4. PHYSICAL SIGNAL TRANSMISSION RECORDS
-- ============================================================================

CREATE TABLE signal_transmissions (
    signal_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    interface_id BIGINT NOT NULL
        REFERENCES network_interfaces(interface_id),

    encoding encoding_type NOT NULL,

    bit_rate BIGINT NOT NULL
        CHECK (bit_rate > 0),

    amplitude NUMERIC(10, 4)
        CHECK (amplitude > 0),

    bit_count BIGINT NOT NULL
        CHECK (bit_count > 0),

    noise_ratio NUMERIC(8, 6) NOT NULL DEFAULT 0
        CHECK (noise_ratio BETWEEN 0 AND 1),

    transmission_duration INTERVAL,

    transmitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_signal_transmissions_time
    ON signal_transmissions(transmitted_at DESC);

-- ============================================================================
-- 5. ETHERNET FRAMES
-- ============================================================================

CREATE TABLE ethernet_frames (
    frame_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    source_mac MACADDR NOT NULL,

    destination_mac MACADDR NOT NULL,

    ether_type INTEGER NOT NULL DEFAULT 2048
        CHECK (ether_type BETWEEN 0 AND 65535),

    payload_length INTEGER NOT NULL
        CHECK (payload_length BETWEEN 0 AND 1500),

    payload BYTEA NOT NULL,

    fcs BIGINT
        CHECK (fcs BETWEEN 0 AND 4294967295),

    frame_length INTEGER GENERATED ALWAYS AS (
        14 + GREATEST(payload_length, 46) + 4
    ) STORED,

    status frame_status NOT NULL DEFAULT 'RECEIVED',

    received_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (source_mac <> destination_mac),

    CHECK (NOT macaddr_is_multicast(source_mac)),

    CHECK (octet_length(payload) = payload_length)
);

CREATE INDEX idx_frames_source
    ON ethernet_frames(source_mac);

CREATE INDEX idx_frames_destination
    ON ethernet_frames(destination_mac);

CREATE INDEX idx_frames_received
    ON ethernet_frames(received_at DESC);

CREATE INDEX idx_frames_status
    ON ethernet_frames(status, received_at DESC);

-- ============================================================================
-- 6. FRAME INGRESS AND EGRESS RECORDS
-- ============================================================================

CREATE TABLE frame_ingress (
    ingress_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    frame_id BIGINT NOT NULL
        REFERENCES ethernet_frames(frame_id)
        ON DELETE CASCADE,

    interface_id BIGINT NOT NULL
        REFERENCES network_interfaces(interface_id),

    received_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(frame_id, interface_id)
);

CREATE TABLE frame_egress (
    egress_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    frame_id BIGINT NOT NULL
        REFERENCES ethernet_frames(frame_id)
        ON DELETE CASCADE,

    interface_id BIGINT NOT NULL
        REFERENCES network_interfaces(interface_id),

    action forwarding_action NOT NULL,

    transmitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(frame_id, interface_id)
);

CREATE INDEX idx_egress_interface_time
    ON frame_egress(interface_id, transmitted_at DESC);

-- ============================================================================
-- 7. MAC ADDRESS LEARNING TABLE
-- ============================================================================

CREATE TABLE mac_learning_table (
    learning_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    device_id BIGINT NOT NULL
        REFERENCES network_devices(device_id)
        ON DELETE CASCADE,

    mac_address MACADDR NOT NULL,

    interface_id BIGINT NOT NULL
        REFERENCES network_interfaces(interface_id),

    learned_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    last_seen TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(device_id, mac_address)
);

CREATE INDEX idx_mac_learning_interface
    ON mac_learning_table(interface_id);

CREATE INDEX idx_mac_learning_last_seen
    ON mac_learning_table(last_seen);

-- ============================================================================
-- 8. SWITCHING POLICIES
-- ============================================================================

CREATE TABLE switching_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    device_id BIGINT NOT NULL
        REFERENCES network_devices(device_id)
        ON DELETE CASCADE,

    policy_name VARCHAR(100) NOT NULL,

    allow_broadcast BOOLEAN NOT NULL DEFAULT TRUE,

    allow_multicast BOOLEAN NOT NULL DEFAULT TRUE,

    allow_unknown_unicast_flooding BOOLEAN NOT NULL DEFAULT TRUE,

    mac_aging_seconds INTEGER NOT NULL DEFAULT 300
        CHECK (mac_aging_seconds > 0),

    max_mtu INTEGER NOT NULL DEFAULT 1500
        CHECK (max_mtu BETWEEN 46 AND 9000),

    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(device_id, policy_name)
);

-- ============================================================================
-- 9. FORWARDING DECISION AUDIT
-- ============================================================================

CREATE TABLE forwarding_decisions (
    decision_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    device_id BIGINT NOT NULL
        REFERENCES network_devices(device_id),

    frame_id BIGINT NOT NULL
        REFERENCES ethernet_frames(frame_id),

    ingress_interface_id BIGINT NOT NULL
        REFERENCES network_interfaces(interface_id),

    action forwarding_action NOT NULL,

    decision_reason TEXT NOT NULL,

    processed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_decisions_device_time
    ON forwarding_decisions(device_id, processed_at DESC);

CREATE INDEX idx_decisions_action
    ON forwarding_decisions(action, processed_at DESC);

-- ============================================================================
-- 10. VALIDATION FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION validate_ethernet_frame()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.source_mac = NEW.destination_mac THEN
        RAISE EXCEPTION 'Source and destination MAC addresses must differ';
    END IF;

    IF macaddr_is_multicast(NEW.source_mac) THEN
        RAISE EXCEPTION 'Source MAC must be unicast';
    END IF;

    IF octet_length(NEW.payload) <> NEW.payload_length THEN
        RAISE EXCEPTION 'Payload length mismatch';
    END IF;

    IF NEW.payload_length > 1500 THEN
        RAISE EXCEPTION 'Ethernet payload exceeds configured MTU';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_ethernet_frame
BEFORE INSERT OR UPDATE ON ethernet_frames
FOR EACH ROW
EXECUTE FUNCTION validate_ethernet_frame();

-- ============================================================================
-- 11. INTERFACE INTEGRITY VALIDATION
-- ============================================================================

CREATE OR REPLACE FUNCTION validate_frame_interface()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    interface_device BIGINT;
    interface_state interface_status;
    frame_size INTEGER;
BEGIN
    SELECT device_id, status
    INTO interface_device, interface_state
    FROM network_interfaces
    WHERE interface_id = NEW.interface_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Interface does not exist';
    END IF;

    IF interface_state <> 'UP' THEN
        RAISE EXCEPTION 'Interface is not operational';
    END IF;

    SELECT frame_length
    INTO frame_size
    FROM ethernet_frames
    WHERE frame_id = NEW.frame_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Ethernet frame does not exist';
    END IF;

    IF frame_size > (
        SELECT mtu + 18
        FROM network_interfaces
        WHERE interface_id = NEW.interface_id
    ) THEN
        RAISE EXCEPTION 'Frame exceeds interface MTU';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_ingress_interface
BEFORE INSERT ON frame_ingress
FOR EACH ROW
EXECUTE FUNCTION validate_frame_interface();

-- ============================================================================
-- 12. MAC LEARNING FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION learn_mac_address(
    p_device_id BIGINT,
    p_mac MACADDR,
    p_interface_id BIGINT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    interface_device BIGINT;
    interface_state interface_status;
BEGIN
    IF macaddr_is_multicast(p_mac) THEN
        RAISE EXCEPTION 'Cannot learn multicast source MAC';
    END IF;

    SELECT device_id, status
    INTO interface_device, interface_state
    FROM network_interfaces
    WHERE interface_id = p_interface_id;

    IF NOT FOUND OR interface_device <> p_device_id THEN
        RAISE EXCEPTION 'Interface does not belong to device';
    END IF;

    IF interface_state <> 'UP' THEN
        RAISE EXCEPTION 'Cannot learn on inactive interface';
    END IF;

    INSERT INTO mac_learning_table (
        device_id,
        mac_address,
        interface_id,
        learned_at,
        last_seen
    )
    VALUES (
        p_device_id,
        p_mac,
        p_interface_id,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    )
    ON CONFLICT (device_id, mac_address)
    DO UPDATE SET
        interface_id = EXCLUDED.interface_id,
        last_seen = CURRENT_TIMESTAMP;
END;
$$;

-- ============================================================================
-- 13. MAC AGING PROCEDURE
-- ============================================================================

CREATE OR REPLACE PROCEDURE expire_mac_entries(
    p_device_id BIGINT
)
LANGUAGE plpgsql
AS $$
BEGIN
    DELETE FROM mac_learning_table learning
    USING switching_policies policy
    WHERE learning.device_id = p_device_id
      AND policy.device_id = learning.device_id
      AND policy.enabled = TRUE
      AND learning.last_seen <
          CURRENT_TIMESTAMP -
          make_interval(secs => policy.mac_aging_seconds);
END;
$$;

-- ============================================================================
-- 14. FORWARDING DECISION FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION evaluate_frame_forwarding(
    p_device_id BIGINT,
    p_frame_id BIGINT,
    p_ingress_interface BIGINT
)
RETURNS TABLE (
    decision forwarding_action,
    output_interface BIGINT,
    explanation TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_source MACADDR;
    v_destination MACADDR;
    v_ingress_device BIGINT;
    v_destination_interface BIGINT;
    v_action forwarding_action;
    v_policy switching_policies%ROWTYPE;
BEGIN
    SELECT source_mac, destination_mac
    INTO v_source, v_destination
    FROM ethernet_frames
    WHERE frame_id = p_frame_id
      AND status IN ('RECEIVED', 'VALIDATED');

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Frame unavailable for processing';
    END IF;

    SELECT device_id
    INTO v_ingress_device
    FROM network_interfaces
    WHERE interface_id = p_ingress_interface
      AND status = 'UP';

    IF NOT FOUND OR v_ingress_device <> p_device_id THEN
        RAISE EXCEPTION 'Invalid ingress interface';
    END IF;

    SELECT *
    INTO v_policy
    FROM switching_policies
    WHERE device_id = p_device_id
      AND enabled = TRUE
    ORDER BY policy_id
    LIMIT 1;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'No active switching policy';
    END IF;

    IF v_destination = 'ff:ff:ff:ff:ff:ff'::MACADDR THEN

        IF NOT v_policy.allow_broadcast THEN
            decision := 'FILTERED';
            output_interface := NULL;
            explanation := 'Broadcast prohibited by policy';
            RETURN NEXT;
            RETURN;
        END IF;

        v_action := 'BROADCAST';

    ELSIF macaddr_is_multicast(v_destination) THEN

        IF NOT v_policy.allow_multicast THEN
            decision := 'FILTERED';
            output_interface := NULL;
            explanation := 'Multicast prohibited by policy';
            RETURN NEXT;
            RETURN;
        END IF;

        v_action := 'MULTICAST';

    ELSE

        SELECT interface_id
        INTO v_destination_interface
        FROM mac_learning_table
        WHERE device_id = p_device_id
          AND mac_address = v_destination;

        IF NOT FOUND THEN
            IF NOT v_policy.allow_unknown_unicast_flooding THEN
                decision := 'DROP';
                output_interface := NULL;
                explanation := 'Unknown unicast flooding disabled';
                RETURN NEXT;
                RETURN;
            END IF;

            v_action := 'FLOOD';

        ELSIF v_destination_interface = p_ingress_interface THEN

            decision := 'DROP';
            output_interface := NULL;
            explanation := 'Destination is reachable on ingress port';
            RETURN NEXT;
            RETURN;

        ELSE
            v_action := 'UNICAST';
        END IF;
    END IF;

    IF v_action IN ('BROADCAST', 'MULTICAST', 'FLOOD') THEN

        RETURN QUERY
        SELECT
            v_action,
            interface.interface_id,
            CASE v_action
                WHEN 'BROADCAST' THEN 'Broadcast forwarding'
                WHEN 'MULTICAST' THEN 'Multicast forwarding'
                ELSE 'Unknown unicast flooding'
            END
        FROM network_interfaces interface
        WHERE interface.device_id = p_device_id
          AND interface.interface_id <> p_ingress_interface
          AND interface.status = 'UP';

    ELSE

        RETURN QUERY
        SELECT
            'UNICAST'::forwarding_action,
            interface.interface_id,
            'Known destination MAC forwarding'
        FROM network_interfaces interface
        WHERE interface.interface_id = v_destination_interface
          AND interface.status = 'UP';

    END IF;
END;
$$;

-- ============================================================================
-- 15. REPORTING VIEWS
-- ============================================================================

CREATE OR REPLACE VIEW v_mac_learning_table AS
SELECT
    device.device_name,
    learning.mac_address,
    interface.interface_name,
    learning.learned_at,
    learning.last_seen
FROM mac_learning_table learning
JOIN network_devices device
    ON device.device_id = learning.device_id
JOIN network_interfaces interface
    ON interface.interface_id = learning.interface_id;

CREATE OR REPLACE VIEW v_ethernet_frame_report AS
SELECT
    frame.frame_id,
    frame.source_mac,
    frame.destination_mac,
    frame.ether_type,
    frame.payload_length,
    frame.frame_length,
    frame.status,
    frame.received_at,
    COUNT(DISTINCT egress.egress_id) AS egress_count
FROM ethernet_frames frame
LEFT JOIN frame_egress egress
    ON egress.frame_id = frame.frame_id
GROUP BY frame.frame_id;

CREATE OR REPLACE VIEW v_switch_statistics AS
SELECT
    device.device_id,
    device.device_name,
    COUNT(*) FILTER (
        WHERE decision.action = 'UNICAST'
    ) AS unicast_decisions,
    COUNT(*) FILTER (
        WHERE decision.action = 'FLOOD'
    ) AS flooding_decisions,
    COUNT(*) FILTER (
        WHERE decision.action = 'BROADCAST'
    ) AS broadcast_decisions,
    COUNT(*) FILTER (
        WHERE decision.action = 'MULTICAST'
    ) AS multicast_decisions,
    COUNT(*) FILTER (
        WHERE decision.action IN ('DROP', 'FILTERED')
    ) AS rejected_decisions
FROM network_devices device
LEFT JOIN forwarding_decisions decision
    ON decision.device_id = device.device_id
GROUP BY device.device_id, device.device_name;

-- ============================================================================
-- 16. SAMPLE DEVICES
-- ============================================================================

INSERT INTO network_devices (
    device_name,
    device_type,
    management_ip,
    location
)
VALUES
    ('CORE-SWITCH-01', 'SWITCH', '192.168.1.1', 'Server Room'),
    ('HOST-ALPHA', 'HOST', '192.168.1.10', 'Office A'),
    ('HOST-BETA', 'HOST', '192.168.1.20', 'Office B'),
    ('HOST-GAMMA', 'HOST', '192.168.1.30', 'Office C');

-- ============================================================================
-- 17. SAMPLE INTERFACES
-- ============================================================================

INSERT INTO network_interfaces (
    device_id,
    interface_name,
    mac_address,
    speed_mbps,
    mtu,
    duplex_mode
)
SELECT device_id, 'eth0', '00:11:22:33:44:01', 1000, 1500, 'FULL'
FROM network_devices
WHERE device_name = 'CORE-SWITCH-01';

INSERT INTO network_interfaces (
    device_id,
    interface_name,
    mac_address
)
SELECT device_id, 'eth0', '00:11:22:33:44:AA'
FROM network_devices
WHERE device_name = 'HOST-ALPHA';

INSERT INTO network_interfaces (
    device_id,
    interface_name,
    mac_address
)
SELECT device_id, 'eth0', '00:11:22:33:44:BB'
FROM network_devices
WHERE device_name = 'HOST-BETA';

INSERT INTO network_interfaces (
    device_id,
    interface_name,
    mac_address
)
SELECT device_id, 'eth0', '00:11:22:33:44:CC'
FROM network_devices
WHERE device_name = 'HOST-GAMMA';

-- ============================================================================
-- 18. SWITCH PORTS
-- ============================================================================

INSERT INTO network_interfaces (
    device_id,
    interface_name,
    mac_address
)
SELECT
    device_id,
    'port1',
    '02:00:00:00:00:01'
FROM network_devices
WHERE device_name = 'CORE-SWITCH-01';

INSERT INTO network_interfaces (
    device_id,
    interface_name,
    mac_address
)
SELECT
    device_id,
    'port2',
    '02:00:00:00:00:02'
FROM network_devices
WHERE device_name = 'CORE-SWITCH-01';

INSERT INTO network_interfaces (
    device_id,
    interface_name,
    mac_address
)
SELECT
    device_id,
    'port3',
    '02:00:00:00:00:03'
FROM network_devices
WHERE device_name = 'CORE-SWITCH-01';

-- ============================================================================
-- 19. SWITCH POLICY
-- ============================================================================

INSERT INTO switching_policies (
    device_id,
    policy_name,
    allow_broadcast,
    allow_multicast,
    allow_unknown_unicast_flooding,
    mac_aging_seconds,
    max_mtu
)
SELECT
    device_id,
    'DEFAULT-ETHERNET-POLICY',
    TRUE,
    TRUE,
    TRUE,
    300,
    1500
FROM network_devices
WHERE device_name = 'CORE-SWITCH-01';

-- ============================================================================
-- 20. PHYSICAL SIGNAL SAMPLE
-- ============================================================================

INSERT INTO signal_transmissions (
    interface_id,
    encoding,
    bit_rate,
    amplitude,
    bit_count,
    noise_ratio,
    transmission_duration
)
SELECT
    interface_id,
    'NRZ',
    1000000000,
    1.0,
    1024,
    0.000001,
    INTERVAL '0.000001024 seconds'
FROM network_interfaces
WHERE interface_name = 'port1'
  AND device_id = (
      SELECT device_id
      FROM network_devices
      WHERE device_name = 'CORE-SWITCH-01'
  );

-- ============================================================================
-- 21. SAMPLE ETHERNET FRAMES
-- ============================================================================

INSERT INTO ethernet_frames (
    source_mac,
    destination_mac,
    ether_type,
    payload_length,
    payload,
    fcs,
    status
)
VALUES
(
    '00:11:22:33:44:AA',
    '00:11:22:33:44:BB',
    2048,
    13,
    convert_to('Hello Ethernet', 'UTF8'),
    123456789,
    'VALIDATED'
),
(
    '00:11:22:33:44:BB',
    '00:11:22:33:44:AA',
    2048,
    12,
    convert_to('Reply Packet', 'UTF8'),
    987654321,
    'VALIDATED'
),
(
    '00:11:22:33:44:AA',
    'FF:FF:FF:FF:FF:FF',
    2048,
    9,
    convert_to('Discovery', 'UTF8'),
    123456789,
    'RECEIVED'
),
(
    '00:11:22:33:44:CC',
    '01:00:5E:00:00:01',
    2048,
    12,
    convert_to('Multicast data', 'UTF8'),
    123456789,
    'RECEIVED'
);

-- ============================================================================
-- 22. MAC LEARNING
-- ============================================================================

SELECT learn_mac_address(
    (
        SELECT device_id
        FROM network_devices
        WHERE device_name = 'CORE-SWITCH-01'
    ),
    '00:11:22:33:44:AA',
    (
        SELECT interface_id
        FROM network_interfaces
        WHERE interface_name = 'port1'
          AND device_id = (
              SELECT device_id
              FROM network_devices
              WHERE device_name = 'CORE-SWITCH-01'
          )
    )
);

SELECT learn_mac_address(
    (
        SELECT device_id
        FROM network_devices
        WHERE device_name = 'CORE-SWITCH-01'
    ),
    '00:11:22:33:44:BB',
    (
        SELECT interface_id
        FROM network_interfaces
        WHERE interface_name = 'port2'
          AND device_id = (
              SELECT device_id
              FROM network_devices
              WHERE device_name = 'CORE-SWITCH-01'
          )
    )
);

-- ============================================================================
-- 23. INGRESS PROCESSING
-- ============================================================================

INSERT INTO frame_ingress (
    frame_id,
    interface_id
)
SELECT
    frame.frame_id,
    interface.interface_id
FROM ethernet_frames frame
CROSS JOIN network_interfaces interface
JOIN network_devices device
    ON device.device_id = interface.device_id
WHERE frame.source_mac = '00:11:22:33:44:AA'
  AND frame.destination_mac = '00:11:22:33:44:BB'
  AND interface.interface_name = 'port1'
  AND device.device_name = 'CORE-SWITCH-01'
LIMIT 1;

-- ============================================================================
-- 24. FORWARDING DECISION PROCESSING
-- ============================================================================

INSERT INTO forwarding_decisions (
    device_id,
    frame_id,
    ingress_interface_id,
    action,
    decision_reason
)
SELECT
    device.device_id,
    frame.frame_id,
    ingress.interface_id,
    result.decision,
    result.explanation
FROM network_devices device
JOIN network_interfaces ingress
    ON ingress.device_id = device.device_id
CROSS JOIN LATERAL evaluate_frame_forwarding(
    device.device_id,
    (
        SELECT frame_id
        FROM ethernet_frames
        WHERE source_mac = '00:11:22:33:44:AA'
          AND destination_mac = '00:11:22:33:44:BB'
        LIMIT 1
    ),
    ingress.interface_id
) result
WHERE device.device_name = 'CORE-SWITCH-01'
  AND ingress.interface_name = 'port1';

-- ============================================================================
-- 25. MAC TABLE RETRIEVAL
-- ============================================================================

SELECT *
FROM v_mac_learning_table
ORDER BY device_name, mac_address;

-- ============================================================================
-- 26. FRAME REPORT
-- ============================================================================

SELECT *
FROM v_ethernet_frame_report
ORDER BY received_at DESC;

-- ============================================================================
-- 27. FORWARDING ANALYTICS
-- ============================================================================

SELECT
    action,
    COUNT(*) AS decision_count
FROM forwarding_decisions
GROUP BY action
ORDER BY decision_count DESC;

-- ============================================================================
-- 28. INTERFACE UTILIZATION
-- ============================================================================

SELECT
    device.device_name,
    interface.interface_name,
    interface.speed_mbps,
    interface.status,
    COUNT(DISTINCT ingress.ingress_id) AS received_frames,
    COUNT(DISTINCT egress.egress_id) AS transmitted_frames
FROM network_interfaces interface
JOIN network_devices device
    ON device.device_id = interface.device_id
LEFT JOIN frame_ingress ingress
    ON ingress.interface_id = interface.interface_id
LEFT JOIN frame_egress egress
    ON egress.interface_id = interface.interface_id
GROUP BY
    device.device_name,
    interface.interface_name,
    interface.speed_mbps,
    interface.status
ORDER BY device.device_name, interface.interface_name;

-- ============================================================================
-- 29. ELIGIBILITY AND POLICY EVALUATION
-- ============================================================================

SELECT
    device.device_name,
    policy.policy_name,
    policy.allow_broadcast,
    policy.allow_multicast,
    policy.allow_unknown_unicast_flooding,
    policy.mac_aging_seconds,
    policy.enabled
FROM switching_policies policy
JOIN network_devices device
    ON device.device_id = policy.device_id
WHERE policy.enabled = TRUE
  AND device.enabled = TRUE;

-- ============================================================================
-- 30. AGGREGATED SWITCH REPORT
-- ============================================================================

SELECT *
FROM v_switch_statistics
ORDER BY device_name;

-- ============================================================================
-- 31. MAC AGING EXECUTION
-- ============================================================================

CALL expire_mac_entries(
    (
        SELECT device_id
        FROM network_devices
        WHERE device_name = 'CORE-SWITCH-01'
    )
);

-- ============================================================================
-- 32. COMMON NETWORK VALIDATION QUERIES
-- ============================================================================

-- Interfaces that are not operational.
SELECT
    device.device_name,
    interface.interface_name,
    interface.status
FROM network_interfaces interface
JOIN network_devices device
    ON device.device_id = interface.device_id
WHERE interface.status <> 'UP';

-- Duplicate MAC addresses across different devices.
SELECT
    mac_address,
    COUNT(*) AS occurrence_count
FROM network_interfaces
GROUP BY mac_address
HAVING COUNT(*) > 1;

-- Frames with failed or incomplete processing.
SELECT *
FROM ethernet_frames
WHERE status IN ('CORRUPTED', 'DROPPED');

-- Unknown or unlearned destination addresses.
SELECT
    frame.frame_id,
    frame.destination_mac
FROM ethernet_frames frame
LEFT JOIN mac_learning_table learning
    ON learning.mac_address = frame.destination_mac
WHERE learning.learning_id IS NULL
  AND NOT macaddr_is_multicast(frame.destination_mac);

-- ============================================================================
-- 33. TRANSACTION HANDLING
-- ============================================================================

SAVEPOINT before_policy_change;

UPDATE switching_policies
SET allow_unknown_unicast_flooding = FALSE
WHERE policy_name = 'DEFAULT-ETHERNET-POLICY';

-- Inspect the changed policy before committing the transaction.
SELECT *
FROM switching_policies
WHERE policy_name = 'DEFAULT-ETHERNET-POLICY';

-- Restore the original policy state for this demonstration.
ROLLBACK TO SAVEPOINT before_policy_change;

COMMIT;

/*
Operational notes:

1. PostgreSQL MACADDR validates and stores hardware addresses.
2. CRC-32 is not implemented as a native SQL function here.
   The supplied FCS values are illustrative records, not verified checksums.
3. The frame-validation trigger enforces structural constraints.
4. Forwarding decisions use learned destination MAC addresses.
5. Unknown unicast traffic can be flooded or dropped by policy.
6. MAC aging removes stale forwarding information.
7. Frame ingress and egress tables provide an audit trail.
8. MAC learning and forwarding operations should be executed in transactions.
9. Production systems should serialize concurrent updates to the same
   device/MAC entry and define a VLAN-aware learning key.
*/
