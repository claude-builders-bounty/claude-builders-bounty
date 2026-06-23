# Next.js SQLite SaaS CLAUDE.md Template

Opinionated Claude Code project instructions for a greenfield SaaS app built with Next.js 15 App Router and SQLite.

## Use It

1. Copy `CLAUDE.md` into the root of a new Next.js 15 App Router project.
2. Adjust only concrete project facts such as package scripts, auth provider, or database driver.
3. Ask Claude Code to implement a small feature and confirm it follows the documented structure before adding more code.

## What It Covers

- Stack and version assumptions for Next.js 15, React Server Components, TypeScript, and SQLite.
- Folder structure for App Router pages, feature modules, server-only code, database migrations, and tests.
- Naming conventions for routes, components, server actions, queries, services, tables, columns, types, and env vars.
- SQL and migration rules for timestamped migrations, constraints, indexes, rollback notes, and idempotent seeds.
- Component, server, auth, data-boundary, and testing patterns.
- Anti-patterns with reasons, so Claude Code has concrete rules instead of generic preferences.

## Verification

The `verification/claude-code-context-check.md` file contains copy-paste prompts and expected context-aware behavior for checking that Claude Code understands the template without extra clarification.
