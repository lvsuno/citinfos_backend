-- This script will update all foreign key constraints in your PostgreSQL database to use ON DELETE CASCADE
-- for all constraints that should be CASCADE according to your Django models.
-- Run this after all migrations are applied and the schema is up to date.

-- Find all constraints that are not CASCADE but should be
SELECT
  'ALTER TABLE ' || nsp.nspname || '.' || conrelid::regclass || ' DROP CONSTRAINT ' || conname || ';' || E'\n' ||
  'ALTER TABLE ' || nsp.nspname || '.' || conrelid::regclass || ' ADD CONSTRAINT ' || conname ||
  ' FOREIGN KEY (' || pg_get_constraintdef(c.oid) || ') ON DELETE CASCADE;'
FROM pg_constraint c
JOIN pg_namespace nsp ON nsp.oid = c.connamespace
WHERE c.contype = 'f'  -- foreign key constraints only
  AND c.confdeltype != 'c'  -- not already CASCADE (c = cascade, r = restrict, n = no action, a = set null, d = set default)
  AND nsp.nspname NOT IN ('information_schema', 'pg_catalog', 'pg_toast')  -- exclude system schemas
  AND c.conname NOT LIKE 'django%';  -- exclude Django-managed constraints if needed