# Next.js SQLite SaaS CLAUDE.md Template

Opinionated Claude Code context for a greenfield SaaS app using Next.js 15 App Router, TypeScript, Tailwind CSS, and SQLite.

## Setup In 3 Steps

1. Copy `CLAUDE.md` into the root of a new Next.js 15 + SQLite project.
2. Add the scripts named in the Commands section to `package.json`.
3. Run a Claude Code task against a small feature request and verify it follows the stack, migration, and testing rules without asking setup questions already answered by the template.

## What It Covers

- Stack and version choices with reasons.
- Folder structure and ownership boundaries.
- SQLite connection, migration, transaction, and data-access rules.
- App Router, server action, component, auth, and security patterns.
- Anti-patterns with the reason each one is forbidden.

## Intended Use

Use this for a new SaaS repository before the first feature is built. It is intentionally specific so Claude Code can make local implementation decisions without repeatedly asking about structure, database patterns, validation, or test strategy.
