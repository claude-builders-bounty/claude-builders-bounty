# TEMPLATE: CLAUDE.md for Next.js 15 + SQLite SaaS

> Bounty #2 — $75 | [Issue Link](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2)

## Setup (1 step)

```bash
cp CLAUDE.md /path/to/your/nextjs-project/CLAUDE.md
```

That's it. Claude Code reads it automatically when you open the project.

## What's inside

| Section | Content |
|---------|---------|
| **Stack** | Next.js 15, SQLite, Drizzle ORM, NextAuth v5, Tailwind, TypeScript |
| **Project Structure** | Full tree with explanations for every directory choice |
| **Naming Conventions** | Table with convention, example, and reasoning for each |
| **Database & Migrations** | Schema patterns, 6 migration rules, connection singleton with WAL mode |
| **Dev Commands** | All commands with what they do |
| **Component Patterns** | Server Components, Client Components, Server Actions with real code examples |
| **Anti-Patterns** | 12 specific "don'ts" — each with BAD/GOOD code comparison and explanation |
| **Environment Variables** | Template with prefix rules explained |
| **Performance Rules** | 5 rules with reasoning |

## What makes this different

Every single rule has a **"Why"** explanation. Not just "do this" but "do this because...":

- *"Why WAL mode? Without it, SQLite blocks all reads during a write."*
- *"Why UUIDs? Safe for multi-device sync, no ID collision when merging databases."*
- *"Why no useEffect for fetching? Causes loading spinners, layout shift, and waterfalls."*

## Tested

Created a fresh Next.js 15 project, dropped in the CLAUDE.md, and asked Claude Code to:
1. "Set up the database" — it followed the schema.ts pattern exactly
2. "Create a user CRUD" — used Server Components + Server Actions as documented
3. "Add a new table" — created migration following the numbered convention

Claude understood the codebase context without asking clarifying questions.

## Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | The template (drop into any Next.js 15 + SQLite project) |
| `README.md` | This file |
| `HOW-TO.md` | Detailed customization guide |
