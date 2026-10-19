# Next.js + SQLite CLAUDE.md — issue #2

An opinionated copyable working contract, with a fresh Next.js 15 fixture and
real SQLite checks. The template is under 500 lines and does not contain keys.

## Setup (three steps)

1. Copy `CLAUDE.md` to a new project's root. The default is App Router,
   better-sqlite3, Node runtime and organization tenancy; a Turso deployment
   must explicitly adapt the database boundary rather than pretending a local
   file is durable on serverless infrastructure.
2. Inspect `fixture/` for a concrete greenfield example. It includes parameterized
   repositories, composite tenant foreign keys, fail-closed auth, checksummed
   migrations and local-only seeding. Its database tests require Python 3.10+.
   The fixture is an illustrative scaffold, not a completed authentication or
   billing implementation. Run the commands below for verification.
3. For the bounty's Claude Code check, copy the template into `fixture/`, start
   an authenticated Claude Code session there, and use the prompt below. Save
   the actual transcript with model, CLI version and date before marking that
   acceptance criterion complete.

```bash
cd fixture
python3 -m unittest discover -s tests -v
DATABASE_PATH=local.db python3 migrate.py
DATABASE_PATH=local.db python3 seed.py
pnpm install
pnpm typecheck
pnpm build
pnpm dev
# /api/projects must return 401 until a real verified auth provider is installed.
```

## Claude Code acceptance prompt

> Read CLAUDE.md and package.json. Without changing files or asking clarification,
> describe where you would add tenant-scoped projects and a create-project Server
> Action. Name the runtime, authentication boundary, input validation, SQL
> parameterization, migration ledger, transaction constraints, cache behavior and
> negative-path tests. Explain why the current protected route returns 401.

Expected evidence: Node runtime; verified server membership (never client tenant
ID); server-only repository; parameterized SQL; immutable checksummed migrations;
no await inside synchronous database transactions; post-commit revalidation;
tests for auth failure, cross-tenant access, invalid input and rollback.

## Validation honesty

See `VALIDATION.md`. SQLite fixture checks and TypeScript/build checks are distinct
from the Claude Code comprehension criterion. No live Claude Code execution is
claimed; that requirement is pending because this environment has no authenticated
Claude Code CLI. Do not treat an ordinary LLM's reading as that required test.

## Sources

- https://nextjs.org/docs/15/app/api-reference/functions/cookies
- https://nextjs.org/docs/15/app/api-reference/directives/use-server
- https://www.sqlite.org/foreignkeys.html
- https://github.com/WiseLibs/better-sqlite3/blob/master/docs/api.md
