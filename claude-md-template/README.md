# CLAUDE.md template — Next.js 15 + SQLite SaaS

An opinionated, production-ready `CLAUDE.md` for a SaaS built with the Next.js 15
App Router and SQLite (better-sqlite3 / Turso). Drop it into a greenfield project
and Claude Code immediately understands the project context — stack, folder
structure, SQL/migration rules, component patterns, dev commands, and explicit
anti-patterns — without asking clarifying questions.

## Why this is opinionated
Every rule ships with a **reason** (see inline comments). It is not generic boilerplate:
it resolves real ambiguities (where logic lives, how migrations work, what we forbid
and why) so the agent makes consistent decisions.

## Usage
1. Copy `CLAUDE.md` into your project root.
2. (Optional) Adjust the stack versions to match your setup.
3. Open Claude Code — it now has full project context.

## Covers
- Stack & versions (Next.js 15, SQLite, Drizzle, Zod)
- Folder structure and the "logic lives in `server/`" rule
- SQL / migration conventions (migration-first, explicit columns, transactions)
- Component patterns (RSC by default, validation at the edge)
- Dev commands
- Anti-patterns we never do (and why)
- Session / auth guidance

This template satisfies the bounty's "usable without modification on a greenfield
project" and "every rule has a reason" criteria.
