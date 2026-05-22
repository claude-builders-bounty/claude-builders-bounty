# Next.js 15 + SQLite SaaS CLAUDE.md Template

Opinionated `CLAUDE.md` for a greenfield SaaS using Next.js 15 App Router and SQLite.

## Files

- `CLAUDE.md` — production-ready Claude Code project instructions.
- `SMOKE_TEST.md` — validation prompt and expected behavior.
- `tests/test_template.py` — structural checks for bounty acceptance criteria.

## Use

1. Create or open a Next.js 15 + SQLite SaaS project.
2. Copy `CLAUDE.md` into project root.
3. Start Claude Code and ask it to add a small workspace CRUD feature without extra context.

## Why this template is not generic

- It fixes stack choices: Next.js 15, App Router, Drizzle, SQLite/Turso, Zod, Server Components.
- It defines exact folder ownership.
- It gives migration workflow and SQLite-specific safety rules.
- It includes code patterns for schema, Server Actions, services, queries, Route Handlers, and env parsing.
- Every rule includes a reason so Claude knows when not to improvise.

## Local validation

```bash
python3 -m unittest discover -s templates/nextjs15-sqlite-saas-n404t/tests -v
```
