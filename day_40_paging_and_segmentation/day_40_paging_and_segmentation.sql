DROP SCHEMA IF EXISTS memory_management_lab CASCADE;
CREATE SCHEMA memory_management_lab;
SET search_path TO memory_management_lab;

-- PostgreSQL model of a segmented and paged virtual-memory subsystem.
-- Segments validate logical offsets and permissions; page mappings translate
-- linear pages into physical frames and enforce page-level permissions.

CREATE TYPE access_type AS ENUM ('READ', 'WRITE', 'EXECUTE');

CREATE TABLE process (
    process_id BIGSERIAL PRIMARY KEY,
    process_name TEXT NOT NULL UNIQUE,
    address_bits INTEGER NOT NULL CHECK (address_bits IN (16, 32, 64)),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE segment (
    segment_id BIGSERIAL PRIMARY KEY,
    process_id BIGINT NOT NULL REFERENCES process(process_id) ON DELETE CASCADE,
    segment_name TEXT NOT NULL,
    base_address BIGINT NOT NULL CHECK (base_address >= 0),
    segment_limit BIGINT NOT NULL CHECK (segment_limit >= 0),
    readable BOOLEAN NOT NULL DEFAULT FALSE,
    writable BOOLEAN NOT NULL DEFAULT FALSE,
    executable BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (process_id, segment_name),
    CHECK (NOT (writable AND executable))
);

CREATE TABLE physical_frame (
    frame_id INTEGER PRIMARY KEY,
    frame_size INTEGER NOT NULL DEFAULT 4096
        CHECK (frame_size IN (4096, 8192, 16384)),
    allocated BOOLEAN NOT NULL DEFAULT FALSE,
    owner_process_id BIGINT REFERENCES process(process_id)
);

CREATE TABLE page_mapping (
    mapping_id BIGSERIAL PRIMARY KEY,
    process_id BIGINT NOT NULL REFERENCES process(process_id) ON DELETE CASCADE,
    virtual_page BIGINT NOT NULL CHECK (virtual_page >= 0),
    frame_id INTEGER NOT NULL REFERENCES physical_frame(frame_id),
    present BOOLEAN NOT NULL DEFAULT TRUE,
    readable BOOLEAN NOT NULL DEFAULT TRUE,
    writable BOOLEAN NOT NULL DEFAULT FALSE,
    executable BOOLEAN NOT NULL DEFAULT FALSE,
    user_accessible BOOLEAN NOT NULL DEFAULT TRUE,
    accessed BOOLEAN NOT NULL DEFAULT FALSE,
    dirty BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (process_id, virtual_page),
    CHECK (NOT (writable AND executable))
);

CREATE TABLE memory_access (
    access_id BIGSERIAL PRIMARY KEY,
    process_id BIGINT NOT NULL REFERENCES process(process_id) ON DELETE CASCADE,
    segment_id BIGINT REFERENCES segment(segment_id),
    virtual_address BIGINT NOT NULL CHECK (virtual_address >= 0),
    access_kind access_type NOT NULL,
    translated_linear_address BIGINT,
    physical_address BIGINT,
    page_number BIGINT,
    frame_id INTEGER REFERENCES physical_frame(frame_id),
    result TEXT NOT NULL CHECK (
        result IN (
            'SUCCESS',
            'SEGMENT_FAULT',
            'PAGE_FAULT',
            'PROTECTION_FAULT'
        )
    ),
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE status_check (
    status_check_id BIGSERIAL PRIMARY KEY,
    process_id BIGINT NOT NULL REFERENCES process(process_id) ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('PENDING', 'PASS', 'FAIL')
    ),
    completed_at TIMESTAMPTZ,
    UNIQUE (process_id, check_name)
);

CREATE INDEX idx_segment_process
    ON segment(process_id);

CREATE INDEX idx_page_mapping_process_page
    ON page_mapping(process_id, virtual_page);

CREATE INDEX idx_page_mapping_frame
    ON page_mapping(frame_id);

CREATE INDEX idx_memory_access_process_time
    ON memory_access(process_id, occurred_at DESC);

INSERT INTO process (process_name, address_bits)
VALUES
    ('compiler_service', 32),
    ('analytics_worker', 32);

INSERT INTO physical_frame (frame_id, frame_size, allocated, owner_process_id)
VALUES
    (10, 4096, TRUE, 1),
    (11, 4096, TRUE, 1),
    (20, 4096, TRUE, 1),
    (21, 4096, TRUE, 1),
    (30, 4096, TRUE, 2);

INSERT INTO segment
    (process_id, segment_name, base_address, segment_limit,
     readable, writable, executable)
VALUES
    (1, 'code', 65536, 8191, TRUE, FALSE, TRUE),
    (1, 'data', 131072, 12287, TRUE, TRUE, FALSE),
    (1, 'stack', 196608, 8191, TRUE, TRUE, FALSE),
    (2, 'code', 262144, 8191, TRUE, FALSE, TRUE);

-- Virtual page 16 maps to frame 10. The offset inside the page remains
-- unchanged during translation.
INSERT INTO page_mapping
    (process_id, virtual_page, frame_id, readable, writable, executable)
VALUES
    (1, 16, 10, TRUE, FALSE, TRUE),
    (1, 17, 11, TRUE, FALSE, TRUE),
    (1, 32, 20, TRUE, TRUE, FALSE),
    (1, 33, 21, TRUE, TRUE, FALSE),
    (2, 64, 30, TRUE, FALSE, TRUE);

INSERT INTO status_check (process_id, check_name, status)
VALUES
    (1, 'page_table_consistency', 'PASS'),
    (1, 'permission_audit', 'PASS'),
    (2, 'page_table_consistency', 'PENDING');

-- A logical address is represented here by a segment plus offset.
-- The segment base converts it into a linear address.
WITH logical_reference AS (
    SELECT
        s.segment_id,
        s.segment_name,
        s.base_address,
        32::BIGINT AS segment_offset
    FROM segment AS s
    WHERE s.process_id = 1
      AND s.segment_name = 'code'
),
linear_reference AS (
    SELECT
        segment_id,
        segment_name,
        base_address + segment_offset AS linear_address
    FROM logical_reference
)
SELECT
    segment_name,
    linear_address,
    FLOOR(linear_address / 4096)::BIGINT AS virtual_page,
    MOD(linear_address, 4096)::BIGINT AS page_offset
FROM linear_reference;

-- Resolve a linear address through the page table.
WITH reference AS (
    SELECT 65568::BIGINT AS linear_address
)
SELECT
    r.linear_address,
    FLOOR(r.linear_address / 4096)::BIGINT AS virtual_page,
    MOD(r.linear_address, 4096)::BIGINT AS page_offset,
    p.frame_id,
    p.frame_id * 4096 + MOD(r.linear_address, 4096) AS physical_address
FROM reference AS r
JOIN page_mapping AS p
  ON p.process_id = 1
 AND p.virtual_page = FLOOR(r.linear_address / 4096)
WHERE p.present;

-- Check whether a requested operation is allowed by both segment and page.
WITH request AS (
    SELECT
        'data'::TEXT AS segment_name,
        100::BIGINT AS segment_offset,
        'WRITE'::access_type AS requested_access
),
resolved AS (
    SELECT
        s.segment_id,
        s.base_address,
        s.segment_limit,
        s.readable AS segment_readable,
        s.writable AS segment_writable,
        s.executable AS segment_executable,
        r.segment_offset,
        r.requested_access,
        s.base_address + r.segment_offset AS linear_address
    FROM request AS r
    JOIN segment AS s
      ON s.process_id = 1
     AND s.segment_name = r.segment_name
),
page_check AS (
    SELECT
        x.*,
        p.frame_id,
        p.present,
        p.readable,
        p.writable,
        p.executable
    FROM resolved AS x
    LEFT JOIN page_mapping AS p
      ON p.process_id = 1
     AND p.virtual_page = FLOOR(x.linear_address / 4096)
)
SELECT
    segment_id,
    linear_address,
    frame_id,
    CASE
        WHEN segment_offset > segment_limit THEN 'SEGMENT_FAULT'
        WHEN NOT present OR present IS NULL THEN 'PAGE_FAULT'
        WHEN requested_access = 'READ'
             AND NOT segment_readable THEN 'PROTECTION_FAULT'
        WHEN requested_access = 'WRITE'
             AND NOT segment_writable THEN 'PROTECTION_FAULT'
        WHEN requested_access = 'EXECUTE'
             AND NOT segment_executable THEN 'PROTECTION_FAULT'
        WHEN requested_access = 'READ' AND NOT readable THEN 'PROTECTION_FAULT'
        WHEN requested_access = 'WRITE' AND NOT writable THEN 'PROTECTION_FAULT'
        WHEN requested_access = 'EXECUTE' AND NOT executable THEN 'PROTECTION_FAULT'
        ELSE 'SUCCESS'
    END AS translation_result
FROM page_check;

-- Demonstrate a page-table audit. Duplicate virtual pages are prevented by
-- the UNIQUE constraint on (process_id, virtual_page).
SELECT
    process_id,
    virtual_page,
    frame_id,
    present,
    readable,
    writable,
    executable,
    accessed,
    dirty
FROM page_mapping
ORDER BY process_id, virtual_page;

-- Detect physical-frame aliasing. Multiple virtual pages mapping to one frame
-- may be intentional for shared memory, but it deserves explicit review.
SELECT
    frame_id,
    COUNT(*) AS mappings,
    ARRAY_AGG(
        process_id::TEXT || ':' || virtual_page::TEXT
        ORDER BY process_id, virtual_page
    ) AS virtual_mappings
FROM page_mapping
WHERE present
GROUP BY frame_id
HAVING COUNT(*) > 1;

-- Transactionally record a successful write and mark the page dirty.
BEGIN;

WITH target AS (
    SELECT
        p.mapping_id,
        p.frame_id,
        131072::BIGINT + 100 AS linear_address
    FROM page_mapping AS p
    WHERE p.process_id = 1
      AND p.virtual_page = FLOOR((131072 + 100) / 4096)
      AND p.present
      AND p.writable
)
UPDATE page_mapping AS p
SET accessed = TRUE,
    dirty = TRUE
FROM target AS t
WHERE p.mapping_id = t.mapping_id;

INSERT INTO memory_access (
    process_id,
    segment_id,
    virtual_address,
    access_kind,
    translated_linear_address,
    physical_address,
    page_number,
    frame_id,
    result
)
SELECT
    1,
    s.segment_id,
    100,
    'WRITE',
    s.base_address + 100,
    p.frame_id * 4096 + MOD(s.base_address + 100, 4096),
    FLOOR((s.base_address + 100) / 4096),
    p.frame_id,
    'SUCCESS'
FROM segment AS s
JOIN page_mapping AS p
  ON p.process_id = 1
 AND p.virtual_page = FLOOR((s.base_address + 100) / 4096)
WHERE s.process_id = 1
  AND s.segment_name = 'data'
  AND s.writable
  AND p.writable
  AND p.present;

COMMIT;

-- The database can expose protection failures without mutating the mapping.
WITH attempted_write AS (
    SELECT
        s.segment_id,
        s.segment_name,
        s.writable AS segment_writable,
        p.virtual_page,
        p.writable AS page_writable,
        p.present
    FROM segment AS s
    JOIN page_mapping AS p
      ON p.process_id = s.process_id
     AND p.virtual_page = FLOOR((s.base_address + 20) / 4096)
    WHERE s.process_id = 1
      AND s.segment_name = 'code'
)
SELECT
    segment_name,
    CASE
        WHEN NOT segment_writable THEN 'SEGMENT_PROTECTION_FAULT'
        WHEN NOT present THEN 'PAGE_FAULT'
        WHEN NOT page_writable THEN 'PAGE_PROTECTION_FAULT'
        ELSE 'WRITE_ALLOWED'
    END AS decision
FROM attempted_write;

-- Inspect pages touched by writes. Dirty pages are candidates for write-back
-- when the operating system eventually evicts them.
SELECT
    process_id,
    virtual_page,
    frame_id,
    accessed,
    dirty
FROM page_mapping
WHERE accessed = TRUE
ORDER BY process_id, virtual_page;

-- Compare segment permissions with page permissions to locate suspicious
-- configurations. A writable segment backed only by read-only pages is legal,
-- but it means application-level writes will still fail at the page layer.
SELECT
    s.segment_name,
    s.writable AS segment_allows_write,
    BOOL_AND(p.writable) AS mapped_pages_all_writable,
    COUNT(p.mapping_id) AS mapped_page_count
FROM segment AS s
LEFT JOIN page_mapping AS p
  ON p.process_id = s.process_id
 AND p.virtual_page BETWEEN
     FLOOR(s.base_address / 4096)
     AND FLOOR((s.base_address + s.segment_limit) / 4096)
WHERE s.process_id = 1
GROUP BY s.segment_name, s.writable
ORDER BY s.segment_name;
