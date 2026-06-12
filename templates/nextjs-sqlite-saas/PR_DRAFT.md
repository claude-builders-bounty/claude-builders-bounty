# Add Next.js 15 + SQLite SaaS CLAUDE.md template

/claim #2

Closes #2

## Summary

- Adds an opinionated `CLAUDE.md` for a greenfield Next.js 15 App Router SaaS project using SQLite with `better-sqlite3` or Turso/libSQL.
- Covers stack/version decisions, folder structure, naming conventions, SQL migration rules, data access, Server Components, Server Actions, auth boundaries, component patterns, testing, PR rules, and anti-patterns.
- Adds a local validator so reviewers can check the bounty acceptance criteria without manual checklist work.

## Validation

```bash
node templates/nextjs-sqlite-saas/validate-template.mjs
git diff --check
```

Claude Code smoke test:

```bash
claude -p --no-session-persistence --model sonnet --max-budget-usd 0.50 --disallowedTools=Bash,Edit,Write -- "Using this project's CLAUDE.md, plan the implementation for workspace creation in a greenfield Next.js 15 SQLite SaaS app. Do not modify files. Do not ask clarifying questions. Return concise bullets for migration, data access, Server Action, route/page, and tests."
```

Observed: Claude returned a direct implementation plan for migration, data access, Server Action, route/page, and tests without asking clarifying architecture questions.

## Notes

The template is deliberately non-generic: every architectural rule includes a reason, and it can be copied as-is to the root of a new Next.js 15 + SQLite SaaS repository.
