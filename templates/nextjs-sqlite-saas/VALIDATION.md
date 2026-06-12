# Validation

Validated locally with:

```bash
node templates/nextjs-sqlite-saas/validate-template.mjs
git diff --check
```

The validator checks that `CLAUDE.md` includes:

- required issue sections: stack/version, folder structure, SQL/migration conventions, component patterns, and anti-patterns;
- Next.js 15 App Router, React 19, SQLite, better-sqlite3, and Turso/libSQL coverage;
- dev commands and expected package scripts;
- concrete migration rules and SQLite safety pragmas;
- naming conventions and project structure;
- reasoned rules using explicit `Reason:` statements;
- greenfield SaaS operating instructions for Claude Code.

Manual greenfield smoke-test prompt:

```text
Create a new Next.js 15 App Router SaaS project using SQLite. Follow the attached CLAUDE.md exactly. Add workspace creation with a SQL migration, repository query functions, a Server Action, a dashboard page, and tests. Do not ask clarifying architecture questions unless the CLAUDE.md leaves something unspecified.
```

Expected result: Claude should proceed using the template decisions: App Router, Node runtime for local SQLite, raw SQL migrations under `src/db/schema`, query functions in `src/db/queries`, Server Actions in `src/actions`, strict env validation, tenant-scoped tables, and tests for migrations/query behavior.

Claude Code smoke test run:

```bash
tmpdir=$(mktemp -d /tmp/next-sqlite-claude-smoke.XXXXXX)
cp templates/nextjs-sqlite-saas/CLAUDE.md "$tmpdir/CLAUDE.md"
cd "$tmpdir"
claude -p --no-session-persistence --model sonnet --max-budget-usd 0.50 --disallowedTools=Bash,Edit,Write -- "Using this project's CLAUDE.md, plan the implementation for workspace creation in a greenfield Next.js 15 SQLite SaaS app. Do not modify files. Do not ask clarifying questions. Return concise bullets for migration, data access, Server Action, route/page, and tests."
```

Observed result: Claude Code exited with status 0 and returned a concrete plan covering migration, data access, Server Action, route/page, tests, auth checks, audit events, and slug collision behavior without asking clarifying architecture questions.
