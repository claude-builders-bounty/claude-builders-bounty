# Next.js 15 + SQLite SaaS CLAUDE.md Template

This directory contains an opinionated `CLAUDE.md` for greenfield SaaS projects using Next.js 15 App Router and SQLite.

## Use it

```bash
cp templates/nextjs-sqlite/CLAUDE.md /path/to/your-app/CLAUDE.md
```

Then ask Claude Code to inspect the project and implement a small feature. The template should give it enough context to choose the right layer without asking for generic architecture clarification.

## What it covers

- Stack and version assumptions.
- Folder structure.
- Naming conventions.
- SQLite migration and query rules.
- App Router, Server Component, Server Action, and route-handler patterns.
- Auth, authorization, errors, observability, testing, and anti-patterns.

## Validation

The repository includes `tests/validate-nextjs-sqlite-template.py`, which checks that the template includes all bounty-required sections and concrete opinionated rules.
