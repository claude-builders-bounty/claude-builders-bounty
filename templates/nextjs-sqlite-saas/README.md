# Next.js 15 + SQLite SaaS CLAUDE.md Template

Use `CLAUDE.md` at the root of a greenfield Next.js 15 App Router SaaS project
that uses SQLite through `better-sqlite3` or Turso/libSQL.

## Setup

1. Copy `CLAUDE.md` into the project root.
2. Confirm `package.json` has equivalent scripts for `dev`, `build`, `typecheck`,
   `db:generate`, and `db:migrate`.
3. Start Claude Code in the project root.

## Greenfield Test Prompt

After copying the template into a fresh project, this prompt should be answerable
without clarifying questions:

```text
Create the organization settings page. Use the project conventions, add any
query helper you need, keep SQLite access server-only, and tell me the validation
commands to run.
```

Expected behavior: Claude Code should use App Router Server Components, a Server
Action for the form mutation, scoped organization queries, and the validation
commands listed in `CLAUDE.md`.
