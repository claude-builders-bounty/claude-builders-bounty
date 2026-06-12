# Next.js 15 + SQLite SaaS CLAUDE.md Template

This directory contains an opinionated `CLAUDE.md` for a greenfield SaaS project using Next.js 15 App Router and SQLite through either `better-sqlite3` or Turso/libSQL.

## Files

- `CLAUDE.md` - the production-ready Claude Code instruction file.
- `validate-template.mjs` - structural validator for the bounty acceptance criteria.
- `VALIDATION.md` - reproducible validation notes.

## Use

Copy `CLAUDE.md` into the root of a new Next.js 15 + SQLite SaaS repository before starting implementation work with Claude Code.

```bash
cp templates/nextjs-sqlite-saas/CLAUDE.md /path/to/new-saas/CLAUDE.md
```

The template is intentionally specific. It chooses App Router, strict TypeScript, server-first rendering, raw SQL migrations, a repository layer, and SQLite safety pragmas so Claude does not need to ask which architecture to follow.

## Validate

```bash
node templates/nextjs-sqlite-saas/validate-template.mjs
git diff --check
```
