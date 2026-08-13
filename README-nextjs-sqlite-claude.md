# Next.js 15 + SQLite SaaS CLAUDE.md Template

This PR adds an opinionated `CLAUDE.md` for a greenfield SaaS built with Next.js 15 App Router and SQLite.

## Setup in 3 steps

1. Copy the template into your project root:
   ```bash
   cp templates/nextjs-sqlite/CLAUDE.md ./CLAUDE.md
   ```
2. Adjust the package manager command names only if your `package.json` differs.
3. Ask Claude Code to read `CLAUDE.md` before making changes.

## Why this template is opinionated

It chooses a small, boring architecture: Server Components by default, route handlers as thin adapters, service/repository layers for business logic, Prisma-backed SQLite access, and explicit SQL migrations.

The goal is to stop Claude Code from asking generic structure questions and to prevent common SaaS mistakes: SQL string interpolation, client-side authentication trust, mutable old migrations, unbounded list queries, skipped tests, and vague utility modules.

## What the template covers

- **Next.js App Router:** route groups, Server Components by default, client components only for browser state.
- **SQLite + Prisma:** local `DATABASE_URL`, repository boundaries, idempotent seed data, and safe migration expectations.
- **Authentication:** server-side session checks, no trust in client-visible role flags, and explicit access-control review.
- **Testing:** required `npm run lint`, `npm run typecheck`, `npm run test`, and migration checks before completion.
- **Security:** parameterized queries, input validation, rate-limit placement, secret handling, and destructive-operation guardrails.

## Manual validation

I validated the template by checking it against a minimal Next.js 15 + SQLite/Prisma project shape and confirming it answers the usual first-context questions without extra clarification:

- where routes, services, repos, migrations, and components go
- how database migrations are named and applied
- how authentication and authorization checks are enforced server-side
- what test commands to run before completion
- what security and anti-pattern rules to follow
