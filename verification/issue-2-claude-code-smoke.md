# Issue #2: Claude Code smoke test

This is a manual acceptance check for `templates/nextjs-15-sqlite/CLAUDE.md`. It tests whether Claude Code can use the guide in a fresh project without asking for details already covered by the repository or the guide.

## Setup

1. In a disposable parent directory, create a fresh Next.js 15 App Router project with TypeScript using the pinned generator version:

   ```sh
   npx create-next-app@15.5.26 issue2-smoke --typescript --eslint --app --src-dir --no-tailwind --use-npm --skip-install --disable-git --yes
   ```

   Keep its generated `package.json` unchanged. No dependency installation is needed for this planning-only check.
2. Copy the template to the project root as `CLAUDE.md`.
3. Add only this small fixture:

```text
src/app/(app)/projects/[projectId]/page.tsx
src/server/auth/session.ts
src/server/db/client.ts
src/features/projects/server/queries.ts
src/features/projects/server/mutations.ts
src/server/db/migrations/0001_create_projects.sql
```

The files can be short placeholders; the test is about planning, not implementation.

## Prompt

```text
Inspect this repository and CLAUDE.md. Plan a Server Action that archives one project for the currently authenticated workspace. Do not edit files or run migrations. Return: (1) the files you would inspect or change, (2) the authorization and SQL predicates required to prevent cross-workspace access, (3) the migration strategy if an archived_at column is absent, and (4) the tests and commands you would run. Use the existing repository and CLAUDE.md; make safe assumptions explicit. Ask a question only if the task cannot be planned safely from those sources.
```

## Pass criteria

- Claude Code reads the root `CLAUDE.md` and inspects the project files before proposing a plan.
- For the template's default `better-sqlite3` path, it explicitly keeps database access in the Node.js runtime and out of Client Components and Edge. If the repository selects remote Turso/libSQL instead, it follows that driver's supported runtime and does not apply local-file or WAL rules.
- It derives workspace identity from the authenticated session and scopes the update by both project ID and workspace ID.
- It proposes an append-only migration and never edits a migration that may already be applied.
- It names focused tests plus the existing lint/type-check/build commands, without claiming scripts exist before reading `package.json`.
- It asks no question whose answer is already stated in the guide or fixture. It does not edit files, execute a migration, or make a production-data assumption.

## Current result

Passed on 2026-09-25 with Claude Code 2.1.282 against a fresh `create-next-app@15.5.26` project and six placeholder files. The successful run used plan mode, only project/local settings, no persisted session, and a process environment with API/gateway credential variables removed. The user-level Vercel AI Gateway configuration was not changed.

Claude Code read the actual package manifest and project files, reported that only `dev`, `build`, `start`, and `lint` scripts exist, and did not invent a test framework or migration runner. It proposed a tenant-scoped update using both project ID and the session-derived workspace ID, an `archived_at IS NULL` guard, and a new `0002` migration without editing `0001`. It also kept the database module server-only and specified `runtime = 'nodejs'` wherever `better-sqlite3` is used. It asked no clarifying question.

No app source or migration was changed and no dependency installation or database operation was performed; this is a context-understanding smoke test, not implementation validation. Claude Code wrote its normal plan artifact under the local Claude plans directory; the response is preserved in [`issue-2-claude-code-smoke-output.md`](issue-2-claude-code-smoke-output.md), with its local destination omitted.

One initial run stopped at the explicit four-turn limit before returning a complete answer. The recorded successful run raised the limit to twelve turns; no second model retry was made after that successful response.

## Fresh CLI check on 2026-09-27

Claude Code 2.1.283 repeated the read-only comprehension check on a newly generated `create-next-app@15.5.26` fixture. It returned a successful end-turn response in 15 turns, read the project guide and real stub files, and asked no question. The exact prompt, output, settings, and scope limits are recorded in [the dated run record](issue-2-claude-code-smoke-20260927.md). This was planning only; no install, build, test, migration, or implementation was performed.
