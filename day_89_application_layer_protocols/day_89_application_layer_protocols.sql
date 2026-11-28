-- ============================================================
-- APPLICATION LAYER PROTOCOLS
-- HTTP, HTTPS, DNS, SMTP, FTP AND SSH
-- PostgreSQL 15+
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS protocol_lab;

SET search_path TO protocol_lab, public;

-- ============================================================
-- 1. Enumerated domain types
-- ============================================================

CREATE TYPE protocol_type AS ENUM (
    'HTTP',
    'HTTPS',
    'DNS',
    'SMTP',
    'FTP',
    'SSH'
);

CREATE TYPE transport_type AS ENUM (
    'TCP',
    'UDP',
    'TCP_UDP'
);

CREATE TYPE connection_state AS ENUM (
    'DISCONNECTED',
    'CONNECTING',
    'CONNECTED',
    'AUTHENTICATED',
    'CLOSED',
    'FAILED'
);

CREATE TYPE dns_record_type AS ENUM (
    'A',
    'AAAA',
    'MX',
    'NS',
    'CNAME',
    'SOA',
    'PTR',
    'TXT'
);

CREATE TYPE request_status AS ENUM (
    'PENDING',
    'APPROVED',
    'REJECTED',
    'COMPLETED',
    'FAILED'
);

CREATE TYPE security_level AS ENUM (
    'PLAINTEXT',
    'TLS',
    'SSH_ENCRYPTION'
);

-- ============================================================
-- 2. Protocol registry
-- ============================================================

CREATE TABLE protocols (
    protocol_id SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    protocol_name protocol_type NOT NULL UNIQUE,

    default_port INTEGER NOT NULL
        CHECK (default_port BETWEEN 1 AND 65535),

    transport transport_type NOT NULL,

    security security_level NOT NULL,

    purpose TEXT NOT NULL,

    active BOOLEAN NOT NULL DEFAULT TRUE
);

INSERT INTO protocols (
    protocol_name,
    default_port,
    transport,
    security,
    purpose
)
VALUES
(
    'HTTP', 80, 'TCP', 'PLAINTEXT',
    'Web communication'
),
(
    'HTTPS', 443, 'TCP', 'TLS',
    'Encrypted web communication'
),
(
    'DNS', 53, 'TCP_UDP', 'PLAINTEXT',
    'Domain name resolution'
),
(
    'SMTP', 587, 'TCP', 'TLS',
    'Email submission'
),
(
    'FTP', 21, 'TCP', 'PLAINTEXT',
    'File transfer control'
),
(
    'SSH', 22, 'TCP', 'SSH_ENCRYPTION',
    'Secure remote administration'
);

-- ============================================================
-- 3. Organizational entities
-- ============================================================

CREATE TABLE organizations (
    organization_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    organization_name VARCHAR(150) NOT NULL UNIQUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),

    username VARCHAR(80) NOT NULL,

    email VARCHAR(254) NOT NULL,

    role_name VARCHAR(40) NOT NULL
        CHECK (
            role_name IN (
                'ADMIN',
                'NETWORK_ENGINEER',
                'DEVELOPER',
                'AUDITOR'
            )
        ),

    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (organization_id, username),

    UNIQUE (organization_id, email)
);

-- ============================================================
-- 4. Network endpoints
-- ============================================================

CREATE TABLE endpoints (
    endpoint_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),

    hostname VARCHAR(253) NOT NULL,

    port INTEGER NOT NULL
        CHECK (port BETWEEN 1 AND 65535),

    ip_address INET,

    description TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (
        organization_id,
        hostname,
        port
    )
);

CREATE INDEX idx_endpoints_ip
ON endpoints USING GIST (ip_address inet_ops);

CREATE INDEX idx_endpoints_hostname
ON endpoints (hostname);

-- ============================================================
-- 5. DNS records
-- ============================================================

CREATE TABLE dns_records (
    dns_record_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),

    hostname VARCHAR(253) NOT NULL,

    record_type dns_record_type NOT NULL,

    record_value TEXT NOT NULL,

    ttl INTEGER NOT NULL
        CHECK (ttl BETWEEN 0 AND 2147483647),

    priority INTEGER,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (
        record_type = 'MX'
        OR priority IS NULL
    ),

    CHECK (
        record_type <> 'A'
        OR record_value ~
        '^(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])(\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])){3}$'
    )
);

CREATE INDEX idx_dns_lookup
ON dns_records (
    organization_id,
    hostname,
    record_type
);

-- ============================================================
-- 6. Network access policies
-- ============================================================

CREATE TABLE protocol_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),

    policy_name VARCHAR(120) NOT NULL,

    require_encryption BOOLEAN NOT NULL DEFAULT TRUE,

    require_authentication BOOLEAN NOT NULL DEFAULT TRUE,

    allow_direct_connections BOOLEAN NOT NULL DEFAULT FALSE,

    allow_unverified_certificates BOOLEAN NOT NULL DEFAULT FALSE,

    maximum_payload_bytes BIGINT NOT NULL DEFAULT 1048576
        CHECK (maximum_payload_bytes > 0),

    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (organization_id, policy_name)
);

CREATE TABLE policy_protocols (
    policy_id BIGINT NOT NULL
        REFERENCES protocol_policies(policy_id)
        ON DELETE CASCADE,

    protocol_id SMALLINT NOT NULL
        REFERENCES protocols(protocol_id),

    permitted BOOLEAN NOT NULL DEFAULT TRUE,

    PRIMARY KEY (policy_id, protocol_id)
);

CREATE TABLE policy_ports (
    policy_id BIGINT NOT NULL
        REFERENCES protocol_policies(policy_id)
        ON DELETE CASCADE,

    port INTEGER NOT NULL
        CHECK (port BETWEEN 1 AND 65535),

    PRIMARY KEY (policy_id, port)
);

-- ============================================================
-- 7. Protocol requests
-- ============================================================

CREATE TABLE protocol_requests (
    request_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),

    requested_by BIGINT NOT NULL
        REFERENCES users(user_id),

    endpoint_id BIGINT NOT NULL
        REFERENCES endpoints(endpoint_id),

    protocol_id SMALLINT NOT NULL
        REFERENCES protocols(protocol_id),

    policy_id BIGINT NOT NULL
        REFERENCES protocol_policies(policy_id),

    operation VARCHAR(80) NOT NULL,

    payload_bytes BIGINT NOT NULL DEFAULT 0
        CHECK (payload_bytes >= 0),

    authenticated BOOLEAN NOT NULL DEFAULT FALSE,

    certificate_verified BOOLEAN NOT NULL DEFAULT FALSE,

    ssh_host_key_verified BOOLEAN NOT NULL DEFAULT FALSE,

    status request_status NOT NULL DEFAULT 'PENDING',

    decision_reason TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_requests_status
ON protocol_requests(status, created_at DESC);

CREATE INDEX idx_requests_organization
ON protocol_requests(organization_id, created_at DESC);

CREATE INDEX idx_requests_protocol
ON protocol_requests(protocol_id, status);

-- ============================================================
-- 8. Connection lifecycle
-- ============================================================

CREATE TABLE protocol_connections (
    connection_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    request_id BIGINT NOT NULL UNIQUE
        REFERENCES protocol_requests(request_id),

    state connection_state NOT NULL DEFAULT 'DISCONNECTED',

    remote_address INET,

    established_at TIMESTAMPTZ,

    closed_at TIMESTAMPTZ,

    failure_reason TEXT,

    CHECK (
        closed_at IS NULL
        OR established_at IS NOT NULL
    )
);

-- ============================================================
-- 9. Audit records
-- ============================================================

CREATE TABLE protocol_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    request_id BIGINT NOT NULL
        REFERENCES protocol_requests(request_id),

    action VARCHAR(60) NOT NULL,

    actor_id BIGINT
        REFERENCES users(user_id),

    previous_status request_status,

    new_status request_status,

    event_details JSONB NOT NULL DEFAULT '{}'::JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_protocol_audit_request
ON protocol_audit(request_id, created_at DESC);

CREATE INDEX idx_protocol_audit_json
ON protocol_audit USING GIN(event_details);

-- ============================================================
-- 10. Automatic request audit trigger
-- ============================================================

CREATE OR REPLACE FUNCTION audit_request_changes()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO protocol_audit (
        request_id,
        action,
        previous_status,
        new_status,
        event_details
    )
    VALUES (
        NEW.request_id,
        CASE
            WHEN TG_OP = 'INSERT'
                THEN 'REQUEST_CREATED'
            ELSE 'REQUEST_UPDATED'
        END,
        CASE
            WHEN TG_OP = 'INSERT'
                THEN NULL
            ELSE OLD.status
        END,
        NEW.status,
        jsonb_build_object(
            'protocol_id', NEW.protocol_id,
            'endpoint_id', NEW.endpoint_id,
            'operation', NEW.operation
        )
    );

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_request_audit
AFTER INSERT OR UPDATE OF status
ON protocol_requests
FOR EACH ROW
EXECUTE FUNCTION audit_request_changes();

-- ============================================================
-- 11. Policy eligibility function
-- ============================================================

CREATE OR REPLACE FUNCTION evaluate_protocol_request(
    p_request_id BIGINT
)
RETURNS TABLE (
    eligible BOOLEAN,
    reason TEXT
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_request protocol_requests%ROWTYPE;
    v_protocol protocols%ROWTYPE;
    v_policy protocol_policies%ROWTYPE;
    v_endpoint endpoints%ROWTYPE;
    v_allowed BOOLEAN;
BEGIN
    SELECT *
    INTO v_request
    FROM protocol_requests
    WHERE request_id = p_request_id;

    IF NOT FOUND THEN
        RETURN QUERY
        SELECT FALSE, 'Request does not exist.'::TEXT;

        RETURN;
    END IF;

    SELECT *
    INTO v_protocol
    FROM protocols
    WHERE protocol_id = v_request.protocol_id;

    SELECT *
    INTO v_policy
    FROM protocol_policies
    WHERE policy_id = v_request.policy_id;

    SELECT *
    INTO v_endpoint
    FROM endpoints
    WHERE endpoint_id = v_request.endpoint_id;

    IF NOT v_policy.active THEN
        RETURN QUERY
        SELECT FALSE, 'Policy is inactive.'::TEXT;

        RETURN;
    END IF;

    IF v_request.organization_id <> v_policy.organization_id
       OR v_request.organization_id <> v_endpoint.organization_id
    THEN
        RETURN QUERY
        SELECT FALSE, 'Organization ownership mismatch.'::TEXT;

        RETURN;
    END IF;

    IF NOT v_protocol.active THEN
        RETURN QUERY
        SELECT FALSE, 'Protocol is inactive.'::TEXT;

        RETURN;
    END IF;

    SELECT EXISTS (
        SELECT 1
        FROM policy_protocols pp
        WHERE pp.policy_id = v_policy.policy_id
          AND pp.protocol_id = v_protocol.protocol_id
          AND pp.permitted = TRUE
    )
    INTO v_allowed;

    IF NOT v_allowed THEN
        RETURN QUERY
        SELECT FALSE, 'Protocol not permitted by policy.'::TEXT;

        RETURN;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM policy_ports
        WHERE policy_id = v_policy.policy_id
          AND port = v_endpoint.port
    ) THEN
        RETURN QUERY
        SELECT FALSE, 'Port not permitted by policy.'::TEXT;

        RETURN;
    END IF;

    IF v_policy.require_encryption
       AND v_protocol.security = 'PLAINTEXT'
    THEN
        RETURN QUERY
        SELECT FALSE, 'Encrypted transport required.'::TEXT;

        RETURN;
    END IF;

    IF v_policy.require_authentication
       AND NOT v_request.authenticated
    THEN
        RETURN QUERY
        SELECT FALSE, 'Authentication required.'::TEXT;

        RETURN;
    END IF;

    IF v_request.payload_bytes > v_policy.maximum_payload_bytes
    THEN
        RETURN QUERY
        SELECT FALSE, 'Payload exceeds policy limit.'::TEXT;

        RETURN;
    END IF;

    IF v_request.protocol_id = (
        SELECT protocol_id
        FROM protocols
        WHERE protocol_name = 'HTTPS'
    )
       AND NOT v_request.certificate_verified
    THEN
        RETURN QUERY
        SELECT FALSE, 'HTTPS certificate verification failed.'::TEXT;

        RETURN;
    END IF;

    IF v_request.protocol_id = (
        SELECT protocol_id
        FROM protocols
        WHERE protocol_name = 'SSH'
    )
       AND NOT v_request.ssh_host_key_verified
    THEN
        RETURN QUERY
        SELECT FALSE, 'SSH host-key verification failed.'::TEXT;

        RETURN;
    END IF;

    RETURN QUERY
    SELECT TRUE, 'All policy requirements satisfied.'::TEXT;
END;
$$;

-- ============================================================
-- 12. Workflow processing procedure
-- ============================================================

CREATE OR REPLACE PROCEDURE process_protocol_request(
    p_request_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_eligible BOOLEAN;
    v_reason TEXT;
    v_current_status request_status;
BEGIN
    SELECT status
    INTO v_current_status
    FROM protocol_requests
    WHERE request_id = p_request_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Protocol request % does not exist',
            p_request_id;
    END IF;

    IF v_current_status <> 'PENDING' THEN
        RAISE EXCEPTION
            'Only pending requests can be processed.';
    END IF;

    SELECT e.eligible, e.reason
    INTO v_eligible, v_reason
    FROM evaluate_protocol_request(p_request_id) e;

    UPDATE protocol_requests
    SET
        status = CASE
            WHEN v_eligible THEN 'APPROVED'::request_status
            ELSE 'REJECTED'::request_status
        END,
        decision_reason = v_reason
    WHERE request_id = p_request_id;

    IF v_eligible THEN
        INSERT INTO protocol_connections (
            request_id,
            state,
            established_at
        )
        VALUES (
            p_request_id,
            'CONNECTED',
            NOW()
        );
    END IF;
END;
$$;

-- ============================================================
-- 13. Reporting view
-- ============================================================

CREATE OR REPLACE VIEW protocol_request_report AS
SELECT
    r.request_id,
    o.organization_name,
    u.username,
    p.protocol_name,
    e.hostname,
    e.port,
    r.operation,
    r.status,
    r.authenticated,
    r.payload_bytes,
    r.decision_reason,
    r.created_at,
    r.completed_at
FROM protocol_requests r
JOIN organizations o
    ON o.organization_id = r.organization_id
JOIN users u
    ON u.user_id = r.requested_by
JOIN protocols p
    ON p.protocol_id = r.protocol_id
JOIN endpoints e
    ON e.endpoint_id = r.endpoint_id;

-- ============================================================
-- 14. Sample enterprise records
-- ============================================================

INSERT INTO organizations (organization_name)
VALUES ('Example Enterprise');

INSERT INTO users (
    organization_id,
    username,
    email,
    role_name
)
VALUES
(1, 'network_admin', 'admin@example.com', 'ADMIN'),
(1, 'developer01', 'developer@example.com', 'DEVELOPER'),
(1, 'auditor01', 'auditor@example.com', 'AUDITOR');

INSERT INTO endpoints (
    organization_id,
    hostname,
    port,
    ip_address,
    description
)
VALUES
(
    1,
    'api.example.com',
    443,
    '192.0.2.10',
    'HTTPS application endpoint'
),
(
    1,
    'dns.example.com',
    53,
    '192.0.2.53',
    'DNS infrastructure'
),
(
    1,
    'mail.example.com',
    587,
    '192.0.2.25',
    'SMTP submission endpoint'
),
(
    1,
    'server.example.com',
    22,
    '192.0.2.40',
    'SSH administration endpoint'
),
(
    1,
    'legacy.example.com',
    80,
    '192.0.2.60',
    'Legacy HTTP endpoint'
);

INSERT INTO dns_records (
    organization_id,
    hostname,
    record_type,
    record_value,
    ttl,
    priority
)
VALUES
(1, 'example.com', 'A', '192.0.2.10', 300, NULL),
(1, 'example.com', 'MX', 'mail.example.com', 600, 10),
(1, 'example.com', 'TXT', 'v=spf1 -all', 300, NULL),
(1, 'www.example.com', 'CNAME', 'example.com', 300, NULL);

INSERT INTO protocol_policies (
    organization_id,
    policy_name,
    require_encryption,
    require_authentication,
    maximum_payload_bytes
)
VALUES (
    1,
    'Enterprise Secure Network',
    TRUE,
    TRUE,
    1048576
);

INSERT INTO policy_protocols (
    policy_id,
    protocol_id,
    permitted
)
SELECT
    1,
    protocol_id,
    TRUE
FROM protocols
WHERE protocol_name IN (
    'HTTPS',
    'DNS',
    'SMTP',
    'SSH'
);

INSERT INTO policy_ports (policy_id, port)
VALUES
(1, 53),
(1, 443),
(1, 587),
(1, 22);

-- ============================================================
-- 15. Request samples
-- ============================================================

INSERT INTO protocol_requests (
    organization_id,
    requested_by,
    endpoint_id,
    protocol_id,
    policy_id,
    operation,
    payload_bytes,
    authenticated,
    certificate_verified,
    ssh_host_key_verified
)
VALUES
(
    1, 2, 1,
    (SELECT protocol_id FROM protocols WHERE protocol_name = 'HTTPS'),
    1,
    'GET /api/data',
    2048,
    TRUE,
    TRUE,
    FALSE
),
(
    1, 2, 5,
    (SELECT protocol_id FROM protocols WHERE protocol_name = 'HTTP'),
    1,
    'GET /legacy',
    1024,
    TRUE,
    FALSE,
    FALSE
),
(
    1, 1, 4,
    (SELECT protocol_id FROM protocols WHERE protocol_name = 'SSH'),
    1,
    'Remote administration',
    512,
    TRUE,
    FALSE,
    FALSE
),
(
    1, 2, 3,
    (SELECT protocol_id FROM protocols WHERE protocol_name = 'SMTP'),
    1,
    'Email submission',
    4096,
    TRUE,
    FALSE,
    FALSE
),
(
    1, 2, 1,
    (SELECT protocol_id FROM protocols WHERE protocol_name = 'HTTPS'),
    1,
    'POST /api/upload',
    2097152,
    TRUE,
    TRUE,
    FALSE
);

-- ============================================================
-- 16. Execute request processing transactionally
-- ============================================================

DO $$
DECLARE
    v_request_id BIGINT;
BEGIN
    FOR v_request_id IN
        SELECT request_id
        FROM protocol_requests
        WHERE status = 'PENDING'
        ORDER BY request_id
    LOOP
        CALL process_protocol_request(v_request_id);
    END LOOP;
END;
$$;

-- ============================================================
-- 17. Retrieval queries
-- ============================================================

SELECT *
FROM protocol_request_report
ORDER BY request_id;

SELECT
    hostname,
    record_type,
    record_value,
    ttl,
    priority
FROM dns_records
WHERE organization_id = 1
  AND hostname = 'example.com'
ORDER BY record_type;

-- ============================================================
-- 18. Validation and eligibility queries
-- ============================================================

SELECT
    r.request_id,
    p.protocol_name,
    e.eligible,
    e.reason
FROM protocol_requests r
CROSS JOIN LATERAL
    evaluate_protocol_request(r.request_id) e
JOIN protocols p
    ON p.protocol_id = r.protocol_id
ORDER BY r.request_id;

-- ============================================================
-- 19. Aggregation and reporting
-- ============================================================

SELECT
    p.protocol_name,
    COUNT(*) AS total_requests,
    COUNT(*) FILTER (
        WHERE r.status = 'APPROVED'
    ) AS approved_requests,
    COUNT(*) FILTER (
        WHERE r.status = 'REJECTED'
    ) AS rejected_requests,
    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE r.status = 'APPROVED'
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS approval_percentage
FROM protocol_requests r
JOIN protocols p
    ON p.protocol_id = r.protocol_id
GROUP BY p.protocol_name
ORDER BY total_requests DESC;

SELECT
    status,
    COUNT(*) AS request_count,
    AVG(payload_bytes) AS average_payload_bytes,
    MAX(payload_bytes) AS maximum_payload_bytes
FROM protocol_requests
GROUP BY status;

-- ============================================================
-- 20. Security audit reporting
-- ============================================================

SELECT
    a.audit_id,
    a.request_id,
    a.action,
    a.previous_status,
    a.new_status,
    a.event_details,
    a.created_at
FROM protocol_audit a
ORDER BY a.created_at DESC;

SELECT
    p.protocol_name,
    COUNT(*) AS failed_requests
FROM protocol_requests r
JOIN protocols p
    ON p.protocol_id = r.protocol_id
WHERE r.status = 'REJECTED'
GROUP BY p.protocol_name;

-- ============================================================
-- 21. CTE-based security analysis
-- ============================================================

WITH request_security AS (
    SELECT
        r.request_id,
        p.protocol_name,
        p.security,
        r.authenticated,
        r.certificate_verified,
        r.ssh_host_key_verified,
        r.status
    FROM protocol_requests r
    JOIN protocols p
        ON p.protocol_id = r.protocol_id
)
SELECT
    *,
    CASE
        WHEN NOT authenticated
            THEN 'AUTHENTICATION_FAILURE'
        WHEN security = 'TLS'
             AND NOT certificate_verified
            THEN 'CERTIFICATE_FAILURE'
        WHEN protocol_name = 'SSH'
             AND NOT ssh_host_key_verified
            THEN 'HOST_KEY_FAILURE'
        ELSE 'CHECK_POLICY_DECISION'
    END AS security_classification
FROM request_security
ORDER BY request_id;

-- ============================================================
-- 22. Transaction demonstration
-- ============================================================

SAVEPOINT before_demo;

-- Demonstration of a reversible update.
UPDATE protocol_policies
SET maximum_payload_bytes = 524288
WHERE policy_id = 1;

ROLLBACK TO SAVEPOINT before_demo;

-- The original policy limit is preserved.
SELECT
    policy_name,
    maximum_payload_bytes
FROM protocol_policies
WHERE policy_id = 1;

COMMIT;

-- ============================================================
-- 23. Final integrity checks
-- ============================================================

SELECT
    (SELECT COUNT(*) FROM protocols) AS protocols,
    (SELECT COUNT(*) FROM organizations) AS organizations,
    (SELECT COUNT(*) FROM users) AS users,
    (SELECT COUNT(*) FROM endpoints) AS endpoints,
    (SELECT COUNT(*) FROM dns_records) AS dns_records,
    (SELECT COUNT(*) FROM protocol_requests) AS requests,
    (SELECT COUNT(*) FROM protocol_audit) AS audit_entries;
