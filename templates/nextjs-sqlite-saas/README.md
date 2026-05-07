# nextjs-sqlite-saas — opinionated CLAUDE.md template

A drop-in `CLAUDE.md` for a SaaS project built on **Next.js 15 App Router + SQLite (better-sqlite3 / Drizzle)**.

## What you get

- A working operating manual for Claude Code (and humans) covering: stack & versions, folder structure, SQL & migration conventions, component patterns, dev commands, and an "anti-patterns" list.
- Every rule has a one-line *why*. No generic advice.
- Tested against a fresh `create-next-app` + Drizzle + better-sqlite3 setup — Claude Code understands the context without asking clarifying questions.

## Use

```sh
curl -L https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/templates/nextjs-sqlite-saas/CLAUDE.md -o CLAUDE.md
```

Then start a Claude Code session in the project root. Done.

## When to fork it

The template is opinionated but the opinions are written down. Disagree with one? Edit the rule **and update its rationale comment** so future-you (or a different agent) doesn't undo the change.

## Sections covered

1. Stack & versions
2. Folder structure
3. SQL / migration conventions
4. Component patterns
5. Dev commands
6. What we **don't** do (and why)
7. Patterns to follow
8. Anti-patterns
9. When the agent is stuck

## License

MIT, matches the parent repo.
