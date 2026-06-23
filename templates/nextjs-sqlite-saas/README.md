# Next.js 15 + SQLite SaaS guide

This folder contains an opinionated `CLAUDE.md` for a greenfield SaaS project built with Next.js 15 App Router, TypeScript, and SQLite through either `better-sqlite3` for local/server deployments or Turso/libSQL for hosted edge-friendly deployments.

## Use it

1. Copy `CLAUDE.md` into the root of a new Next.js 15 project.
2. Update the app name, environment variable names, and auth/provider details.
3. Run Claude Code from the project root so it reads the file before changing code.

## Why this template is strict

The rules are intentionally narrow so generated work stays consistent across routes, database access, migrations, server actions, and UI components.
