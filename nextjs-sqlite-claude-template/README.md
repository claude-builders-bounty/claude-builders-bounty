# Next.js 15 + SQLite SaaS CLAUDE.md Template

This bounty submission provides an opinionated `CLAUDE.md` that can be pasted
into the root of a greenfield Next.js 15 App Router + SQLite SaaS project.

## What it covers

- Stack and version assumptions
- Folder structure
- Server vs Client Component rules
- SQLite connection, schema, and migration conventions
- Auth and tenant authorization rules
- Server Actions and route handler patterns
- Naming conventions
- Dev commands
- Patterns to follow and anti-patterns to avoid

## Validation

The template was reviewed against a standard greenfield SaaS shape:

- Next.js 15 App Router
- TypeScript strict mode
- SQLite via `better-sqlite3`, Drizzle, or Turso
- Server Actions for forms
- Organization-scoped SaaS authorization

It is designed to answer the common context questions Claude Code otherwise asks
before editing a new project: where code belongs, which layer owns data access,
how migrations work, and how tenant boundaries are enforced.

