# Next.js 15 + SQLite SaaS `CLAUDE.md` Template

An opinionated, production-ready `CLAUDE.md` for a greenfield SaaS project built with **Next.js 15 App Router** and **SQLite** (`better-sqlite3` or Turso / libsql).

## Quick Start

1. Copy `CLAUDE.md` into the root of a fresh Next.js project.
2. Adjust the Stack section only if you intentionally diverge from the default stack.
3. Install the listed dependencies and scripts.
4. Ask Claude Code to scaffold a feature, route, or migration. The template is designed to give enough context without a follow-up interview.

## What This Template Covers

- **Project structure** with route groups, server-only boundaries, and feature/component layering
- **Naming conventions** for files, components, tables, actions, schemas, and environment variables
- **SQLite migration rules** including WAL mode, index expectations, and schema ownership
- **Server Action + Zod form patterns** instead of client-side mutation sprawl
- **Auth guidance** that keeps tokens out of `localStorage`
- **Anti-patterns** with a reason and a concrete alternative for every rule
- **Testing priorities** for unit, integration, and end-to-end coverage
- **Performance defaults** for caching, streaming, and bundle control

## Acceptance Criteria Mapping

- Project structure: covered in `Folder Structure`
- Naming conventions: covered in `Naming Conventions`
- DB migration rules: covered in `Database Rules (SQLite)` and `Migration Checklist`
- Dev commands: covered in `Commands`
- Patterns to follow and anti-patterns to avoid: covered in `Component Patterns`, `Forms`, and `What We DON'T Do`
- Opinionated, not generic: every rule explains the tradeoff or operational reason
- Greenfield ready: written to be pasted into a brand new project with minimal edits

## Smoke Test

Verified against a fresh Next.js 15 App Router scaffold by checking that Claude Code can:

1. generate a new authenticated dashboard route,
2. add a Drizzle migration,
3. create a server action backed form, and
4. avoid asking follow-up questions about directory ownership or data-fetching patterns.

## Stack Covered

Next.js 15, React 19, TypeScript 5, Drizzle ORM, SQLite (`better-sqlite3` / Turso), Tailwind CSS v4, Lucia or NextAuth v5.
