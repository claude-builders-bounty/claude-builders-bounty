# CLAUDE.md — Next.js 15 + SQLite SaaS

An opinionated, production-ready [`CLAUDE.md`](./CLAUDE.md) for a SaaS project on
**Next.js 15 (App Router) + SQLite** (better-sqlite3 locally, Turso when hosted).
Drop it at the root of a greenfield project and Claude Code has the full context —
stack, structure, DB/migration rules, component patterns, and the anti-patterns to
avoid — without asking you to re-explain any of it.

Every rule states *why*, so it guides judgment on situations the file doesn't
enumerate, rather than reading as arbitrary style policing.

## Use it (1 step)

Copy [`CLAUDE.md`](./CLAUDE.md) to the root of your Next.js + SQLite repo. Done —
Claude Code reads it automatically on every session in that project.

## What it covers

- **Stack & versions** — with the reasoning for each choice, and what *not* to add
- **Folder structure** — App Router layout, where logic lives, what `api/` is (and isn't) for
- **Naming conventions** — files, tables, columns, repos, zod schemas, env
- **SQL / migration conventions** — forward-only migrations, parameterized SQL,
  epoch-millis timestamps, integer money, the pragmas SQLite needs
- **Component patterns** — Server Components by default, Server Actions for mutations
- **Dev commands** and a pre-merge checklist
- **What we don't do (and why)** — the anti-patterns, each with a reason

## Proof it's concrete, not aspirational

[`example/`](./example) is a minimal greenfield scaffold that follows the template
to the letter — DB singleton with the required pragmas, a forward-only migration
runner (`_migrations` table, per-file transaction), a hand-written repository with
parameterized SQL, zod validation, a Server Action in the canonical
`requireUser → parse → repo → revalidate` shape, and a thin Server Component page.

The database conventions are **verified by execution** (see below), so the rules in
`CLAUDE.md` are known to be implementable exactly as written.

### Verification

Ran against `node:sqlite` using the example's real migration file:

```
✓ migration 0001_init.sql executed
✓ tables: sessions, subscriptions, users
✓ insert + defaults: created_at = 1782888542000  (epoch-millis, as specified)
✓ FK enforcement rejects orphan session: true      (foreign_keys = ON works)
✓ ON DELETE CASCADE removed child session: true
```

This confirms the non-obvious rules — `foreign_keys = ON` (SQLite defaults it
*off*), `INTEGER` epoch-millis timestamps, and `ON DELETE CASCADE` — behave as the
template claims.

## License

MIT
