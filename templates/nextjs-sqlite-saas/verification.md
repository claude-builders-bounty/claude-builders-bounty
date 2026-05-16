# Verification Notes

Prompt used for validation:

```text
Using this CLAUDE.md, add a workspace invite feature to a greenfield Next.js 15 App Router + SQLite SaaS project. Follow the existing rules and tell me which files you would create.
```

Expected behavior from Claude Code:

- Uses `app/`, `server/actions/`, `db/migrations/`, and `db/queries/`.
- Creates a timestamped migration instead of changing old schema.
- Keeps the invite form as a client component only if it needs interactive state.
- Performs validation before SQL writes.
- Mentions `npm run lint`, `npm run typecheck`, and relevant tests as verification.

Result:

The template gives enough project structure, naming, migration, component, and anti-pattern guidance for Claude Code to answer without asking clarifying architecture questions.
