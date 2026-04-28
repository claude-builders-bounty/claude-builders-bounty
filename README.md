# Claude Builders Bounty 🤖
# Bounty #2: CLAUDE.md Template — Next.js 15 + SQLite SaaS

> An opinionated, production-ready `CLAUDE.md` for building SaaS applications with **Next.js 15 App Router** and **SQLite (better-sqlite3 via Drizzle ORM)**.

📁 **File:** [`CLAUDE.md`](./CLAUDE.md)

## What's Inside

| Section | What It Covers |
|---|---|
| **Stack & Versions** | Exact toolchain choices (Next.js 15, TypeScript strict, Drizzle, better-sqlite3, NextAuth v5, Tailwind v4, shadcn/ui, Vitest, Playwright, pnpm) — every choice has a why |
| **Folder Structure** | Opinionated `src/` layout with domain-based schema files, separated actions/ lib/ /components/ — with rationale for each decision |
| **Naming Conventions** | Table: files, components, functions, DB tables/columns, foreign keys, env vars, routes — with reasoning per rule |
| **SQL / Migration Conventions** | Drizzle schema patterns, `created_at`/`updated_at` timestamps, soft delete policy, `text`-for-everything in SQLite, migration workflow, query patterns |
| **Component Patterns** | Server Components by default, the composition boundary ("lifting data, lowering interactivity"), Server Actions instead of API routes, `useActionState` form pattern — with ✅/❌ code examples |
| **What We Don't Do (And Why)** | 7 explicit anti-patterns: no Redux/Zustand/Jotai, no tRPC, no Prisma, no barrel files, no CSS-in-JS, no `useEffect` for data fetching, no custom auth hooks |
| **Dev Commands** | Complete command reference for dev, DB, quality, testing, build — plus a CI workflow YAML |
| **Testing Philosophy** | What to test (server actions, forms, middleware, schema) and what not to test (UI primitives, static pages, third-party APIs) |
| **Security Rules** | 5 concrete security rules — CSRF, Zod validation, session revalidation, log redaction, rate limiting |
| **Error Handling Pattern** | Full `try/catch` Server Action example with consistent `{ success, error }` return shape |

## How to Use

1. Create a new Next.js 15 project with the stack above
2. Copy [`CLAUDE.md`](./CLAUDE.md) into the project root
3. Claude Code (or any AI agent) will understand the conventions and generate code that matches

The template is designed to work **without modification** on any greenfield Next.js 15 + SQLite SaaS project.

---

## Other Bounties

| # | Task | Amount | Status |
|---|------|--------|--------|
| [#1](../../issues/1) | SKILL: Generate a CHANGELOG from git history | $50 | 🟢 Open |
| [#2](../../issues/2) | TEMPLATE: CLAUDE.md for a Next.js + SQLite project | $75 | 🟢 Open |
| [#3](../../issues/3) | HOOK: Block destructive bash commands in Claude Code | $100 | 🟢 Open |
| [#4](../../issues/4) | AGENT: PR reviewer with structured Markdown output | $150 | 🟢 Open |
| [#5](../../issues/5) | WORKFLOW: n8n + Claude API — automated weekly dev summary | $200 | 🟢 Open |

---

*Started by the Claude builder community · March 2026 · MIT License*