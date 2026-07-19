## 💰 Bounty: $75 — powered by [Opire](https://opire.dev)

## What

Production-ready `CLAUDE.md` template for a Next.js 15 + SQLite SaaS project.

## Deliverable

`templates/claude-md/nextjs-sqlite-saas/CLAUDE.md`

## Acceptance Criteria Met

- ✅ Covers: project structure, naming conventions, DB migration rules
- ✅ Includes: dev commands, patterns to follow, anti-patterns to avoid
- ✅ Opinionated — every rule has a reason (e.g., "No Prisma — Prisma generates a massive client (~20MB) and its migration system is opaque")
- ✅ Usable without modification on a greenfield Next.js + SQLite project
- ✅ Tested: paste into a new project, Claude Code understands the context without clarifying questions

## Sections Included

- **Stack & Versions** — exact versions with rationale
- **Folder Structure** — annotated tree with rules per directory
- **SQL / Migration Conventions** — schema patterns, column naming, migration workflow
- **Component Patterns** — Server vs Client components, server actions, with code examples
- **What We Don't Do (and Why)** — 8 anti-patterns with explanations
- **Dev Commands** — all commands + pre-commit checklist

/opire try

Closes #2
