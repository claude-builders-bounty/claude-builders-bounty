# Next.js SQLite SaaS CLAUDE.md

Opinionated `CLAUDE.md` template for a greenfield SaaS app built with Next.js
15 App Router and SQLite.

## Setup

1. Create a new Next.js app.
2. Copy `CLAUDE.md` into the project root.
3. Ask Claude Code to implement a small SaaS task, such as adding a project
   creation form with a SQLite-backed server action.

## What It Covers

- Stack and version assumptions
- Folder structure
- Naming conventions
- Development commands
- SQL and migration rules
- Server/client component patterns
- Auth, billing, and multi-tenant rules
- Testing expectations
- Anti-patterns and the reason each one is avoided

## Validation

The template was copied into a greenfield fixture at
`templates/nextjs-sqlite-saas/fixtures/greenfield-app/` and checked for required
sections with `templates/nextjs-sqlite-saas/validate.py`.

The local environment did not include the `claude` CLI, so live Claude Code
execution is documented as a reviewer-run step instead of being claimed as a
completed local run.
