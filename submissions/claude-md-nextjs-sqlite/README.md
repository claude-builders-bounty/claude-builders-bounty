# CLAUDE.md — Next.js 15 + SQLite SaaS Template

**Bounty #2** — $75 | [claude-builders-bounty/claude-builders-bounty#2](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2)

A production-ready, opinionated `CLAUDE.md` for SaaS projects built with Next.js 15 App Router and SQLite (better-sqlite3).

## What's Included

- **Project structure** — directory layout with rationale
- **Database rules** — migration workflow, query patterns, SQLite gotchas
- **Auth patterns** — session handling, protection rules
- **TypeScript rules** — strict mode, type conventions
- **Component patterns** — Server vs Client Components, data fetching
- **Stripe integration** — webhook handling, billing patterns
- **Anti-patterns table** — 9 things NOT to do and why
- **Naming conventions** — files, functions, env vars, branches
- **Common task recipes** — add a table, add a page, add an API route

## Why This CLAUDE.md is Different

Most CLAUDE.md templates are generic checklists. This one is **opinionated** and **justified** — every rule includes the reason it exists (usually: "someone got burned").

Examples:
- "Never modify existing migration files" → **Why:** Breaks production deployments
- "No `useEffect` for data fetching" → **Why:** Race conditions and waterfalls
- "No `any` without a comment" → **Why:** Defeats the purpose of TypeScript strict mode

## Usage

1. Copy `CLAUDE.md` to your project root
2. Update the "Project Overview" section with your stack specifics
3. Add project-specific rules to the relevant sections
4. Done — Claude Code will follow these rules in all sessions

## Tested On

Validated on a greenfield Next.js 15 + better-sqlite3 project:
- Claude Code respected all SQL injection prevention rules
- Claude Code used Server Components by default
- Claude Code created migration files instead of direct schema edits
- Claude Code checked session before every API route handler
