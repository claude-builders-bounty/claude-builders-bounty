# Next.js + SQLite SaaS CLAUDE.md Template

This bounty deliverable is an opinionated `CLAUDE.md` for a greenfield SaaS app using Next.js 15 App Router and SQLite.

It covers:

- stack and version assumptions
- folder structure and naming conventions
- SQLite, Drizzle, and migration rules
- Server Component, Server Action, and Route Handler patterns
- auth, tenancy, validation, testing, and error handling
- anti-patterns with reasons

## Use

Copy `CLAUDE.md` into the root of a new Next.js 15 + SQLite SaaS project.

## Validation

Run the smoke check:

```bash
bash validation/check-template.sh
```

Then use the prompt in `validation/greenfield-prompt.md` from a fresh project root after copying in `CLAUDE.md`. Passing behavior is that Claude Code can infer the stack, file layout, migration policy, component defaults, and commands without needing clarifying questions for ordinary greenfield implementation work.
