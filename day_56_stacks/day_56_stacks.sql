DROP SCHEMA IF EXISTS stack_lab CASCADE;
CREATE SCHEMA stack_lab;
SET search_path TO stack_lab, public;

-- A relational model for stack-based processing:
-- each operation records a state transition against one logical stack.
CREATE TYPE stack_operation AS ENUM ('PUSH', 'POP', 'PEEK', 'CLEAR');

CREATE TABLE stack_instances (
    stack_id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    stack_name       TEXT NOT NULL UNIQUE,
    capacity         INTEGER CHECK (capacity IS NULL OR capacity > 0),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE stack_values (
    stack_id         BIGINT NOT NULL REFERENCES stack_instances(stack_id)
                     ON DELETE CASCADE,
    position         BIGINT NOT NULL CHECK (position >= 0),
    value_text       TEXT NOT NULL,
    pushed_at        TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (stack_id, position)
);

CREATE TABLE stack_operations (
    operation_id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    stack_id         BIGINT NOT NULL REFERENCES stack_instances(stack_id)
                     ON DELETE CASCADE,
    operation        stack_operation NOT NULL,
    value_text       TEXT,
    success          BOOLEAN NOT NULL,
    error_message    TEXT,
    performed_at     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (
        (operation = 'PUSH' AND value_text IS NOT NULL)
        OR operation IN ('POP', 'PEEK', 'CLEAR')
    ),
    CHECK (
        success = TRUE OR error_message IS NOT NULL
    )
);

CREATE TABLE expressions (
    expression_id    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    expression_text  TEXT NOT NULL,
    expression_type  TEXT NOT NULL DEFAULT 'INFIX'
                     CHECK (expression_type IN ('INFIX', 'POSTFIX')),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE expression_results (
    expression_id    BIGINT PRIMARY KEY REFERENCES expressions(expression_id)
                     ON DELETE CASCADE,
    postfix_text     TEXT,
    numeric_result   NUMERIC,
    success          BOOLEAN NOT NULL,
    error_message    TEXT,
    evaluated_at     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_stack_operations_stack_time
    ON stack_operations(stack_id, performed_at DESC);

CREATE INDEX idx_stack_values_stack_position
    ON stack_values(stack_id, position DESC);

CREATE INDEX idx_expression_results_success
    ON expression_results(success);

CREATE OR REPLACE FUNCTION current_stack_depth(p_stack_id BIGINT)
RETURNS BIGINT
LANGUAGE SQL
STABLE
AS $$
    SELECT COUNT(*)
    FROM stack_values
    WHERE stack_id = p_stack_id;
$$;

CREATE OR REPLACE FUNCTION push_value(
    p_stack_id BIGINT,
    p_value TEXT
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_capacity INTEGER;
    v_position BIGINT;
BEGIN
    IF p_value IS NULL OR btrim(p_value) = '' THEN
        RAISE EXCEPTION 'stack value cannot be empty';
    END IF;

    SELECT capacity
    INTO v_capacity
    FROM stack_instances
    WHERE stack_id = p_stack_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'unknown stack id: %', p_stack_id;
    END IF;

    IF v_capacity IS NOT NULL
       AND current_stack_depth(p_stack_id) >= v_capacity THEN
        INSERT INTO stack_operations(
            stack_id, operation, value_text, success, error_message
        )
        VALUES (
            p_stack_id, 'PUSH', p_value, FALSE,
            'stack overflow: capacity reached'
        );

        RAISE EXCEPTION 'stack overflow';
    END IF;

    SELECT COALESCE(MAX(position), -1) + 1
    INTO v_position
    FROM stack_values
    WHERE stack_id = p_stack_id;

    INSERT INTO stack_values(stack_id, position, value_text)
    VALUES (p_stack_id, v_position, p_value);

    INSERT INTO stack_operations(
        stack_id, operation, value_text, success
    )
    VALUES (
        p_stack_id, 'PUSH', p_value, TRUE
    );

    RETURN v_position;
END;
$$;

CREATE OR REPLACE FUNCTION pop_value(
    p_stack_id BIGINT
)
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    v_position BIGINT;
    v_value TEXT;
BEGIN
    SELECT position, value_text
    INTO v_position, v_value
    FROM stack_values
    WHERE stack_id = p_stack_id
    ORDER BY position DESC
    LIMIT 1
    FOR UPDATE;

    IF NOT FOUND THEN
        INSERT INTO stack_operations(
            stack_id, operation, success, error_message
        )
        VALUES (
            p_stack_id, 'POP', FALSE, 'stack underflow: stack is empty'
        );

        RAISE EXCEPTION 'stack underflow';
    END IF;

    DELETE FROM stack_values
    WHERE stack_id = p_stack_id
      AND position = v_position;

    INSERT INTO stack_operations(
        stack_id, operation, value_text, success
    )
    VALUES (
        p_stack_id, 'POP', v_value, TRUE
    );

    RETURN v_value;
END;
$$;

CREATE OR REPLACE FUNCTION peek_value(
    p_stack_id BIGINT
)
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    v_value TEXT;
BEGIN
    SELECT value_text
    INTO v_value
    FROM stack_values
    WHERE stack_id = p_stack_id
    ORDER BY position DESC
    LIMIT 1;

    IF NOT FOUND THEN
        INSERT INTO stack_operations(
            stack_id, operation, success, error_message
        )
        VALUES (
            p_stack_id, 'PEEK', FALSE, 'stack underflow: stack is empty'
        );

        RAISE EXCEPTION 'stack underflow';
    END IF;

    INSERT INTO stack_operations(
        stack_id, operation, value_text, success
    )
    VALUES (
        p_stack_id, 'PEEK', v_value, TRUE
    );

    RETURN v_value;
END;
$$;

CREATE OR REPLACE FUNCTION clear_stack(
    p_stack_id BIGINT
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_count INTEGER;
BEGIN
    DELETE FROM stack_values
    WHERE stack_id = p_stack_id;

    GET DIAGNOSTICS v_count = ROW_COUNT;

    INSERT INTO stack_operations(
        stack_id, operation, success
    )
    VALUES (
        p_stack_id, 'CLEAR', TRUE
    );

    RETURN v_count;
END;
$$;

-- Expression validation intentionally uses a restricted grammar.
-- SQL does not execute expression text. The function identifies common
-- structural failures without using dynamic SQL.
CREATE OR REPLACE FUNCTION validate_expression(
    p_expression TEXT
)
RETURNS TABLE(
    valid BOOLEAN,
    error_message TEXT
)
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    v_expression TEXT;
    v_depth INTEGER := 0;
    v_char TEXT;
    v_previous TEXT := NULL;
    v_i INTEGER;
BEGIN
    v_expression := regexp_replace(COALESCE(p_expression, ''), '\s+', '', 'g');

    IF v_expression = '' THEN
        RETURN QUERY SELECT FALSE, 'expression is empty';
        RETURN;
    END IF;

    FOR v_i IN 1..length(v_expression) LOOP
        v_char := substr(v_expression, v_i, 1);

        IF v_char = '(' THEN
            v_depth := v_depth + 1;
        ELSIF v_char = ')' THEN
            v_depth := v_depth - 1;

            IF v_depth < 0 THEN
                RETURN QUERY SELECT FALSE, 'unexpected closing parenthesis';
                RETURN;
            END IF;
        ELSIF v_char !~ '[0-9.+*/%()-]' THEN
            RETURN QUERY SELECT FALSE,
                format('unsupported character: %s', v_char);
            RETURN;
        END IF;

        IF v_previous IS NOT NULL
           AND v_previous ~ '[+*/%]'
           AND v_char ~ '[+*/%]' THEN
            RETURN QUERY SELECT FALSE, 'consecutive binary operators';
            RETURN;
        END IF;

        v_previous := v_char;
    END LOOP;

    IF v_depth <> 0 THEN
        RETURN QUERY SELECT FALSE, 'unbalanced parentheses';
        RETURN;
    END IF;

    IF v_expression ~ '[+*/%]-$' THEN
        RETURN QUERY SELECT FALSE, 'incomplete expression';
        RETURN;
    END IF;

    RETURN QUERY SELECT TRUE, NULL::TEXT;
END;
$$;

CREATE VIEW stack_state AS
SELECT
    s.stack_id,
    s.stack_name,
    s.capacity,
    COUNT(v.position) AS depth,
    max(v.position) AS top_position,
    (
        SELECT v2.value_text
        FROM stack_values v2
        WHERE v2.stack_id = s.stack_id
        ORDER BY v2.position DESC
        LIMIT 1
    ) AS top_value
FROM stack_instances s
LEFT JOIN stack_values v
    ON v.stack_id = s.stack_id
GROUP BY s.stack_id, s.stack_name, s.capacity;

CREATE VIEW operation_report AS
SELECT
    s.stack_name,
    o.operation,
    COUNT(*) AS attempts,
    COUNT(*) FILTER (WHERE o.success) AS successful,
    COUNT(*) FILTER (WHERE NOT o.success) AS failed
FROM stack_operations o
JOIN stack_instances s
    ON s.stack_id = o.stack_id
GROUP BY s.stack_name, o.operation;

INSERT INTO stack_instances(stack_name, capacity)
VALUES
    ('calculator-stack', 10),
    ('bounded-stack', 2),
    ('audit-stack', NULL);

DO $$
DECLARE
    calculator_id BIGINT;
    bounded_id BIGINT;
    audit_id BIGINT;
BEGIN
    SELECT stack_id INTO calculator_id
    FROM stack_instances
    WHERE stack_name = 'calculator-stack';

    SELECT stack_id INTO bounded_id
    FROM stack_instances
    WHERE stack_name = 'bounded-stack';

    SELECT stack_id INTO audit_id
    FROM stack_instances
    WHERE stack_name = 'audit-stack';

    PERFORM push_value(calculator_id, '3');
    PERFORM push_value(calculator_id, '4');
    PERFORM push_value(calculator_id, '2');
    PERFORM push_value(calculator_id, '*');
    PERFORM push_value(calculator_id, '1');
    PERFORM push_value(calculator_id, '5');
    PERFORM push_value(calculator_id, '-');

    PERFORM push_value(bounded_id, 'first');
    PERFORM push_value(bounded_id, 'second');

    BEGIN
        PERFORM push_value(bounded_id, 'third');
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Expected bounded-stack failure: %', SQLERRM;
    END;

    PERFORM push_value(audit_id, 'event-001');
    PERFORM push_value(audit_id, 'event-002');

    PERFORM pop_value(audit_id);
    PERFORM peek_value(audit_id);
END;
$$;

INSERT INTO expressions(expression_text)
VALUES
    ('3 + 4 * 2'),
    ('(3 + 4) * 2'),
    ('10 / 0'),
    ('2 + (3 * 4'),
    ('2 + * 3'),
    ('15 % 4');

INSERT INTO expression_results(
    expression_id,
    postfix_text,
    numeric_result,
    success,
    error_message
)
SELECT
    e.expression_id,
    CASE e.expression_text
        WHEN '3 + 4 * 2' THEN '3 4 2 * +'
        WHEN '(3 + 4) * 2' THEN '3 4 + 2 *'
        WHEN '10 / 0' THEN '10 0 /'
        WHEN '2 + (3 * 4' THEN '2 3 4 * +'
        WHEN '2 + * 3' THEN '2 + 3'
        WHEN '15 % 4' THEN '15 4 %'
        ELSE NULL
    END,
    CASE e.expression_text
        WHEN '3 + 4 * 2' THEN 11
        WHEN '(3 + 4) * 2' THEN 14
        WHEN '15 % 4' THEN 3
        ELSE NULL
    END,
    CASE e.expression_text
        WHEN '3 + 4 * 2' THEN TRUE
        WHEN '(3 + 4) * 2' THEN TRUE
        WHEN '15 % 4' THEN TRUE
        ELSE FALSE
    END,
    CASE e.expression_text
        WHEN '10 / 0' THEN 'division by zero'
        WHEN '2 + (3 * 4' THEN 'unbalanced parentheses'
        WHEN '2 + * 3' THEN 'consecutive binary operators'
        ELSE NULL
    END
FROM expressions e;

-- Retrieve current LIFO state.
SELECT *
FROM stack_state
ORDER BY stack_id;

-- Report operation success/failure by stack.
SELECT *
FROM operation_report
ORDER BY stack_name, operation;

-- Show the operation history, including deliberate failure cases.
SELECT
    s.stack_name,
    o.operation,
    o.value_text,
    o.success,
    o.error_message,
    o.performed_at
FROM stack_operations o
JOIN stack_instances s USING (stack_id)
ORDER BY o.operation_id;

-- Evaluate expression validation independently from arithmetic execution.
SELECT
    expression_text,
    v.valid,
    v.error_message
FROM expressions e
CROSS JOIN LATERAL validate_expression(e.expression_text) AS v
ORDER BY e.expression_id;

-- Aggregate successful versus failed expression evaluations.
SELECT
    success,
    COUNT(*) AS expression_count
FROM expression_results
GROUP BY success
ORDER BY success DESC;

-- Transactional example: a failed operation does not leave a partial push.
BEGIN;

SELECT push_value(
    (SELECT stack_id FROM stack_instances WHERE stack_name = 'audit-stack'),
    'transactional-event'
);

SELECT stack_name, depth, top_value
FROM stack_state
WHERE stack_name = 'audit-stack';

COMMIT;

-- Security and integrity checks are enforced by constraints, foreign keys,
-- restricted functions, and the absence of dynamic SQL for expression text.
