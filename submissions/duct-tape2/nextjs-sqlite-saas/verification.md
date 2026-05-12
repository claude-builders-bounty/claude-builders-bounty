# Verification

This submission was checked against the bounty requirements for an opinionated Next.js 15 App Router + SQLite SaaS `CLAUDE.md`.

## Acceptance checklist

- Covers project structure, naming conventions, and DB migration rules.
- Includes dev commands, patterns to follow, and anti-patterns to avoid.
- Gives every rule a reason.
- Is specific to greenfield Next.js 15 App Router + SQLite SaaS projects.
- Explains when to use `better-sqlite3` versus Turso/libSQL.
- Keeps README setup instructions to 3 steps.

## Context questions

After copying `CLAUDE.md` into a greenfield project root, Claude Code should answer these without extra clarification:

### 1. Where should a `users` table migration go?

Expected answer: add the schema to `db/schema.ts`, generate an append-only migration under `db/migrations/`, and test both a fresh database and an upgraded database. The migration should use SQL-native `snake_case` column names and should not rewrite old migrations.

### 2. When should I use a Server Action instead of a Route Handler?

Expected answer: use a Server Action for first-party dashboard forms and mutations. Use a Route Handler for public APIs, webhooks, third-party callbacks, and non-browser clients because those need explicit HTTP methods, status codes, and signature verification.

### 3. What are five SQLite SaaS anti-patterns to avoid?

Expected answer: avoid local SQLite on ephemeral serverless storage, schema push against production, manual production database edits, unscoped tenant queries, and marking every component `use client`.

### 4. Where should a new billing feature live?

Expected answer: put billing-specific actions, queries, schemas, and components under `features/billing/`; put webhook endpoints under `app/api/webhooks/`; put shared payment/auth helpers in `lib/`; keep database tables and migrations under `db/`.

## Local checks

Run before submitting:

```bash
git diff --check
```

Also inspect the submission files for hidden Unicode, BOM, NBSP, CRLF, and non-ASCII characters.
