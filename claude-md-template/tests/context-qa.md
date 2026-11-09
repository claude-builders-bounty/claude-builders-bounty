# Context Q&A — does the template answer a fresh session's questions?

The issue's test criterion is: paste the CLAUDE.md into a new project and
confirm Claude Code understands the context without asking clarifying
questions. The ten questions below are the ones a fresh session would
otherwise have to ask before writing code. Each is answered verbatim by
the template, at the location cited — no project-specific knowledge is
needed from the human.

| # | Question a fresh session would ask | Answered in CLAUDE.md |
|---|---|---|
| 1 | Which database driver, and where does the connection live? | Stack & versions (better-sqlite3 11.x); DB rule 1 (`src/lib/db/index.ts`, server-only singleton) |
| 2 | I need to add a column to `users`. How? | DB rule 2: new `NNNN_name.sql` migration; never edit an applied migration |
| 3 | What command applies migrations? Typechecks? Runs tests? | Dev commands: `npm run db:migrate`, `npm run typecheck`, `npm run test` |
| 4 | Where does the code for a new billing feature go? | Folder structure + Working in this repo: `src/features/billing/` with `actions.ts` + `queries.ts` |
| 5 | Can I fetch this data in `useEffect`? | What we don't do: no — request waterfalls, bypasses `queries.ts`; reads belong in Server Components |
| 6 | Can this route run on the Edge runtime? | DB rule 7: no — Node runtime only, native driver |
| 7 | Sessions: JWT or database-backed? | Component & data patterns: database-backed, revocable, httpOnly cookie |
| 8 | How do I name a table, a foreign key, a timestamp column? | Naming conventions: snake_case plural tables, `<singular>_id`, `created_at`/`updated_at` as INTEGER unix ms |
| 9 | Can I use Prisma to move faster? | DB rule 5 + What we don't do: no ORM; migration SQL is the schema truth |
| 10 | Two writes must succeed or fail together. How? | DB rule 6: one `db.transaction(...)` |
| 11 | How is money stored? | What we don't do: INTEGER cents, format at display only |
| 12 | Before I say I'm done, what must pass? | Working in this repo: typecheck + tests, migration for schema changes |

## Honest scope note

This answer key plus the automated checks in `verify_template.py` and
the greenfield run in `greenfield-test-report.md` are the evidence this
build provides. A literal interactive Claude Code session against the
scaffold could not be run from the build environment (no Claude Code
CLI installed there), so the five-minute manual confirmation is:

1. `cd` into the scaffold, open Claude Code.
2. Ask questions 1, 2, 6, and 7 from the table.
3. Expected: direct answers matching the cited rules, with no
   clarifying questions and no invented conventions.
