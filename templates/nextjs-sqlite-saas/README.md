# Next.js 15 + SQLite SaaS CLAUDE.md template

This directory contains an opinionated, production-ready `CLAUDE.md` template for a greenfield SaaS project using:

- Next.js 15 App Router
- TypeScript
- SQLite via `better-sqlite3` or Turso/libSQL
- Zod validation
- Server actions / route handlers

## Install in 3 steps

1. Copy the template into your project root:

   ```bash
   cp templates/nextjs-sqlite-saas/CLAUDE.md /path/to/your-saas/CLAUDE.md
   ```

2. Make sure your project uses the expected baseline stack:

   ```bash
   node --version
   npm install next@latest react@latest react-dom@latest zod better-sqlite3
   ```

   If you deploy to a read-only or edge environment, use Turso/libSQL instead of `better-sqlite3` and keep the repository interface described in the template.

3. Start Claude Code from the project root so it can read the file:

   ```bash
   cd /path/to/your-saas && claude
   ```

## What the template covers

- Stack and version assumptions
- Folder structure
- Server/client component boundaries
- SQLite connection and migration rules
- SQL naming and indexing conventions
- Server action and route handler patterns
- Auth/session rules
- Zod validation rules
- Component and UI patterns
- Testing expectations
- Security, performance, and anti-pattern guidance
- PR checklist

## Why this is opinionated

The template intentionally chooses explicit SQL, server-only data modules, and append-only migrations. These rules prevent common Next.js SaaS mistakes:

- leaking secrets into client bundles,
- trusting browser-provided user IDs,
- editing committed migrations,
- hiding database behavior behind generic abstractions,
- placing business logic in JSX.

## Test evidence

See `TEST_REPORT.md` for the validation steps used for this bounty submission.
