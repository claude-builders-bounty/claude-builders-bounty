# Next.js SQLite SaaS CLAUDE.md Template

This folder contains an opinionated `CLAUDE.md` for a greenfield Next.js 15 App Router SaaS backed by SQLite, Drizzle ORM, and either `better-sqlite3` or Turso.

## Setup

1. Create a new Next.js 15 TypeScript project.
2. Copy `nextjs-sqlite-saas/CLAUDE.md` into the project root as `CLAUDE.md`.
3. Start Claude Code in the project root and ask it to implement a dashboard feature using the project contract.

## Validation Notes

The template is written so Claude Code can infer:

- project structure and ownership boundaries
- naming conventions for routes, components, actions, queries, and tables
- SQLite migration rules and safety constraints
- expected development commands
- patterns to follow and anti-patterns to reject

No project-specific names are required before use; the placeholder `<domain>` folder is the only application-specific slot.
