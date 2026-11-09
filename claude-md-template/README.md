# CLAUDE.md template — Next.js 15 + SQLite SaaS

An opinionated, production-ready `CLAUDE.md` for a SaaS project built
with Next.js 15 (App Router) and SQLite via `better-sqlite3`. Drop it
into a greenfield project root as-is: stack pins, folder structure,
naming conventions, migration law, dev commands, component patterns,
and a "What we don't do" list where **every rule carries its reason**.

## Setup (3 steps)

1. Create the project: `npx create-next-app@15 my-app --typescript
   --tailwind --eslint --app --src-dir --use-npm`.
2. Copy this folder's `CLAUDE.md` into the project root. Nothing to
   fill in, no placeholders.
3. Add the `typecheck` script (`"typecheck": "tsc --noEmit"`) and,
   when the first schema change lands, the `db:migrate` / `db:seed`
   scripts the template names. Done — Claude Code now works to these
   conventions.

## What's inside the template

- **Stack & versions** — Node 20, Next.js 15.x, React 19, TypeScript
  strict, better-sqlite3 11.x, zod, Vitest, Tailwind 4; SQLite file as
  the production database, with libSQL/Turso as the single documented
  switch point if the app ever outgrows one instance.
- **Folder structure** — routes as wiring only; one folder per feature
  under `src/features/` with `actions.ts` (writes) and `queries.ts`
  (reads); one DB module at `src/lib/db/index.ts`.
- **Naming conventions** — files, exports, actions/queries, tables,
  foreign keys, booleans, timestamps.
- **Database & migration rules** — append-only numbered SQL migrations
  (never edit an applied one), single server-only connection with WAL
  and foreign keys on, prepared statements only, transactions for
  multi-step writes, no ORM, Node-runtime-only DB access, no N+1.
- **Component & data patterns** — Server Components by default, Server
  Actions with auth + zod first, database-backed revocable sessions,
  validated env.
- **What we don't do (and why)** — 10 anti-patterns, each with its
  reason: no editing migrations, no Edge/middleware DB access, no
  string-built SQL, no ORM, no JWT sessions, no `useEffect` fetching,
  no logic in routes, no `any`, no speculative database server, no
  float money.

## How it was tested

- `tests/verify_template.py` — **12/12 checks pass**: the issue's
  expected sections, acceptance topics, pinned stack, dev commands,
  reason-carrying rules (≥15 "because" clauses), zero placeholders,
  plus consistency against the real scaffold below.
- **Greenfield run** (`tests/greenfield-test-report.md`): a genuine
  `create-next-app@15` project (Next 15.5.29 / React 19.1.0), the
  template's folder structure applied, `CLAUDE.md` pasted in
  **unmodified** — production build, typecheck, and lint all pass.
- `tests/context-qa.md` — the 12 questions a fresh Claude session
  would otherwise have to ask, each mapped to the template section
  that already answers it.

## Acceptance criteria (issue #2) — how this build meets each

| Criterion | Evidence |
|---|---|
| Covers project structure, naming conventions, DB migration rules | "Folder structure", "Naming conventions", "Database & migration rules" sections |
| Includes dev commands, patterns to follow, anti-patterns to avoid | "Dev commands" (9 commands), "Component & data patterns", "What we don't do (and why)" |
| Opinionated — every rule has a reason | Rules are decisions with because-clauses throughout; the verify suite mechanically checks every anti-pattern carries a reason |
| Usable without modification on a greenfield project | Pasted byte-identical into a fresh create-next-app project; no placeholders (suite-checked) |
| Tested: new project + paste + Claude understands without clarifying questions | **Partially met — gap stated plainly.** The new-project + paste + build/typecheck/lint half is done and documented (`tests/greenfield-test-report.md`). The literal interactive Claude Code confirmation could NOT be run from the build environment (no Claude Code CLI installed there). `tests/context-qa.md` maps 12 would-be clarifying questions to the template lines that answer them, and gives a 5-minute manual protocol to complete the confirmation at submission time |

## Honest limitations

- The stack choices are deliberately single-path (better-sqlite3, no
  ORM, DB sessions). A team that wants Drizzle or Turso from day one
  should edit those sections — the template says where the switch
  points are, but it does not pretend to cover every stack.
- Versions are pinned as of November 2026 (Next.js 15.x line); bump
  the pins when the project upgrades.
