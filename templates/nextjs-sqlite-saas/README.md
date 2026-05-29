# Next.js + SQLite SaaS CLAUDE.md Template

Opinionated Claude Code project instructions for a greenfield SaaS using Next.js 15 App Router and SQLite.

## Setup

1. Copy `CLAUDE.md` into the root of a Next.js 15 + SQLite project.
2. Adjust package manager commands only if the project does not use `pnpm`.
3. Run Claude Code from the project root and ask it to inspect the app before making changes.

## What It Covers

- Stack and version assumptions
- Folder structure and naming conventions
- SQLite schema and migration rules
- App Router, component, and server action patterns
- Auth, tenancy, validation, security, testing, and PR expectations
- Anti-patterns with reasons

## Validation Notes

This template was checked against a greenfield `create-next-app` style SaaS layout with SQLite-oriented `src/db`, `src/server`, and `src/features` folders. The instructions are self-contained and should not require Claude Code to ask for missing project conventions before starting routine implementation work.
