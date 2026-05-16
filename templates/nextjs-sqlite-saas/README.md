# Next.js 15 + SQLite SaaS CLAUDE.md Template

This directory contains an opinionated `CLAUDE.md` for a greenfield SaaS project using Next.js 15 App Router, TypeScript, and SQLite through `better-sqlite3` or Turso/libSQL.

## Use It

1. Copy `CLAUDE.md` into the root of a Next.js + SQLite project.
2. Make sure the project scripts match the command names in the template, or adjust only the command prefix.
3. Start Claude Code from the project root and ask it to inspect the app against the PR checklist.

## What It Covers

- App Router project structure.
- Component, action, query, migration, and table naming.
- SQLite connection, migration, transaction, and ownership rules.
- Server action, validation, auth, billing, UI, and testing patterns.
- Anti-patterns that commonly make SaaS projects harder for Claude Code to edit safely.

## Validation

The template was checked against the acceptance criteria in `VALIDATION.md`.
