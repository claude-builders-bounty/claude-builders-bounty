# CLAUDE.md For Next.js 15 + SQLite SaaS

This folder contains an opinionated `CLAUDE.md` template for a greenfield SaaS project using Next.js 15 App Router and SQLite.

## Install

1. Copy `CLAUDE.md` into the root of a Next.js 15 + SQLite project.
2. Adjust command names only if the project uses a different package manager.
3. Start Claude Code from the project root.

## Scope

The template covers:

- stack and expected versions
- folder structure
- server/client boundaries
- SQLite and migration conventions
- Server Actions and Route Handlers
- auth, sessions, and permission checks
- component patterns
- testing and PR expectations
- anti-patterns with reasons

## Test Note

This template is designed to be usable without modification for a typical greenfield Next.js 15 App Router SaaS app using SQLite through `better-sqlite3` or Turso/libSQL.
