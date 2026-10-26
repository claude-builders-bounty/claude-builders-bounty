## What
Drop-in `CLAUDE.md` for a Next.js 15 (App Router) + SQLite SaaS codebase — the working agreement that makes Claude Code consistent and predictable on this project.

## Contents
- Stack & conventions: Next.js 15 App Router, TypeScript, better-sqlite3, `data/app.db`
- Dev commands: dev/build/start/test/lint, DB migrate & seed
- Architecture map: `app/` routes, `lib/`, migrations
- Data access rules: parameterized SQL only, transaction guidance, UTC ISO datetimes
- Testing: vitest + testing-library, in-memory sqlite setup
- Security: SQL injection, auth notes, env var hygiene
- "How to use this template" section (what to customize per project)

## Verification
- 177 lines, single consistent stack; every section is actionable (concrete paths and commands)
- Written to be self-sufficient: the file instructs Claude Code not to ask questions it can already answer from it

## Acceptance criteria mapping
- Covers project overview/stack, dev commands, architecture map, conventions, testing, security, and gotchas ✓
- Ready to drop at repo root as `CLAUDE.md` ✓
