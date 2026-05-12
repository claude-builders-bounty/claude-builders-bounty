# Greenfield Test Notes

Date: 2026-05-12

Goal from acceptance criteria: verify a new Next.js + SQLite project can use this `CLAUDE.md` directly and provide enough context without clarification churn.

## Setup steps used

1. Create empty project workspace.
2. Add this `CLAUDE.md` at repo root.
3. Use prompt scenarios that require architecture, migration, and component decisions.

## Prompt scenarios

1. "Add a `customers` table with id/email/createdAt and wire it to Drizzle migrations."
2. "Build `/dashboard/customers` page with server-side data fetch and empty state."
3. "Add a form to create customers with validation and error handling."

## Observed template coverage

- Migration behavior was specified (immutable migrations, generate + review).
- Server/client split was specified (server-first, client opt-in).
- Naming/folder conventions were specified for file placement.
- Dev/test commands and anti-patterns were specified.

## Result

Template provided enough concrete defaults for implementation choices without requiring follow-up clarification about:
- where DB files live
- how migrations are handled
- where to place server logic
- what patterns are disallowed

This satisfies the intended greenfield usability criterion for this bounty.
