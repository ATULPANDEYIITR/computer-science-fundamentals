DROP SCHEMA IF EXISTS language_concepts CASCADE;
CREATE SCHEMA language_concepts;
SET search_path TO language_concepts;

-- PostgreSQL model:
-- scope_regions represent where bindings are valid,
-- bindings represent name-to-entity associations,
-- objects represent entities whose lifetimes can be tracked,
-- typed_values represent runtime type information,
-- type_rules represent operations permitted by a type system.

CREATE TYPE binding_kind AS ENUM (
    'VARIABLE',
    'FUNCTION',
    'PARAMETER',
    'FIELD',
    'TYPE'
);

CREATE TYPE lifetime_kind AS ENUM (
    'BLOCK',
    'FUNCTION',
    'OBJECT',
    'PROCESS',
    'RESOURCE'
);

CREATE TYPE type_category AS ENUM (
    'INTEGER',
    'DECIMAL',
    'BOOLEAN',
    'STRING',
    'OBJECT',
    'COLLECTION',
    'FUNCTION'
);

CREATE TYPE typing_mode AS ENUM (
    'STATIC',
    'DYNAMIC'
);

CREATE TABLE scope_regions (
    scope_id BIGSERIAL PRIMARY KEY,
    scope_name TEXT NOT NULL,
    parent_scope_id BIGINT REFERENCES scope_regions(scope_id)
        ON DELETE CASCADE,
    scope_kind TEXT NOT NULL CHECK (
        scope_kind IN (
            'MODULE',
            'FUNCTION',
            'BLOCK',
            'CLASS',
            'GLOBAL'
        )
    ),
    UNIQUE (parent_scope_id, scope_name)
);

CREATE TABLE bindings (
    binding_id BIGSERIAL PRIMARY KEY,
    scope_id BIGINT NOT NULL REFERENCES scope_regions(scope_id)
        ON DELETE CASCADE,
    identifier TEXT NOT NULL,
    binding_kind binding_kind NOT NULL,
    target_description TEXT NOT NULL,
    is_mutable BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (scope_id, identifier)
);

CREATE INDEX idx_bindings_identifier
    ON bindings(identifier);

CREATE TABLE runtime_objects (
    object_id BIGSERIAL PRIMARY KEY,
    object_type type_category NOT NULL,
    lifetime_kind lifetime_kind NOT NULL,
    allocated_at TIMESTAMPTZ NOT NULL,
    released_at TIMESTAMPTZ,
    CHECK (released_at IS NULL OR released_at >= allocated_at)
);

CREATE TABLE value_instances (
    value_id BIGSERIAL PRIMARY KEY,
    object_id BIGINT REFERENCES runtime_objects(object_id)
        ON DELETE SET NULL,
    declared_type type_category,
    runtime_type type_category NOT NULL,
    typing typing_mode NOT NULL,
    textual_value TEXT,
    CHECK (
        declared_type IS NOT NULL
        OR typing = 'DYNAMIC'
    )
);

CREATE INDEX idx_value_runtime_type
    ON value_instances(runtime_type);

CREATE TABLE type_operations (
    operation_id BIGSERIAL PRIMARY KEY,
    type_name type_category NOT NULL,
    operation_name TEXT NOT NULL,
    operand_count INTEGER NOT NULL CHECK (operand_count > 0),
    result_type type_category NOT NULL,
    UNIQUE (type_name, operation_name, operand_count)
);

CREATE TABLE operation_attempts (
    attempt_id BIGSERIAL PRIMARY KEY,
    operation_id BIGINT NOT NULL REFERENCES type_operations(operation_id),
    left_runtime_type type_category NOT NULL,
    right_runtime_type type_category,
    succeeded BOOLEAN NOT NULL,
    failure_reason TEXT,
    attempted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (
        succeeded
        OR failure_reason IS NOT NULL
    )
);

CREATE TABLE scope_lookup_events (
    lookup_id BIGSERIAL PRIMARY KEY,
    identifier TEXT NOT NULL,
    starting_scope_id BIGINT NOT NULL REFERENCES scope_regions(scope_id),
    resolved_scope_id BIGINT REFERENCES scope_regions(scope_id),
    binding_id BIGINT REFERENCES bindings(binding_id),
    resolved BOOLEAN NOT NULL,
    looked_up_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_scope_lookup_identifier
    ON scope_lookup_events(identifier);

-- Scope hierarchy representing a module containing a function,
-- which contains a nested block.

INSERT INTO scope_regions (
    scope_name,
    parent_scope_id,
    scope_kind
)
VALUES
    ('application', NULL, 'GLOBAL');

INSERT INTO scope_regions (
    scope_name,
    parent_scope_id,
    scope_kind
)
SELECT
    'repository_service',
    scope_id,
    'FUNCTION'
FROM scope_regions
WHERE scope_name = 'application';

INSERT INTO scope_regions (
    scope_name,
    parent_scope_id,
    scope_kind
)
SELECT
    'validation_block',
    scope_id,
    'BLOCK'
FROM scope_regions
WHERE scope_name = 'repository_service';

INSERT INTO bindings (
    scope_id,
    identifier,
    binding_kind,
    target_description,
    is_mutable
)
SELECT
    scope_id,
    'repository_name',
    'VARIABLE',
    'Name of repository being analyzed',
    FALSE
FROM scope_regions
WHERE scope_name = 'application';

INSERT INTO bindings (
    scope_id,
    identifier,
    binding_kind,
    target_description,
    is_mutable
)
SELECT
    scope_id,
    'pull_request',
    'VARIABLE',
    'Current pull request object',
    TRUE
FROM scope_regions
WHERE scope_name = 'repository_service';

INSERT INTO bindings (
    scope_id,
    identifier,
    binding_kind,
    target_description,
    is_mutable
)
SELECT
    scope_id,
    'threshold',
    'VARIABLE',
    'Validation threshold local to nested block',
    FALSE
FROM scope_regions
WHERE scope_name = 'validation_block';

-- Object lifetime records show active and released entities.

INSERT INTO runtime_objects (
    object_type,
    lifetime_kind,
    allocated_at,
    released_at
)
VALUES
    (
        'OBJECT',
        'OBJECT',
        CURRENT_TIMESTAMP - INTERVAL '2 hours',
        CURRENT_TIMESTAMP - INTERVAL '1 hour'
    ),
    (
        'OBJECT',
        'BLOCK',
        CURRENT_TIMESTAMP - INTERVAL '20 minutes',
        CURRENT_TIMESTAMP - INTERVAL '19 minutes'
    ),
    (
        'RESOURCE',
        'RESOURCE',
        CURRENT_TIMESTAMP - INTERVAL '10 minutes',
        NULL
    );

-- A statically typed value has a declared type matching its runtime type.
INSERT INTO value_instances (
    object_id,
    declared_type,
    runtime_type,
    typing,
    textual_value
)
VALUES
    (
        NULL,
        'INTEGER',
        'INTEGER',
        'STATIC',
        '42'
    ),
    (
        NULL,
        'STRING',
        'STRING',
        'STATIC',
        'main'
    );

-- A dynamic value may change runtime type between assignments.
INSERT INTO value_instances (
    object_id,
    declared_type,
    runtime_type,
    typing,
    textual_value
)
VALUES
    (
        NULL,
        NULL,
        'INTEGER',
        'DYNAMIC',
        '42'
    ),
    (
        NULL,
        NULL,
        'STRING',
        'DYNAMIC',
        '42'
    );

INSERT INTO type_operations (
    type_name,
    operation_name,
    operand_count,
    result_type
)
VALUES
    ('INTEGER', 'addition', 2, 'INTEGER'),
    ('DECIMAL', 'addition', 2, 'DECIMAL'),
    ('STRING', 'concatenation', 2, 'STRING'),
    ('BOOLEAN', 'logical_and', 2, 'BOOLEAN');

INSERT INTO operation_attempts (
    operation_id,
    left_runtime_type,
    right_runtime_type,
    succeeded,
    failure_reason
)
SELECT
    operation_id,
    'INTEGER',
    'INTEGER',
    TRUE,
    NULL
FROM type_operations
WHERE type_name = 'INTEGER'
  AND operation_name = 'addition';

INSERT INTO operation_attempts (
    operation_id,
    left_runtime_type,
    right_runtime_type,
    succeeded,
    failure_reason
)
SELECT
    operation_id,
    'INTEGER',
    'STRING',
    FALSE,
    'No INTEGER + STRING operation is defined'
FROM type_operations
WHERE type_name = 'INTEGER'
  AND operation_name = 'addition';

-- Recursive lookup models lexical scope resolution.
WITH RECURSIVE scope_chain AS (
    SELECT
        scope_id,
        scope_name,
        parent_scope_id,
        0 AS depth
    FROM scope_regions
    WHERE scope_name = 'validation_block'

    UNION ALL

    SELECT
        parent.scope_id,
        parent.scope_name,
        parent.parent_scope_id,
        child.depth + 1
    FROM scope_regions parent
    JOIN scope_chain child
      ON parent.scope_id = child.parent_scope_id
)
SELECT
    sc.depth,
    sc.scope_name,
    b.identifier,
    b.binding_kind,
    b.target_description
FROM scope_chain sc
JOIN bindings b
  ON b.scope_id = sc.scope_id
WHERE b.identifier = 'repository_name'
ORDER BY sc.depth;

-- Resolve an identifier beginning in the nested block.
WITH RECURSIVE scope_chain AS (
    SELECT
        scope_id,
        parent_scope_id,
        0 AS depth
    FROM scope_regions
    WHERE scope_name = 'validation_block'

    UNION ALL

    SELECT
        parent.scope_id,
        parent.parent_scope_id,
        child.depth + 1
    FROM scope_regions parent
    JOIN scope_chain child
      ON parent.scope_id = child.parent_scope_id
),
resolution AS (
    SELECT
        sc.depth,
        sc.scope_id,
        b.binding_id,
        b.identifier
    FROM scope_chain sc
    JOIN bindings b
      ON b.scope_id = sc.scope_id
    WHERE b.identifier = 'repository_name'
)
SELECT *
FROM resolution
ORDER BY depth
LIMIT 1;

-- Type-system report separates declared and runtime types.
SELECT
    value_id,
    declared_type,
    runtime_type,
    typing,
    textual_value,
    CASE
        WHEN typing = 'STATIC'
             AND declared_type = runtime_type
            THEN 'compile-time type agrees with runtime value'
        WHEN typing = 'DYNAMIC'
            THEN 'runtime type determines current value behavior'
        ELSE 'type mismatch'
    END AS interpretation
FROM value_instances
ORDER BY value_id;

-- Failed operations expose runtime type incompatibilities.
SELECT
    attempt_id,
    left_runtime_type,
    right_runtime_type,
    succeeded,
    failure_reason
FROM operation_attempts
WHERE NOT succeeded;

-- Lifetime report identifies unreleased resources.
SELECT
    object_id,
    object_type,
    lifetime_kind,
    allocated_at,
    released_at,
    CASE
        WHEN released_at IS NULL THEN 'ACTIVE'
        ELSE 'RELEASED'
    END AS lifecycle_state
FROM runtime_objects
ORDER BY allocated_at;

-- Transactional demonstration:
-- the temporary binding is inserted and then rolled back, so the
-- database returns to its previous consistent state.
BEGIN;

INSERT INTO bindings (
    scope_id,
    identifier,
    binding_kind,
    target_description
)
SELECT
    scope_id,
    'transaction_local_value',
    'VARIABLE',
    'Binding created only inside this transaction'
FROM scope_regions
WHERE scope_name = 'validation_block';

SELECT
    identifier,
    target_description
FROM bindings
WHERE identifier = 'transaction_local_value';

ROLLBACK;

SELECT
    COUNT(*) AS bindings_remaining_after_rollback
FROM bindings
WHERE identifier = 'transaction_local_value';
