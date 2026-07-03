-- 20260315120000_create_organizations.sql
-- Org-scoped root table for tenant references.
--
-- Migration best practices (see CLAUDE.md SQL & Migration Conventions):
-- 1. Append-only — never edit after merge; fix forward with a new file.
-- 2. One concern per file — this file creates only the organizations table.
-- 3. Idempotent DDL — IF NOT EXISTS so dev re-runs are safe.
-- 4. Soft deletes via deleted_at — queries must filter deleted_at IS NULL.

CREATE TABLE IF NOT EXISTS organizations (
  id         TEXT PRIMARY KEY NOT NULL,
  slug       TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  deleted_at TEXT
);
