-- PostgreSQL 15+
-- Operating-system security model:
-- authentication, authorization, file permissions, role assignments,
-- security classifications, sessions, access decisions, and audit history.
--
-- This schema simulates OS security policy in a database. It does not configure
-- PostgreSQL server authentication or change host filesystem permissions.

BEGIN;

DROP SCHEMA IF EXISTS os_security_lab CASCADE;
CREATE SCHEMA os_security_lab;
SET search_path TO os_security_lab, public;

CREATE TYPE account_state AS ENUM ('active', 'disabled', 'locked');
CREATE TYPE resource_kind AS ENUM ('file', 'directory', 'service', 'secret');
CREATE TYPE sensitivity_level AS ENUM ('public', 'internal', 'confidential', 'restricted');
CREATE TYPE access_action AS ENUM ('read', 'write', 'execute');
CREATE TYPE decision_effect AS ENUM ('allow', 'deny');

CREATE TABLE security_principal (
    principal_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    account_status account_state NOT NULL DEFAULT 'active',
    password_hash TEXT NOT NULL,
    password_changed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    mfa_required BOOLEAN NOT NULL DEFAULT FALSE,
    failed_login_count INTEGER NOT NULL DEFAULT 0 CHECK (failed_login_count >= 0),
    locked_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (username ~ '^[a-z][a-z0-9._-]{1,63}$')
);

CREATE TABLE security_group (
    group_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    group_name TEXT NOT NULL UNIQUE
);

CREATE TABLE principal_group (
    principal_id BIGINT NOT NULL REFERENCES security_principal(principal_id)
        ON DELETE CASCADE,
    group_id BIGINT NOT NULL REFERENCES security_group(group_id)
        ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (principal_id, group_id)
);

CREATE TABLE security_role (
    role_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    role_name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL
);

CREATE TABLE role_permission (
    role_id BIGINT NOT NULL REFERENCES security_role(role_id) ON DELETE CASCADE,
    action access_action NOT NULL,
    PRIMARY KEY (role_id, action)
);

CREATE TABLE principal_role (
    principal_id BIGINT NOT NULL REFERENCES security_principal(principal_id)
        ON DELETE CASCADE,
    role_id BIGINT NOT NULL REFERENCES security_role(role_id)
        ON DELETE CASCADE,
    assigned_by BIGINT REFERENCES security_principal(principal_id),
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (principal_id, role_id)
);

CREATE TABLE protected_resource (
    resource_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    resource_path TEXT NOT NULL UNIQUE,
    resource_type resource_kind NOT NULL,
    owner_id BIGINT NOT NULL REFERENCES security_principal(principal_id),
    group_id BIGINT REFERENCES security_group(group_id),
    unix_mode SMALLINT NOT NULL CHECK (unix_mode BETWEEN 0 AND 511),
    classification sensitivity_level NOT NULL DEFAULT 'internal',
    immutable BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (resource_path LIKE '/%'),
    CHECK (resource_path !~ '(^|/)\.\.(/|$)')
);

CREATE TABLE resource_policy (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    resource_id BIGINT NOT NULL REFERENCES protected_resource(resource_id)
        ON DELETE CASCADE,
    principal_id BIGINT REFERENCES security_principal(principal_id)
        ON DELETE CASCADE,
    group_id BIGINT REFERENCES security_group(group_id)
        ON DELETE CASCADE,
    action access_action NOT NULL,
    effect decision_effect NOT NULL,
    reason TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (num_nonnulls(principal_id, group_id) = 1)
);

CREATE TABLE authentication_session (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    principal_id BIGINT NOT NULL REFERENCES security_principal(principal_id)
        ON DELETE CASCADE,
    issued_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    mfa_verified BOOLEAN NOT NULL DEFAULT FALSE,
    source_address INET,
    CHECK (expires_at > issued_at),
    CHECK (revoked_at IS NULL OR revoked_at >= issued_at)
);

CREATE TABLE authentication_event (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    principal_id BIGINT REFERENCES security_principal(principal_id)
        ON DELETE SET NULL,
    attempted_username TEXT NOT NULL,
    succeeded BOOLEAN NOT NULL,
    event_time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source_address INET,
    failure_reason TEXT,
    CHECK (succeeded OR failure_reason IS NOT NULL)
);

CREATE TABLE access_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    session_id UUID REFERENCES authentication_session(session_id)
        ON DELETE SET NULL,
    principal_id BIGINT REFERENCES security_principal(principal_id)
        ON DELETE SET NULL,
    resource_id BIGINT REFERENCES protected_resource(resource_id)
        ON DELETE SET NULL,
    action access_action NOT NULL,
    effect decision_effect NOT NULL,
    reason TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sessions_principal_expiry
    ON authentication_session(principal_id, expires_at)
    WHERE revoked_at IS NULL;

CREATE INDEX idx_auth_events_failed_time
    ON authentication_event(event_time DESC)
    WHERE succeeded = FALSE;

CREATE INDEX idx_access_audit_denials
    ON access_audit(occurred_at DESC, principal_id)
    WHERE effect = 'deny';

CREATE INDEX idx_resource_policy_principal
    ON resource_policy(principal_id, resource_id, action);

CREATE INDEX idx_resource_policy_group
    ON resource_policy(group_id, resource_id, action);

INSERT INTO security_principal
    (username, password_hash, mfa_required)
VALUES
    ('alice', 'DEMO_HASH_NOT_A_REAL_CREDENTIAL', FALSE),
    ('bob', 'DEMO_HASH_NOT_A_REAL_CREDENTIAL', FALSE),
    ('secadmin', 'DEMO_HASH_NOT_A_REAL_CREDENTIAL', TRUE),
    ('disableduser', 'DEMO_HASH_NOT_A_REAL_CREDENTIAL', FALSE);

UPDATE security_principal
SET account_status = 'disabled'
WHERE username = 'disableduser';

INSERT INTO security_group (group_name)
VALUES ('engineering'), ('operations'), ('security');

INSERT INTO principal_group (principal_id, group_id)
SELECT p.principal_id, g.group_id
FROM (VALUES
    ('alice', 'engineering'),
    ('bob', 'operations'),
    ('secadmin', 'security')
) AS membership(username, group_name)
JOIN security_principal p ON p.username = membership.username
JOIN security_group g ON g.group_name = membership.group_name;

INSERT INTO security_role (role_name, description)
VALUES
    ('reader', 'Read access to assigned resources'),
    ('maintainer', 'Read and write access to assigned resources'),
    ('deployer', 'Read and execute access to deployment resources');

INSERT INTO role_permission (role_id, action)
SELECT r.role_id, p.action
FROM (VALUES
    ('reader', 'read'::access_action),
    ('maintainer', 'read'::access_action),
    ('maintainer', 'write'::access_action),
    ('deployer', 'read'::access_action),
    ('deployer', 'execute'::access_action)
) AS p(role_name, action)
JOIN security_role r ON r.role_name = p.role_name;

INSERT INTO principal_role (principal_id, role_id)
SELECT p.principal_id, r.role_id
FROM (VALUES
    ('alice', 'maintainer'),
    ('bob', 'reader'),
    ('secadmin', 'deployer')
) AS assignments(username, role_name)
JOIN security_principal p ON p.username = assignments.username
JOIN security_role r ON r.role_name = assignments.role_name;

INSERT INTO protected_resource
    (resource_path, resource_type, owner_id, group_id, unix_mode, classification, immutable)
SELECT
    sample.resource_path,
    sample.resource_type::resource_kind,
    owner.principal_id,
    g.group_id,
    sample.unix_mode,
    sample.classification::sensitivity_level,
    sample.immutable
FROM (VALUES
    ('/srv/app/config.yml', 'file', 'alice', 'engineering',
        416::smallint, 'confidential', FALSE),
    ('/srv/app/deploy.sh', 'file', 'secadmin', 'security',
        488::smallint, 'restricted', FALSE),
    ('/srv/app/release.lock', 'file', 'secadmin', 'security',
        420::smallint, 'internal', TRUE),
    ('/srv/app/public.txt', 'file', 'alice', 'engineering',
        420::smallint, 'public', FALSE)
) AS sample(resource_path, resource_type, owner_name, group_name,
            unix_mode, classification, immutable)
JOIN security_principal owner ON owner.username = sample.owner_name
LEFT JOIN security_group g ON g.group_name = sample.group_name;

-- Decimal 416 is octal 0640, 488 is octal 0750, and 420 is octal 0644.

INSERT INTO authentication_session
    (session_id, principal_id, issued_at, expires_at, mfa_verified)
SELECT
    '10000000-0000-0000-0000-000000000001'::uuid,
    principal_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '30 minutes', FALSE
FROM security_principal WHERE username = 'alice';

INSERT INTO authentication_session
    (session_id, principal_id, issued_at, expires_at, mfa_verified)
SELECT
    '10000000-0000-0000-0000-000000000002'::uuid,
    principal_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '30 minutes', FALSE
FROM security_principal WHERE username = 'bob';

INSERT INTO authentication_session
    (session_id, principal_id, issued_at, expires_at, mfa_verified)
SELECT
    '10000000-0000-0000-0000-000000000003'::uuid,
    principal_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '30 minutes', TRUE
FROM security_principal WHERE username = 'secadmin';

INSERT INTO authentication_session
    (session_id, principal_id, issued_at, expires_at, revoked_at)
SELECT
    '10000000-0000-0000-0000-000000000004'::uuid,
    principal_id,
    CURRENT_TIMESTAMP - INTERVAL '2 hours',
    CURRENT_TIMESTAMP - INTERVAL '1 hour',
    CURRENT_TIMESTAMP - INTERVAL '1 hour'
FROM security_principal WHERE username = 'alice';

INSERT INTO resource_policy
    (resource_id, principal_id, action, effect, reason)
SELECT r.resource_id, p.principal_id, 'read', 'deny',
       'Incident-response hold overrides ordinary access'
FROM protected_resource r
CROSS JOIN security_principal p
WHERE r.resource_path = '/srv/app/public.txt'
  AND p.username = 'bob';

INSERT INTO authentication_event
    (principal_id, attempted_username, succeeded, failure_reason)
SELECT principal_id, username, FALSE, 'Invalid password'
FROM security_principal
WHERE username = 'bob';

INSERT INTO authentication_event
    (principal_id, attempted_username, succeeded, failure_reason)
SELECT principal_id, username, TRUE, NULL
FROM security_principal
WHERE username = 'alice';

-- Unix DAC uses owner, group, or other bits. The classes are not unioned.
-- The following query calculates mode-based permission and then applies
-- role permissions, session validity, resource classification, immutability,
-- and explicit deny policies. It evaluates one requested action per row.

CREATE VIEW effective_access_decisions AS
WITH request_set AS (
    SELECT
        s.session_id,
        p.principal_id,
        p.username,
        p.account_status,
        p.mfa_required,
        s.mfa_verified,
        s.expires_at,
        s.revoked_at,
        r.resource_id,
        r.resource_path,
        r.unix_mode,
        r.classification,
        r.immutable,
        r.owner_id,
        r.group_id AS resource_group_id,
        g.clearance,
        requested.action
    FROM authentication_session s
    JOIN security_principal p ON p.principal_id = s.principal_id
    JOIN protected_resource r ON TRUE
    JOIN (VALUES
        ('alice', 'confidential'::sensitivity_level),
        ('bob', 'internal'::sensitivity_level),
        ('secadmin', 'restricted'::sensitivity_level),
        ('disableduser', 'public'::sensitivity_level)
    ) AS g(username, clearance) ON g.username = p.username
    CROSS JOIN (VALUES
        ('read'::access_action),
        ('write'::access_action),
        ('execute'::access_action)
    ) AS requested(action)
),
permission_bits AS (
    SELECT
        q.*,
        CASE
            WHEN q.principal_id = q.owner_id
                THEN (q.unix_mode >> 6) & 7
            WHEN EXISTS (
                SELECT 1
                FROM principal_group pg
                WHERE pg.principal_id = q.principal_id
                  AND pg.group_id = q.resource_group_id
            )
                THEN (q.unix_mode >> 3) & 7
            ELSE q.unix_mode & 7
        END AS selected_mode,
        CASE q.action
            WHEN 'read' THEN 4
            WHEN 'write' THEN 2
            WHEN 'execute' THEN 1
        END AS required_bit
    FROM request_set q
),
role_checks AS (
    SELECT
        b.*,
        EXISTS (
            SELECT 1
            FROM principal_role pr
            JOIN role_permission rp ON rp.role_id = pr.role_id
            WHERE pr.principal_id = b.principal_id
              AND rp.action = b.action
        ) AS role_grants,
        EXISTS (
            SELECT 1
            FROM resource_policy policy
            WHERE policy.resource_id = b.resource_id
              AND policy.action = b.action
              AND policy.effect = 'deny'
              AND (
                  policy.principal_id = b.principal_id
                  OR (
                      policy.group_id IS NOT NULL
                      AND EXISTS (
                          SELECT 1
                          FROM principal_group pg
                          WHERE pg.principal_id = b.principal_id
                            AND pg.group_id = policy.group_id
                      )
                  )
              )
        ) AS explicit_deny
    FROM permission_bits b
)
SELECT
    session_id,
    username,
    resource_path,
    action,
    CASE
        WHEN account_status <> 'active' THEN 'deny'
        WHEN revoked_at IS NOT NULL OR expires_at <= CURRENT_TIMESTAMP THEN 'deny'
        WHEN mfa_required AND NOT mfa_verified THEN 'deny'
        WHEN explicit_deny THEN 'deny'
        WHEN (selected_mode & required_bit) <> required_bit THEN 'deny'
        WHEN clearance::text = 'public'
             AND classification <> 'public' THEN 'deny'
        WHEN clearance::text = 'internal'
             AND classification IN ('confidential', 'restricted') THEN 'deny'
        WHEN clearance::text = 'confidential'
             AND classification = 'restricted' THEN 'deny'
        WHEN immutable AND action = 'write' THEN 'deny'
        WHEN NOT role_grants THEN 'deny'
        ELSE 'allow'
    END AS effect,
    CASE
        WHEN account_status <> 'active' THEN 'Account disabled or locked'
        WHEN revoked_at IS NOT NULL OR expires_at <= CURRENT_TIMESTAMP
            THEN 'Session revoked or expired'
        WHEN mfa_required AND NOT mfa_verified THEN 'MFA required'
        WHEN explicit_deny THEN 'Explicit deny policy'
        WHEN (selected_mode & required_bit) <> required_bit
            THEN 'Unix mode denies operation'
        WHEN clearance::text = 'public'
             AND classification <> 'public' THEN 'Insufficient clearance'
        WHEN clearance::text = 'internal'
             AND classification IN ('confidential', 'restricted')
            THEN 'Insufficient clearance'
        WHEN clearance::text = 'confidential'
             AND classification = 'restricted' THEN 'Insufficient clearance'
        WHEN immutable AND action = 'write' THEN 'Resource is immutable'
        WHEN NOT role_grants THEN 'Role does not grant operation'
        ELSE 'All modeled policy checks passed'
    END AS reason
FROM role_checks;

-- Review calculated decisions.
SELECT username, resource_path, action, effect, reason
FROM effective_access_decisions
WHERE username IN ('alice', 'bob', 'secadmin')
ORDER BY username, resource_path, action;

-- Persist a snapshot of the calculated decisions as audit evidence.
INSERT INTO access_audit
    (session_id, principal_id, resource_id, action, effect, reason)
SELECT
    d.session_id,
    p.principal_id,
    r.resource_id,
    d.action,
    d.effect::decision_effect,
    d.reason
FROM effective_access_decisions d
JOIN security_principal p ON p.username = d.username
JOIN protected_resource r ON r.resource_path = d.resource_path;

-- Failed authentication trend: repeated failures can inform lockout policy.
SELECT
    attempted_username,
    COUNT(*) FILTER (WHERE NOT succeeded) AS failed_attempts,
    MAX(event_time) FILTER (WHERE NOT succeeded) AS latest_failure
FROM authentication_event
GROUP BY attempted_username
ORDER BY failed_attempts DESC, attempted_username;

-- Review denied access by principal and resource.
SELECT
    p.username,
    r.resource_path,
    COUNT(*) AS denied_operations,
    MAX(a.occurred_at) AS most_recent_denial
FROM access_audit a
JOIN security_principal p ON p.principal_id = a.principal_id
JOIN protected_resource r ON r.resource_id = a.resource_id
WHERE a.effect = 'deny'
GROUP BY p.username, r.resource_path
ORDER BY denied_operations DESC, p.username;

-- Atomic administrative update: disable an account and revoke its sessions
-- together. Either both actions commit, or neither does.
SAVEPOINT before_disable;
UPDATE security_principal
SET account_status = 'disabled'
WHERE username = 'disableduser';

UPDATE authentication_session
SET revoked_at = CURRENT_TIMESTAMP
WHERE principal_id = (
    SELECT principal_id
    FROM security_principal
    WHERE username = 'disableduser'
)
AND revoked_at IS NULL;

-- The demonstration has no disableduser session, but the transaction-safe
-- pattern remains valid when such sessions exist.
RELEASE SAVEPOINT before_disable;

COMMIT;
