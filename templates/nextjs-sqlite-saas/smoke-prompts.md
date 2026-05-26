# Next.js SQLite CLAUDE.md Smoke Prompts

Use these prompts after copying `templates/nextjs-sqlite-saas/CLAUDE.md` into a greenfield Next.js App Router + SQLite SaaS repository as `CLAUDE.md`.

## Prompt 1: Workspace Member Access Check

> Add a `workspace_members` table, a schema migration, and a helper query for checking whether the current user has access to a specific workspace.

**Expected behavior from Claude Code**:
- Creates or updates the schema in `db/schema.ts`.
- Generates migrations under `db/migrations/` using Drizzle commands (`pnpm db:generate`).
- Restricts membership checks to server-side components/actions and confirms ownership checks.
- Uses integer data types for SQLite compatibility (like storing foreign keys and booleans).

## Prompt 2: Stripe Billing Webhook Integration

> Create a route handler for handling Stripe billing webhooks (such as subscription updates and cancellations).

**Expected behavior from Claude Code**:
- Creates `app/api/webhooks/stripe/route.ts`.
- Verifies webhook signatures using the Stripe SDK and webhook secret.
- Stores processed event IDs in SQLite to enforce idempotency.
- Pulls pricing/plan configurations from environment variables rather than hardcoding.
- Performs all calculations on the server side.

## Prompt 3: Invoices Dashboard Table

> Create a dashboard page layout listing recent invoices for the currently authenticated workspace.

**Expected behavior from Claude Code**:
- Places the page in `app/(dashboard)/invoices/page.tsx` or similar.
- Restricts access using server-side auth check.
- Directly calls SQLite/Drizzle queries in the React Server Component rather than calling an internal `/api/invoices` endpoint.
- Enforces strict tenant isolation by matching the workspace ID.
