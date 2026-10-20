DROP SCHEMA IF EXISTS oop_demo CASCADE;
CREATE SCHEMA oop_demo;
SET search_path = oop_demo;

-- The relational model represents classes as tables and object relationships
-- as foreign keys. Encapsulation is represented by constraints and functions
-- that prevent invalid state transitions.

CREATE TYPE account_status AS ENUM ('ACTIVE', 'FROZEN', 'CLOSED');
CREATE TYPE account_type AS ENUM ('SAVINGS', 'BUSINESS');

CREATE TABLE customer (
    customer_id BIGSERIAL PRIMARY KEY,
    customer_code TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL CHECK (length(trim(full_name)) >= 2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bank_account (
    account_id BIGSERIAL PRIMARY KEY,
    account_number TEXT NOT NULL UNIQUE,
    customer_id BIGINT NOT NULL REFERENCES customer(customer_id),
    account_type account_type NOT NULL,
    status account_status NOT NULL DEFAULT 'ACTIVE',
    balance NUMERIC(14, 2) NOT NULL DEFAULT 0,
    interest_rate NUMERIC(6, 5),
    credit_limit NUMERIC(14, 2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (length(trim(account_number)) >= 4),
    CHECK (balance >= 0),
    CHECK (interest_rate IS NULL OR interest_rate BETWEEN 0 AND 1),
    CHECK (credit_limit IS NULL OR credit_limit >= 0),

    CHECK (
        (account_type = 'SAVINGS'
            AND interest_rate IS NOT NULL
            AND credit_limit IS NULL)
        OR
        (account_type = 'BUSINESS'
            AND interest_rate IS NULL
            AND credit_limit IS NOT NULL)
    )
);

CREATE INDEX idx_bank_account_customer
    ON bank_account(customer_id);

CREATE INDEX idx_bank_account_status
    ON bank_account(status);

CREATE TABLE account_transaction (
    transaction_id BIGSERIAL PRIMARY KEY,
    account_id BIGINT NOT NULL REFERENCES bank_account(account_id),
    transaction_type TEXT NOT NULL
        CHECK (transaction_type IN ('DEPOSIT', 'WITHDRAWAL', 'INTEREST')),
    amount NUMERIC(14, 2) NOT NULL CHECK (amount > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_account_transaction_account_time
    ON account_transaction(account_id, created_at DESC);

CREATE OR REPLACE FUNCTION validate_account_state()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.status = 'CLOSED' AND NEW.balance <> 0 THEN
        RAISE EXCEPTION
            'Account % cannot be closed with balance %',
            NEW.account_number,
            NEW.balance;
    END IF;

    IF NEW.account_type = 'SAVINGS'
       AND NEW.interest_rate IS NULL THEN
        RAISE EXCEPTION 'Savings accounts require an interest rate';
    END IF;

    IF NEW.account_type = 'BUSINESS'
       AND NEW.credit_limit IS NULL THEN
        RAISE EXCEPTION 'Business accounts require a credit limit';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_account_state
BEFORE INSERT OR UPDATE ON bank_account
FOR EACH ROW
EXECUTE FUNCTION validate_account_state();

CREATE OR REPLACE FUNCTION deposit_money(
    p_account_id BIGINT,
    p_amount NUMERIC
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_amount <= 0 THEN
        RAISE EXCEPTION 'Deposit must be positive';
    END IF;

    UPDATE bank_account
    SET balance = balance + p_amount
    WHERE account_id = p_account_id
      AND status = 'ACTIVE';

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Account does not exist or is not active';
    END IF;

    INSERT INTO account_transaction(account_id, transaction_type, amount)
    VALUES (p_account_id, 'DEPOSIT', p_amount);
END;
$$;

CREATE OR REPLACE FUNCTION withdraw_money(
    p_account_id BIGINT,
    p_amount NUMERIC
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_type account_type;
    v_balance NUMERIC(14, 2);
    v_credit_limit NUMERIC(14, 2);
BEGIN
    IF p_amount <= 0 THEN
        RAISE EXCEPTION 'Withdrawal must be positive';
    END IF;

    SELECT account_type, balance, COALESCE(credit_limit, 0)
    INTO v_type, v_balance, v_credit_limit
    FROM bank_account
    WHERE account_id = p_account_id
      AND status = 'ACTIVE'
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Account does not exist or is not active';
    END IF;

    IF p_amount > v_balance + v_credit_limit THEN
        RAISE EXCEPTION
            'Withdrawal of % exceeds available funds and credit limit',
            p_amount;
    END IF;

    UPDATE bank_account
    SET balance = balance - p_amount
    WHERE account_id = p_account_id;

    INSERT INTO account_transaction(account_id, transaction_type, amount)
    VALUES (p_account_id, 'WITHDRAWAL', p_amount);
END;
$$;

CREATE OR REPLACE FUNCTION apply_savings_interest(
    p_account_id BIGINT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_rate NUMERIC(6, 5);
    v_amount NUMERIC(14, 2);
BEGIN
    SELECT interest_rate
    INTO v_rate
    FROM bank_account
    WHERE account_id = p_account_id
      AND account_type = 'SAVINGS'
      AND status = 'ACTIVE'
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Active savings account not found';
    END IF;

    SELECT ROUND(balance * v_rate, 2)
    INTO v_amount
    FROM bank_account
    WHERE account_id = p_account_id;

    UPDATE bank_account
    SET balance = balance + v_amount
    WHERE account_id = p_account_id;

    INSERT INTO account_transaction(account_id, transaction_type, amount)
    VALUES (p_account_id, 'INTEREST', v_amount);
END;
$$;

CREATE VIEW account_report AS
SELECT
    a.account_number,
    c.customer_code,
    c.full_name,
    a.account_type,
    a.status,
    a.balance,
    a.interest_rate,
    a.credit_limit
FROM bank_account a
JOIN customer c
    ON c.customer_id = a.customer_id;

INSERT INTO customer(customer_code, full_name)
VALUES
    ('C001', 'Alice Sharma'),
    ('C002', 'Acme Systems'),
    ('C003', 'Ravi Kumar');

INSERT INTO bank_account(
    account_number,
    customer_id,
    account_type,
    balance,
    interest_rate
)
SELECT 'S-1001', customer_id, 'SAVINGS', 5000, 0.04000
FROM customer
WHERE customer_code = 'C001';

INSERT INTO bank_account(
    account_number,
    customer_id,
    account_type,
    balance,
    credit_limit
)
SELECT 'B-2001', customer_id, 'BUSINESS', 10000, 5000
FROM customer
WHERE customer_code = 'C002';

INSERT INTO bank_account(
    account_number,
    customer_id,
    account_type,
    balance,
    interest_rate
)
SELECT 'S-3001', customer_id, 'SAVINGS', 1500, 0.02500
FROM customer
WHERE customer_code = 'C003';

BEGIN;

SELECT deposit_money(
    (SELECT account_id FROM bank_account WHERE account_number = 'S-1001'),
    1000
);

SELECT apply_savings_interest(
    (SELECT account_id FROM bank_account WHERE account_number = 'S-1001')
);

SELECT withdraw_money(
    (SELECT account_id FROM bank_account WHERE account_number = 'B-2001'),
    12000
);

COMMIT;

-- CTE-based aggregation reports the transaction profile of each account.
WITH transaction_totals AS (
    SELECT
        account_id,
        COUNT(*) AS transaction_count,
        SUM(amount) FILTER (WHERE transaction_type = 'DEPOSIT') AS deposits,
        SUM(amount) FILTER (WHERE transaction_type = 'WITHDRAWAL') AS withdrawals,
        SUM(amount) FILTER (WHERE transaction_type = 'INTEREST') AS interest
    FROM account_transaction
    GROUP BY account_id
)
SELECT
    a.account_number,
    c.full_name,
    a.account_type,
    a.balance,
    COALESCE(t.transaction_count, 0) AS transaction_count,
    COALESCE(t.deposits, 0) AS deposits,
    COALESCE(t.withdrawals, 0) AS withdrawals,
    COALESCE(t.interest, 0) AS interest
FROM bank_account a
JOIN customer c
    ON c.customer_id = a.customer_id
LEFT JOIN transaction_totals t
    ON t.account_id = a.account_id
ORDER BY a.account_number;

-- Polymorphism is represented by querying the common account abstraction
-- while retaining subtype-specific attributes.
SELECT
    account_number,
    full_name,
    account_type,
    balance,
    CASE
        WHEN account_type = 'SAVINGS'
            THEN format('Interest rate: %s%%', interest_rate * 100)
        WHEN account_type = 'BUSINESS'
            THEN format('Credit limit: %s', credit_limit)
    END AS specialized_behavior
FROM account_report
ORDER BY account_type, account_number;

-- This statement demonstrates database-enforced failure handling.
DO $$
BEGIN
    BEGIN
        PERFORM withdraw_money(
            (SELECT account_id
             FROM bank_account
             WHERE account_number = 'S-3001'),
            999999
        );
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Expected withdrawal failure: %', SQLERRM;
    END;
END;
$$;

-- A zero-balance account can transition to CLOSED.
UPDATE bank_account
SET balance = 0
WHERE account_number = 'S-3001';

UPDATE bank_account
SET status = 'CLOSED'
WHERE account_number = 'S-3001';

SELECT *
FROM account_report
ORDER BY account_number;
