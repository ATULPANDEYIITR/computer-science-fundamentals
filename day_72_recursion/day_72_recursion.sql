-- ============================================================
-- RECURSION: RECURSIVE THINKING, BASE CASES, AND RECURSIVE SQL
-- PostgreSQL 14+
--
-- Demonstrates:
-- 1. Recursive mathematical functions
-- 2. Recursive CTEs
-- 3. Hierarchical data traversal
-- 4. Recursive dependency resolution
-- 5. Cycle detection
-- 6. Tree depth and path computation
-- 7. Recursive aggregation
-- 8. Memoization through relational result storage
-- 9. Input validation
-- 10. Transaction handling and reporting
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS recursion_lab;

SET search_path TO recursion_lab, public;

-- ============================================================
-- 1. DOMAIN TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS organizations (
    organization_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_name VARCHAR(150) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS employees (
    employee_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),
    manager_id BIGINT,
    employee_name VARCHAR(120) NOT NULL,
    job_title VARCHAR(120) NOT NULL,
    salary NUMERIC(14, 2) NOT NULL CHECK (salary >= 0),
    CONSTRAINT employee_manager_fk
        FOREIGN KEY (manager_id)
        REFERENCES employees(employee_id)
        DEFERRABLE INITIALLY IMMEDIATE,
    CONSTRAINT employee_not_self_managed
        CHECK (manager_id IS DISTINCT FROM employee_id),
    UNIQUE (organization_id, employee_id)
);

CREATE INDEX IF NOT EXISTS idx_employees_manager
    ON employees(manager_id);

CREATE INDEX IF NOT EXISTS idx_employees_organization
    ON employees(organization_id);

CREATE TABLE IF NOT EXISTS projects (
    project_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_name VARCHAR(150) NOT NULL UNIQUE,
    project_status VARCHAR(20) NOT NULL DEFAULT 'PLANNED'
        CHECK (
            project_status IN (
                'PLANNED',
                'ACTIVE',
                'COMPLETED',
                'BLOCKED'
            )
        )
);

CREATE TABLE IF NOT EXISTS tasks (
    task_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL
        REFERENCES projects(project_id),
    parent_task_id BIGINT,
    assigned_employee_id BIGINT
        REFERENCES employees(employee_id),
    task_name VARCHAR(180) NOT NULL,
    task_status VARCHAR(20) NOT NULL DEFAULT 'PENDING'
        CHECK (
            task_status IN (
                'PENDING',
                'IN_PROGRESS',
                'COMPLETED',
                'BLOCKED'
            )
        ),
    estimated_hours NUMERIC(10, 2) NOT NULL DEFAULT 0
        CHECK (estimated_hours >= 0),
    CONSTRAINT task_parent_fk
        FOREIGN KEY (parent_task_id)
        REFERENCES tasks(task_id)
        DEFERRABLE INITIALLY IMMEDIATE,
    CONSTRAINT task_not_own_parent
        CHECK (parent_task_id IS DISTINCT FROM task_id),
    UNIQUE (project_id, task_id)
);

CREATE INDEX IF NOT EXISTS idx_tasks_parent
    ON tasks(parent_task_id);

CREATE INDEX IF NOT EXISTS idx_tasks_project_status
    ON tasks(project_id, task_status);

CREATE INDEX IF NOT EXISTS idx_tasks_assignee
    ON tasks(assigned_employee_id);

CREATE TABLE IF NOT EXISTS task_dependencies (
    task_id BIGINT NOT NULL REFERENCES tasks(task_id),
    depends_on_task_id BIGINT NOT NULL REFERENCES tasks(task_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (task_id, depends_on_task_id),
    CHECK (task_id <> depends_on_task_id)
);

CREATE INDEX IF NOT EXISTS idx_task_dependencies_reverse
    ON task_dependencies(depends_on_task_id);

-- ============================================================
-- 2. RECURSION RESULT CACHE
-- ============================================================

CREATE TABLE IF NOT EXISTS fibonacci_cache (
    n INTEGER PRIMARY KEY CHECK (n >= 0),
    result NUMERIC(1000, 0) NOT NULL CHECK (result >= 0),
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 3. MATHEMATICAL RECURSION
-- ============================================================

CREATE OR REPLACE FUNCTION recursive_factorial(p_n INTEGER)
RETURNS NUMERIC
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
BEGIN
    IF p_n < 0 THEN
        RAISE EXCEPTION
            'Factorial input cannot be negative: %', p_n;
    END IF;

    IF p_n > 500 THEN
        RAISE EXCEPTION
            'Factorial input exceeds configured limit: %', p_n;
    END IF;

    -- Base case: 0! = 1 and 1! = 1.
    IF p_n <= 1 THEN
        RETURN 1;
    END IF;

    -- Recursive case reduces the input by one.
    RETURN p_n * recursive_factorial(p_n - 1);
END;
$$;

CREATE OR REPLACE FUNCTION recursive_fibonacci(p_n INTEGER)
RETURNS NUMERIC
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
BEGIN
    IF p_n < 0 THEN
        RAISE EXCEPTION
            'Fibonacci input cannot be negative.';
    END IF;

    IF p_n > 40 THEN
        RAISE EXCEPTION
            'Naive recursive Fibonacci is restricted to n <= 40.';
    END IF;

    -- Base cases.
    IF p_n = 0 THEN
        RETURN 0;
    END IF;

    IF p_n = 1 THEN
        RETURN 1;
    END IF;

    RETURN recursive_fibonacci(p_n - 1)
         + recursive_fibonacci(p_n - 2);
END;
$$;

-- ============================================================
-- 4. MEMOIZED FIBONACCI
-- ============================================================

CREATE OR REPLACE FUNCTION memoized_fibonacci(p_n INTEGER)
RETURNS NUMERIC
LANGUAGE plpgsql
VOLATILE
AS $$
DECLARE
    v_result NUMERIC;
BEGIN
    IF p_n < 0 OR p_n > 10000 THEN
        RAISE EXCEPTION
            'Memoized Fibonacci input must be between 0 and 10000.';
    END IF;

    -- Base cases are stored for reuse.
    INSERT INTO fibonacci_cache(n, result)
    VALUES (0, 0), (1, 1)
    ON CONFLICT (n) DO NOTHING;

    -- Check persistent cache.
    SELECT result
    INTO v_result
    FROM fibonacci_cache
    WHERE n = p_n;

    IF FOUND THEN
        RETURN v_result;
    END IF;

    -- Recursive subproblems are solved once and persisted.
    v_result :=
        memoized_fibonacci(p_n - 1)
        + memoized_fibonacci(p_n - 2);

    INSERT INTO fibonacci_cache(n, result)
    VALUES (p_n, v_result)
    ON CONFLICT (n)
    DO UPDATE SET result = EXCLUDED.result;

    RETURN v_result;
END;
$$;

-- ============================================================
-- 5. RECURSIVE HIERARCHY INTEGRITY
-- ============================================================

CREATE OR REPLACE FUNCTION prevent_employee_management_cycle()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_cycle BOOLEAN;
BEGIN
    IF NEW.manager_id IS NULL THEN
        RETURN NEW;
    END IF;

    IF NEW.manager_id = NEW.employee_id THEN
        RAISE EXCEPTION
            'An employee cannot manage themselves.';
    END IF;

    -- Walk upward through the manager hierarchy.
    WITH RECURSIVE management_chain(employee_id, manager_id, path) AS (
        SELECT
            e.employee_id,
            e.manager_id,
            ARRAY[e.employee_id]
        FROM employees e
        WHERE e.employee_id = NEW.manager_id

        UNION ALL

        SELECT
            e.employee_id,
            e.manager_id,
            mc.path || e.employee_id
        FROM employees e
        JOIN management_chain mc
            ON e.employee_id = mc.manager_id
        WHERE NOT e.employee_id = ANY(mc.path)
    )
    SELECT EXISTS (
        SELECT 1
        FROM management_chain
        WHERE employee_id = NEW.employee_id
    )
    INTO v_cycle;

    IF v_cycle THEN
        RAISE EXCEPTION
            'Management cycle detected for employee %.',
            NEW.employee_id;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_employee_cycle
    ON employees;

CREATE TRIGGER trg_employee_cycle
BEFORE INSERT OR UPDATE OF manager_id
ON employees
FOR EACH ROW
EXECUTE FUNCTION prevent_employee_management_cycle();

-- ============================================================
-- 6. TASK HIERARCHY CYCLE PREVENTION
-- ============================================================

CREATE OR REPLACE FUNCTION prevent_task_hierarchy_cycle()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_cycle BOOLEAN;
BEGIN
    IF NEW.parent_task_id IS NULL THEN
        RETURN NEW;
    END IF;

    WITH RECURSIVE ancestors(task_id, parent_task_id, path) AS (
        SELECT
            t.task_id,
            t.parent_task_id,
            ARRAY[t.task_id]
        FROM tasks t
        WHERE t.task_id = NEW.parent_task_id

        UNION ALL

        SELECT
            t.task_id,
            t.parent_task_id,
            a.path || t.task_id
        FROM tasks t
        JOIN ancestors a
            ON t.task_id = a.parent_task_id
        WHERE NOT t.task_id = ANY(a.path)
    )
    SELECT EXISTS (
        SELECT 1
        FROM ancestors
        WHERE task_id = NEW.task_id
    )
    INTO v_cycle;

    IF v_cycle THEN
        RAISE EXCEPTION
            'Task hierarchy cycle detected.';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_task_hierarchy_cycle
    ON tasks;

CREATE TRIGGER trg_task_hierarchy_cycle
BEFORE INSERT OR UPDATE OF parent_task_id
ON tasks
FOR EACH ROW
EXECUTE FUNCTION prevent_task_hierarchy_cycle();

-- ============================================================
-- 7. DEPENDENCY CYCLE PREVENTION
-- ============================================================

CREATE OR REPLACE FUNCTION prevent_dependency_cycle()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_cycle BOOLEAN;
BEGIN
    IF NEW.task_id = NEW.depends_on_task_id THEN
        RAISE EXCEPTION
            'A task cannot depend on itself.';
    END IF;

    -- Adding A -> B creates a cycle if B already reaches A.
    WITH RECURSIVE reachable(task_id, path) AS (
        SELECT
            NEW.depends_on_task_id,
            ARRAY[NEW.depends_on_task_id]

        UNION ALL

        SELECT
            d.depends_on_task_id,
            r.path || d.depends_on_task_id
        FROM task_dependencies d
        JOIN reachable r
            ON d.task_id = r.task_id
        WHERE NOT d.depends_on_task_id = ANY(r.path)
    )
    SELECT EXISTS (
        SELECT 1
        FROM reachable
        WHERE task_id = NEW.task_id
    )
    INTO v_cycle;

    IF v_cycle THEN
        RAISE EXCEPTION
            'Task dependency cycle detected.';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_dependency_cycle
    ON task_dependencies;

CREATE TRIGGER trg_dependency_cycle
BEFORE INSERT OR UPDATE
ON task_dependencies
FOR EACH ROW
EXECUTE FUNCTION prevent_dependency_cycle();

-- ============================================================
-- 8. RECURSIVE ORGANIZATION REPORTING
-- ============================================================

CREATE OR REPLACE VIEW employee_hierarchy AS
WITH RECURSIVE hierarchy AS (
    SELECT
        employee_id,
        manager_id,
        organization_id,
        employee_name,
        job_title,
        salary,
        0 AS hierarchy_level,
        ARRAY[employee_id] AS employee_path
    FROM employees
    WHERE manager_id IS NULL

    UNION ALL

    SELECT
        e.employee_id,
        e.manager_id,
        e.organization_id,
        e.employee_name,
        e.job_title,
        e.salary,
        h.hierarchy_level + 1,
        h.employee_path || e.employee_id
    FROM employees e
    JOIN hierarchy h
        ON e.manager_id = h.employee_id
    WHERE NOT e.employee_id = ANY(h.employee_path)
)
SELECT *
FROM hierarchy;

-- ============================================================
-- 9. RECURSIVE TASK REPORTING
-- ============================================================

CREATE OR REPLACE VIEW task_hierarchy AS
WITH RECURSIVE hierarchy AS (
    SELECT
        task_id,
        project_id,
        parent_task_id,
        task_name,
        task_status,
        estimated_hours,
        0 AS hierarchy_level,
        ARRAY[task_id] AS task_path
    FROM tasks
    WHERE parent_task_id IS NULL

    UNION ALL

    SELECT
        t.task_id,
        t.project_id,
        t.parent_task_id,
        t.task_name,
        t.task_status,
        t.estimated_hours,
        h.hierarchy_level + 1,
        h.task_path || t.task_id
    FROM tasks t
    JOIN hierarchy h
        ON t.parent_task_id = h.task_id
    WHERE NOT t.task_id = ANY(h.task_path)
)
SELECT *
FROM hierarchy;

-- ============================================================
-- 10. DEPENDENCY EXECUTION ORDER
-- ============================================================

CREATE OR REPLACE FUNCTION get_task_execution_order()
RETURNS TABLE (
    task_id BIGINT,
    execution_level INTEGER,
    task_name VARCHAR,
    task_status VARCHAR
)
LANGUAGE sql
STABLE
AS $$
    WITH RECURSIVE dependency_levels AS (
        SELECT
            t.task_id,
            t.task_name,
            t.task_status,
            0 AS execution_level,
            ARRAY[t.task_id] AS path
        FROM tasks t
        WHERE NOT EXISTS (
            SELECT 1
            FROM task_dependencies d
            WHERE d.task_id = t.task_id
        )

        UNION ALL

        SELECT
            t.task_id,
            t.task_name,
            t.task_status,
            dl.execution_level + 1,
            dl.path || t.task_id
        FROM dependency_levels dl
        JOIN task_dependencies d
            ON d.depends_on_task_id = dl.task_id
        JOIN tasks t
            ON t.task_id = d.task_id
        WHERE NOT t.task_id = ANY(dl.path)
    ),
    maximum_levels AS (
        SELECT
            task_id,
            MAX(execution_level) AS execution_level
        FROM dependency_levels
        GROUP BY task_id
    )
    SELECT
        t.task_id,
        ml.execution_level,
        t.task_name,
        t.task_status
    FROM maximum_levels ml
    JOIN tasks t USING (task_id)
    ORDER BY ml.execution_level, t.task_id;
$$;

-- ============================================================
-- 11. RECURSIVE PROJECT COST AGGREGATION
-- ============================================================

CREATE OR REPLACE VIEW project_recursive_effort AS
WITH RECURSIVE descendants AS (
    SELECT
        task_id,
        project_id,
        parent_task_id,
        estimated_hours,
        ARRAY[task_id] AS path
    FROM tasks
    WHERE parent_task_id IS NULL

    UNION ALL

    SELECT
        child.task_id,
        child.project_id,
        child.parent_task_id,
        child.estimated_hours,
        parent.path || child.task_id
    FROM tasks child
    JOIN descendants parent
        ON child.parent_task_id = parent.task_id
    WHERE NOT child.task_id = ANY(parent.path)
)
SELECT
    p.project_id,
    p.project_name,
    COUNT(d.task_id) AS task_count,
    COALESCE(SUM(d.estimated_hours), 0) AS total_estimated_hours
FROM projects p
LEFT JOIN descendants d
    ON d.project_id = p.project_id
GROUP BY p.project_id, p.project_name;

-- ============================================================
-- 12. SAMPLE ORGANIZATIONAL DATA
-- ============================================================

INSERT INTO organizations(organization_name)
VALUES ('Technology Research Division')
ON CONFLICT (organization_name) DO NOTHING;

INSERT INTO employees(
    organization_id,
    manager_id,
    employee_name,
    job_title,
    salary
)
SELECT
    o.organization_id,
    NULL,
    'Aarav Sharma',
    'Engineering Director',
    180000
FROM organizations o
WHERE o.organization_name = 'Technology Research Division'
AND NOT EXISTS (
    SELECT 1
    FROM employees e
    WHERE e.employee_name = 'Aarav Sharma'
);

INSERT INTO employees(
    organization_id,
    manager_id,
    employee_name,
    job_title,
    salary
)
SELECT
    manager.organization_id,
    manager.employee_id,
    'Meera Singh',
    'Engineering Manager',
    125000
FROM employees manager
WHERE manager.employee_name = 'Aarav Sharma'
AND NOT EXISTS (
    SELECT 1
    FROM employees e
    WHERE e.employee_name = 'Meera Singh'
);

INSERT INTO employees(
    organization_id,
    manager_id,
    employee_name,
    job_title,
    salary
)
SELECT
    manager.organization_id,
    manager.employee_id,
    'Rohan Verma',
    'Senior Developer',
    95000
FROM employees manager
WHERE manager.employee_name = 'Meera Singh'
AND NOT EXISTS (
    SELECT 1
    FROM employees e
    WHERE e.employee_name = 'Rohan Verma'
);

INSERT INTO employees(
    organization_id,
    manager_id,
    employee_name,
    job_title,
    salary
)
SELECT
    manager.organization_id,
    manager.employee_id,
    'Ananya Gupta',
    'Database Engineer',
    90000
FROM employees manager
WHERE manager.employee_name = 'Meera Singh'
AND NOT EXISTS (
    SELECT 1
    FROM employees e
    WHERE e.employee_name = 'Ananya Gupta'
);

-- ============================================================
-- 13. SAMPLE PROJECTS AND TASKS
-- ============================================================

INSERT INTO projects(project_name, project_status)
VALUES
    ('Recursive Analytics Platform', 'ACTIVE'),
    ('Dependency Processing Engine', 'PLANNED')
ON CONFLICT (project_name) DO NOTHING;

INSERT INTO tasks(
    project_id,
    parent_task_id,
    task_name,
    task_status,
    estimated_hours,
    assigned_employee_id
)
SELECT
    p.project_id,
    NULL,
    'Platform Development',
    'IN_PROGRESS',
    40,
    e.employee_id
FROM projects p
JOIN employees e
    ON e.employee_name = 'Meera Singh'
WHERE p.project_name = 'Recursive Analytics Platform'
AND NOT EXISTS (
    SELECT 1
    FROM tasks t
    WHERE t.task_name = 'Platform Development'
);

INSERT INTO tasks(
    project_id,
    parent_task_id,
    task_name,
    task_status,
    estimated_hours,
    assigned_employee_id
)
SELECT
    p.project_id,
    parent.task_id,
    'Recursive Algorithm Module',
    'IN_PROGRESS',
    16,
    e.employee_id
FROM projects p
JOIN tasks parent
    ON parent.task_name = 'Platform Development'
JOIN employees e
    ON e.employee_name = 'Rohan Verma'
WHERE p.project_name = 'Recursive Analytics Platform'
AND NOT EXISTS (
    SELECT 1
    FROM tasks t
    WHERE t.task_name = 'Recursive Algorithm Module'
);

INSERT INTO tasks(
    project_id,
    parent_task_id,
    task_name,
    task_status,
    estimated_hours,
    assigned_employee_id
)
SELECT
    p.project_id,
    parent.task_id,
    'Base Case Validation',
    'COMPLETED',
    5,
    e.employee_id
FROM projects p
JOIN tasks parent
    ON parent.task_name = 'Recursive Algorithm Module'
JOIN employees e
    ON e.employee_name = 'Ananya Gupta'
WHERE p.project_name = 'Recursive Analytics Platform'
AND NOT EXISTS (
    SELECT 1
    FROM tasks t
    WHERE t.task_name = 'Base Case Validation'
);

INSERT INTO tasks(
    project_id,
    parent_task_id,
    task_name,
    task_status,
    estimated_hours,
    assigned_employee_id
)
SELECT
    p.project_id,
    parent.task_id,
    'Performance Testing',
    'PENDING',
    8,
    e.employee_id
FROM projects p
JOIN tasks parent
    ON parent.task_name = 'Recursive Algorithm Module'
JOIN employees e
    ON e.employee_name = 'Rohan Verma'
WHERE p.project_name = 'Recursive Analytics Platform'
AND NOT EXISTS (
    SELECT 1
    FROM tasks t
    WHERE t.task_name = 'Performance Testing'
);

-- Independent dependency-processing project.
INSERT INTO tasks(
    project_id,
    parent_task_id,
    task_name,
    task_status,
    estimated_hours
)
SELECT
    project_id,
    NULL,
    'Compile Source',
    'COMPLETED',
    4
FROM projects
WHERE project_name = 'Dependency Processing Engine'
AND NOT EXISTS (
    SELECT 1 FROM tasks WHERE task_name = 'Compile Source'
);

INSERT INTO tasks(
    project_id,
    parent_task_id,
    task_name,
    task_status,
    estimated_hours
)
SELECT
    project_id,
    NULL,
    'Run Unit Tests',
    'PENDING',
    6
FROM projects
WHERE project_name = 'Dependency Processing Engine'
AND NOT EXISTS (
    SELECT 1 FROM tasks WHERE task_name = 'Run Unit Tests'
);

INSERT INTO tasks(
    project_id,
    parent_task_id,
    task_name,
    task_status,
    estimated_hours
)
SELECT
    project_id,
    NULL,
    'Deploy Application',
    'PENDING',
    3
FROM projects
WHERE project_name = 'Dependency Processing Engine'
AND NOT EXISTS (
    SELECT 1 FROM tasks WHERE task_name = 'Deploy Application'
);

INSERT INTO task_dependencies(task_id, depends_on_task_id)
SELECT
    child.task_id,
    parent.task_id
FROM tasks child
JOIN tasks parent
    ON (
        child.task_name = 'Run Unit Tests'
        AND parent.task_name = 'Compile Source'
    )
    OR (
        child.task_name = 'Deploy Application'
        AND parent.task_name = 'Run Unit Tests'
    )
ON CONFLICT DO NOTHING;

-- ============================================================
-- 14. RECURSIVE FUNCTION EXECUTION
-- ============================================================

SELECT recursive_factorial(5) AS factorial_5;

SELECT recursive_fibonacci(10) AS fibonacci_10;

SELECT memoized_fibonacci(100) AS memoized_fibonacci_100;

-- ============================================================
-- 15. RECURSIVE CACHE REPORT
-- ============================================================

SELECT
    n,
    result,
    calculated_at
FROM fibonacci_cache
ORDER BY n
LIMIT 20;

-- ============================================================
-- 16. ORGANIZATIONAL HIERARCHY REPORT
-- ============================================================

SELECT
    employee_id,
    employee_name,
    job_title,
    manager_id,
    hierarchy_level,
    employee_path
FROM employee_hierarchy
ORDER BY employee_path;

-- ============================================================
-- 17. TASK TREE REPORT
-- ============================================================

SELECT
    task_id,
    task_name,
    task_status,
    hierarchy_level,
    task_path,
    estimated_hours
FROM task_hierarchy
ORDER BY project_id, task_path;

-- ============================================================
-- 18. RECURSIVE DEPENDENCY EVALUATION
-- ============================================================

SELECT *
FROM get_task_execution_order();

-- ============================================================
-- 19. PROJECT EFFORT AGGREGATION
-- ============================================================

SELECT
    project_name,
    task_count,
    total_estimated_hours
FROM project_recursive_effort
ORDER BY project_name;

-- ============================================================
-- 20. COMPLETION AND VALIDATION REPORT
-- ============================================================

SELECT
    p.project_name,
    COUNT(t.task_id) AS total_tasks,
    COUNT(*) FILTER (
        WHERE t.task_status = 'COMPLETED'
    ) AS completed_tasks,
    COUNT(*) FILTER (
        WHERE t.task_status = 'BLOCKED'
    ) AS blocked_tasks,
    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE t.task_status = 'COMPLETED'
        ) / NULLIF(COUNT(t.task_id), 0),
        2
    ) AS completion_percentage
FROM projects p
LEFT JOIN tasks t
    ON t.project_id = p.project_id
GROUP BY p.project_id, p.project_name
ORDER BY p.project_name;

-- ============================================================
-- 21. VALIDATION QUERIES
-- ============================================================

-- Detect tasks with missing parent references.
SELECT
    t.task_id,
    t.task_name
FROM tasks t
LEFT JOIN tasks parent
    ON parent.task_id = t.parent_task_id
WHERE t.parent_task_id IS NOT NULL
AND parent.task_id IS NULL;

-- Detect unresolved dependencies.
SELECT
    t.task_id,
    t.task_name,
    dependency.task_name AS prerequisite,
    dependency.task_status AS prerequisite_status
FROM task_dependencies d
JOIN tasks t
    ON t.task_id = d.task_id
JOIN tasks dependency
    ON dependency.task_id = d.depends_on_task_id
WHERE dependency.task_status <> 'COMPLETED';

-- Find hierarchy leaves.
SELECT
    t.task_id,
    t.task_name
FROM tasks t
WHERE NOT EXISTS (
    SELECT 1
    FROM tasks child
    WHERE child.parent_task_id = t.task_id
);

-- ============================================================
-- 22. TRANSACTIONAL DEPENDENCY PROCESSING
-- ============================================================

-- Demonstrate safe status processing.
-- A task can be marked complete only after its prerequisites
-- are complete. FOR UPDATE protects the selected task row.

CREATE OR REPLACE PROCEDURE complete_task(p_task_id BIGINT)
LANGUAGE plpgsql
AS $$
DECLARE
    v_status VARCHAR(20);
    v_unfinished BIGINT;
BEGIN
    SELECT task_status
    INTO v_status
    FROM tasks
    WHERE task_id = p_task_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Task % does not exist.', p_task_id;
    END IF;

    IF v_status = 'COMPLETED' THEN
        RAISE NOTICE 'Task % is already completed.', p_task_id;
        RETURN;
    END IF;

    IF v_status = 'BLOCKED' THEN
        RAISE EXCEPTION
            'Blocked task % cannot be completed.', p_task_id;
    END IF;

    SELECT COUNT(*)
    INTO v_unfinished
    FROM task_dependencies d
    JOIN tasks prerequisite
        ON prerequisite.task_id = d.depends_on_task_id
    WHERE d.task_id = p_task_id
      AND prerequisite.task_status <> 'COMPLETED';

    IF v_unfinished > 0 THEN
        RAISE EXCEPTION
            'Task % has % unfinished dependencies.',
            p_task_id,
            v_unfinished;
    END IF;

    UPDATE tasks
    SET task_status = 'COMPLETED'
    WHERE task_id = p_task_id;
END;
$$;

-- Example successful operation:
-- CALL complete_task(<task_id_of_an_eligible_task>);

-- Example invalid operation:
-- CALL complete_task(<task_id_with_unfinished_dependencies>);

-- ============================================================
-- 23. TRANSACTIONAL SAFETY DEMONSTRATION
-- ============================================================

SAVEPOINT recursion_demo;

-- This transaction is intentionally rolled back.
-- It demonstrates how invalid operational changes can be
-- isolated without retaining the test mutation.

UPDATE tasks
SET task_status = 'IN_PROGRESS'
WHERE task_name = 'Performance Testing'
AND task_status = 'PENDING';

ROLLBACK TO SAVEPOINT recursion_demo;

RELEASE SAVEPOINT recursion_demo;

-- ============================================================
-- 24. EXECUTION COMPLEXITY REFERENCE
-- ============================================================

CREATE OR REPLACE VIEW recursion_complexity_reference AS
SELECT *
FROM (
    VALUES
        (
            'Factorial',
            'O(n)',
            'O(n)',
            'One recursive call per level'
        ),
        (
            'Naive Fibonacci',
            'O(2^n)',
            'O(n)',
            'Overlapping subproblems'
        ),
        (
            'Memoized Fibonacci',
            'O(n)',
            'O(n)',
            'Persistent or in-memory caching'
        ),
        (
            'Binary Search',
            'O(log n)',
            'O(log n)',
            'Half the search interval per call'
        ),
        (
            'Merge Sort',
            'O(n log n)',
            'O(n)',
            'Divide and combine'
        ),
        (
            'Tree Traversal',
            'O(V)',
            'O(h)',
            'Visit each node once'
        ),
        (
            'Dependency Resolution',
            'O(V + E)',
            'O(V)',
            'Depth-first graph traversal'
        )
) AS complexity(
    algorithm,
    time_complexity,
    auxiliary_space,
    explanation
);

SELECT * FROM recursion_complexity_reference;

-- ============================================================
-- 25. FINAL DATABASE COUNTS
-- ============================================================

SELECT
    (SELECT COUNT(*) FROM organizations) AS organizations,
    (SELECT COUNT(*) FROM employees) AS employees,
    (SELECT COUNT(*) FROM projects) AS projects,
    (SELECT COUNT(*) FROM tasks) AS tasks,
    (SELECT COUNT(*) FROM task_dependencies) AS dependencies,
    (SELECT COUNT(*) FROM fibonacci_cache) AS cached_results;

COMMIT;
