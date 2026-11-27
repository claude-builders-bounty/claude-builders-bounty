# Greenfield test of CLAUDE.md

Done in a sandbox, outside this repo. Node v24.22.1, pnpm 12.23.0 (via corepack). Node 22, Turso, Playwright and auth were **not** tested.

## Versions (from the test project's package.json)

`next` 15.5.29, `react` 19.1.0, `typescript` ^5 (5.9.3 installed), `better-sqlite3` ^13.2.0, `zod` ^4.6.7, `vitest` ^5.1.2, `tsx` ^4.23.15.

## Steps

1. `npx -y create-next-app@15 greenfield --ts --app --eslint --tailwind --no-src-dir --import-alias "@/*" --use-pnpm --yes`
2. `pnpm add better-sqlite3 zod` and `pnpm add -D @types/better-sqlite3 vitest tsx`
3. Copied `CLAUDE.md` to the project root unchanged.
4. Spawned one fresh subagent (type `opus-reviewer`, no model override) with only that project as context. Prompt: read `CLAUDE.md` and the tree, plan a `projects` table with migration, list page and create form, list clarifying questions or "none".
5. Implemented the feature by hand following the plan and CLAUDE.md, then ran the commands below.
6. Fixed CLAUDE.md where it fell short (see below), re-copied it, re-ran typecheck, lint, test and build.

## Clarifying questions asked by the fresh agent

It did ask four, none about stack, structure, naming or migrations. They were about things CLAUDE.md can't know: auth/ownership ("The `auth/` helpers, `requireUser()` and a `users` table don't exist, so I assumed the projects are global"), project fields, route path, and post-create behaviour. It also said "If none of these can be answered, CLAUDE.md's rule is to pick the most consistent option and state the assumption", and proceeded with a full plan.

It also reported that CLAUDE.md referenced scripts and files absent from a fresh project (`typecheck`, `test`, `db:*`, `lib/`, `migrations/`, `.nvmrc`, `.env.example`, `noUncheckedIndexedAccess`).

## Changes made to CLAUDE.md because of the test

- Added a "Greenfield bootstrap (once)" section: scripts, config tweaks and the specs of the missing files.
- Node row now says "22 LTS (verified on 24.x)".
- Notes found by running it: `pnpm add` reported `ERR_PNPM_IGNORED_BUILDS` for esbuild; scripts can't use top-level `await` under tsx (CJS); vitest config must be `.mts` and use `import.meta.dirname`.

## Results

| Command | Result |
|---|---|
| `pnpm typecheck` | exit 0 |
| `pnpm lint` | exit 0 |
| `pnpm test` | `Test Files 1 passed (1)`, `Tests 1 passed (1)` |
| `pnpm db:migrate` (1st) | `applied: 0001_add_projects_table.sql` |
| `pnpm db:migrate` (2nd) | `no pending migrations` |
| `pnpm db:new add_users_table` | created `migrations/0002_add_users_table.sql` (then removed) |
| `pnpm db:reset` | first try failed (top-level await error); fixed the script; then `deleted ./data/app.db`, `applied: 0001_add_projects_table.sql` |
| `pnpm build` | `✓ Compiled successfully`, `/projects` listed as dynamic |

## Limits

- The agent's plan was checked by implementing it myself; a second fresh session was not run after the CLAUDE.md edit.
- The agent reply saved in the sandbox is a condensed copy, not byte-for-byte.
- `requireUser()` was skipped (no auth in the test project).
- `pnpm dev` and the create form were not exercised in a browser.
