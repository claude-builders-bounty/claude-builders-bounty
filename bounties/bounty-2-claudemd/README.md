# CLAUDE.md — Next.js 15 + SQLite (better-sqlite3) SaaS Template

**Bounty #2 — claude-builders-bounty/claude-builders-bounty**

A production-ready, opinionated [CLAUDE.md](CLAUDE.md) template for greenfield Next.js 15 App Router SaaS projects using SQLite (better-sqlite3), Drizzle ORM, and TypeScript.

## What This Replaces

This CLAUDE.md replaces the default generic CLAUDE.md that ships with most project scaffolds. It's not a list of "nice to have" suggestions — it's a **rulebook** that guides every design decision: component architecture, database access patterns, folder layout, migration workflow, and anti-patterns to avoid (each with a concrete *why*).

Designed for the specific shape of a single-tenant, SQLite-backed SaaS: no PostgreSQL connection poolers, no raw SQL in route handlers, no `useEffect` data fetching, no barrel exports for types.

## Setup in 3 Steps or Fewer

### 1. Copy the template

```bash
cp CLAUDE.md /path/to/your/project/CLAUDE.md
```

### 2. Install dependencies

```bash
pnpm add next@15 react react-dom better-sqlite3 drizzle-orm drizzle-kit @types/better-sqlite3
pnpm add -D vitest @playwright/test eslint prettier
```

### 3. Initialize the database

```bash
# Create the schema directory
mkdir -p src/db/schema src/db/migrations

# Create a drizzle.config.ts from the template, then:
pnpm db:generate   # Generate initial migration
pnpm db:migrate    # Apply it
pnpm db:seed       # Seed with starter data
```

**That's it.** You now have a fully wired SaaS project skeleton with typed DB access, migration tooling, and a component architecture that defaults to Server Components.

> For a complete project scaffold including auth (NextAuth v5), billing (Stripe), and UI (Tailwind v4), see the companion [next-saas-starter](https://github.com/claude-builders-bounty/next-saas-starter) repository.
