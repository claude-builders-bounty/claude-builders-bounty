# Next.js 15 + SQLite SaaS — CLAUDE.md Template

Opinionated [Claude Code](https://docs.anthropic.com/en/docs/claude-code) context file for greenfield multi-tenant SaaS projects.

## Setup (3 steps)

1. Scaffold a Next.js 15 App Router project with TypeScript, Tailwind, and `src/` directory.
2. Copy `CLAUDE.md` to the project root.
3. Open the project in Claude Code — it will follow the conventions without clarifying questions for routine tasks.

## What it covers

- Stack pins (Next 15, React 19, better-sqlite3 / Turso, Zod, pnpm)
- Folder structure with tenant-scoped routing
- SQL migration rules and query conventions
- Server Component / Client island / Server Action patterns
- Anti-patterns table with reasons

## Verify

```bash
node templates/nextjs-sqlite-saas/validate-template.mjs
bash templates/nextjs-sqlite-saas/tests/smoke-greenfield.sh
```
