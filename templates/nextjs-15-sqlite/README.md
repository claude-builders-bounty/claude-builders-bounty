# Next.js 15 + SQLite template

Copy `CLAUDE.md` to the root of a greenfield Next.js 15 App Router project. The default database choice is `better-sqlite3` on Node.js; the guide also says how to handle a project that has explicitly chosen Turso/libSQL.

The rules are intentionally opinionated around server-only data access, tenant authorization, append-only migrations, and SQLite's single-writer model. They are starter defaults; the repository's actual manifest, lockfile, and deployed database contract remain authoritative.

## Claude Code smoke test

1. Create a fresh Next.js 15 App Router project with TypeScript and copy `CLAUDE.md` into its root.
2. Start Claude Code in that project and paste the non-editing prompt and pass/fail checklist in [`../../verification/issue-2-claude-code-smoke.md`](../../verification/issue-2-claude-code-smoke.md).
3. Record the Claude Code version and the unedited response. Do not describe the smoke test as passed unless it was run in Claude Code with a real model session.

A Claude Code smoke test was run against a fresh Next.js 15.5.26 project on 2026-09-25. See the verification note and recorded output for the exact scope and result.
