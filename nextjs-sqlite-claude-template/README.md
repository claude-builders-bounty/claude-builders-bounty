# Next.js SQLite CLAUDE.md Template

This directory contains an opinionated `CLAUDE.md` for a production-ready SaaS application built with:

- Next.js 15 App Router
- TypeScript
- React Server Components
- SQLite via `better-sqlite3` or Turso/libSQL

## Use

Copy the template into the root of a greenfield project:

```bash
cp nextjs-sqlite-claude-template/CLAUDE.md /path/to/your-saas/CLAUDE.md
```

Then open Claude Code in that project. The file gives Claude rules for project structure, naming, migrations, query boundaries, Server Components, Server Actions, auth, testing, and security.

## Why this is opinionated

The template intentionally chooses boring defaults:

- Server Components by default to reduce client JavaScript and avoid secret leakage.
- Raw SQL isolated in `db/` so pages stay testable.
- Append-only migrations because SQLite schema changes need discipline.
- Zod at external boundaries because SaaS apps fail at edges.
- No Prisma by default because small SQLite SaaS apps do not need the extra migration and runtime complexity unless already chosen.

## Validation performed

See `TEST_NOTES.md` for the checklist used to validate the template against the bounty acceptance criteria.
