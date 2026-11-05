# CLAUDE.md for Next.js 15 + SQLite SaaS

An opinionated, production-ready `CLAUDE.md` for a typical SaaS built with
**Next.js 15 App Router + SQLite (better-sqlite3 / Turso)**. Drop it in a greenfield
repo and Claude Code has all the context it needs — no clarifying questions.

## Use (3 steps)
1. Copy `CLAUDE.md` to your project root.
2. (Optional) bump versions in §1 to match your lockfile.
3. Start Claude Code — it follows §1–§9 automatically.

## Covers
Stack & versions · commands · folder structure · naming conventions ·
**SQL / migration conventions** · component patterns · auth & security ·
testing · **what we don't do (and why)**.

## Design principle
Every rule states the failure it prevents. It is deliberately opinionated
(one router, one ORM, one data layer, server-first components, append-only
migrations, validated env) so the codebase stays consistent as it grows.

Tested by pasting into a fresh `create-next-app` + Drizzle + better-sqlite3 project:
Claude Code scaffolds features that match the structure without asking questions.
