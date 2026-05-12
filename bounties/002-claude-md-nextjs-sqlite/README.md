# Bounty #2 — CLAUDE.md for Next.js 15 + SQLite SaaS

Closes #2

## What this is

An opinionated `CLAUDE.md` for a greenfield B2B SaaS app built with:

- **Next.js 15** App Router + React Server Components
- **SQLite** / Turso libSQL for the database
- **Drizzle ORM** with checked-in SQL migrations
- **Better Auth** for multi-tenant session management
- **TypeScript** `strict: true`, Zod, pnpm, Vitest + Playwright

## Why it stands out

Every rule includes an explicit reason. The file answers not just *what* to do but *why this choice over the obvious alternative* — so Claude Code never needs to ask a clarifying question like "should I use Prisma or Drizzle?" or "is this a client or server component?"

The **"What We Don't Do (and Why)"** table is a first-class section covering 12 common mistakes with explicit rationale, so Claude Code can reject anti-patterns without being asked.

## Acceptance Criteria Coverage

| Criterion | How it's addressed |
|-----------|-------------------|
| Stack & versions | Table with every layer and the reason for each choice |
| Dev commands | All 10 commands with descriptions |
| Folder structure | Annotated tree + rules about what goes where |
| Naming conventions | Table for files, components, DB, env vars |
| DB migration rules | Append-only rule, naming, generate/migrate workflow |
| Component patterns | Server vs Client decision rule + code examples |
| Anti-patterns to avoid | 12-entry "What We Don't Do (and Why)" table |
| Usable without modification | Concrete — specifies pnpm, Drizzle, Better Auth, cuid2 |

## Test

Paste `CLAUDE.md` into a fresh Next.js 15 project root. Open Claude Code and ask:

> "Add an invite-member feature: a form that sends an invite email and creates a pending member record."

Claude Code should:
1. Create the migration without prompting for DB choice
2. Add the query in `src/db/queries/organizations.ts` without asking
3. Add the Server Action in `src/server/actions/organizations.action.ts` with Zod validation
4. Not ask about state managers, not use `useEffect` for data, not use `any`

No clarifying questions needed — everything is decided in the CLAUDE.md.
