DROP SCHEMA IF EXISTS memory_management_demo CASCADE;
CREATE SCHEMA memory_management_demo;
SET search_path TO memory_management_demo;

-- PostgreSQL model of a variable-partition contiguous memory manager.
-- Addresses are represented as integer offsets inside a physical memory arena.

CREATE TABLE memory_arenas (
    arena_id       BIGSERIAL PRIMARY KEY,
    arena_name     TEXT NOT NULL UNIQUE,
    total_units    INTEGER NOT NULL CHECK (total_units > 0),
    allocation_strategy TEXT NOT NULL
        CHECK (allocation_strategy IN ('first-fit', 'best-fit', 'worst-fit'))
);

CREATE TABLE processes (
    process_id     BIGSERIAL PRIMARY KEY,
    process_name   TEXT NOT NULL UNIQUE,
    process_type   TEXT NOT NULL,
    requested_units INTEGER NOT NULL CHECK (requested_units > 0)
);

CREATE TABLE memory_blocks (
    block_id       BIGSERIAL PRIMARY KEY,
    arena_id       BIGINT NOT NULL REFERENCES memory_arenas(arena_id)
                    ON DELETE CASCADE,
    start_address  INTEGER NOT NULL CHECK (start_address >= 0),
    block_units    INTEGER NOT NULL CHECK (block_units > 0),
    state          TEXT NOT NULL CHECK (state IN ('FREE', 'ALLOCATED')),
    process_id     BIGINT REFERENCES processes(process_id),
    CHECK (
        (state = 'FREE' AND process_id IS NULL)
        OR
        (state = 'ALLOCATED' AND process_id IS NOT NULL)
    ),
    UNIQUE (arena_id, start_address)
);

CREATE INDEX idx_memory_blocks_arena_state
    ON memory_blocks(arena_id, state);

CREATE INDEX idx_memory_blocks_process
    ON memory_blocks(process_id);

CREATE TABLE memory_events (
    event_id       BIGSERIAL PRIMARY KEY,
    arena_id       BIGINT NOT NULL REFERENCES memory_arenas(arena_id)
                    ON DELETE CASCADE,
    process_id     BIGINT REFERENCES processes(process_id),
    event_type     TEXT NOT NULL CHECK (
        event_type IN (
            'ALLOCATE',
            'RELEASE',
            'COMPACT',
            'ALLOCATION_FAILURE'
        )
    ),
    requested_units INTEGER CHECK (requested_units IS NULL OR requested_units > 0),
    event_time     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    details        JSONB NOT NULL DEFAULT '{}'::jsonb
);

INSERT INTO memory_arenas
    (arena_name, total_units, allocation_strategy)
VALUES
    ('analytics-node-01', 1000, 'best-fit');

INSERT INTO processes
    (process_name, process_type, requested_units)
VALUES
    ('ETL-A', 'batch', 180),
    ('MODEL-A', 'analytics', 240),
    ('REPORT-A', 'reporting', 120),
    ('CACHE-A', 'cache', 160),
    ('LARGE-MODEL', 'analytics', 300);

-- Initial contiguous layout.
INSERT INTO memory_blocks
    (arena_id, start_address, block_units, state, process_id)
SELECT
    1, 0, 180, 'ALLOCATED',
    process_id
FROM processes WHERE process_name = 'ETL-A';

INSERT INTO memory_blocks
    (arena_id, start_address, block_units, state, process_id)
SELECT
    1, 180, 240, 'ALLOCATED',
    process_id
FROM processes WHERE process_name = 'MODEL-A';

INSERT INTO memory_blocks
    (arena_id, start_address, block_units, state, process_id)
SELECT
    1, 420, 120, 'ALLOCATED',
    process_id
FROM processes WHERE process_name = 'REPORT-A';

INSERT INTO memory_blocks
    (arena_id, start_address, block_units, state, process_id)
SELECT
    1, 540, 160, 'ALLOCATED',
    process_id
FROM processes WHERE process_name = 'CACHE-A';

INSERT INTO memory_blocks
    (arena_id, start_address, block_units, state)
VALUES
    (1, 700, 300, 'FREE');

-- The following transaction models the release of MODEL-A and REPORT-A.
-- Releasing blocks creates holes while preserving the addresses of the
-- remaining allocations.
BEGIN;

UPDATE memory_blocks
SET state = 'FREE',
    process_id = NULL
WHERE arena_id = 1
  AND process_id IN (
      SELECT process_id
      FROM processes
      WHERE process_name IN ('MODEL-A', 'REPORT-A')
  );

INSERT INTO memory_events
    (arena_id, event_type, details)
VALUES
    (
        1,
        'RELEASE',
        '{"processes":["MODEL-A","REPORT-A"]}'
    );

COMMIT;

-- Total free memory and largest contiguous free region must be measured
-- separately. A large request requires the second value to be sufficient.
WITH free_blocks AS (
    SELECT block_units
    FROM memory_blocks
    WHERE arena_id = 1
      AND state = 'FREE'
)
SELECT
    COALESCE(SUM(block_units), 0) AS total_free_units,
    COALESCE(MAX(block_units), 0) AS largest_contiguous_free_units,
    COALESCE(SUM(block_units), 0)
      - COALESCE(MAX(block_units), 0) AS external_fragmentation_units
FROM free_blocks;

-- Show the physical layout in address order.
SELECT
    start_address,
    start_address + block_units - 1 AS end_address,
    block_units,
    state,
    p.process_name
FROM memory_blocks mb
LEFT JOIN processes p ON p.process_id = mb.process_id
WHERE mb.arena_id = 1
ORDER BY start_address;

-- Demonstrate a policy query for a contiguous request.
-- The request can succeed only if at least one free block is large enough.
SELECT
    EXISTS (
        SELECT 1
        FROM memory_blocks
        WHERE arena_id = 1
          AND state = 'FREE'
          AND block_units >= (
              SELECT requested_units
              FROM processes
              WHERE process_name = 'LARGE-MODEL'
          )
    ) AS contiguous_request_can_fit;

-- Best-fit selection chooses the smallest adequate free region.
SELECT
    block_id,
    start_address,
    block_units
FROM memory_blocks
WHERE arena_id = 1
  AND state = 'FREE'
  AND block_units >= (
      SELECT requested_units
      FROM processes
      WHERE process_name = 'LARGE-MODEL'
  )
ORDER BY block_units, start_address
LIMIT 1;

-- Release adjacent regions and coalesce them by constructing a normalized
-- representation. PostgreSQL window functions identify contiguous free runs.
WITH ordered AS (
    SELECT
        *,
        start_address
          - SUM(block_units) OVER (
                PARTITION BY arena_id
                ORDER BY start_address
                ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
            ) AS grouping_key
    FROM memory_blocks
    WHERE arena_id = 1
      AND state = 'FREE'
),
runs AS (
    SELECT
        arena_id,
        MIN(start_address) AS run_start,
        SUM(block_units) AS run_units
    FROM ordered
    GROUP BY arena_id, grouping_key
)
SELECT
    arena_id,
    run_start,
    run_units
FROM runs
ORDER BY run_start;

-- Database-level validation for overlap is useful when blocks are inserted
-- independently. PostgreSQL range types can express address occupancy.
ALTER TABLE memory_blocks
ADD COLUMN address_range int4range
GENERATED ALWAYS AS (
    int4range(start_address, start_address + block_units, '[)')
) STORED;

CREATE INDEX idx_memory_blocks_address_range
    ON memory_blocks USING gist(address_range);

-- Detect overlapping blocks. A correct contiguous layout should return zero.
SELECT
    a.block_id AS first_block,
    b.block_id AS second_block
FROM memory_blocks a
JOIN memory_blocks b
  ON a.block_id < b.block_id
 AND a.arena_id = b.arena_id
 AND a.address_range && b.address_range;

-- Fixed-partition internal fragmentation example.
CREATE TABLE fixed_partitions (
    partition_id    BIGSERIAL PRIMARY KEY,
    partition_size  INTEGER NOT NULL CHECK (partition_size > 0),
    requested_units INTEGER NOT NULL CHECK (requested_units > 0),
    CHECK (requested_units <= partition_size)
);

INSERT INTO fixed_partitions (partition_size, requested_units)
VALUES
    (64, 7),
    (64, 31),
    (64, 60),
    (64, 64);

SELECT
    SUM(requested_units) AS requested_units,
    SUM(partition_size) AS reserved_units,
    SUM(partition_size - requested_units) AS internal_fragmentation_units
FROM fixed_partitions;

-- A compacted representation moves allocated blocks toward address zero.
-- This transaction deliberately rebuilds the arena layout rather than
-- pretending that compaction is free: application code must account for
-- relocation of allocated objects.
BEGIN;

WITH allocated_order AS (
    SELECT
        block_id,
        arena_id,
        block_units,
        process_id,
        COALESCE(
            SUM(block_units) OVER (
                PARTITION BY arena_id
                ORDER BY start_address
                ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
            ),
            0
        ) AS new_start
    FROM memory_blocks
    WHERE arena_id = 1
      AND state = 'ALLOCATED'
)
UPDATE memory_blocks mb
SET start_address = ao.new_start
FROM allocated_order ao
WHERE mb.block_id = ao.block_id;

DELETE FROM memory_blocks
WHERE arena_id = 1
  AND state = 'FREE';

INSERT INTO memory_blocks
    (arena_id, start_address, block_units, state)
SELECT
    1,
    COALESCE(MAX(start_address + block_units), 0),
    1000 - COALESCE(MAX(start_address + block_units), 0),
    'FREE'
FROM memory_blocks
WHERE arena_id = 1;

INSERT INTO memory_events
    (arena_id, event_type, details)
VALUES
    (1, 'COMPACT', '{"reason":"contiguous-allocation-recovery"}');

COMMIT;

-- Verify that the post-compaction layout covers the arena without overlap.
SELECT
    start_address,
    start_address + block_units AS exclusive_end,
    block_units,
    state
FROM memory_blocks
WHERE arena_id = 1
ORDER BY start_address;

-- Query suitable for an allocator dashboard.
SELECT
    a.arena_name,
    a.total_units,
    COALESCE(SUM(mb.block_units)
        FILTER (WHERE mb.state = 'FREE'), 0) AS free_units,
    COALESCE(MAX(mb.block_units)
        FILTER (WHERE mb.state = 'FREE'), 0) AS largest_free_block,
    COALESCE(SUM(mb.block_units)
        FILTER (WHERE mb.state = 'FREE'), 0)
      - COALESCE(MAX(mb.block_units)
        FILTER (WHERE mb.state = 'FREE'), 0) AS external_fragmentation
FROM memory_arenas a
LEFT JOIN memory_blocks mb
    ON mb.arena_id = a.arena_id
GROUP BY a.arena_id, a.arena_name, a.total_units;
