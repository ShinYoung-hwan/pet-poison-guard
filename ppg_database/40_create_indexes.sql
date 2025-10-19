-- Create ivfflat index for rec_embeds.embedding after data load.
-- This script is intended to be placed in /docker-entrypoint-initdb.d/ so it runs
-- after the table creation and data loading scripts (10_*, 20_*).

-- Increase maintenance_work_mem for this session to speed up index build.
-- Note: we use a session-level SET here because CREATE INDEX CONCURRENTLY
-- must be run outside of a transaction block. When run via psql -c or the
-- docker-entrypoint-initdb.d mechanism, this will execute in a session.

-- Tune `lists` according to dataset size. Example uses 1000 as a starting point.

-- Use CONCURRENTLY in production to avoid locking writes/reads. If your init
-- environment wraps SQL in a transaction, CONCURRENTLY will fail; in that case
-- use the non-concurrent statement (commented below) after ensuring it's safe.

SET maintenance_work_mem = '1GB';

-- Recommended (concurrent, non-blocking):
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_rec_embeds_embedding_ivfflat
    ON rec_embeds USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 1000);

-- If CONCURRENTLY is not allowed in your init environment, use the following
-- (will block writes during index creation):
-- CREATE INDEX IF NOT EXISTS idx_rec_embeds_embedding_ivfflat ON rec_embeds
--     USING ivfflat (embedding vector_cosine_ops) WITH (lists = 1000);

-- Reset to default if desired; server will continue using the prior setting
-- for new sessions, but we reset here just to be explicit.
RESET maintenance_work_mem;
