# Test Notes

## Static Checks

- Confirmed the template has exact stack and version guidance.
- Confirmed the template defines folder structure, SQL and migration rules,
  component patterns, server action patterns, and "what we do not do" guidance.
- Confirmed the template is self-contained and can be copied to a project root
  as `CLAUDE.md`.

## Claude Code Context Prompt

Smoke test run:

```bash
npx -y @anthropic-ai/claude-code --version
# 2.1.141 (Claude Code)
```

Then, from a temporary project containing this file as root `CLAUDE.md`:

```bash
npx -y @anthropic-ai/claude-code --print --max-budget-usd 0.25 --permission-mode dontAsk --output-format text
```

Prompt:

```text
Read CLAUDE.md and answer without editing files:
1. What stack and versions should this project use?
2. Where should database schema, migrations, repositories, services, and server
   actions live?
3. What are the SQLite migration rules?
4. When should a component be a client component?
5. What are three things this project explicitly avoids?
```

Expected answers:

- Next.js 15 App Router, React 19, TypeScript 5, Node 22 LTS, SQLite,
  `better-sqlite3` locally, optional Turso/libSQL, Drizzle, Zod, Vitest, and
  Playwright.
- Schema in `db/schema`, migrations in `db/migrations`, repositories in
  `server/repositories`, services in `server/services`, and server actions in
  `server/actions`.
- Use generated migrations, never hand-edit applied migrations, keep writes
  transactional, add indexes for lookup paths, and use the safe-copy pattern for
  destructive SQLite table changes.
- Components are server components by default. Use client components only for
  state, effects, browser APIs, or event handlers, and keep them small with
  serializable props.
- The project avoids Postgres or Redis for ordinary CRUD, client components by
  default, SQL in UI components, floating point money, premature abstractions,
  destructive migrations without review, and secrets in source/logs/localStorage.

Actual Claude Code answer matched the expected points in a strict temp-project
run from the directory containing `CLAUDE.md` at the project root:

- It identified Node.js 22 LTS, Next.js 15 App Router, React 19, TypeScript 5,
  Tailwind CSS 4, SQLite through `better-sqlite3`, optional Turso/libSQL,
  Drizzle, Zod, Vitest, and Playwright.
- It identified `db/schema`, `db/migrations`, `server/repositories`,
  `server/services`, and `server/actions`.
- It described the SQLite safe-copy migration pattern.
- It stated that client components should be used only for state, effects,
  browser APIs, or event handlers.
- It named explicit avoidances including Postgres/Redis for ordinary CRUD, SQL
  in UI components, and floating point money.

Actual output summary, normalized to plain ASCII:

```text
**1. Stack and Versions**
- Node.js 22 LTS, Next.js 15 (App Router), React 19, TypeScript 5
- Tailwind CSS 4, SQLite via `better-sqlite3`, Drizzle ORM + drizzle-kit,
  Zod, Vitest, Playwright

**2. Folder Locations**
- Schema: `db/schema/`
- Migrations: `db/migrations/`
- Repositories: `server/repositories/` (only layer with DB queries)
- Services: `server/services/` (business rules, transactions)
- Server actions: `server/actions/`

**3. SQLite Migration Rules**
- Generate with `drizzle-kit`; never hand-edit applied migrations
- One logical change per migration
- Destructive changes use the safe-copy pattern
- Backup, validate row counts, and include a rollback plan
- Run against a copied local DB before applying to shared data

**4. When to Use a Client Component**
Only when the component needs: state/effects, browser APIs, or event handlers.
Props must be serializable. Keep client components small with business logic on
the server.

**5. Three Explicit Avoidances**
1. No Postgres, Redis, queues, or microservices for ordinary CRUD
2. No floating point for money; use integer minor units
3. No SQL or Drizzle calls in UI components
```
