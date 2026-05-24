# Next.js 15 + SQLite SaaS CLAUDE.md Template

Opinionated `CLAUDE.md` for a greenfield SaaS app using Next.js 15 App Router and SQLite (`better-sqlite3` or Turso/libSQL).

## Setup in 3 steps

1. Copy `CLAUDE.md` into the root of a Next.js 15 + SQLite SaaS project.
2. Adjust only the package-manager command names if the project does not use npm.
3. Start Claude Code from the project root so it loads the file before making changes.

## What it covers

- Stack and versions
- Folder structure
- SQL and migration conventions
- Component/server-action patterns
- Auth, tenancy, and billing rules
- Testing gates
- Anti-patterns and the reason behind each rule

## Greenfield smoke test

Use this prompt after copying the file into a new project:

```text
Read CLAUDE.md and propose the first migration, route structure, and server-action pattern for a tiny B2B todo SaaS. Do not write files yet.
```

Expected behavior: Claude should propose a tenant-scoped schema, App Router folders, server actions, and validation steps without asking what stack or migration style to use.
