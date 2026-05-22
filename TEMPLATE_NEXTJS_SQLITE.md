# Next.js + SQLite SaaS CLAUDE.md Template

This submission adds an opinionated CLAUDE.md template for bounty #2.

## Contents

- Project structure for App Router SaaS projects.
- Naming conventions for components, hooks, server actions, routes, schema, migrations, and environment variables.
- Database and SQLite rules for prepared queries, transactions, indexes, timestamps, and tenant scoping.
- Migration rules, including append-only migrations and destructive-change safeguards.
- Auth/session, billing, UI, testing, and finish-check guidance.
- Commands for install, development, linting, typechecking, tests, and database migration workflows.

## Usage

Copy the template into a Next.js + SQLite SaaS repository:

    cp templates/nextjs-sqlite-saas/CLAUDE.md CLAUDE.md

Then edit command names only if the target project uses a package manager or ORM script with different names.

## Validation

Run the zero-dependency verifier:

    node scripts/verify-nextjs-sqlite-template.mjs

Then copy the template into a greenfield project and try the smoke prompts in templates/nextjs-sqlite-saas/smoke-prompts.md. Claude Code should apply the SQLite, migration, tenant-scoping, billing, and testing rules without asking for a different stack or generic project context.
