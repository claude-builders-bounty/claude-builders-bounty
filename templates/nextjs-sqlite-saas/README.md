# Next.js SQLite SaaS CLAUDE.md Template

This folder contains an opinionated `CLAUDE.md` for a greenfield SaaS app built with Next.js 15 App Router and SQLite.

## Use

```bash
cp templates/nextjs-sqlite-saas/CLAUDE.md /path/to/your-app/CLAUDE.md
```

Then ask Claude Code to inspect the project and follow the rules in `CLAUDE.md` before making changes.

## Validation Notes

The template is intentionally concrete about:

- App Router route groups and server-first components.
- SQLite migration safety and transaction rules.
- Multi-tenant SaaS authorization boundaries.
- Server actions, route handlers, and data access layering.
- Anti-patterns to avoid and why each rule exists.
