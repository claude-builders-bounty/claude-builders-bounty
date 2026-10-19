# Next.js 15 + SQLite SaaS — `CLAUDE.md` template

An opinionated `CLAUDE.md` for a SaaS built on **Next.js 15 App Router + SQLite** (`better-sqlite3` locally, Turso in production).
Drop it in a greenfield project and Claude Code starts with the same context a senior teammate would have: commands, layout, naming, migration discipline, and the list of things we deliberately do not do.

## Use it

```bash
cp CLAUDE.md /path/to/your-saas/CLAUDE.md
```

That is the whole installation. No dependencies, no scripts, no imports.

Then, in the project:

```bash
claude          # start Claude Code
/context        # confirm CLAUDE.md is listed under "Memory files"
```

If you prefer the hidden location, `./.claude/CLAUDE.md` works identically. Keep only one of the two — two copies drift.

## What it assumes

| Assumption | If your project differs |
|---|---|
| Next.js 15, App Router | Update §1 and §2; the rest still applies |
| `better-sqlite3` locally, Turso in prod | If Turso-only, drop the driver line in §1 and the WAL note in §6 |
| Tailwind CSS | Delete the styling row in §1; nothing else references it |
| `zod` for validation | Swap for Valibot/TypeBox; keep the "validate at the boundary" rule |
| `vitest` | Point §4 and §8 at your runner; keep the "real temp database" rule |
| No ORM | If you already use Drizzle/Prisma, delete §10's first bullet and rewrite §5 for your migration tool |

## Why it is written this way

- **Under 200 lines.** Claude Code's own guidance targets <200 lines per `CLAUDE.md`; longer files cost context and reduce adherence. Anything that only matters for one folder belongs in `.claude/rules/` with `paths:` frontmatter, not here.
- **Every rule carries a `Why:`.** A rule without a reason gets ignored the first time it is inconvenient. With the reason attached, Claude can tell a genuine exception from a violation, and reviewers can too.
- **Commands are copy-pasteable and match CI** (`build` → `tsc --noEmit` → `test`). If the file says a command, that command is expected to exist in `package.json`.
- **"What we don't do" is a section, not an afterthought.** Most of the value is in the refusals: no ORM, no `any`, no client-side DB, no invented endpoints.

## Verification performed

Created a fresh project with `create-next-app` (TypeScript, App Router, `src/`, Tailwind), pinned **Next 15**, added `better-sqlite3`, wrote the migration runner described in §5, and confirmed:

- `npm run build` passes with this `CLAUDE.md` in the project root
- `npx tsc --noEmit` passes
- `npm run db:migrate` applies `0001_init.sql`, records the version in `_migrations`, and a second run is a no-op (idempotent)

See `VERIFICATION.md` for the exact commands and output.

## Extending it

Keep the root file short and push detail into path-scoped rules, which only load when Claude touches matching files:

```markdown
<!-- .claude/rules/sql-migrations.md -->
---
paths:
  - "src/db/**/*.sql"
  - "src/db/*.ts"
---

# Migration specifics
- ...
```

## License

MIT — same as the bounty board repository.
