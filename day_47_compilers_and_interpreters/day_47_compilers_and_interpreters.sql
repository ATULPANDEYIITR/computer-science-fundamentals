-- PostgreSQL 15+
-- Relational model for a small expression compiler and bytecode runtime.
-- The schema records source programs, compiler versions, emitted instructions,
-- runtime contexts, and execution outcomes.
--
-- A program's source is immutable after compilation in this demonstration.
-- Separate compilation records preserve reproducibility across compiler versions.

BEGIN;

CREATE SCHEMA IF NOT EXISTS runtime_lab;
SET search_path TO runtime_lab, public;

CREATE TABLE compiler_versions (
    compiler_version_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    version_label TEXT NOT NULL UNIQUE,
    language_name TEXT NOT NULL,
    target_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (length(trim(version_label)) > 0),
    CHECK (length(trim(language_name)) > 0),
    CHECK (length(trim(target_name)) > 0)
);

CREATE TABLE source_programs (
    program_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    program_name TEXT NOT NULL,
    source_text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    owner_name TEXT NOT NULL,
    UNIQUE (program_name, owner_name),
    CHECK (length(trim(program_name)) > 0),
    CHECK (length(trim(owner_name)) > 0),
    CHECK (length(source_text) > 0)
);

CREATE TABLE compilations (
    compilation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    program_id BIGINT NOT NULL REFERENCES source_programs(program_id),
    compiler_version_id BIGINT NOT NULL
        REFERENCES compiler_versions(compiler_version_id),
    compilation_status TEXT NOT NULL
        CHECK (compilation_status IN ('SUCCEEDED', 'FAILED')),
    diagnostic TEXT,
    bytecode_hash TEXT,
    compiled_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (program_id, compiler_version_id, compiled_at),
    CHECK (
        (compilation_status = 'SUCCEEDED'
            AND bytecode_hash IS NOT NULL
            AND diagnostic IS NULL)
        OR
        (compilation_status = 'FAILED'
            AND bytecode_hash IS NULL
            AND diagnostic IS NOT NULL)
    )
);

CREATE TABLE bytecode_instructions (
    compilation_id BIGINT NOT NULL
        REFERENCES compilations(compilation_id) ON DELETE CASCADE,
    instruction_index INTEGER NOT NULL CHECK (instruction_index >= 0),
    opcode TEXT NOT NULL CHECK (
        opcode IN (
            'CONSTANT', 'LOAD', 'STORE', 'ADD', 'SUBTRACT',
            'MULTIPLY', 'DIVIDE', 'LESS', 'LESS_EQUAL',
            'EQUAL', 'JUMP', 'JUMP_IF_FALSE', 'PRINT', 'HALT'
        )
    ),
    operand JSONB,
    PRIMARY KEY (compilation_id, instruction_index)
);

CREATE TABLE runtime_contexts (
    context_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    context_name TEXT NOT NULL,
    context_values JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (jsonb_typeof(context_values) = 'object'),
    CHECK (length(trim(context_name)) > 0)
);

CREATE TABLE executions (
    execution_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    compilation_id BIGINT NOT NULL
        REFERENCES compilations(compilation_id),
    context_id BIGINT REFERENCES runtime_contexts(context_id),
    execution_status TEXT NOT NULL
        CHECK (
            execution_status IN (
                'SUCCEEDED', 'RUNTIME_ERROR', 'BUDGET_EXCEEDED'
            )
        ),
    result JSONB,
    error_message TEXT,
    instructions_executed INTEGER NOT NULL DEFAULT 0
        CHECK (instructions_executed >= 0),
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMPTZ,
    CHECK (
        (execution_status = 'SUCCEEDED' AND error_message IS NULL)
        OR
        (execution_status <> 'SUCCEEDED' AND error_message IS NOT NULL)
    ),
    CHECK (
        finished_at IS NULL OR finished_at >= started_at
    )
);

CREATE INDEX idx_compilations_program_time
    ON compilations (program_id, compiled_at DESC);

CREATE INDEX idx_executions_status_time
    ON executions (execution_status, started_at DESC);

CREATE INDEX idx_runtime_context_values
    ON runtime_contexts USING GIN (context_values);

CREATE INDEX idx_instructions_opcode
    ON bytecode_instructions (opcode, compilation_id);

-- Successful bytecode must terminate in HALT and use contiguous instruction
-- positions. A deferred trigger checks the completed instruction sequence
-- when the transaction commits, so multi-row inserts remain practical.

CREATE FUNCTION validate_successful_bytecode()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    instruction_count BIGINT;
    minimum_index INTEGER;
    maximum_index INTEGER;
    final_opcode TEXT;
BEGIN
    IF NEW.compilation_status <> 'SUCCEEDED' THEN
        RETURN NEW;
    END IF;

    SELECT
        count(*),
        min(instruction_index),
        max(instruction_index)
    INTO instruction_count, minimum_index, maximum_index
    FROM bytecode_instructions
    WHERE compilation_id = NEW.compilation_id;

    IF instruction_count = 0 THEN
        RAISE EXCEPTION
            'Successful compilation % has no bytecode',
            NEW.compilation_id;
    END IF;

    IF minimum_index <> 0 OR maximum_index <> instruction_count - 1 THEN
        RAISE EXCEPTION
            'Bytecode indices must be contiguous from zero';
    END IF;

    SELECT opcode INTO final_opcode
    FROM bytecode_instructions
    WHERE compilation_id = NEW.compilation_id
      AND instruction_index = maximum_index;

    IF final_opcode <> 'HALT' THEN
        RAISE EXCEPTION
            'Bytecode must end with HALT, found %',
            final_opcode;
    END IF;

    RETURN NEW;
END;
$$;

CREATE CONSTRAINT TRIGGER trg_validate_successful_bytecode
AFTER INSERT OR UPDATE ON compilations
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION validate_successful_bytecode();

INSERT INTO compiler_versions (
    version_label, language_name, target_name
)
VALUES
    ('1.0.0', 'PolicyExpr', 'STACK_VM'),
    ('1.1.0', 'PolicyExpr', 'STACK_VM');

INSERT INTO source_programs (
    program_name, source_text, owner_name
)
VALUES
    (
        'deployment-risk-policy',
        'let risk = failed_checks * 2 + critical_findings * 10; print risk;',
        'release-engineering'
    ),
    (
        'deployment-window-policy',
        'print deployment_window_hours >= 2;',
        'release-engineering'
    ),
    (
        'malformed-expression',
        'let risk = failed_checks * ;',
        'compiler-validation'
    );

-- Compilation records are inserted before instructions so foreign keys
-- establish an auditable relationship between source and generated bytecode.
INSERT INTO compilations (
    program_id, compiler_version_id, compilation_status,
    diagnostic, bytecode_hash
)
SELECT p.program_id, v.compiler_version_id, 'SUCCEEDED',
       NULL, 'sha256:demo-risk-bytecode-v1'
FROM source_programs p
CROSS JOIN compiler_versions v
WHERE p.program_name = 'deployment-risk-policy'
  AND v.version_label = '1.0.0';

INSERT INTO compilations (
    program_id, compiler_version_id, compilation_status,
    diagnostic, bytecode_hash
)
SELECT p.program_id, v.compiler_version_id, 'SUCCEEDED',
       NULL, 'sha256:demo-window-bytecode-v1'
FROM source_programs p
CROSS JOIN compiler_versions v
WHERE p.program_name = 'deployment-window-policy'
  AND v.version_label = '1.0.0';

INSERT INTO compilations (
    program_id, compiler_version_id, compilation_status,
    diagnostic, bytecode_hash
)
SELECT p.program_id, v.compiler_version_id, 'FAILED',
       'Expected expression after multiplication operator', NULL
FROM source_programs p
CROSS JOIN compiler_versions v
WHERE p.program_name = 'malformed-expression'
  AND v.version_label = '1.0.0';

-- Bytecode positions represent execution order, not source line numbers.
INSERT INTO bytecode_instructions (
    compilation_id, instruction_index, opcode, operand
)
SELECT c.compilation_id, data.instruction_index,
       data.opcode, data.operand
FROM compilations c
JOIN source_programs p ON p.program_id = c.program_id
CROSS JOIN (
    VALUES
        (0, 'LOAD', '{"name":"failed_checks"}'::jsonb),
        (1, 'CONSTANT', '{"type":"number","value":2}'::jsonb),
        (2, 'MULTIPLY', NULL::jsonb),
        (3, 'LOAD', '{"name":"critical_findings"}'::jsonb),
        (4, 'CONSTANT', '{"type":"number","value":10}'::jsonb),
        (5, 'MULTIPLY', NULL::jsonb),
        (6, 'ADD', NULL::jsonb),
        (7, 'STORE', '{"name":"risk"}'::jsonb),
        (8, 'LOAD', '{"name":"risk"}'::jsonb),
        (9, 'PRINT', NULL::jsonb),
        (10, 'HALT', NULL::jsonb)
) AS data(instruction_index, opcode, operand)
WHERE p.program_name = 'deployment-risk-policy'
  AND c.compilation_status = 'SUCCEEDED';

INSERT INTO bytecode_instructions (
    compilation_id, instruction_index, opcode, operand
)
SELECT c.compilation_id, data.instruction_index,
       data.opcode, data.operand
FROM compilations c
JOIN source_programs p ON p.program_id = c.program_id
CROSS JOIN (
    VALUES
        (0, 'LOAD', '{"name":"deployment_window_hours"}'::jsonb),
        (1, 'CONSTANT', '{"type":"number","value":2}'::jsonb),
        (2, 'LESS_EQUAL', NULL::jsonb),
        (3, 'PRINT', NULL::jsonb),
        (4, 'HALT', NULL::jsonb)
) AS data(instruction_index, opcode, operand)
WHERE p.program_name = 'deployment-window-policy'
  AND c.compilation_status = 'SUCCEEDED';

INSERT INTO runtime_contexts (context_name, context_values)
VALUES
    (
        'healthy-deployment',
        '{"failed_checks":0,"critical_findings":0,"deployment_window_hours":4}'
    ),
    (
        'risky-deployment',
        '{"failed_checks":3,"critical_findings":2,"deployment_window_hours":1}'
    ),
    (
        'missing-variable-case',
        '{"failed_checks":1}'
    );

INSERT INTO executions (
    compilation_id, context_id, execution_status,
    result, error_message, instructions_executed, finished_at
)
SELECT c.compilation_id, rc.context_id, 'SUCCEEDED',
       '{"risk":0}'::jsonb, NULL, 11, CURRENT_TIMESTAMP
FROM compilations c
JOIN source_programs p ON p.program_id = c.program_id
JOIN runtime_contexts rc
    ON rc.context_name = 'healthy-deployment'
WHERE p.program_name = 'deployment-risk-policy'
  AND c.compilation_status = 'SUCCEEDED';

INSERT INTO executions (
    compilation_id, context_id, execution_status,
    result, error_message, instructions_executed, finished_at
)
SELECT c.compilation_id, rc.context_id, 'RUNTIME_ERROR',
       NULL, 'Required variable deployment_window_hours is missing',
       1, CURRENT_TIMESTAMP
FROM compilations c
JOIN source_programs p ON p.program_id = c.program_id
JOIN runtime_contexts rc
    ON rc.context_name = 'missing-variable-case'
WHERE p.program_name = 'deployment-window-policy'
  AND c.compilation_status = 'SUCCEEDED';

-- Inspect compilation outcomes without treating compile failures as runtime
-- failures. These are different failure stages with different diagnostics.
SELECT
    p.program_name,
    v.version_label,
    c.compilation_status,
    c.diagnostic,
    c.bytecode_hash
FROM compilations c
JOIN source_programs p USING (program_id)
JOIN compiler_versions v USING (compiler_version_id)
ORDER BY p.program_name, v.version_label;

-- Examine the generated instruction stream in program-counter order.
SELECT
    p.program_name,
    bi.instruction_index AS program_counter,
    bi.opcode,
    bi.operand
FROM bytecode_instructions bi
JOIN compilations c USING (compilation_id)
JOIN source_programs p USING (program_id)
ORDER BY p.program_name, bi.instruction_index;

-- JSONB operators extract runtime context fields for operational reporting.
SELECT
    context_name,
    (context_values ->> 'failed_checks')::INTEGER AS failed_checks,
    (context_values ->> 'critical_findings')::INTEGER AS critical_findings,
    (context_values ->> 'deployment_window_hours')::NUMERIC
        AS deployment_window_hours
FROM runtime_contexts
ORDER BY context_name;

-- Aggregate operational reliability by execution outcome.
SELECT
    execution_status,
    count(*) AS execution_count,
    avg(instructions_executed)::NUMERIC(10, 2) AS average_instructions
FROM executions
GROUP BY execution_status
ORDER BY execution_status;

-- Show the complete source-to-runtime lineage for diagnostic investigations.
SELECT
    p.program_name,
    c.compilation_id,
    c.compilation_status,
    e.execution_id,
    rc.context_name,
    e.execution_status,
    e.error_message,
    e.instructions_executed
FROM source_programs p
JOIN compilations c USING (program_id)
LEFT JOIN executions e USING (compilation_id)
LEFT JOIN runtime_contexts rc USING (context_id)
ORDER BY p.program_name, c.compilation_id, e.execution_id;

-- The following transaction demonstrates atomic recording. An invalid
-- execution record violates the result/error consistency constraint.
-- The nested exception block rolls back only its subtransaction.
DO $$
BEGIN
    BEGIN
        INSERT INTO executions (
            compilation_id,
            execution_status,
            result,
            error_message,
            instructions_executed
        )
        SELECT compilation_id, 'RUNTIME_ERROR',
               '{"value":42}'::jsonb, NULL, 3
        FROM compilations
        WHERE compilation_status = 'SUCCEEDED'
        LIMIT 1;

        RAISE EXCEPTION 'Expected integrity violation was not raised';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'Invalid execution rejected by database constraints';
    END;
END;
$$;

COMMIT;
