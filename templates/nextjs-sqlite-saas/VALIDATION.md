# Validation Notes

Issue: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2

## Acceptance Criteria Check

- Covers project structure: yes, in `Project Shape` and `Directory Conventions`.
- Covers naming conventions: yes, in `Naming Rules`.
- Covers DB migration rules: yes, in `SQLite Rules`.
- Includes dev commands: yes, in `Dev Commands`.
- Includes patterns to follow: yes, in `Data Access Pattern`, `App Router Rules`, `Authentication And Authorization`, `Validation`, `UI Pattern`, `Payment And Billing`, and `Testing Expectations`.
- Includes anti-patterns to avoid: yes, in `Anti-Patterns To Avoid`.
- Opinionated with reasons: yes, each major section explains why the rule exists.
- Usable without modification on a greenfield Next.js + SQLite project: yes, the template assumes common scripts and paths and avoids app-specific names.

## Greenfield Smoke Scenario

Expected project root after copy:

```text
CLAUDE.md
app/
components/
features/
lib/db/
migrations/
package.json
tests/
```

Prompt used for mental smoke test:

```text
Read CLAUDE.md and propose the first database-backed feature for this Next.js 15 + SQLite SaaS without asking clarifying questions.
```

The template gives Claude Code enough project structure, naming, database, validation, and test guidance to proceed without needing extra architecture clarification.
