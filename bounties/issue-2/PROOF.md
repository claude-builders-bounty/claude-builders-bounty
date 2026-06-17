# Issue #2 — CLAUDE.md Template for Next.js + SQLite SaaS

Delivery for [claude-builders-bounty#2](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2).

## What was implemented

An opinionated, production-ready `CLAUDE.md` for Next.js 15 App Router + SQLite SaaS projects.

| File | Purpose |
|------|---------|
| `skills/claude-md-nextjs-saas/CLAUDE.md` | Full project instructions for Claude Code |
| `skills/claude-md-nextjs-saas/README.md` | Context and usage |

## Sections covered

- Stack & versions (Next.js 15, SQLite, TypeScript)
- Folder structure (App Router conventions)
- Naming conventions (files, components, DB tables)
- SQL / migration conventions (WAL mode, no ORM)
- Component patterns (Server Components by default)
- What we don't do (and why)
- Dev commands
- Environment variables
- Testing requirements

## Verification

```bash
python3 build.py
# All checks pass
```

The CLAUDE.md is opinionated — every rule has a reason. It's usable without modification on a greenfield Next.js + SQLite project.

Closes #2
