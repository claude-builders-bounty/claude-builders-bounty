# Next.js 15 + SQLite SaaS CLAUDE Template

Production-ready `CLAUDE.md` for a greenfield SaaS built with Next.js 15 App
Router and SQLite.

## Setup

1. Copy `templates/next15-sqlite-saas/CLAUDE.md` into the root of your app.
2. Update the package manager commands if your project does not use `pnpm`.
3. Run Claude Code from the project root and ask it to inspect `CLAUDE.md`
   before making changes.

## Validation

This template was checked against a fresh Next.js 15 App Router project shape
with SQLite-oriented folders. It gives Claude Code concrete rules for structure,
migrations, components, server actions, anti-patterns, and completion gates
without requiring follow-up clarification.

Run the acceptance guard after edits:

```bash
python3 templates/next15-sqlite-saas/check-template.py
```

The guard verifies the expected sections, SQLite/Turso/better-sqlite3 coverage,
standard dev commands, and that opinionated rule bullets include a reason.
