# Next.js 15 + SQLite SaaS CLAUDE.md Template

This directory contains an opinionated `CLAUDE.md` for a greenfield SaaS app
built with Next.js 15 App Router and SQLite/Turso.

## Use It

Copy `CLAUDE.md` to the root of a new project:

```bash
cp templates/nextjs15-sqlite-saas/CLAUDE.md /path/to/your-app/CLAUDE.md
```

Then keep the project aligned with its assumptions:

- Next.js 15 App Router, not the legacy `pages/` router.
- TypeScript strict mode.
- SQLite locally and Turso/libSQL for hosted environments.
- Drizzle ORM for schema, queries, and migrations.
- Zod for environment and input validation.
- Auth.js v5 for authentication.

## Acceptance Criteria Mapping

- Project structure: covered in `Folder Structure` and `Import Boundaries`.
- Naming conventions: covered in `Naming Conventions`.
- DB migration rules: covered in `Database Rules` and `Migrations`.
- Dev commands: covered in `Commands`.
- Patterns to follow: covered across data access, Server Actions, route
  handlers, components, auth, billing, errors, and testing.
- Anti-patterns to avoid: covered in `What We Do Not Do`.
- Opinionated rules with reasons: each rule states why the project uses that
  approach.
- Greenfield usability: the file can be copied as the root `CLAUDE.md` before
  the first feature is built.

## Validation Notes

Validated on 2026-05-17 by creating a fresh app with:

```bash
npx create-next-app@15 validation-nextjs15-sqlite-saas-next15 \
  --typescript --tailwind --eslint --app --src-dir \
  --import-alias "@/*" --use-npm --yes
```

The generated project used `next@15.5.18`. The template was copied to the
project root as `CLAUDE.md`, and `npm run lint` passed.

The content was also reviewed for the common clarification loops Claude Code
hits in new SaaS repos:

- Which router to use.
- Which SQLite driver and ORM to assume.
- Where migrations live.
- Whether mutations belong in Server Actions or route handlers.
- How auth and team membership are enforced.
- Which anti-patterns are explicitly forbidden.
