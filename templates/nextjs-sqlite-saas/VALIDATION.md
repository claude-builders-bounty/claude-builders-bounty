# Validation Notes

Issue: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2

## Static Checks

The submitted `CLAUDE.md` was checked against the acceptance criteria:

- Covers stack and versions.
- Defines folder structure.
- Defines naming conventions.
- Defines SQLite, migration, and query rules.
- Defines component, server action, auth, testing, and error-handling patterns.
- Lists anti-patterns with reasons.
- Includes dev commands and completion checklist.
- Is specific to Next.js 15 App Router plus SQLite/Turso, not a generic project
  prompt.

## Paste Test Prompt

Use this prompt in a new Next.js 15 + SQLite project with the submitted
`CLAUDE.md` at the project root:

```txt
Read CLAUDE.md, then implement a workspace invite feature. Tell me which files
you would edit and which migration you would add before writing code.
```

Expected behavior:

- Claude should identify route/server-action/service/query boundaries.
- Claude should mention a numbered migration under `db/migrations/`.
- Claude should avoid putting SQL in React components.
- Claude should ask for missing product details only after stating the safe
  default structure.

I did not run a paid Claude Code model invocation for this validation because
the bounty can be reviewed from the submitted project-context artifact without
requiring paid API usage from the contributor.

