# CLAUDE.md — Next.js 15 + SQLite SaaS Template

An opinionated, production-ready `CLAUDE.md` for SaaS projects built with Next.js 15 App Router and SQLite (better-sqlite3).

## What's covered

- **Stack & versions** — exact technologies and why
- **Project structure** — every folder explained
- **Dev commands** — copy-paste ready
- **Database rules** — migrations, query patterns, schema types
- **Naming conventions** — files, components, DB columns, env vars
- **Component patterns** — Server vs Client, Server Actions, error handling
- **Auth pattern** — cookie sessions (no NextAuth)
- **Anti-patterns** — what we don't do, with reasons
- **Environment variables** — what goes where
- **Testing** — Vitest, no E2E in CI
- **Deployment** — Docker with SQLite volume

## Usage

```bash
# Copy to your project root
cp CLAUDE.md /path/to/your/nextjs-project/

# Claude Code will read it automatically
claude
```

## Design Decisions

Every rule has a reason. No generic advice. Highlights:

- **Raw SQL over ORMs** — SQLite queries are simple enough. ORMs hide performance problems.
- **No NextAuth** — Cookie + session table = 50 lines of code. No magic.
- **Server Components by default** — `"use client"` only for interactive leaves.
- **No barrel exports** — Breaks tree-shaking, slows builds.
- **Fail-fast env vars** — Missing config throws at startup, not at 3 AM.

## Tested

Created a fresh Next.js 15 project, dropped this CLAUDE.md in, and asked Claude Code to:
1. "Add a teams feature with invitations" → correctly created migration, schema type, Server Actions, no ORM
2. "Fix the auth to handle expired sessions" → followed the cookie pattern, no JWT
3. "Add a pricing page" → Server Component, no `"use client"`, queried plans from DB

Claude followed every convention without clarification questions.
