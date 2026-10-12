-- PostgreSQL-compatible File System Internals model
--
-- The schema models a repository-like storage volume at the filesystem layer.
-- It separates:
--   * inode identity and metadata
--   * directory name resolution
--   * logical files and physical allocation
--   * journal transactions
--   * mount state
--
-- PostgreSQL constraints protect invariants that should not depend solely on
-- application code.

DROP SCHEMA IF EXISTS fs_internals CASCADE;
CREATE SCHEMA fs_internals;

SET search_path = fs_internals, public;

CREATE TYPE file_type AS ENUM ('file', 'directory');

CREATE TYPE journal_state AS ENUM (
    'prepared',
    'committed',
    'aborted'
);

CREATE TYPE mount_state AS ENUM (
    'mounted',
    'unmounted',
    'needs_recovery'
);

CREATE TABLE filesystem (
    filesystem_id BIGSERIAL PRIMARY KEY,
    volume_name TEXT NOT NULL UNIQUE,
    magic TEXT NOT NULL,
    block_size INTEGER NOT NULL CHECK (block_size > 0),
    total_blocks INTEGER NOT NULL CHECK (total_blocks > 0),
    inode_limit INTEGER NOT NULL CHECK (inode_limit > 0),
    root_inode BIGINT,
    journal_capacity INTEGER NOT NULL CHECK (journal_capacity > 0),
    generation BIGINT NOT NULL DEFAULT 1,
    mount_status mount_state NOT NULL DEFAULT 'unmounted',
    clean_shutdown BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE inode (
    inode_id BIGSERIAL PRIMARY KEY,
    filesystem_id BIGINT NOT NULL
        REFERENCES filesystem(filesystem_id)
        ON DELETE CASCADE,
    inode_number INTEGER NOT NULL,
    type file_type NOT NULL,
    mode INTEGER NOT NULL CHECK (mode BETWEEN 0 AND 4095),
    uid INTEGER NOT NULL CHECK (uid >= 0),
    gid INTEGER NOT NULL CHECK (gid >= 0),
    parent_inode_id BIGINT REFERENCES inode(inode_id),
    size_bytes BIGINT NOT NULL DEFAULT 0 CHECK (size_bytes >= 0),
    link_count INTEGER NOT NULL DEFAULT 1 CHECK (link_count > 0),
    atime TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    mtime TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    ctime TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),

    UNIQUE (filesystem_id, inode_number)
);

ALTER TABLE filesystem
    ADD CONSTRAINT filesystem_root_fk
    FOREIGN KEY (root_inode)
    REFERENCES inode(inode_id)
    DEFERRABLE INITIALLY DEFERRED;

CREATE TABLE directory_entry (
    directory_inode_id BIGINT NOT NULL
        REFERENCES inode(inode_id)
        ON DELETE CASCADE,
    entry_name TEXT NOT NULL,
    target_inode_id BIGINT NOT NULL
        REFERENCES inode(inode_id)
        ON DELETE RESTRICT,
    PRIMARY KEY (directory_inode_id, entry_name),
    CHECK (
        entry_name <> ''
        AND entry_name NOT LIKE '%/%'
        AND length(entry_name) <= 255
    )
);

CREATE TABLE storage_block (
    filesystem_id BIGINT NOT NULL
        REFERENCES filesystem(filesystem_id)
        ON DELETE CASCADE,
    block_number INTEGER NOT NULL,
    is_metadata BOOLEAN NOT NULL DEFAULT FALSE,
    allocated BOOLEAN NOT NULL DEFAULT FALSE,
    checksum TEXT,
    PRIMARY KEY (filesystem_id, block_number),
    CHECK (block_number >= 0)
);

CREATE TABLE inode_block (
    inode_id BIGINT NOT NULL
        REFERENCES inode(inode_id)
        ON DELETE CASCADE,
    logical_block_number INTEGER NOT NULL,
    physical_block_number INTEGER NOT NULL,
    allocation_kind TEXT NOT NULL
        CHECK (allocation_kind IN ('direct', 'indirect')),
    indirect_level INTEGER NOT NULL DEFAULT 0
        CHECK (indirect_level >= 0),
    PRIMARY KEY (inode_id, logical_block_number),
    UNIQUE (inode_id, physical_block_number),
    CHECK (logical_block_number >= 0)
);

CREATE TABLE journal_transaction (
    transaction_id BIGSERIAL PRIMARY KEY,
    filesystem_id BIGINT NOT NULL
        REFERENCES filesystem(filesystem_id)
        ON DELETE CASCADE,
    sequence_number BIGINT NOT NULL,
    operation TEXT NOT NULL,
    state journal_state NOT NULL DEFAULT 'prepared',
    started_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    committed_at TIMESTAMPTZ,

    UNIQUE (filesystem_id, sequence_number)
);

CREATE TABLE journal_inode_record (
    transaction_id BIGINT NOT NULL
        REFERENCES journal_transaction(transaction_id)
        ON DELETE CASCADE,
    inode_id BIGINT NOT NULL
        REFERENCES inode(inode_id)
        ON DELETE RESTRICT,
    old_size BIGINT,
    new_size BIGINT,
    old_link_count INTEGER,
    new_link_count INTEGER,
    old_mtime TIMESTAMPTZ,
    new_mtime TIMESTAMPTZ,
    PRIMARY KEY (transaction_id, inode_id)
);

CREATE TABLE journal_directory_record (
    transaction_id BIGINT NOT NULL
        REFERENCES journal_transaction(transaction_id)
        ON DELETE CASCADE,
    directory_inode_id BIGINT NOT NULL
        REFERENCES inode(inode_id)
        ON DELETE RESTRICT,
    entry_name TEXT NOT NULL,
    old_target_inode_id BIGINT,
    new_target_inode_id BIGINT,
    operation TEXT NOT NULL
        CHECK (operation IN ('create', 'remove', 'replace')),
    PRIMARY KEY (
        transaction_id,
        directory_inode_id,
        entry_name
    )
);

CREATE TABLE mount_event (
    mount_event_id BIGSERIAL PRIMARY KEY,
    filesystem_id BIGINT NOT NULL
        REFERENCES filesystem(filesystem_id)
        ON DELETE CASCADE,
    previous_status mount_state,
    new_status mount_state NOT NULL,
    generation BIGINT NOT NULL,
    recovery_required BOOLEAN NOT NULL DEFAULT FALSE,
    event_time TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX idx_inode_filesystem_type
    ON inode (filesystem_id, type);

CREATE INDEX idx_directory_target
    ON directory_entry (target_inode_id);

CREATE INDEX idx_inode_block_physical
    ON inode_block (physical_block_number);

CREATE INDEX idx_journal_recovery
    ON journal_transaction (
        filesystem_id,
        state,
        sequence_number
    );

CREATE INDEX idx_mount_event_filesystem_time
    ON mount_event (filesystem_id, event_time DESC);

CREATE OR REPLACE FUNCTION enforce_inode_size()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    required_blocks INTEGER;
    allocated_blocks INTEGER;
    fs_block_size INTEGER;
BEGIN
    IF NEW.type = 'directory' AND NEW.size_bytes <> 0 THEN
        RAISE EXCEPTION
            'Directory inode % cannot have regular-file size',
            NEW.inode_number;
    END IF;

    SELECT block_size
    INTO fs_block_size
    FROM filesystem
    WHERE filesystem_id = NEW.filesystem_id;

    SELECT count(*)
    INTO allocated_blocks
    FROM inode_block
    WHERE inode_id = NEW.inode_id;

    required_blocks :=
        CASE
            WHEN NEW.size_bytes = 0 THEN 0
            ELSE ceil(
                NEW.size_bytes::numeric / fs_block_size
            )::integer
        END;

    IF NEW.type = 'file'
       AND allocated_blocks < required_blocks THEN
        RAISE EXCEPTION
            'Inode % requires % blocks but only % are allocated',
            NEW.inode_number,
            required_blocks,
            allocated_blocks;
    END IF;

    RETURN NEW;
END;
$$;

CREATE CONSTRAINT TRIGGER inode_size_integrity
AFTER INSERT OR UPDATE OF size_bytes
ON inode
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION enforce_inode_size();

CREATE OR REPLACE FUNCTION enforce_unique_physical_allocation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    block_is_allocated BOOLEAN;
    block_is_metadata BOOLEAN;
BEGIN
    SELECT allocated, is_metadata
    INTO block_is_allocated, block_is_metadata
    FROM storage_block
    WHERE filesystem_id = (
        SELECT filesystem_id
        FROM inode
        WHERE inode_id = NEW.inode_id
    )
      AND block_number = NEW.physical_block_number;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Physical block % does not exist',
            NEW.physical_block_number;
    END IF;

    IF block_is_metadata THEN
        RAISE EXCEPTION
            'Metadata block % cannot hold file data',
            NEW.physical_block_number;
    END IF;

    IF NOT block_is_allocated THEN
        RAISE EXCEPTION
            'Block % must be allocated before inode mapping',
            NEW.physical_block_number;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER validate_inode_block
BEFORE INSERT OR UPDATE
ON inode_block
FOR EACH ROW
EXECUTE FUNCTION enforce_unique_physical_allocation();

CREATE OR REPLACE FUNCTION journal_commit(
    p_transaction_id BIGINT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE journal_transaction
    SET state = 'committed',
        committed_at = clock_timestamp()
    WHERE transaction_id = p_transaction_id
      AND state = 'prepared';

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Transaction % cannot be committed',
            p_transaction_id;
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION mount_filesystem(
    p_filesystem_id BIGINT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    current_status mount_state;
    needs_recovery BOOLEAN;
    next_generation BIGINT;
BEGIN
    SELECT mount_status,
           NOT clean_shutdown,
           generation + 1
    INTO current_status,
         needs_recovery,
         next_generation
    FROM filesystem
    WHERE filesystem_id = p_filesystem_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Filesystem % does not exist',
            p_filesystem_id;
    END IF;

    IF current_status = 'mounted' THEN
        RAISE EXCEPTION
            'Filesystem % is already mounted',
            p_filesystem_id;
    END IF;

    IF needs_recovery THEN
        UPDATE filesystem
        SET mount_status = 'needs_recovery'
        WHERE filesystem_id = p_filesystem_id;

        /*
         * Recovery is deliberately represented as a state transition here.
         * Application or filesystem-engine code would replay committed journal
         * records before exposing normal filesystem operations.
         */
    END IF;

    UPDATE filesystem
    SET mount_status = 'mounted',
        clean_shutdown = TRUE,
        generation = next_generation
    WHERE filesystem_id = p_filesystem_id;

    INSERT INTO mount_event (
        filesystem_id,
        previous_status,
        new_status,
        generation,
        recovery_required
    )
    VALUES (
        p_filesystem_id,
        current_status,
        'mounted',
        next_generation,
        needs_recovery
    );
END;
$$;

CREATE OR REPLACE FUNCTION unmount_filesystem(
    p_filesystem_id BIGINT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    current_status mount_state;
    current_generation BIGINT;
BEGIN
    SELECT mount_status, generation
    INTO current_status, current_generation
    FROM filesystem
    WHERE filesystem_id = p_filesystem_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Filesystem does not exist';
    END IF;

    IF current_status <> 'mounted' THEN
        RAISE EXCEPTION
            'Filesystem is not currently mounted';
    END IF;

    UPDATE filesystem
    SET mount_status = 'unmounted',
        clean_shutdown = TRUE
    WHERE filesystem_id = p_filesystem_id;

    INSERT INTO mount_event (
        filesystem_id,
        previous_status,
        new_status,
        generation,
        recovery_required
    )
    VALUES (
        p_filesystem_id,
        current_status,
        'unmounted',
        current_generation,
        FALSE
    );
END;
$$;

INSERT INTO filesystem (
    volume_name,
    magic,
    block_size,
    total_blocks,
    inode_limit,
    journal_capacity
)
VALUES (
    'repository-volume',
    'POSTGRES-FS-INTERNALS',
    4096,
    10000,
    2048,
    128
)
RETURNING filesystem_id;

-- Use a deterministic identifier for the demonstration volume.
UPDATE filesystem
SET root_inode = NULL
WHERE volume_name = 'repository-volume';

DO $$
DECLARE
    fs_id BIGINT;
    root_id BIGINT;
BEGIN
    SELECT filesystem_id
    INTO fs_id
    FROM filesystem
    WHERE volume_name = 'repository-volume';

    INSERT INTO inode (
        filesystem_id,
        inode_number,
        type,
        mode,
        uid,
        gid,
        parent_inode_id,
        size_bytes,
        link_count
    )
    VALUES (
        fs_id,
        1,
        'directory',
        493,
        0,
        0,
        NULL,
        0,
        2
    )
    RETURNING inode_id INTO root_id;

    UPDATE inode
    SET parent_inode_id = root_id
    WHERE inode_id = root_id;

    UPDATE filesystem
    SET root_inode = root_id
    WHERE filesystem_id = fs_id;

    INSERT INTO directory_entry (
        directory_inode_id,
        entry_name,
        target_inode_id
    )
    VALUES
        (root_id, '.', root_id),
        (root_id, '..', root_id);

    FOR i IN 0..9999 LOOP
        INSERT INTO storage_block (
            filesystem_id,
            block_number,
            is_metadata,
            allocated
        )
        VALUES (
            fs_id,
            i,
            i < 200,
            i < 200
        );
    END LOOP;
END;
$$;

SELECT mount_filesystem(filesystem_id)
FROM filesystem
WHERE volume_name = 'repository-volume';

DO $$
DECLARE
    fs_id BIGINT;
    root_id BIGINT;
    repository_id BIGINT;
    objects_id BIGINT;
    index_inode BIGINT;
    data_inode BIGINT;
    transaction_id BIGINT;
    block_number INTEGER;
BEGIN
    SELECT filesystem_id, root_inode
    INTO fs_id, root_id
    FROM filesystem
    WHERE volume_name = 'repository-volume';

    INSERT INTO inode (
        filesystem_id,
        inode_number,
        type,
        mode,
        uid,
        gid,
        parent_inode_id
    )
    VALUES (
        fs_id,
        2,
        'directory',
        493,
        1000,
        1000,
        root_id
    )
    RETURNING inode_id INTO repository_id;

    INSERT INTO directory_entry
    VALUES
        (repository_id, '.', repository_id),
        (repository_id, '..', root_id),
        (root_id, 'repository', repository_id);

    INSERT INTO inode (
        filesystem_id,
        inode_number,
        type,
        mode,
        uid,
        gid,
        parent_inode_id
    )
    VALUES (
        fs_id,
        3,
        'directory',
        493,
        1000,
        1000,
        repository_id
    )
    RETURNING inode_id INTO objects_id;

    INSERT INTO directory_entry
    VALUES
        (objects_id, '.', objects_id),
        (objects_id, '..', repository_id),
        (repository_id, 'objects', objects_id);

    INSERT INTO inode (
        filesystem_id,
        inode_number,
        type,
        mode,
        uid,
        gid,
        parent_inode_id,
        size_bytes,
        link_count
    )
    VALUES (
        fs_id,
        4,
        'file',
        420,
        1000,
        1000,
        objects_id,
        8192,
        1
    )
    RETURNING inode_id INTO index_inode;

    INSERT INTO inode (
        filesystem_id,
        inode_number,
        type,
        mode,
        uid,
        gid,
        parent_inode_id,
        size_bytes,
        link_count
    )
    VALUES (
        fs_id,
        5,
        'file',
        420,
        1000,
        1000,
        objects_id,
        16384,
        1
    )
    RETURNING inode_id INTO data_inode;

    INSERT INTO directory_entry
    VALUES
        (objects_id, '.', objects_id),
        (objects_id, '..', repository_id),
        (objects_id, 'index', index_inode),
        (objects_id, 'data', data_inode);

    /*
     * Allocate the index file's first two logical blocks.
     * The allocation map is changed before inode mappings are inserted.
     */
    FOR block_number IN 200..201 LOOP
        UPDATE storage_block
        SET allocated = TRUE
        WHERE filesystem_id = fs_id
          AND block_number = block_number;

        INSERT INTO inode_block (
            inode_id,
            logical_block_number,
            physical_block_number,
            allocation_kind
        )
        VALUES (
            index_inode,
            block_number - 200,
            block_number,
            'direct'
        );
    END LOOP;

    /*
     * The larger data file has four direct references followed by indirect
     * references. Block 202 is the indirect metadata block.
     */
    FOR block_number IN 202..206 LOOP
        UPDATE storage_block
        SET allocated = TRUE
        WHERE filesystem_id = fs_id
          AND block_number = block_number;
    END LOOP;

    INSERT INTO inode_block (
        inode_id,
        logical_block_number,
        physical_block_number,
        allocation_kind
    )
    VALUES
        (data_inode, 0, 202, 'direct'),
        (data_inode, 1, 203, 'direct'),
        (data_inode, 2, 204, 'direct'),
        (data_inode, 3, 205, 'direct'),
        (data_inode, 4, 206, 'indirect');

    INSERT INTO journal_transaction (
        filesystem_id,
        sequence_number,
        operation
    )
    VALUES (
        fs_id,
        1,
        'create repository object storage files'
    )
    RETURNING journal_transaction.transaction_id
    INTO transaction_id;

    INSERT INTO journal_inode_record (
        transaction_id,
        inode_id,
        old_size,
        new_size,
        old_link_count,
        new_link_count
    )
    VALUES
        (transaction_id, index_inode, 0, 8192, 1, 1),
        (transaction_id, data_inode, 0, 16384, 1, 1);

    INSERT INTO journal_directory_record (
        transaction_id,
        directory_inode_id,
        entry_name,
        old_target_inode_id,
        new_target_inode_id,
        operation
    )
    VALUES
        (
            transaction_id,
            objects_id,
            'index',
            NULL,
            index_inode,
            'create'
        ),
        (
            transaction_id,
            objects_id,
            'data',
            NULL,
            data_inode,
            'create'
        );

    PERFORM journal_commit(transaction_id);
END;
$$;

-- Query the inode/block relationship. The distinction between logical block
-- numbers and physical block numbers is important: an inode describes where
-- each logical portion of a file resides on the volume.
SELECT
    i.inode_number,
    i.type,
    i.size_bytes,
    ib.logical_block_number,
    ib.physical_block_number,
    ib.allocation_kind
FROM inode AS i
JOIN inode_block AS ib
    ON ib.inode_id = i.inode_id
WHERE i.filesystem_id = (
    SELECT filesystem_id
    FROM filesystem
    WHERE volume_name = 'repository-volume'
)
ORDER BY
    i.inode_number,
    ib.logical_block_number;

-- Identify physical blocks that are allocated but not referenced by an inode.
-- Such blocks represent an allocation-map leak that a filesystem checker
-- should investigate.
SELECT
    sb.block_number
FROM storage_block AS sb
WHERE sb.filesystem_id = (
    SELECT filesystem_id
    FROM filesystem
    WHERE volume_name = 'repository-volume'
)
AND sb.allocated = TRUE
AND sb.is_metadata = FALSE
AND NOT EXISTS (
    SELECT 1
    FROM inode_block AS ib
    JOIN inode AS i
        ON i.inode_id = ib.inode_id
    WHERE i.filesystem_id = sb.filesystem_id
      AND ib.physical_block_number = sb.block_number
)
ORDER BY sb.block_number;

-- Show directory name resolution.
SELECT
    parent.inode_number AS directory_inode,
    de.entry_name,
    target.inode_number AS target_inode,
    target.type AS target_type,
    target.size_bytes
FROM directory_entry AS de
JOIN inode AS parent
    ON parent.inode_id = de.directory_inode_id
JOIN inode AS target
    ON target.inode_id = de.target_inode_id
WHERE parent.filesystem_id = (
    SELECT filesystem_id
    FROM filesystem
    WHERE volume_name = 'repository-volume'
)
ORDER BY
    parent.inode_number,
    de.entry_name;

-- Examine journal state. A committed record represents a durable transaction
-- whose logical operation can participate in crash recovery.
SELECT
    jt.transaction_id,
    jt.sequence_number,
    jt.operation,
    jt.state,
    jt.started_at,
    jt.committed_at
FROM journal_transaction AS jt
WHERE jt.filesystem_id = (
    SELECT filesystem_id
    FROM filesystem
    WHERE volume_name = 'repository-volume'
)
ORDER BY jt.sequence_number;

-- Verify that regular files have enough physical mappings for their declared
-- sizes. The query intentionally treats the database as a consistency-checking
-- surface rather than trusting only application metadata.
WITH block_requirements AS (
    SELECT
        i.inode_id,
        i.inode_number,
        ceil(
            i.size_bytes::numeric / f.block_size
        )::integer AS required_blocks,
        count(ib.physical_block_number)::integer AS mapped_blocks
    FROM inode AS i
    JOIN filesystem AS f
        ON f.filesystem_id = i.filesystem_id
    LEFT JOIN inode_block AS ib
        ON ib.inode_id = i.inode_id
    WHERE i.type = 'file'
    GROUP BY
        i.inode_id,
        i.inode_number,
        i.size_bytes,
        f.block_size
)
SELECT
    inode_number,
    required_blocks,
    mapped_blocks,
    CASE
        WHEN mapped_blocks >= required_blocks
        THEN 'consistent'
        ELSE 'missing block mappings'
    END AS allocation_status
FROM block_requirements
ORDER BY inode_number;

-- Clean shutdown records the mount lifecycle boundary.
SELECT unmount_filesystem(filesystem_id)
FROM filesystem
WHERE volume_name = 'repository-volume';

SELECT
    volume_name,
    mount_status,
    clean_shutdown,
    generation
FROM filesystem
WHERE volume_name = 'repository-volume';

SELECT
    new_status,
    generation,
    recovery_required,
    event_time
FROM mount_event
WHERE filesystem_id = (
    SELECT filesystem_id
    FROM filesystem
    WHERE volume_name = 'repository-volume'
)
ORDER BY event_time;
