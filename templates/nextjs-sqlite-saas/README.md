# Next.js 15 + SQLite SaaS CLAUDE.md Template

This template is an opinionated `CLAUDE.md` for greenfield SaaS apps using Next.js 15 App Router and SQLite through `better-sqlite3` or Turso/libSQL.

Setup:

1. Copy `CLAUDE.md` into the root of a new Next.js + SQLite project.
2. Add the package scripts listed in the template if the project does not already have equivalents.
3. Ask Claude Code to implement a small feature and verify it follows the route -> action -> service -> query flow.

The template intentionally avoids ORM-first advice and generic folder rules. It is designed to make Claude Code produce predictable SaaS code with explicit SQL migrations, server-side permission checks, and small client boundaries.

