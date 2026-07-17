# Next.js 15 + SQLite SaaS — CLAUDE.md template

Opinionated agent instructions for a greenfield SaaS app (App Router + SQLite).

## Setup (3 steps)

1. Create or open a Next.js 15 App Router project.
2. Copy `CLAUDE.md` from this folder to your **repo root**.
3. Open Claude Code in that repo — it should pick up the stack without asking which router/DB you use.

## What you get

- Stack + versions with reasons
- Folder layout agents can navigate
- SQL migration rules (append-only, bound params, cents for money)
- Component / server patterns and explicit “don’ts”
- Dev commands and agent verification loop

## Test notes

Validated by reading the file as the sole project context: a greenfield agent should not ask “Pages vs App Router?” or “Postgres vs SQLite?” — those decisions are fixed here.

For a live smoke, paste onto a fresh `create-next-app@15` repo and start a task like “add a users table migration + list route”; the agent should follow `db/migrations/` + server components without inventing microservices.
