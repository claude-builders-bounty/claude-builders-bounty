# Bounty #2 — CLAUDE.md Template for Next.js 15 + SQLite SaaS

A production-ready, opinionated `CLAUDE.md` for greenfield SaaS projects using Next.js 15 App Router and SQLite via `better-sqlite3`.

## What it covers

| Area | Details |
|---|---|
| **Project structure** | Full directory layout with rationale for every top-level folder |
| **Naming conventions** | Files, components, functions, DB columns, constants — all specified with reasons |
| **React / Next.js patterns** | Server Components as default, when to use `"use client"`, Server Actions vs API routes, data fetching in layouts vs pages |
| **SQLite / better-sqlite3** | DB singleton setup (WAL mode, FK constraints), query function organization, prepared statements |
| **Transactions** | Rule: all multi-step writes use `db.transaction()`, with a working example |
| **DB migrations** | Numbered SQL files in `/migrations/`, migration runner implementation, immutability rule |
| **Error handling** | Never swallow errors, log before throwing, typed `AppError` hierarchy, route handler pattern |
| **Environment variables** | `.env.local` vs `.env.example` vs `.env`, startup validation, never-commit rule |
| **Dev commands** | All `npm run *` commands + pre-PR checklist |
| **Testing** | Co-located tests, real in-memory SQLite (no mocks), what to test and what not to |
| **Anti-patterns** | 8 explicitly forbidden patterns with code examples |
| **TypeScript** | Strict mode, `Row` type convention, `satisfies` usage |
| **Security** | Input validation with zod, session token generation, cookie flags, rate limiting |
| **Git conventions** | Branch naming, Conventional Commits, PR requirements |

## How to use

1. Copy `CLAUDE.md` to the root of your Next.js project.
2. Adjust `DATABASE_PATH` and any env var names to match your project.
3. Optionally remove sections that don't apply (e.g., Stripe env vars if not using billing).
4. The file is ready to use with Claude Code on day one — no other setup required.

## Design philosophy

Every rule in the file includes a **reason**. This matters because:
- Claude can make better judgment calls in edge cases when it knows *why* a rule exists
- New developers reading the file understand the intent, not just the prescription
- Rules without reasons get ignored or cargo-culted

The file is intentionally opinionated. Generic advice ("write clean code") is useless to an AI agent. Specific, reasoned constraints ("never raw SQL in route handlers because…") are actionable.
