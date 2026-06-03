# CLAUDE.md — Next.js 15 SaaS + SQLite Template

An opinionated, production-ready CLAUDE.md for Next.js 15 (App Router) SaaS projects using SQLite (better-sqlite3 or Turso).

## What's included

- **Stack & versions** — exact pinned versions for Next.js 15, React 19, TypeScript 5.7, Drizzle ORM, better-sqlite3, Tailwind 4
- **Folder structure** — full tree with `/app`, `/components`, `/lib`, `/db`, `/actions`
- **DB migration rules** — Drizzle schema-first, no raw SQL, migration files generated, never edited
- **Component patterns** — server-first, Server Actions for mutations, `'use client'` only at leaves
- **Anti-patterns to avoid** — "What we don't do (and why)" section
- **Dev commands** — `pnpm dev`, `pnpm db:push`, `pnpm db:studio`, `pnpm test`, `pnpm build`
- **Naming conventions** — kebab-case files, PascalCase components, snake_case DB columns

## Why this is opinionated

Every rule has a reason. Examples:
- **"Always use Server Actions for mutations"** — eliminates need for API routes, smaller bundle, type-safe end-to-end
- **"Never edit migration files after they're committed"** — migrations are immutable history; modify schema → generate new migration
- **"Use `cn()` helper for className merging"** — handles Tailwind conflicts deterministically
- **"All DB queries go through `/db/queries/`"** — no `db.execute()` in components; queries are typed, testable, swappable

## Tested

Created a new Next.js 15 project, pasted this CLAUDE.md, ran Claude Code — no clarifying questions, all suggestions aligned with conventions.

## Installation

```bash
# Copy to your project root
cp CLAUDE.md /path/to/your-project/CLAUDE.md

# Verify Claude Code picks it up
cd /path/to/your-project && claude
```

## Sections

1. **Stack & Versions** — pinned dependencies
2. **Project Structure** — folder tree
3. **Naming Conventions** — file/component/column names
4. **Database Conventions** — Drizzle schema, migrations, queries
5. **Component Patterns** — server-first, Server Actions, client boundaries
6. **Dev Commands** — all the scripts
7. **Anti-Patterns** — what we don't do (and why)
8. **Testing** — Vitest + Playwright conventions
9. **Deployment** — Vercel + Turso for production
10. **PR Review Checklist** — what to verify before submitting

## File

Single file: `CLAUDE.md` (4.8 KB, 200 lines)

## License

MIT
