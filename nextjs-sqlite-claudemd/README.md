# CLAUDE.md for Next.js 15 + SQLite SaaS

Production-ready `CLAUDE.md` for greenfield Next.js + SQLite projects.

## Setup (2 steps)

**Step 1:** Copy `CLAUDE.md` to your project root.

**Step 2:** Adjust stack versions and auth provider names to match your repo.

Claude Code reads this file automatically each session.

## What's inside

- Stack, commands, and folder structure
- Drizzle/SQLite migration rules with WAL + FK guidance
- Server action + Zod validation pattern
- Server vs client component boundaries
- Explicit anti-patterns with reasons
- Env var table and deployment checklist

## Greenfield validation (bounty #2)

1. Create `npx create-next-app@latest` with App Router + TypeScript.
2. Copy this `CLAUDE.md` to the project root.
3. Open Claude Code and ask: "Where should I add a Drizzle migration?" — it should answer using this file without asking stack clarifiers.

## Acceptance criteria

- [x] Structure, naming, DB migration rules
- [x] Dev commands, patterns, anti-patterns with reasons
- [x] Opinionated SaaS Next.js 15 + SQLite template

Closes claude-builders-bounty/claude-builders-bounty#2
