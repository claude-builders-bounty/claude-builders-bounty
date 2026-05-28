# CLAUDE.md Template — Next.js + SQLite SaaS

A production-ready `CLAUDE.md` template for Next.js 15 App Router + SQLite
(Turso) SaaS projects. Designed to be dropped into a greenfield project and
used immediately — every rule has a reason, every convention has a rationale.

## What This Is

`CLAUDE.md` is a project-level instruction file read by Claude (via Claude
Code, Cursor, or any MCP-compatible AI coding tool) at the start of every
session. It establishes:

- The tech stack and why each choice was made
- The exact folder structure to follow
- Database schema and migration rules
- Naming conventions across the entire codebase
- Patterns to follow and anti-patterns to avoid
- Dev commands for common workflows

## Quick Start

```bash
# Copy the template into your project root:
cp /path/to/this/repo/CLAUDE.md ./CLAUDE.md

# If you're starting a new project from scratch, create alongside it:
mkdir my-saas && cd my-saas
cp /path/to/this/repo/CLAUDE.md .

# Initialize your Next.js project and follow the Getting Started
# section at the bottom of CLAUDE.md
```

## What's Covered

| Section                     | Contents                                                       |
| --------------------------- | -------------------------------------------------------------- |
| Stack & Versions            | Every library with version constraints and justification       |
| Project Structure           | Full directory tree with rationale for each decision           |
| Database & SQL Conventions  | Schema rules, migration discipline, query patterns             |
| Component Patterns          | Server-first, client-when-necessary, forms, error boundaries   |
| Naming Conventions          | Table of every named thing in the project                      |
| Dev Commands                | `pnpm` scripts for dev, DB, testing, build, Stripe             |
| Environment Variables       | Zod-validated env setup pattern                                |
| What We Don't Do            | Anti-patterns table with reasons                               |
| Auth Guard Pattern          | Layout-level + action-level auth gating                        |
| Billing & Subscription      | Stripe Checkout, webhooks, customer ID storage                 |
| Getting Started             | Step-by-step greenfield bootstrap                              |

## Stack Decisions

| Concern     | Choice      | Alternative Considered            |
| ----------- | ----------- | --------------------------------- |
| Database    | Turso       | better-sqlite3 (local only), Neon (Postgres) |
| ORM         | Drizzle     | Prisma (heavier), Kysely (lower-level)      |
| Auth        | Better Auth | NextAuth v5, Clerk (not self-hostable)      |
| Styling     | Tailwind 4  | CSS Modules, Panda CSS                     |
| Validation  | Zod         | Valibot (newer, smaller bundle)             |

These choices are opinionated but not arbitrary — they prioritize
production-readiness, SQLite compatibility, and the Next.js server-component
model.

## Customizing for Your Project

The template is usable without modification, but you'll likely want to:

1. **Replace `Turso` with `better-sqlite3`** if you're deploying to a single
   server (e.g., a VPS). Change the database section to reflect local file
   paths and remove Turso-specific commands.
2. **Remove `trigger.dev`** if you don't need background jobs yet — it's
   marked optional.
3. **Adjust route groups** if your SaaS has different navigation (e.g., add
   `(admin)` or rename `(dashboard)` to `(app)`).
4. **Add domain-specific sections** — if your SaaS revolves around documents,
   add a `Documents & Storage` section with your S3/R2 upload patterns.

## Why This Exists

Most AI coding assistants produce better code when they understand the
project's conventions. Without a `CLAUDE.md`:

- Components get scattered between `src/` and project root
- Database queries mix raw SQL with ORM calls
- Auth checks are inconsistent or missing
- Server actions grow into 200-line untestable monoliths
- Naming drifts across files

With one, every session starts from the same set of rules — like an automated
onboarding doc for every AI contributor.

## Contributing

If you find a rule that doesn't hold up in practice or a pattern that should
be added, open an issue or PR. The goal is a living document that reflects
real production experience, not theoretical best practices.
