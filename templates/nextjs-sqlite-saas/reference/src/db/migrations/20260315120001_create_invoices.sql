-- 20260315120001_create_invoices.sql
-- Org-scoped invoices for billing.
--
-- Migration best practices (see CLAUDE.md SQL & Migration Conventions):
-- 1. FK to organizations(id) enforces tenant boundary at the schema level.
-- 2. CHECK constraints validate status enum and non-negative amounts in SQL.
-- 3. Partial index (WHERE deleted_at IS NULL) keeps list queries fast.
-- 4. Apply via `pnpm db:migrate` — migrations never run on `pnpm dev`.

CREATE TABLE IF NOT EXISTS invoices (
  id           TEXT PRIMARY KEY NOT NULL,
  org_id       TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  amount_cents INTEGER NOT NULL CHECK (amount_cents >= 0),
  status       TEXT NOT NULL DEFAULT 'draft'
               CHECK (status IN ('draft', 'sent', 'paid', 'void')),
  created_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  updated_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  deleted_at   TEXT
);

CREATE INDEX IF NOT EXISTS idx_invoices_org_created
  ON invoices (org_id, created_at DESC)
  WHERE deleted_at IS NULL;
