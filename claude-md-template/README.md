# CLAUDE.md Template for Next.js + SQLite SaaS Projects 📋

An opinionated, production-ready `CLAUDE.md` for greenfield Next.js 15 + SQLite SaaS projects.

## What's Included

- **Tech stack** with rationale — every choice has a reason
- **Project structure** — complete directory layout with explanations
- **Naming conventions** — components, files, DB tables, branches
- **DB migration rules** — how to create, run, and manage migrations
- **Component patterns** — server components, client components, server actions, API routes
- **Anti-patterns** — what we don't do and why (ORMs, barrel exports, `@apply`, etc.)
- **Commands** — dev, build, test, database, linting
- **Gotchas** — SQLite concurrency, Server Component limits, caching

## Usage

1. Copy `CLAUDE.md` to your project root
2. Replace `[Project Name]` with your project's name
3. Commit it — Claude Code reads it automatically

That's it. Claude Code will now understand your stack, conventions, and patterns without asking clarifying questions.

## Why Opinionated?

Generic templates tell Claude "use TypeScript" and leave it at that. This template tells Claude:

- **Why** we use raw SQL instead of Prisma
- **Why** Server Components are the default
- **Why** we don't use `any` or barrel exports
- **Why** SQLite writes must be serialized

Every rule has a reason. Claude follows rules better when it understands the reasoning.

## Customization

### Minimal Version

Keep only:
- Project Overview
- Commands
- Key conventions from "Patterns to Follow"

### Extended Version

Add:
- Deployment instructions (Vercel, Fly.io, Railway)
- Environment variable docs
- Architecture decision records
- Team-specific conventions

## License

MIT
