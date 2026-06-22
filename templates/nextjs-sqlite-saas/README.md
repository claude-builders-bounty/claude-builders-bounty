# Next.js 15 + SQLite SaaS — CLAUDE.md Template

Opire bounty [#2](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2) — **$75**

## Install (2 commands)

```bash
# greenfield Next.js project
npx create-next-app@latest my-saas --typescript --tailwind --eslint --app --src-dir=false

# copy template
cp path/to/CLAUDE.md my-saas/CLAUDE.md
```

Or for Claude Code: copy to project root as `CLAUDE.md`.

## Verify (greenfield smoke test)

```bash
cd my-saas
cp ../CLAUDE.md .
# Open Claude Code in this directory and ask:
# "Add a projects table with organization_id and a dashboard page listing projects."
# Claude should use Drizzle, Server Components, and org-scoped queries without asking stack questions.
```

## Contents

- `CLAUDE.md` — opinionated rules for Next.js 15 App Router + SQLite + Drizzle + Auth.js
- Every section includes **why**, not just what
- Covers: structure, naming, migrations, components, anti-patterns, dev commands
