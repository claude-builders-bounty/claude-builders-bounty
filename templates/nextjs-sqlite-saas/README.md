# Next.js SQLite SaaS CLAUDE.md Template

This directory contains an opinionated `CLAUDE.md` for a greenfield SaaS project
built with Next.js 15 App Router and SQLite.

## Use

Copy `CLAUDE.md` into the root of a new or existing project:

```bash
cp templates/nextjs-sqlite-saas/CLAUDE.md /path/to/project/CLAUDE.md
```

The template defines stack choices, folder structure, naming rules, SQL
migration rules, component patterns, server action rules, testing expectations,
and anti-patterns.

## Validation

To validate the template against a greenfield app:

1. Create a new Next.js app with TypeScript, App Router, and Tailwind.
2. Add SQLite using either `better-sqlite3` for file-backed deployments or
   Turso/libSQL for hosted SQLite.
3. Paste this `CLAUDE.md` into the project root.
4. Ask Claude Code to add an organization dashboard with a SQLite-backed
   organizations table, migration, query function, server action, and form.

Expected result: Claude Code should know where files belong, how to name them,
how migrations are ordered, how SQL is validated, when to use server and client
components, and which checks to run before a PR.
