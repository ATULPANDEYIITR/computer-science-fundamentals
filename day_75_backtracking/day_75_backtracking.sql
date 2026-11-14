-- ============================================================
-- BACKTRACKING AND STATE SPACE TREE MANAGEMENT
-- PostgreSQL 14+
--
-- Models:
--   Search jobs
--   Search configurations
--   State-space tree nodes
--   Candidate decisions
--   Partial assignments
--   Complete solutions
--   Constraint evaluation
--   Search statistics
--   Search execution and reporting
--
-- Includes executable permutation, combination and N-Queens
-- search functions.
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS backtracking;

SET search_path TO backtracking, public;

-- ------------------------------------------------------------
-- 1. Domain types
-- ------------------------------------------------------------

CREATE TYPE search_type AS ENUM (
    'PERMUTATION',
    'COMBINATION',
    'N_QUEENS'
);

CREATE TYPE search_status AS ENUM (
    'CREATED',
    'RUNNING',
    'COMPLETED',
    'FAILED',
    'LIMIT_EXCEEDED'
);

CREATE TYPE node_status AS ENUM (
    'EXPANDED',
    'PRUNED',
    'SOLUTION',
    'DEAD_END'
);

CREATE TYPE decision_status AS ENUM (
    'ACCEPTED',
    'REJECTED'
);

-- ------------------------------------------------------------
-- 2. Search jobs
-- ------------------------------------------------------------

CREATE TABLE search_jobs (
    job_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    job_name VARCHAR(120) NOT NULL,

    algorithm search_type NOT NULL,

    status search_status NOT NULL DEFAULT 'CREATED',

    input_values INTEGER[] NOT NULL DEFAULT '{}',

    selection_size INTEGER,

    board_size INTEGER,

    max_nodes BIGINT NOT NULL DEFAULT 100000,

    max_solutions BIGINT NOT NULL DEFAULT 10000,

    nodes_visited BIGINT NOT NULL DEFAULT 0,

    solutions_found BIGINT NOT NULL DEFAULT 0,

    pruned_branches BIGINT NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    failure_reason TEXT,

    CONSTRAINT valid_job_name
        CHECK (length(trim(job_name)) > 0),

    CONSTRAINT valid_limits
        CHECK (max_nodes > 0 AND max_solutions > 0),

    CONSTRAINT valid_counters
        CHECK (
            nodes_visited >= 0
            AND solutions_found >= 0
            AND pruned_branches >= 0
        ),

    CONSTRAINT valid_selection_size
        CHECK (
            selection_size IS NULL
            OR selection_size >= 0
        ),

    CONSTRAINT valid_board_size
        CHECK (
            board_size IS NULL
            OR board_size BETWEEN 1 AND 15
        ),

    CONSTRAINT valid_algorithm_configuration
        CHECK (
            (
                algorithm = 'PERMUTATION'
                AND selection_size IS NULL
                AND board_size IS NULL
            )
            OR
            (
                algorithm = 'COMBINATION'
                AND selection_size IS NOT NULL
                AND board_size IS NULL
                AND selection_size <= cardinality(input_values)
            )
            OR
            (
                algorithm = 'N_QUEENS'
                AND board_size IS NOT NULL
                AND selection_size IS NULL
            )
        )
);

CREATE INDEX idx_jobs_status_created
    ON search_jobs(status, created_at DESC);

CREATE INDEX idx_jobs_algorithm
    ON search_jobs(algorithm, created_at DESC);

-- ------------------------------------------------------------
-- 3. State-space tree nodes
-- ------------------------------------------------------------

CREATE TABLE search_nodes (
    node_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    job_id BIGINT NOT NULL
        REFERENCES search_jobs(job_id) ON DELETE CASCADE,

    parent_node_id BIGINT,

    depth INTEGER NOT NULL,

    state_values INTEGER[] NOT NULL DEFAULT '{}',

    status node_status NOT NULL DEFAULT 'EXPANDED',

    rejection_reason TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_node_depth CHECK (depth >= 0),

    CONSTRAINT unique_node_identity
        UNIQUE (node_id, job_id),

    CONSTRAINT parent_node_same_job
        FOREIGN KEY (parent_node_id, job_id)
        REFERENCES search_nodes(node_id, job_id)
        DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX idx_nodes_job_depth
    ON search_nodes(job_id, depth);

CREATE INDEX idx_nodes_parent
    ON search_nodes(parent_node_id);

CREATE INDEX idx_nodes_status
    ON search_nodes(job_id, status);

-- ------------------------------------------------------------
-- 4. Candidate decisions
-- ------------------------------------------------------------

CREATE TABLE candidate_decisions (
    decision_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    node_id BIGINT NOT NULL
        REFERENCES search_nodes(node_id) ON DELETE CASCADE,

    candidate_value INTEGER NOT NULL,

    decision decision_status NOT NULL,

    constraint_name VARCHAR(100) NOT NULL,

    explanation TEXT,

    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_decisions_node
    ON candidate_decisions(node_id, decision);

-- ------------------------------------------------------------
-- 5. Complete solutions
-- ------------------------------------------------------------

CREATE TABLE search_solutions (
    solution_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    job_id BIGINT NOT NULL
        REFERENCES search_jobs(job_id) ON DELETE CASCADE,

    terminal_node_id BIGINT
        REFERENCES search_nodes(node_id) ON DELETE SET NULL,

    solution_number INTEGER NOT NULL,

    solution_values INTEGER[] NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT positive_solution_number
        CHECK (solution_number > 0),

    CONSTRAINT unique_job_solution
        UNIQUE (job_id, solution_number)
);

CREATE INDEX idx_solutions_job
    ON search_solutions(job_id, solution_number);

-- ------------------------------------------------------------
-- 6. Search execution audit
-- ------------------------------------------------------------

CREATE TABLE search_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    job_id BIGINT NOT NULL
        REFERENCES search_jobs(job_id) ON DELETE CASCADE,

    event_type VARCHAR(50) NOT NULL,

    event_details JSONB NOT NULL DEFAULT '{}'::jsonb,

    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_events_job_time
    ON search_events(job_id, recorded_at DESC);

-- ------------------------------------------------------------
-- 7. State-space tree integrity trigger
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_search_node()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    parent_depth INTEGER;
BEGIN
    IF NEW.parent_node_id IS NULL THEN
        IF NEW.depth <> 0 THEN
            RAISE EXCEPTION
                'Root nodes must have depth zero';
        END IF;

        RETURN NEW;
    END IF;

    SELECT depth
    INTO parent_depth
    FROM search_nodes
    WHERE node_id = NEW.parent_node_id
      AND job_id = NEW.job_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Parent node does not belong to the same job';
    END IF;

    IF NEW.depth <> parent_depth + 1 THEN
        RAISE EXCEPTION
            'Child depth must equal parent depth plus one';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_search_node
BEFORE INSERT ON search_nodes
FOR EACH ROW
EXECUTE FUNCTION validate_search_node();

-- ------------------------------------------------------------
-- 8. Job lifecycle validation
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_job_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status IN ('COMPLETED', 'FAILED', 'LIMIT_EXCEEDED')
       AND NEW.status <> OLD.status THEN
        RAISE EXCEPTION
            'Terminal search jobs cannot be reopened';
    END IF;

    IF OLD.status = 'RUNNING'
       AND NEW.status = 'CREATED' THEN
        RAISE EXCEPTION
            'Running jobs cannot return to CREATED';
    END IF;

    IF NEW.status = 'RUNNING'
       AND OLD.status = 'CREATED' THEN
        NEW.started_at := CURRENT_TIMESTAMP;
    END IF;

    IF NEW.status IN ('COMPLETED', 'FAILED', 'LIMIT_EXCEEDED')
       AND OLD.status <> NEW.status THEN
        NEW.completed_at := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_job_transition
BEFORE UPDATE OF status ON search_jobs
FOR EACH ROW
EXECUTE FUNCTION validate_job_transition();

-- ------------------------------------------------------------
-- 9. Record a search event
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE record_event(
    p_job_id BIGINT,
    p_event_type VARCHAR,
    p_details JSONB DEFAULT '{}'::jsonb
)
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO search_events(
        job_id,
        event_type,
        event_details
    )
    VALUES (
        p_job_id,
        p_event_type,
        COALESCE(p_details, '{}'::jsonb)
    );
END;
$$;

-- ------------------------------------------------------------
-- 10. Generic job creation
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION create_search_job(
    p_name VARCHAR,
    p_algorithm search_type,
    p_values INTEGER[],
    p_selection_size INTEGER DEFAULT NULL,
    p_board_size INTEGER DEFAULT NULL,
    p_max_nodes BIGINT DEFAULT 100000,
    p_max_solutions BIGINT DEFAULT 10000
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    new_job_id BIGINT;
BEGIN
    IF p_name IS NULL OR length(trim(p_name)) = 0 THEN
        RAISE EXCEPTION 'Job name is required';
    END IF;

    IF p_max_nodes <= 0 OR p_max_solutions <= 0 THEN
        RAISE EXCEPTION 'Search limits must be positive';
    END IF;

    IF p_algorithm = 'N_QUEENS'
       AND (p_board_size IS NULL OR p_board_size NOT BETWEEN 1 AND 15) THEN
        RAISE EXCEPTION 'Invalid N-Queens board size';
    END IF;

    IF p_algorithm = 'COMBINATION'
       AND (
           p_selection_size IS NULL
           OR p_selection_size < 0
           OR p_selection_size > cardinality(p_values)
       ) THEN
        RAISE EXCEPTION 'Invalid combination size';
    END IF;

    INSERT INTO search_jobs(
        job_name,
        algorithm,
        input_values,
        selection_size,
        board_size,
        max_nodes,
        max_solutions
    )
    VALUES (
        p_name,
        p_algorithm,
        COALESCE(p_values, '{}'),
        p_selection_size,
        p_board_size,
        p_max_nodes,
        p_max_solutions
    )
    RETURNING job_id INTO new_job_id;

    CALL record_event(
        new_job_id,
        'JOB_CREATED',
        jsonb_build_object(
            'algorithm', p_algorithm,
            'input', COALESCE(p_values, '{}')
        )
    );

    RETURN new_job_id;
END;
$$;

-- ------------------------------------------------------------
-- 11. Search execution engine
--
-- This function supports all three algorithms.
-- The node tree is persisted for each visited search state.
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION execute_search(p_job_id BIGINT)
RETURNS search_status
LANGUAGE plpgsql
AS $$
DECLARE
    job_record search_jobs%ROWTYPE;

    node_counter BIGINT := 0;
    solution_counter BIGINT := 0;
    pruned_counter BIGINT := 0;

    root_id BIGINT;

    results INTEGER[][] := ARRAY[]::INTEGER[][];

    sorted_values INTEGER[];

    path INTEGER[] := '{}';

    used BOOLEAN[];

    n INTEGER;
    k INTEGER;

    columns_mask BIGINT := 0;
    descending_mask BIGINT := 0;
    ascending_mask BIGINT := 0;
    full_mask BIGINT;

    terminal_status search_status := 'COMPLETED';

    started TIMESTAMPTZ := clock_timestamp();

    -- Insert a node and preserve its parent-child relationship.
    FUNCTION add_node(
        p_parent BIGINT,
        p_depth INTEGER,
        p_values INTEGER[],
        p_status node_status,
        p_reason TEXT DEFAULT NULL
    )
    RETURNS BIGINT
    LANGUAGE plpgsql
    AS $inner$
    DECLARE
        new_node BIGINT;
    BEGIN
        node_counter := node_counter + 1;

        IF node_counter > job_record.max_nodes THEN
            RAISE EXCEPTION USING
                ERRCODE = 'P0001',
                MESSAGE = 'SEARCH_NODE_LIMIT';
        END IF;

        INSERT INTO search_nodes(
            job_id,
            parent_node_id,
            depth,
            state_values,
            status,
            rejection_reason
        )
        VALUES (
            p_job_id,
            p_parent,
            p_depth,
            p_values,
            p_status,
            p_reason
        )
        RETURNING node_id INTO new_node;

        RETURN new_node;
    END;
    $inner$;

    -- Persist a complete solution.
    PROCEDURE save_solution(
        p_terminal_node BIGINT,
        p_values INTEGER[]
    )
    LANGUAGE plpgsql
    AS $inner$
    BEGIN
        IF solution_counter >= job_record.max_solutions THEN
            RAISE EXCEPTION USING
                ERRCODE = 'P0001',
                MESSAGE = 'SEARCH_SOLUTION_LIMIT';
        END IF;

        solution_counter := solution_counter + 1;

        INSERT INTO search_solutions(
            job_id,
            terminal_node_id,
            solution_number,
            solution_values
        )
        VALUES (
            p_job_id,
            p_terminal_node,
            solution_counter,
            p_values
        );
    END;

    -- Recursive permutation search.
    PROCEDURE permutation_search(
        p_parent BIGINT,
        p_depth INTEGER
    )
    LANGUAGE plpgsql
    AS $inner$
    DECLARE
        i INTEGER;
        current_node BIGINT;
    BEGIN
        current_node := add_node(
            p_parent,
            p_depth,
            path,
            CASE
                WHEN p_depth = n THEN 'SOLUTION'::node_status
                ELSE 'EXPANDED'::node_status
            END
        );

        IF p_depth = n THEN
            CALL save_solution(current_node, path);
            RETURN;
        END IF;

        FOR i IN 1..n LOOP
            IF used[i] THEN
                CONTINUE;
            END IF;

            IF i > 1
               AND sorted_values[i] = sorted_values[i - 1]
               AND NOT used[i - 1] THEN

                pruned_counter := pruned_counter + 1;

                INSERT INTO candidate_decisions(
                    node_id,
                    candidate_value,
                    decision,
                    constraint_name,
                    explanation
                )
                VALUES (
                    current_node,
                    sorted_values[i],
                    'REJECTED',
                    'DUPLICATE_PERMUTATION',
                    'Equivalent unused predecessor exists'
                );

                CONTINUE;
            END IF;

            INSERT INTO candidate_decisions(
                node_id,
                candidate_value,
                decision,
                constraint_name
            )
            VALUES (
                current_node,
                sorted_values[i],
                'ACCEPTED',
                'UNUSED_POSITION'
            );

            used[i] := TRUE;
            path := array_append(path, sorted_values[i]);

            CALL permutation_search(current_node, p_depth + 1);

            path := path[1:cardinality(path) - 1];
            used[i] := FALSE;
        END LOOP;
    END;

    -- Recursive combination search.
    PROCEDURE combination_search(
        p_parent BIGINT,
        p_depth INTEGER,
        p_start INTEGER
    )
    LANGUAGE plpgsql
    AS $inner$
    DECLARE
        i INTEGER;
        last_index INTEGER;
        current_node BIGINT;
    BEGIN
        current_node := add_node(
            p_parent,
            p_depth,
            path,
            CASE
                WHEN p_depth = k THEN 'SOLUTION'::node_status
                ELSE 'EXPANDED'::node_status
            END
        );

        IF p_depth = k THEN
            CALL save_solution(current_node, path);
            RETURN;
        END IF;

        last_index := n - (k - p_depth) + 1;

        IF p_start > last_index THEN
            UPDATE search_nodes
            SET status = 'DEAD_END'
            WHERE node_id = current_node;

            RETURN;
        END IF;

        FOR i IN p_start..last_index LOOP
            IF i > p_start
               AND sorted_values[i] = sorted_values[i - 1] THEN
                pruned_counter := pruned_counter + 1;
                CONTINUE;
            END IF;

            path := array_append(path, sorted_values[i]);

            CALL combination_search(
                current_node,
                p_depth + 1,
                i + 1
            );

            path := path[1:cardinality(path) - 1];
        END LOOP;
    END;

    -- Recursive N-Queens search.
    PROCEDURE queens_search(
        p_parent BIGINT,
        p_row INTEGER
    )
    LANGUAGE plpgsql
    AS $inner$
    DECLARE
        col INTEGER;
        d1 INTEGER;
        d2 INTEGER;
        current_node BIGINT;
        bit_value BIGINT;
    BEGIN
        current_node := add_node(
            p_parent,
            p_row,
            path,
            CASE
                WHEN p_row = n THEN 'SOLUTION'::node_status
                ELSE 'EXPANDED'::node_status
            END
        );

        IF p_row = n THEN
            CALL save_solution(current_node, path);
            RETURN;
        END IF;

        FOR col IN 1..n LOOP
            d1 := p_row - col;
            d2 := p_row + col;

            bit_value := 1::BIGINT << (col - 1);

            IF (columns_mask & bit_value) <> 0
               OR (descending_mask & (1::BIGINT << (d1 + n - 1))) <> 0
               OR (ascending_mask & (1::BIGINT << d2)) <> 0 THEN

                pruned_counter := pruned_counter + 1;

                INSERT INTO candidate_decisions(
                    node_id,
                    candidate_value,
                    decision,
                    constraint_name,
                    explanation
                )
                VALUES (
                    current_node,
                    col,
                    'REJECTED',
                    'QUEEN_ATTACK_CONSTRAINT',
                    'Column or diagonal already occupied'
                );

                CONTINUE;
            END IF;

            INSERT INTO candidate_decisions(
                node_id,
                candidate_value,
                decision,
                constraint_name
            )
            VALUES (
                current_node,
                col,
                'ACCEPTED',
                'QUEEN_ATTACK_CONSTRAINT'
            );

            columns_mask := columns_mask | bit_value;

            descending_mask :=
                descending_mask |
                (1::BIGINT << (d1 + n - 1));

            ascending_mask :=
                ascending_mask |
                (1::BIGINT << d2);

            path := array_append(path, col);

            CALL queens_search(current_node, p_row + 1);

            path := path[1:cardinality(path) - 1];

            columns_mask :=
                columns_mask & ~bit_value;

            descending_mask :=
                descending_mask &
                ~(1::BIGINT << (d1 + n - 1));

            ascending_mask :=
                ascending_mask &
                ~(1::BIGINT << d2);
        END LOOP;
    END;

BEGIN
    SELECT *
    INTO job_record
    FROM search_jobs
    WHERE job_id = p_job_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Search job % does not exist', p_job_id;
    END IF;

    IF job_record.status <> 'CREATED' THEN
        RAISE EXCEPTION 'Only CREATED jobs can execute';
    END IF;

    UPDATE search_jobs
    SET status = 'RUNNING'
    WHERE job_id = p_job_id;

    CALL record_event(p_job_id, 'SEARCH_STARTED');

    n := cardinality(job_record.input_values);
    k := job_record.selection_size;

    IF job_record.algorithm = 'N_QUEENS' THEN
        n := job_record.board_size;
    END IF;

    sorted_values := COALESCE(
        (
            SELECT array_agg(value ORDER BY value)
            FROM unnest(job_record.input_values) AS value
        ),
        '{}'::INTEGER[]
    );

    IF job_record.algorithm = 'N_QUEENS' THEN
        root_id := add_node(
            NULL,
            0,
            '{}',
            'EXPANDED'
        );

        CALL queens_search(root_id, 0);

    ELSIF job_record.algorithm = 'PERMUTATION' THEN
        used := array_fill(FALSE, ARRAY[n]);

        root_id := add_node(
            NULL,
            0,
            '{}',
            'EXPANDED'
        );

        CALL permutation_search(root_id, 0);

    ELSIF job_record.algorithm = 'COMBINATION' THEN

        root_id := add_node(
            NULL,
            0,
            '{}',
            'EXPANDED'
        );

        CALL combination_search(root_id, 0, 1);
    END IF;

    UPDATE search_jobs
    SET status = 'COMPLETED',
        nodes_visited = node_counter,
        solutions_found = solution_counter,
        pruned_branches = pruned_counter
    WHERE job_id = p_job_id;

    CALL record_event(
        p_job_id,
        'SEARCH_COMPLETED',
        jsonb_build_object(
            'nodes', node_counter,
            'solutions', solution_counter,
            'pruned', pruned_counter,
            'elapsed_ms',
            EXTRACT(EPOCH FROM clock_timestamp() - started) * 1000
        )
    );

    RETURN 'COMPLETED';

EXCEPTION
    WHEN SQLSTATE 'P0001' THEN
        GET STACKED DIAGNOSTICS
            job_record.failure_reason = MESSAGE_TEXT;

        IF job_record.failure_reason IN (
            'SEARCH_NODE_LIMIT',
            'SEARCH_SOLUTION_LIMIT'
        ) THEN
            UPDATE search_jobs
            SET status = 'LIMIT_EXCEEDED',
                nodes_visited = node_counter,
                solutions_found = solution_counter,
                pruned_branches = pruned_counter,
                failure_reason = job_record.failure_reason
            WHERE job_id = p_job_id;

            CALL record_event(
                p_job_id,
                'SEARCH_LIMIT_EXCEEDED',
                jsonb_build_object(
                    'reason', job_record.failure_reason
                )
            );

            RETURN 'LIMIT_EXCEEDED';
        END IF;

        RAISE;

    WHEN OTHERS THEN
        UPDATE search_jobs
        SET status = 'FAILED',
            failure_reason = SQLERRM,
            nodes_visited = node_counter,
            solutions_found = solution_counter,
            pruned_branches = pruned_counter
        WHERE job_id = p_job_id
          AND status = 'RUNNING';

        RAISE;
END;
$$;

-- ------------------------------------------------------------
-- 12. Views for reporting
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW search_job_report AS
SELECT
    j.job_id,
    j.job_name,
    j.algorithm,
    j.status,
    j.nodes_visited,
    j.solutions_found,
    j.pruned_branches,
    CASE
        WHEN j.nodes_visited > 0
        THEN ROUND(
            j.pruned_branches::NUMERIC /
            j.nodes_visited,
            4
        )
        ELSE 0
    END AS pruning_ratio,
    j.created_at,
    j.started_at,
    j.completed_at,
    j.failure_reason
FROM search_jobs j;

CREATE OR REPLACE VIEW solution_summary AS
SELECT
    j.job_id,
    j.job_name,
    j.algorithm,
    COUNT(s.solution_id) AS solution_count
FROM search_jobs j
LEFT JOIN search_solutions s
    ON s.job_id = j.job_id
GROUP BY j.job_id, j.job_name, j.algorithm;

-- ------------------------------------------------------------
-- 13. Sample search jobs
-- ------------------------------------------------------------

INSERT INTO search_jobs(
    job_name,
    algorithm,
    input_values,
    max_nodes,
    max_solutions
)
VALUES (
    'Permutation Demonstration',
    'PERMUTATION',
    ARRAY[1, 2, 2],
    100000,
    1000
);

INSERT INTO search_jobs(
    job_name,
    algorithm,
    input_values,
    selection_size
)
VALUES (
    'Combination Demonstration',
    'COMBINATION',
    ARRAY[1, 2, 3, 4],
    2
);

INSERT INTO search_jobs(
    job_name,
    algorithm,
    board_size
)
VALUES (
    'N Queens Four',
    'N_QUEENS',
    4
);

INSERT INTO search_jobs(
    job_name,
    algorithm,
    board_size
)
VALUES (
    'N Queens Five',
    'N_QUEENS',
    5
);

-- ------------------------------------------------------------
-- 14. Execute the workflows transactionally
-- ------------------------------------------------------------

DO $$
DECLARE
    job RECORD;
    result_status search_status;
BEGIN
    FOR job IN
        SELECT job_id
        FROM search_jobs
        ORDER BY job_id
    LOOP
        result_status := execute_search(job.job_id);

        RAISE NOTICE
            'Job % finished with status %',
            job.job_id,
            result_status;
    END LOOP;
END;
$$;

-- ------------------------------------------------------------
-- 15. Retrieval
-- ------------------------------------------------------------

SELECT *
FROM search_job_report
ORDER BY job_id;

SELECT
    job_id,
    solution_number,
    solution_values
FROM search_solutions
ORDER BY job_id, solution_number;

-- ------------------------------------------------------------
-- 16. Aggregation
-- ------------------------------------------------------------

SELECT
    algorithm,
    COUNT(*) AS job_count,
    SUM(nodes_visited) AS total_nodes,
    SUM(solutions_found) AS total_solutions,
    SUM(pruned_branches) AS total_pruned_branches
FROM search_jobs
GROUP BY algorithm
ORDER BY algorithm;

-- ------------------------------------------------------------
-- 17. State-space tree inspection
-- ------------------------------------------------------------

SELECT
    n.node_id,
    n.parent_node_id,
    n.depth,
    n.state_values,
    n.status,
    n.rejection_reason
FROM search_nodes n
ORDER BY n.job_id, n.node_id
LIMIT 100;

-- ------------------------------------------------------------
-- 18. Constraint evaluation reporting
-- ------------------------------------------------------------

SELECT
    constraint_name,
    decision,
    COUNT(*) AS decision_count
FROM candidate_decisions
GROUP BY constraint_name, decision
ORDER BY constraint_name, decision;

-- ------------------------------------------------------------
-- 19. Solution eligibility validation
-- ------------------------------------------------------------

SELECT
    j.job_name,
    s.solution_number,
    s.solution_values,
    CASE
        WHEN j.algorithm = 'N_QUEENS'
             AND cardinality(s.solution_values) = j.board_size
             AND (
                 SELECT COUNT(DISTINCT value)
                 FROM unnest(s.solution_values) AS value
             ) = j.board_size
             AND (
                 SELECT COUNT(DISTINCT row_index - column_value)
                 FROM unnest(s.solution_values)
                     WITH ORDINALITY AS q(column_value, row_index)
             ) = j.board_size
             AND (
                 SELECT COUNT(DISTINCT row_index + column_value)
                 FROM unnest(s.solution_values)
                     WITH ORDINALITY AS q(column_value, row_index)
             ) = j.board_size
        THEN TRUE

        WHEN j.algorithm <> 'N_QUEENS'
        THEN TRUE

        ELSE FALSE
    END AS solution_valid
FROM search_solutions s
JOIN search_jobs j
    ON j.job_id = s.job_id
ORDER BY j.job_id, s.solution_number;

-- ------------------------------------------------------------
-- 20. Failed or restricted workflow retrieval
-- ------------------------------------------------------------

SELECT
    job_id,
    job_name,
    status,
    failure_reason
FROM search_jobs
WHERE status IN ('FAILED', 'LIMIT_EXCEEDED');

-- ------------------------------------------------------------
-- 21. Search execution audit
-- ------------------------------------------------------------

SELECT
    event_id,
    job_id,
    event_type,
    event_details,
    recorded_at
FROM search_events
ORDER BY event_id;

COMMIT;
