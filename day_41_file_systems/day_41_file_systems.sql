-- PostgreSQL-compatible filesystem inventory and permissions model.
-- The database stores logical filesystem metadata and access policy.
-- Actual operating-system file permissions remain controlled by the OS.

DROP SCHEMA IF EXISTS filesystem_lab CASCADE;
CREATE SCHEMA filesystem_lab;
SET search_path = filesystem_lab;

CREATE TYPE resource_kind AS ENUM (
    'file',
    'directory',
    'symbolic_link'
);

CREATE TYPE access_right AS ENUM (
    'read',
    'write',
    'execute'
);

CREATE TYPE permission_scope AS ENUM (
    'owner',
    'group',
    'other'
);

CREATE TABLE filesystem_nodes (
    node_id          BIGSERIAL PRIMARY KEY,
    parent_node_id   BIGINT REFERENCES filesystem_nodes(node_id)
                     ON DELETE CASCADE,
    name             TEXT NOT NULL,
    kind             resource_kind NOT NULL,
    size_bytes       BIGINT NOT NULL DEFAULT 0
                     CHECK (size_bytes >= 0),
    inode_number     BIGINT,
    target_path      TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_node_name
        CHECK (
            name <> ''
            AND name NOT IN ('.', '..')
            AND name NOT LIKE '%/%'
        ),

    CONSTRAINT valid_directory_size
        CHECK (
            kind <> 'directory' OR size_bytes = 0
        ),

    CONSTRAINT symlink_target_required
        CHECK (
            kind <> 'symbolic_link'
            OR target_path IS NOT NULL
        )
);

CREATE UNIQUE INDEX uq_sibling_name
ON filesystem_nodes (
    COALESCE(parent_node_id, 0),
    name
);

CREATE INDEX idx_nodes_parent
ON filesystem_nodes(parent_node_id);

CREATE INDEX idx_nodes_kind
ON filesystem_nodes(kind);

CREATE TABLE filesystem_permissions (
    node_id       BIGINT NOT NULL REFERENCES filesystem_nodes(node_id)
                  ON DELETE CASCADE,
    scope         permission_scope NOT NULL,
    access        access_right NOT NULL,
    granted       BOOLEAN NOT NULL DEFAULT FALSE,

    PRIMARY KEY (node_id, scope, access)
);

CREATE TABLE filesystem_users (
    user_id       BIGSERIAL PRIMARY KEY,
    username      TEXT NOT NULL UNIQUE,
    group_name    TEXT NOT NULL,
    active        BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE filesystem_audit (
    audit_id      BIGSERIAL PRIMARY KEY,
    user_id       BIGINT REFERENCES filesystem_users(user_id),
    node_id       BIGINT REFERENCES filesystem_nodes(node_id)
                  ON DELETE SET NULL,
    operation     TEXT NOT NULL,
    succeeded     BOOLEAN NOT NULL,
    details       TEXT,
    occurred_at   TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_operation
        CHECK (
            operation IN (
                'create',
                'read',
                'write',
                'delete',
                'chmod',
                'rename'
            )
        )
);

CREATE OR REPLACE FUNCTION validate_parent_directory()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.parent_node_id IS NOT NULL
       AND NOT EXISTS (
           SELECT 1
           FROM filesystem_nodes parent
           WHERE parent.node_id = NEW.parent_node_id
             AND parent.kind = 'directory'
       )
    THEN
        RAISE EXCEPTION
            'Parent node % is not a directory',
            NEW.parent_node_id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_parent_directory
BEFORE INSERT OR UPDATE OF parent_node_id
ON filesystem_nodes
FOR EACH ROW
EXECUTE FUNCTION validate_parent_directory();

CREATE OR REPLACE FUNCTION set_modified_timestamp()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.modified_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_modified_timestamp
BEFORE UPDATE
ON filesystem_nodes
FOR EACH ROW
EXECUTE FUNCTION set_modified_timestamp();

CREATE OR REPLACE FUNCTION has_access(
    requested_node BIGINT,
    requested_user BIGINT,
    requested_access access_right
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    result BOOLEAN;
BEGIN
    SELECT COALESCE(bool_or(p.granted), FALSE)
    INTO result
    FROM filesystem_permissions p
    JOIN filesystem_users u ON u.user_id = requested_user
    WHERE p.node_id = requested_node
      AND p.access = requested_access
      AND u.active = TRUE
      AND (
          p.scope = 'other'
          OR (
              p.scope = 'owner'
              AND requested_user IS NOT NULL
          )
          OR (
              p.scope = 'group'
              AND EXISTS (
                  SELECT 1
                  FROM filesystem_users group_member
                  WHERE group_member.user_id = requested_user
                    AND group_member.group_name = u.group_name
              )
          )
      );

    RETURN COALESCE(result, FALSE);
END;
$$;

-- Root and application directories.
INSERT INTO filesystem_nodes
    (parent_node_id, name, kind)
VALUES
    (NULL, 'application', 'directory');

INSERT INTO filesystem_nodes
    (parent_node_id, name, kind)
SELECT node_id, 'config', 'directory'
FROM filesystem_nodes
WHERE name = 'application';

INSERT INTO filesystem_nodes
    (parent_node_id, name, kind)
SELECT node_id, 'data', 'directory'
FROM filesystem_nodes
WHERE name = 'application';

INSERT INTO filesystem_nodes
    (parent_node_id, name, kind)
SELECT node_id, 'logs', 'directory'
FROM filesystem_nodes
WHERE name = 'application';

INSERT INTO filesystem_nodes
    (parent_node_id, name, kind, size_bytes, inode_number)
SELECT
    node_id,
    'application.properties',
    'file',
    82,
    41001
FROM filesystem_nodes
WHERE name = 'config';

INSERT INTO filesystem_nodes
    (parent_node_id, name, kind, size_bytes, inode_number)
SELECT
    node_id,
    'customer-records.csv',
    'file',
    52,
    41002
FROM filesystem_nodes
WHERE name = 'data';

INSERT INTO filesystem_nodes
    (parent_node_id, name, kind, size_bytes, inode_number)
SELECT
    node_id,
    'application.log',
    'file',
    44,
    41003
FROM filesystem_nodes
WHERE name = 'logs';

INSERT INTO filesystem_users (username, group_name)
VALUES
    ('alice', 'developers'),
    ('bob', 'operations'),
    ('audit_reader', 'auditors');

-- Configuration is readable and writable by the application owner.
INSERT INTO filesystem_permissions (node_id, scope, access, granted)
SELECT node_id, 'owner', right_name, TRUE
FROM filesystem_nodes
CROSS JOIN (
    VALUES
        ('application.properties'::TEXT, 'read'::access_right),
        ('application.properties'::TEXT, 'write'::access_right)
) AS rights(file_name, right_name)
WHERE filesystem_nodes.name = rights.file_name;

-- Operational data is readable by users in the operations group.
INSERT INTO filesystem_permissions (node_id, scope, access, granted)
SELECT node_id, 'group', 'read', TRUE
FROM filesystem_nodes
WHERE name = 'customer-records.csv';

-- Logs are readable but not writable by general users.
INSERT INTO filesystem_permissions (node_id, scope, access, granted)
SELECT node_id, 'other', 'read', TRUE
FROM filesystem_nodes
WHERE name = 'application.log';

-- Filesystem inventory query with parent paths.
WITH RECURSIVE tree AS (
    SELECT
        node_id,
        parent_node_id,
        name,
        kind,
        size_bytes,
        name::TEXT AS logical_path
    FROM filesystem_nodes
    WHERE parent_node_id IS NULL

    UNION ALL

    SELECT
        child.node_id,
        child.parent_node_id,
        child.name,
        child.kind,
        child.size_bytes,
        tree.logical_path || '/' || child.name
    FROM filesystem_nodes child
    JOIN tree
      ON child.parent_node_id = tree.node_id
)
SELECT
    logical_path,
    kind,
    size_bytes
FROM tree
ORDER BY logical_path;

-- Permission matrix.
SELECT
    n.name,
    p.scope,
    p.access,
    p.granted
FROM filesystem_nodes n
JOIN filesystem_permissions p
  ON p.node_id = n.node_id
ORDER BY n.name, p.scope, p.access;

-- Audit a successful read and an intentionally rejected write.
INSERT INTO filesystem_audit
    (user_id, node_id, operation, succeeded, details)
SELECT
    u.user_id,
    n.node_id,
    'read',
    TRUE,
    'Operations inventory read'
FROM filesystem_users u
JOIN filesystem_nodes n
  ON n.name = 'customer-records.csv'
WHERE u.username = 'bob';

INSERT INTO filesystem_audit
    (user_id, node_id, operation, succeeded, details)
SELECT
    u.user_id,
    n.node_id,
    'write',
    FALSE,
    'Write rejected because only owner write permission exists'
FROM filesystem_users u
JOIN filesystem_nodes n
  ON n.name = 'application.properties'
WHERE u.username = 'audit_reader';

-- Transactional rename: the logical node name changes together with audit data.
BEGIN;

UPDATE filesystem_nodes
SET name = 'customer-records-current.csv'
WHERE name = 'customer-records.csv'
  AND kind = 'file';

INSERT INTO filesystem_audit
    (user_id, node_id, operation, succeeded, details)
SELECT
    u.user_id,
    n.node_id,
    'rename',
    TRUE,
    'Data file renamed inside one transaction'
FROM filesystem_users u
JOIN filesystem_nodes n
  ON n.name = 'customer-records-current.csv'
WHERE u.username = 'bob';

COMMIT;

-- Find files larger than the operational threshold.
SELECT
    name,
    size_bytes,
    modified_at
FROM filesystem_nodes
WHERE kind = 'file'
  AND size_bytes > 40
ORDER BY size_bytes DESC;

-- Detect files that have no explicit permission rows.
SELECT
    n.node_id,
    n.name,
    n.kind
FROM filesystem_nodes n
LEFT JOIN filesystem_permissions p
  ON p.node_id = n.node_id
WHERE p.node_id IS NULL
ORDER BY n.node_id;

-- Database-level constraints prevent:
-- * negative file sizes
-- * duplicate names under one directory
-- * non-directory parents
-- * invalid resource kinds
-- * symbolic links without a target
-- * references to nonexistent users or filesystem nodes.
