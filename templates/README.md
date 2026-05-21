# CLAUDE.md Template: Next.js 15 + SQLite SaaS

A production-ready, opinionated `CLAUDE.md` template for greenfield SaaS projects built with Next.js 15 App Router and SQLite.

## Quick Start

```bash
# 1. Copy to your project root
cp templates/CLAUDE-nextjs-sqlite.md /path/to/your-project/CLAUDE.md

# 2. Customize the project name and any specifics
# 3. Start using Claude Code — it now understands your entire stack
```

## What It Covers

- **Stack & Versions**: Next.js 15, TypeScript, SQLite (better-sqlite3/Turso), Drizzle ORM, NextAuth v5, Tailwind CSS, Zod, Stripe, Resend
- **Project Structure**: App Router directory layout with clear separation of concerns
- **Naming Conventions**: Files, components, database tables, server actions, types
- **Database Rules**: Migration workflow, query patterns, indexing strategy, prepared statements
- **Component Patterns**: Server-first architecture, client boundaries, form handling
- **Dev Commands**: All the npm scripts you need (dev, db, lint, test, stripe)
- **Do's and Don'ts**: 8 practices we follow and 8 anti-patterns we avoid, each with a clear reason
- **Auth Patterns**: Server component auth checks, server action guards, middleware configuration
- **Error Handling**: Discriminated unions, error boundaries, logging strategy
- **Environment Variables**: Required and optional env vars with descriptions
- **Testing**: Unit, integration, and E2E testing strategy

## Opinionated Design

Every rule in this template has an explicit reason. The goal is for Claude Code to understand not just *what* to do, but *why* — so it can make correct decisions in novel situations without asking clarifying questions.

## Testing the Template

1. Create a new Next.js 15 project: `npx create-next-app@latest test-project`
2. Copy this CLAUDE.md to `test-project/CLAUDE.md`
3. Install dependencies: `npm install better-sqlite3 drizzle-orm drizzle-kit`
4. Start Claude Code in the project directory
5. Ask Claude to add a database table or create a server action
6. Verify it follows the conventions without needing clarification
