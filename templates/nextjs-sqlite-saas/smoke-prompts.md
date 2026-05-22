# Next.js SQLite CLAUDE.md Smoke Prompts

Use these prompts after copying templates/nextjs-sqlite-saas/CLAUDE.md into a greenfield Next.js App Router + SQLite SaaS repository as CLAUDE.md.

## Prompt 1

Add a workspace_members table, migration, and helper query for checking whether the current user can access a workspace.

Expected behavior from Claude Code:

- Places schema and migration work under the database layer.
- Uses a migration instead of editing prior migrations.
- Includes workspace/account ownership checks.
- Adds a focused SQL-backed test or explains the exact missing test harness.

## Prompt 2

Add a billing webhook route for subscription updates.

Expected behavior from Claude Code:

- Verifies webhook signatures.
- Stores processed event IDs for idempotency.
- Keeps pricing IDs in typed server config or environment variables.
- Avoids trusting client-provided plan names or prices.

## Prompt 3

Add a dashboard table listing invoices for the signed-in workspace.

Expected behavior from Claude Code:

- Uses server-side authorization before reading tenant data.
- Keeps large lists paginated or query-limited.
- Uses existing UI components before adding new primitives.
- Keeps client state limited to UI state.
