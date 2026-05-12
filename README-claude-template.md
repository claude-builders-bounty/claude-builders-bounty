# Next.js 15 + SQLite CLAUDE.md Template

This submission provides a production-oriented `CLAUDE.md` for a greenfield SaaS product built with Next.js 15 App Router and SQLite.

## Why it is opinionated

- It assumes `better-sqlite3` and Drizzle instead of leaving the database layer vague.
- It treats workspace scoping and server-side auth as first-class constraints.
- It forbids common SaaS failure modes such as route-level raw SQL and client-side-only authorization.
- Every section explains the reason behind the rule so Claude Code can act without asking generic follow-up questions.

## Setup

1. Create a new Next.js 15 TypeScript project
2. Add this `CLAUDE.md` at the repo root
3. Open the project in Claude Code

## Validation

Use this prompt after adding `CLAUDE.md`:

```text
Add a workspace settings page with a form to rename the current workspace and store the update in SQLite.
```

Expected behavior:

- Claude should place route code in `app/`
- keep schema and queries under `db/`
- validate input with Zod
- preserve workspace scoping
- avoid asking broad stack-setup questions
