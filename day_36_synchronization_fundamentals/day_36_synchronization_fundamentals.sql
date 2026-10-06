/*
 * Synchronization Fundamentals
 *
 * PostgreSQL 14+ compatible.
 *
 * This script models a concurrent inventory reservation workflow. The database
 * layer demonstrates:
 *   - race conditions in check-then-update workflows
 *   - critical sections created by row-level locks
 *   - mutual exclusion through SELECT ... FOR UPDATE
 *   - atomic UPDATE statements
 *   - transaction isolation
 *   - advisory locks for application-defined critical sections
 *   - constraints that preserve invariants
 *
 * The examples are intentionally transaction-oriented because SQL concurrency
 * is about protecting shared database state rather than protecting variables
 * inside one application process.
 */

DROP SCHEMA IF EXISTS synchronization_lab CASCADE;
CREATE SCHEMA synchronization_lab;
SET search_path = synchronization_lab, public;

CREATE TABLE products (
    product_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sku TEXT NOT NULL UNIQUE,
    product_name TEXT NOT NULL,
    stock_quantity INTEGER NOT NULL CHECK (stock_quantity >= 0),
    version_number INTEGER NOT NULL DEFAULT 1 CHECK (version_number > 0)
);

CREATE TABLE reservation_requests (
    reservation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES products(product_id),
    customer_reference TEXT NOT NULL,
    requested_quantity INTEGER NOT NULL CHECK (requested_quantity > 0),
    status TEXT NOT NULL CHECK (
        status IN ('PENDING', 'CONFIRMED', 'REJECTED')
    ),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMPTZ
);

CREATE TABLE reservation_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    reservation_id BIGINT NOT NULL
        REFERENCES reservation_requests(reservation_id),
    event_type TEXT NOT NULL CHECK (
        event_type IN ('CREATED', 'CONFIRMED', 'REJECTED')
    ),
    event_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    details TEXT
);

CREATE INDEX idx_reservation_requests_product_status
    ON reservation_requests(product_id, status);

CREATE INDEX idx_reservation_events_reservation
    ON reservation_events(reservation_id);

INSERT INTO products (sku, product_name, stock_quantity)
VALUES
    ('SYNC-100', 'Synchronization Lab Resource', 100),
    ('LOCK-200', 'Critical Section Test Resource', 20),
    ('ATOMIC-300', 'Atomic Update Test Resource', 5);

INSERT INTO reservation_requests (
    product_id,
    customer_reference,
    requested_quantity,
    status
)
SELECT
    product_id,
    'CUSTOMER-A',
    10,
    'PENDING'
FROM products
WHERE sku = 'SYNC-100';

INSERT INTO reservation_requests (
    product_id,
    customer_reference,
    requested_quantity,
    status
)
SELECT
    product_id,
    'CUSTOMER-B',
    80,
    'PENDING'
FROM products
WHERE sku = 'SYNC-100';

INSERT INTO reservation_requests (
    product_id,
    customer_reference,
    requested_quantity,
    status
)
SELECT
    product_id,
    'CUSTOMER-C',
    80,
    'PENDING'
FROM products
WHERE sku = 'SYNC-100';


/*
 * Atomic UPDATE
 *
 * The database evaluates the stock predicate and performs the decrement as one
 * statement. Competing transactions cannot independently read the same row and
 * then both apply an unchecked decrement.
 */
WITH changed AS (
    UPDATE products
    SET
        stock_quantity = stock_quantity - 15,
        version_number = version_number + 1
    WHERE sku = 'SYNC-100'
      AND stock_quantity >= 15
    RETURNING product_id, stock_quantity, version_number
)
SELECT *
FROM changed;


/*
 * Row-level critical section
 *
 * In a transaction, SELECT ... FOR UPDATE locks the selected product row.
 * Another transaction attempting to lock the same row must wait until this
 * transaction commits or rolls back.
 *
 * Execute the following transaction interactively as a complete unit:
 *
 * BEGIN;
 *
 * SELECT product_id, stock_quantity
 * FROM products
 * WHERE sku = 'LOCK-200'
 * FOR UPDATE;
 *
 * UPDATE products
 * SET
 *     stock_quantity = stock_quantity - 5,
 *     version_number = version_number + 1
 * WHERE sku = 'LOCK-200'
 *   AND stock_quantity >= 5;
 *
 * COMMIT;
 */


/*
 * Transactional reservation procedure
 *
 * PostgreSQL functions can combine row locking, validation, state mutation,
 * and event creation. The row lock protects the critical section containing
 * the balance check and decrement.
 */
CREATE OR REPLACE FUNCTION reserve_inventory(
    p_product_id BIGINT,
    p_customer_reference TEXT,
    p_quantity INTEGER
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_stock INTEGER;
    v_reservation_id BIGINT;
BEGIN
    IF p_customer_reference IS NULL
       OR length(trim(p_customer_reference)) = 0 THEN
        RAISE EXCEPTION 'Customer reference cannot be empty';
    END IF;

    IF p_quantity <= 0 THEN
        RAISE EXCEPTION 'Reservation quantity must be positive';
    END IF;

    /*
     * This SELECT establishes the database-level critical section for the
     * product row. Concurrent reservations for the same product serialize here.
     */
    SELECT stock_quantity
    INTO v_stock
    FROM products
    WHERE product_id = p_product_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Product % does not exist', p_product_id;
    END IF;

    IF v_stock < p_quantity THEN
        INSERT INTO reservation_requests (
            product_id,
            customer_reference,
            requested_quantity,
            status,
            processed_at
        )
        VALUES (
            p_product_id,
            p_customer_reference,
            p_quantity,
            'REJECTED',
            CURRENT_TIMESTAMP
        )
        RETURNING reservation_id INTO v_reservation_id;

        INSERT INTO reservation_events (
            reservation_id,
            event_type,
            details
        )
        VALUES (
            v_reservation_id,
            'REJECTED',
            format(
                'Insufficient stock. Available=%s requested=%s',
                v_stock,
                p_quantity
            )
        );

        RETURN v_reservation_id;
    END IF;

    UPDATE products
    SET
        stock_quantity = stock_quantity - p_quantity,
        version_number = version_number + 1
    WHERE product_id = p_product_id;

    INSERT INTO reservation_requests (
        product_id,
        customer_reference,
        requested_quantity,
        status,
        processed_at
    )
    VALUES (
        p_product_id,
        p_customer_reference,
        p_quantity,
        'CONFIRMED',
        CURRENT_TIMESTAMP
    )
    RETURNING reservation_id INTO v_reservation_id;

    INSERT INTO reservation_events (
        reservation_id,
        event_type,
        details
    )
    VALUES (
        v_reservation_id,
        'CONFIRMED',
        format('Reserved quantity=%s', p_quantity)
    );

    RETURN v_reservation_id;
END;
$$;


/*
 * Execute several reservations against the same product.
 *
 * Each function invocation participates in its caller's transaction and uses
 * row-level mutual exclusion around the stock check and decrement.
 */
BEGIN;

SELECT reserve_inventory(
    product_id,
    'TX-CUSTOMER-A',
    20
)
FROM products
WHERE sku = 'LOCK-200';

SELECT reserve_inventory(
    product_id,
    'TX-CUSTOMER-B',
    20
)
FROM products
WHERE sku = 'LOCK-200';

COMMIT;


/*
 * Optimistic version validation
 *
 * This pattern does not hold a database lock for the entire application
 * workflow. The caller records the version it observed and the UPDATE succeeds
 * only if that version is still current.
 */
WITH current_product AS (
    SELECT product_id, version_number
    FROM products
    WHERE sku = 'ATOMIC-300'
)
SELECT *
FROM current_product;


/*
 * The following statement represents a client that previously observed
 * version 1. If another transaction has already changed the row, zero rows
 * are updated and the client must treat that as a concurrency conflict.
 */
UPDATE products
SET
    stock_quantity = stock_quantity - 1,
    version_number = version_number + 1
WHERE sku = 'ATOMIC-300'
  AND version_number = 1
  AND stock_quantity >= 1
RETURNING product_id, stock_quantity, version_number;


/*
 * Advisory lock example
 *
 * PostgreSQL advisory locks are useful when the critical resource is not
 * naturally represented by a row. The integer key should be derived from a
 * stable application-defined resource identifier.
 *
 * pg_advisory_xact_lock is transaction-scoped: PostgreSQL releases it
 * automatically when the transaction ends.
 */
BEGIN;

SELECT pg_advisory_xact_lock(20261006);

SELECT
    pg_backend_pid() AS backend_id,
    'application-defined critical section acquired' AS state;

COMMIT;


/*
 * Inspect current state.
 */
SELECT
    product_id,
    sku,
    product_name,
    stock_quantity,
    version_number
FROM products
ORDER BY product_id;

SELECT
    r.reservation_id,
    p.sku,
    r.customer_reference,
    r.requested_quantity,
    r.status,
    r.created_at,
    r.processed_at
FROM reservation_requests AS r
JOIN products AS p
    ON p.product_id = r.product_id
ORDER BY r.reservation_id;


/*
 * Detect inventory invariants.
 *
 * A negative stock value should be impossible because both the CHECK constraint
 * and reservation procedure protect it.
 */
SELECT
    sku,
    stock_quantity,
    CASE
        WHEN stock_quantity < 0 THEN 'INVALID'
        ELSE 'VALID'
    END AS invariant_status
FROM products;


/*
 * Show reservation outcomes.
 */
SELECT
    p.sku,
    COUNT(*) FILTER (
        WHERE r.status = 'CONFIRMED'
    ) AS confirmed_reservations,
    COUNT(*) FILTER (
        WHERE r.status = 'REJECTED'
    ) AS rejected_reservations,
    COALESCE(SUM(r.requested_quantity) FILTER (
        WHERE r.status = 'CONFIRMED'
    ), 0) AS confirmed_quantity
FROM products AS p
LEFT JOIN reservation_requests AS r
    ON r.product_id = p.product_id
GROUP BY p.product_id, p.sku
ORDER BY p.sku;


/*
 * Inspect event history.
 */
SELECT
    e.event_id,
    r.reservation_id,
    p.sku,
    e.event_type,
    e.event_at,
    e.details
FROM reservation_events AS e
JOIN reservation_requests AS r
    ON r.reservation_id = e.reservation_id
JOIN products AS p
    ON p.product_id = r.product_id
ORDER BY e.event_id;


/*
 * Important concurrency distinction:
 *
 * A database constraint such as CHECK (stock_quantity >= 0) enforces a state
 * invariant, but it does not by itself make a multi-step check-then-update
 * application workflow safe. Mutual exclusion or an atomic conditional UPDATE
 * is required when multiple transactions can modify the same resource.
 */
