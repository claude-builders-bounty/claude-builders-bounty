# CLAUDE.md Template for Next.js + SQLite SaaS

A production-ready, opinionated [CLAUDE.md](https://docs.anthropic.com/en/docs/claude-code) template for greenfield Next.js 15 App Router + SQLite SaaS projects.

## Usage

1. Create a new Next.js project:

```bash
pnpm create next-app@latest my-saas --typescript --tailwind --app
cd my-saas
pnpm add better-sqlite3 @types/better-sqlite3 next-auth@beta
```

2. Copy `CLAUDE.md` to the root of your new project:

```bash
cp /path/to/claude-builders-bounty/CLAUDE.md ./CLAUDE.md
```

3. Set up the folder structure:

```bash
mkdir -p lib/db/queries migrations components/ui components/forms components/layouts config tests/{unit,integration,e2e}
```

4. Create `lib/db/client.ts`:

```typescript
import Database from 'better-sqlite3'

const db = new Database(process.env.DATABASE_URL || './data.db')
db.pragma('journal_mode = WAL')
db.pragma('foreign_keys = ON')

export default db
```

5. Start Claude Code in your project — it will read `CLAUDE.md` and understand the conventions without asking clarifying questions.

## What makes this opinionated

This template makes deliberate technical choices and explains why:

- **No ORM** — raw SQL via better-sqlite3 is the source of truth
- **Server Components by default** — client components are the exception, not the rule
- **Co-located loading & error boundaries** — per-route Suspense, not global
- **Manual migrations** — no auto-migrate in CI
- **No client state library** — Server Actions + URL state cover most needs

Every rule includes reasoning so you can decide whether to override it.

## Sections

- [x] Stack & versions
- [x] Folder structure
- [x] Dev commands
- [x] Naming conventions (files, variables, routes)
- [x] SQL / migration conventions
- [x] Component patterns (server vs client, loading, errors)
- [x] Data access patterns (Server Actions, transactions)
- [x] What we don't do (and why) — 10 anti-patterns with reasoning

## Bounty Submission

This is a submission for [Bounty #2](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2) in the claude-builders-bounty repository.
