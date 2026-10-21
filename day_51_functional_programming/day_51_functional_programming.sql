DROP SCHEMA IF EXISTS functional_programming_demo CASCADE;
CREATE SCHEMA functional_programming_demo;
SET search_path TO functional_programming_demo;

-- The model represents functional concepts through immutable-style snapshots:
-- source values remain unchanged while derived values are computed by queries
-- and SQL functions.

CREATE TYPE order_state AS ENUM (
    'RECEIVED',
    'VALIDATED',
    'ELIGIBLE',
    'REJECTED'
);

CREATE TABLE customers (
    customer_id BIGSERIAL PRIMARY KEY,
    customer_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT customers_name_not_blank
        CHECK (length(btrim(customer_name)) > 0)
);

CREATE TABLE orders (
    order_id BIGSERIAL PRIMARY KEY,
    customer_id BIGINT NOT NULL
        REFERENCES customers(customer_id),
    discount_rate NUMERIC(5,4) NOT NULL DEFAULT 0,
    state order_state NOT NULL DEFAULT 'RECEIVED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT orders_discount_valid
        CHECK (discount_rate BETWEEN 0 AND 1)
);

CREATE TABLE order_items (
    order_item_id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL
        REFERENCES orders(order_id)
        ON DELETE CASCADE,
    price NUMERIC(12,2) NOT NULL,
    CONSTRAINT order_items_price_valid
        CHECK (price >= 0)
);

CREATE TABLE order_events (
    event_id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL
        REFERENCES orders(order_id)
        ON DELETE CASCADE,
    previous_state order_state,
    new_state order_state NOT NULL,
    event_message TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_orders_customer
    ON orders(customer_id);

CREATE INDEX idx_order_items_order
    ON order_items(order_id);

CREATE INDEX idx_order_events_order_time
    ON order_events(order_id, occurred_at DESC);

-- A pure SQL function: it derives a value from arguments without modifying
-- database state.
CREATE OR REPLACE FUNCTION calculate_subtotal(
    p_order_id BIGINT
)
RETURNS NUMERIC(12,2)
LANGUAGE SQL
STABLE
AS $$
    SELECT COALESCE(SUM(price), 0)::NUMERIC(12,2)
    FROM order_items
    WHERE order_id = p_order_id;
$$;

-- This function is also read-only and deterministic for a stable database
-- snapshot.
CREATE OR REPLACE FUNCTION calculate_total(
    p_order_id BIGINT
)
RETURNS NUMERIC(12,2)
LANGUAGE SQL
STABLE
AS $$
    SELECT ROUND(
        calculate_subtotal(o.order_id) * (1 - o.discount_rate),
        2
    )::NUMERIC(12,2)
    FROM orders o
    WHERE o.order_id = p_order_id;
$$;

-- A higher-order-function analogue is represented by a parameterized
-- predicate function. PostgreSQL does not treat ordinary SQL functions as
-- first-class values in exactly the same way as Python or JavaScript, so
-- separate predicate functions make the policy explicit.
CREATE OR REPLACE FUNCTION qualifies_high_value(
    p_total NUMERIC
)
RETURNS BOOLEAN
LANGUAGE SQL
IMMUTABLE
AS $$
    SELECT p_total >= 1000;
$$;

CREATE OR REPLACE FUNCTION set_order_state(
    p_order_id BIGINT,
    p_new_state order_state,
    p_message TEXT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    old_state order_state;
BEGIN
    SELECT state
    INTO old_state
    FROM orders
    WHERE order_id = p_order_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Order % does not exist', p_order_id;
    END IF;

    UPDATE orders
    SET state = p_new_state
    WHERE order_id = p_order_id;

    INSERT INTO order_events (
        order_id,
        previous_state,
        new_state,
        event_message
    )
    VALUES (
        p_order_id,
        old_state,
        p_new_state,
        p_message
    );
END;
$$;

-- The trigger records state transitions, separating audit behavior from
-- business calculations.
CREATE OR REPLACE FUNCTION audit_order_state()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.state IS DISTINCT FROM NEW.state THEN
        INSERT INTO order_events (
            order_id,
            previous_state,
            new_state,
            event_message
        )
        VALUES (
            NEW.order_id,
            OLD.state,
            NEW.state,
            'Order state changed'
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_audit_order_state
AFTER UPDATE OF state ON orders
FOR EACH ROW
EXECUTE FUNCTION audit_order_state();

CREATE VIEW order_totals AS
SELECT
    o.order_id,
    c.customer_name,
    o.state,
    calculate_subtotal(o.order_id) AS subtotal,
    o.discount_rate,
    calculate_total(o.order_id) AS total
FROM orders o
JOIN customers c
    ON c.customer_id = o.customer_id;

CREATE VIEW eligible_high_value_orders AS
SELECT *
FROM order_totals
WHERE qualifies_high_value(total);

INSERT INTO customers (customer_name)
VALUES
    ('Acme Analytics'),
    ('Beta Systems'),
    ('Gamma Research');

INSERT INTO orders (customer_id, discount_rate)
VALUES
    (1, 0.10),
    (2, 0.05),
    (3, 0.15),
    (1, 0.00);

INSERT INTO order_items (order_id, price)
VALUES
    (1, 650.00),
    (1, 500.00),
    (2, 300.00),
    (2, 250.00),
    (3, 1500.00),
    (3, 900.00),
    (4, 25.00),
    (4, 30.00);

-- Transactional validation keeps a state transition atomic.
BEGIN;

SELECT set_order_state(
    1,
    'VALIDATED',
    'Order passed structural validation'
);

SELECT set_order_state(
    1,
    'ELIGIBLE',
    'Order passed value policy'
);

COMMIT;

-- CTE evaluation provides a declarative equivalent of a functional pipeline:
-- source orders -> computed totals -> policy filter -> final projection.
WITH computed AS (
    SELECT
        order_id,
        customer_name,
        total
    FROM order_totals
),
qualified AS (
    SELECT *
    FROM computed
    WHERE qualifies_high_value(total)
)
SELECT
    order_id,
    customer_name,
    total
FROM qualified
ORDER BY total DESC;

-- Aggregate processing remains declarative and does not mutate the source rows.
SELECT
    customer_name,
    COUNT(*) AS order_count,
    ROUND(SUM(total), 2) AS customer_value
FROM order_totals
GROUP BY customer_name
ORDER BY customer_value DESC;

-- Demonstrate immutable-style derivation: the original order remains intact
-- while the query calculates a hypothetical 20% discount.
SELECT
    order_id,
    total AS current_total,
    ROUND(total * 0.80, 2) AS hypothetical_total
FROM order_totals
ORDER BY order_id;

-- Validation query for data-quality failures.
SELECT
    o.order_id,
    COUNT(oi.order_item_id) AS item_count
FROM orders o
LEFT JOIN order_items oi
    ON oi.order_id = o.order_id
GROUP BY o.order_id
HAVING COUNT(oi.order_item_id) = 0;

-- Transaction demonstrating rollback of an invalid state change.
BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM orders
        WHERE order_id = 2
    ) THEN
        RAISE EXCEPTION 'Expected sample order does not exist';
    END IF;

    PERFORM set_order_state(
        2,
        'REJECTED',
        'Temporary policy evaluation'
    );
END;
$$;

ROLLBACK;

-- The rollback leaves order 2 in its original state.
SELECT
    order_id,
    state
FROM orders
WHERE order_id = 2;
