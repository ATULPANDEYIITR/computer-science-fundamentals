DROP SCHEMA IF EXISTS array_operations CASCADE;
CREATE SCHEMA array_operations;

SET search_path = array_operations, public;

-- A logical array is represented as ordered rows. The position column
-- preserves explicit indexing while constraints prevent duplicate positions.
CREATE TABLE integer_arrays (
    array_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    array_name text NOT NULL UNIQUE,
    capacity integer NOT NULL DEFAULT 4,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    CHECK (capacity > 0)
);

CREATE TABLE array_elements (
    array_id bigint NOT NULL REFERENCES integer_arrays(array_id) ON DELETE CASCADE,
    position integer NOT NULL,
    value integer NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (array_id, position),
    CHECK (position >= 0)
);

CREATE INDEX idx_array_elements_value
    ON array_elements (array_id, value);

CREATE TABLE array_operation_log (
    operation_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    array_id bigint NOT NULL REFERENCES integer_arrays(array_id) ON DELETE CASCADE,
    operation_type text NOT NULL,
    position integer,
    old_value integer,
    new_value integer,
    performed_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    CHECK (operation_type IN (
        'ACCESS', 'SEARCH', 'INSERT', 'DELETE', 'UPDATE'
    )),
    CHECK (position IS NULL OR position >= 0)
);

CREATE OR REPLACE FUNCTION validate_array_position()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    array_capacity integer;
BEGIN
    SELECT capacity
    INTO array_capacity
    FROM integer_arrays
    WHERE array_id = NEW.array_id;

    IF array_capacity IS NULL THEN
        RAISE EXCEPTION 'Array % does not exist', NEW.array_id;
    END IF;

    IF NEW.position < 0 THEN
        RAISE EXCEPTION 'Array position cannot be negative';
    END IF;

    IF NEW.position >= array_capacity THEN
        RAISE EXCEPTION
            'Position % exceeds array capacity %',
            NEW.position,
            array_capacity - 1;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_array_position
BEFORE INSERT OR UPDATE ON array_elements
FOR EACH ROW
EXECUTE FUNCTION validate_array_position();

CREATE OR REPLACE FUNCTION log_array_change()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO array_operation_log(
            array_id, operation_type, position, new_value
        )
        VALUES (
            NEW.array_id, 'INSERT', NEW.position, NEW.value
        );
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO array_operation_log(
            array_id, operation_type, position, old_value, new_value
        )
        VALUES (
            NEW.array_id, 'UPDATE', NEW.position, OLD.value, NEW.value
        );
        RETURN NEW;
    ELSE
        INSERT INTO array_operation_log(
            array_id, operation_type, position, old_value
        )
        VALUES (
            OLD.array_id, 'DELETE', OLD.position, OLD.value
        );
        RETURN OLD;
    END IF;
END;
$$;

CREATE TRIGGER trg_log_array_change
AFTER INSERT OR UPDATE OR DELETE ON array_elements
FOR EACH ROW
EXECUTE FUNCTION log_array_change();

CREATE OR REPLACE FUNCTION create_integer_array(
    p_name text,
    p_capacity integer DEFAULT 4
)
RETURNS bigint
LANGUAGE plpgsql
AS $$
DECLARE
    new_id bigint;
BEGIN
    IF p_name IS NULL OR btrim(p_name) = '' THEN
        RAISE EXCEPTION 'Array name cannot be empty';
    END IF;

    IF p_capacity <= 0 THEN
        RAISE EXCEPTION 'Capacity must be positive';
    END IF;

    INSERT INTO integer_arrays(array_name, capacity)
    VALUES (p_name, p_capacity)
    RETURNING array_id INTO new_id;

    RETURN new_id;
END;
$$;

CREATE OR REPLACE FUNCTION insert_array_value(
    p_array_id bigint,
    p_position integer,
    p_value integer
)
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
    current_size integer;
    current_capacity integer;
BEGIN
    SELECT capacity
    INTO current_capacity
    FROM integer_arrays
    WHERE array_id = p_array_id
    FOR UPDATE;

    IF current_capacity IS NULL THEN
        RAISE EXCEPTION 'Array % does not exist', p_array_id;
    END IF;

    SELECT count(*)::integer
    INTO current_size
    FROM array_elements
    WHERE array_id = p_array_id;

    IF current_size >= current_capacity THEN
        RAISE EXCEPTION 'Array % is at capacity', p_array_id;
    END IF;

    IF p_position < 0 OR p_position > current_size THEN
        RAISE EXCEPTION 'Insertion position % is invalid', p_position;
    END IF;

    -- Move the suffix right before inserting the new element.
    UPDATE array_elements
    SET position = position + 1
    WHERE array_id = p_array_id
      AND position >= p_position;

    INSERT INTO array_elements(array_id, position, value)
    VALUES (p_array_id, p_position, p_value);
END;
$$;

CREATE OR REPLACE FUNCTION delete_array_value(
    p_array_id bigint,
    p_position integer
)
RETURNS integer
LANGUAGE plpgsql
AS $$
DECLARE
    removed_value integer;
BEGIN
    SELECT value
    INTO removed_value
    FROM array_elements
    WHERE array_id = p_array_id
      AND position = p_position
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Position % does not exist in array %',
            p_position, p_array_id;
    END IF;

    DELETE FROM array_elements
    WHERE array_id = p_array_id
      AND position = p_position;

    -- Compact the suffix so indexing remains contiguous.
    UPDATE array_elements
    SET position = position - 1
    WHERE array_id = p_array_id
      AND position > p_position;

    RETURN removed_value;
END;
$$;

CREATE OR REPLACE FUNCTION array_at(
    p_array_id bigint,
    p_position integer
)
RETURNS integer
LANGUAGE plpgsql
AS $$
DECLARE
    result_value integer;
BEGIN
    SELECT value
    INTO result_value
    FROM array_elements
    WHERE array_id = p_array_id
      AND position = p_position;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Position % does not exist in array %',
            p_position, p_array_id;
    END IF;

    INSERT INTO array_operation_log(
        array_id, operation_type, position, new_value
    )
    VALUES (
        p_array_id, 'ACCESS', p_position, result_value
    );

    RETURN result_value;
END;
$$;

CREATE OR REPLACE FUNCTION linear_search(
    p_array_id bigint,
    p_value integer
)
RETURNS integer
LANGUAGE plpgsql
AS $$
DECLARE
    found_position integer;
BEGIN
    SELECT position
    INTO found_position
    FROM array_elements
    WHERE array_id = p_array_id
      AND value = p_value
    ORDER BY position
    LIMIT 1;

    INSERT INTO array_operation_log(
        array_id, operation_type, new_value
    )
    VALUES (
        p_array_id, 'SEARCH', p_value
    );

    RETURN COALESCE(found_position, -1);
END;
$$;

CREATE VIEW array_contents AS
SELECT
    a.array_id,
    a.array_name,
    a.capacity,
    count(e.position)::integer AS size,
    array_agg(e.value ORDER BY e.position)
        FILTER (WHERE e.position IS NOT NULL) AS values
FROM integer_arrays a
LEFT JOIN array_elements e
    ON e.array_id = a.array_id
GROUP BY a.array_id, a.array_name, a.capacity;

CREATE VIEW array_operation_report AS
SELECT
    array_id,
    operation_type,
    count(*) AS operation_count,
    max(performed_at) AS last_operation
FROM array_operation_log
GROUP BY array_id, operation_type;

-- Sample arrays represent both normal and boundary-oriented states.
SELECT create_integer_array('release_versions', 8);
SELECT create_integer_array('build_numbers', 6);

INSERT INTO array_elements(array_id, position, value)
SELECT 1, position, value
FROM (VALUES
    (0, 101),
    (1, 203),
    (2, 305),
    (3, 407)
) AS seed(position, value);

INSERT INTO array_elements(array_id, position, value)
SELECT 2, position, value
FROM (VALUES
    (0, 10),
    (1, 20),
    (2, 30),
    (3, 40),
    (4, 50)
) AS seed(position, value);

-- Indexed retrieval.
SELECT array_at(1, 2) AS value_at_position_2;

-- Linear search returns the first matching position.
SELECT linear_search(1, 305) AS position_of_305;
SELECT linear_search(1, 999) AS position_of_missing_value;

-- Transactional insertion shifts the suffix before inserting.
BEGIN;
SELECT insert_array_value(1, 2, 306);
COMMIT;

-- Update validates the target row through the primary key.
UPDATE array_elements
SET value = 204
WHERE array_id = 1
  AND position = 1;

-- Transactional deletion removes the row and compacts the suffix.
BEGIN;
SELECT delete_array_value(1, 2) AS deleted_value;
COMMIT;

-- Retrieval and aggregation.
SELECT *
FROM array_contents
ORDER BY array_id;

SELECT
    array_id,
    array_name,
    size,
    capacity,
    capacity - size AS free_slots
FROM array_contents
ORDER BY array_id;

-- CTE identifying arrays whose values are monotonically nondecreasing.
WITH ordered_values AS (
    SELECT
        array_id,
        position,
        value,
        lag(value) OVER (
            PARTITION BY array_id
            ORDER BY position
        ) AS previous_value
    FROM array_elements
)
SELECT
    array_id,
    bool_and(
        previous_value IS NULL OR value >= previous_value
    ) AS is_sorted
FROM ordered_values
GROUP BY array_id;

-- Find the largest element in each logical array.
SELECT DISTINCT ON (array_id)
    array_id,
    position,
    value
FROM array_elements
ORDER BY array_id, value DESC, position;

-- Operation audit report.
SELECT *
FROM array_operation_report
ORDER BY array_id, operation_type;

-- Demonstrate a failed indexed access without damaging persistent state.
DO $$
BEGIN
    BEGIN
        PERFORM array_at(1, 99);
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Expected access failure: %', SQLERRM;
    END;
END;
$$;

-- Demonstrate transactional rollback for an invalid insertion.
BEGIN;
DO $$
BEGIN
    PERFORM insert_array_value(1, 99, 999);
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Expected insertion failure: %', SQLERRM;
        RAISE EXCEPTION USING MESSAGE = 'Rollback invalid insertion';
END;
$$;
ROLLBACK;
