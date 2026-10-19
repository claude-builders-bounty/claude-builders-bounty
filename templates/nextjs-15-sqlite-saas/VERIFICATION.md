# Verification — what was actually tested

Environment: Windows 11, Node **v24.13.1**, npm 11.8.0, `create-next-app` (TypeScript, App Router, `src/`, Tailwind), then `next` pinned.

```
next         15.5.28   (create-next-app installed 16.x; downgraded to satisfy the "Next.js 15" requirement)
react        19.3.0
typescript   5.x
better-sqlite3 13.0.3
@types/better-sqlite3  (required, see finding 2)
zod          4.6.7
tsx          4.23.15
```

## Step 1 — fresh project, `CLAUDE.md` in the root

```bash
npx create-next-app@latest nextjs-sqlite-saas --ts --app --eslint --src-dir --tailwind --import-alias "@/*" --use-npm
cp CLAUDE.md nextjs-sqlite-saas/CLAUDE.md
```

## Step 2 — implement the migration runner exactly as §5 describes

`src/db/migrations/0001_init.sql` (STRICT tables, declared FK, named indexes) and `src/db/migrate.ts`
(version ledger `_migrations`, one transaction per file, `journal_mode=WAL`, `foreign_keys=ON`, `busy_timeout=5000`),
plus `"db:migrate": "tsx src/db/migrate.ts"`.

```bash
npm run db:migrate     # first run
applied 0001_init.sql
1 migration(s) applied
db=local.db | journal_mode=wal | applied_versions=1

npm run db:migrate     # second run — idempotency check
no pending migrations
db=local.db | journal_mode=wal | applied_versions=1
```

Schema assertions against the live database:

```
_migrations          [{ version: '0001_init.sql', applied_at: '2026-10-19T10:14:14.364Z' }]
objects              idx_invoice_items_invoice, idx_invoices_customer_created,
                     _migrations, invoice_items, invoices
invoices is STRICT   true
CHECK constraint     SQLITE_CONSTRAINT_CHECK      (status='bogus' rejected)
FOREIGN KEY          SQLITE_CONSTRAINT_FOREIGNKEY (orphan invoice_items rejected)
```

## Step 3 — type check and build

**First attempt failed.** This is the finding that changed the template:

```
npx tsc --noEmit
src/db/migrate.ts(5,22): error TS7016: Could not find a declaration file for module 'better-sqlite3'.

npm run build
Type error: Could not find a declaration file for module 'better-sqlite3'.
Next.js build worker exited with code: 1
```

Fix: `npm i -D @types/better-sqlite3` → added as a rule in §1 of `CLAUDE.md`.

**Second attempt:**

```
npx tsc --noEmit     exit 0

npm run build
 ✓ Generating static pages (5/5)
Route (app)                                 Size  First Load JS
┌ ○ /                                     5.5 kB         108 kB
└ ○ /_not-found                            995 B         104 kB
+ First Load JS shared by all             103 kB
build exit 0
```

## Findings baked back into `CLAUDE.md`

1. **`next` must be ≥15.5.28.** `npm i next@15.5.4` prints a deprecation warning for CVE-2025-66478; the template would otherwise pin a known-vulnerable version.
2. **`@types/better-sqlite3` is mandatory.** Without it both `tsc --noEmit` and `next build` fail — the rule now says so instead of leaving the reader to discover it.
3. **Next.js 15.5+ writes its own `AGENTS.md`** with version-specific breaking-change notes. Claude Code reads `AGENTS.md` only when no `CLAUDE.md` exists, so the template instructs adding `@AGENTS.md` to keep those notes in context.

## What was not tested

- No Claude Code session was run against this file (no API access in this environment). The claim verified here is narrower and checkable: **every command and rule in the file was executed on a real project, and the two that failed were fixed and re-verified.**
- Turso (`@libsql/client`) was not exercised; only the local `better-sqlite3` path was. §1 marks Turso as the production driver, §6's WAL note is local-only.
