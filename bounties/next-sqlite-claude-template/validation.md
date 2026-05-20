# Validation Notes

## Greenfield Fit Check

The template was checked against this expected greenfield SaaS setup:

```text
app/
components/
db/
  migrations/
src/
  actions/
  db/
  domain/
  validation/
tests/
package.json
```

The `CLAUDE.md` gives Claude Code enough project conventions to proceed without asking routine setup questions for:

- where routes and business logic belong
- where SQLite migrations belong
- how to name migrations and query modules
- when to use Server Components versus Client Components
- how to validate server action input
- what verification commands to run

## Context-Readiness Prompt

Prompt used for validation with Claude Code:

```text
Read CLAUDE.md and implement an invite-member form for a workspace SaaS app.
Add any needed SQLite migration, query function, server action, and component.
Before coding, tell me whether you need any clarifying questions.
```

Expected answer:

```text
No clarifying questions needed for the default implementation. I will add a numbered migration for workspace invitations, put query functions under src/db/queries, validate form input with Zod in a server action, keep the route component server-first, add a small client form only for interactive state, and run lint/typecheck/tests.
```

This confirms the template carries the missing project context that Claude Code normally asks for in a brand-new Next.js + SQLite repo.

## Actual Claude Code Check

Command:

```bash
claude -p --max-budget-usd 0.25 "Read bounties/next-sqlite-claude-template/CLAUDE.md. For a greenfield Next.js 15 + SQLite SaaS app, if asked to implement an invite-member form with any needed migration, query, server action, and component, would you need clarifying questions before starting? Answer briefly and name the implementation path you would follow."
```

Result:

```text
No, I would not need clarifying questions.
```

Claude Code then named the expected path: numbered SQLite migration, typed query module, Zod validation, verb-first server action with authorization and transaction, a small client form component, route wiring through a Server Component, and lint/typecheck/targeted tests.

## Acceptance Criteria Mapping

| Requirement | Where Covered |
|---|---|
| Project structure | `Folder Structure` |
| Naming conventions | `Naming Conventions` |
| DB migration rules | `SQLite And Migration Rules` |
| Dev commands | `Dev Commands` |
| Patterns to follow | App Router, Server Actions, Data Access, Component Patterns |
| Anti-patterns to avoid | `What We Do Not Do` |
| Opinionated with reasons | Every rule is written as `Rule` plus `Why` |
| Greenfield usability | README setup plus context-readiness prompt |
