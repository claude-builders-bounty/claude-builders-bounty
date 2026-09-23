# Real PR review outputs

The following structured outputs were produced from the diffs of two real public pull requests and are included as validation examples for the required review contract.

## PR #3885 — destructive Bash PreToolUse hook

Source: `https://github.com/claude-builders-bounty/claude-builders-bounty/pull/3885`

### Review output

## Summary

This PR adds a dependency-free Claude Code `PreToolUse` hook that detects destructive Bash and SQL command patterns, logs blocked attempts, and returns a deny decision. It also includes installation documentation and unit coverage for the required destructive-command cases.

## Identified risks

- The detection is intentionally text-based, so harmless shell commands that merely contain strings such as `DROP TABLE` or `TRUNCATE` can be denied even when those strings are only being echoed, documented, or passed as inert data.
- Logging failures are silently ignored; the destructive command is still blocked, but operators may believe every denied attempt was recorded when filesystem permissions or disk errors prevent that.

## Improvement suggestions

- Add regression tests for quoted/inert destructive-looking text and document the conservative false-positive behavior, or add lightweight shell-context handling if the hook is expected to distinguish executable SQL from plain text.
- Consider emitting a secondary warning when audit logging fails while preserving the deny decision.

## Confidence

High

---

## PR #3886 — Next.js + SQLite CLAUDE.md template

Source: `https://github.com/claude-builders-bounty/claude-builders-bounty/pull/3886`

### Review output

## Summary

This PR adds a comprehensive project-level `CLAUDE.md` for a Next.js 15 App Router SaaS using TypeScript and SQLite. The document gives explicit conventions for structure, naming, migrations, server/client boundaries, validation, authorization, testing, and completion criteria, with reasons attached to most rules.

## Identified risks

- The template says it is usable without modification but its definition of done requires scripts such as `npm run typecheck`, `npm test`, `db:generate`, and `db:migrate`; a fresh project may not define those scripts yet, which could cause Claude Code to follow commands that immediately fail.
- The database guidance allows either `better-sqlite3` or Turso/libSQL while also preferring Drizzle; without a single greenfield default, Claude may still need to decide between materially different deployment and driver paths.

## Improvement suggestions

- Define the exact starter `package.json` scripts expected by the template, or state that Claude should first add missing scripts before using them as completion checks.
- Choose one default greenfield database path and describe the alternative as an explicit migration/deployment option rather than an equal default.

## Confidence

High
