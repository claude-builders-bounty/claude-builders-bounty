# CLAUDE.md — Next.js 15 + SQLite (Turso/Drizzle) SaaS Template

An opinionated, production-ready `CLAUDE.md` for SaaS projects using:

- **Next.js 15** (App Router, React 19, TypeScript 5)
- **SQLite** via Turso (production) / `better-sqlite3` (local)
- **Drizzle ORM** (explicit queries, zero runtime overhead)
- **NextAuth.js v5** with Drizzle adapter
- **Tailwind CSS v4** + `shadcn/ui`
- **Vitest** + **Playwright** for testing

## Usage

1. Copy `CLAUDE.md` into the root of your greenfield Next.js 15 + SQLite project
2. Open the project with Claude Code
3. Claude Code will understand the stack, conventions, patterns, and anti-patterns without additional prompting

## What's Covered

| Section | Details |
|---------|---------|
| Stack & Versions | Exact packages with rationale for every choice |
| Dev Commands | `npm run dev`, `db:generate`, `db:migrate`, etc. |
| Folder Structure | Full SaaS layout (auth groups, dashboard, multi-tenant orgs, webhooks) |
| Schema Patterns | Table templates, relations, cursor pagination, soft deletes, migrations |
| API Routes | Route handler patterns, Server Actions with `useActionState`, Zod validation |
| Component Patterns | RSC-first, Client Component boundaries, form patterns |
| Auth Pattern | Middleware, `requireAuth()`, `requireOrgMembership()`, webhook auth |
| Error Handling | `error.tsx`, `not-found.tsx`, `loading.tsx`, structured action returns |
| Testing | Vitest unit/integration patterns, Playwright E2E, mocking strategies |
| Anti-Patterns | 13 explicit don'ts with reasons (Prisma, barrel exports, global state, etc.) |
| Environment Variables | Full `.env.example` with validation strategy |
| Deployment | Vercel vs Fly.io guidance, migration pipeline, Edge vs Node runtime |
| Git Workflow | Commit convention, branch naming, PR description format |
