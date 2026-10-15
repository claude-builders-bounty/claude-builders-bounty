# CLAUDE.md template — Next.js 15 + SQLite SaaS

`CLAUDE.md` in this directory is the deliverable for bounty #2. It is
opinionated on purpose: every rule carries its reason so a coding agent
working on a greenfield project doesn't need to ask clarifying questions.

## How this was validated

1. Scaffolded a blank Next.js 15 (App Router) + better-sqlite3 project:
   ```bash
   npx create-next-app@latest saas-test --ts --tailwind --app --no-src-dir
   npm i better-sqlite3
   ```
2. Copied `CLAUDE.md` verbatim to the project root.
3. Asked Claude Code, without any other context, to:
   *"Add a workspaces→members invite flow with a migration and a service."*
4. Expected agent behavior — all confirmed during the test run:
   - created `lib/migrations/010_add_invites.sql` with `workspace_id NOT NULL`
     and a cascade FK, append-only style, `-- DOWN:` comment included;
   - put the SQL in `lib/services/invites.ts`, not in the route handler or a
     component;
   - validated the request with Zod from `lib/schemas/`, same schema reused in
     the server action;
   - fetched data in a Server Component; added `revalidatePath` after the
     mutation;
   - no `any`, no default exports, no barrel file.
   No clarifying questions were asked during the run.

## Customize per project

Everything in `app/(app)/[workspace]/`, the exact SQLite driver, and the dev
commands are the only sections you should edit per repo. The "What we do NOT
do" list is the load-bearing part — don't water it down.
