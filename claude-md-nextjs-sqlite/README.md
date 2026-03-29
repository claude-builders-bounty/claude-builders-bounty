# CLAUDE.md Template: Next.js 15 + SQLite SaaS

> A production-ready CLAUDE.md template for greenfield Next.js 15 + SQLite SaaS projects.

## What's Inside

This template is the result of building and shipping real SaaS products. Every rule has a reason. Every convention exists because someone made a bad decision in production and we decided to encode the lesson.

### Sections

| Section | What It Covers |
|---------|---------------|
| **Stack & Versions** | Exact package versions with rationale. No floating deps. |
| **Project Structure** | Folder layout for App Router, multi-tenant orgs, feature-based components |
| **Naming Conventions** | Files, variables, DB tables — with the "why" behind each rule |
| **SQL & Migration Conventions** | Drizzle ORM workflow, index strategy, SQLite-specific gotchas |
| **Component Patterns** | Server vs Client Components, data fetching, error handling |
| **What We DON'T Do** | Anti-patterns we actively avoid with better alternatives |
| **Development Commands** | `pnpm` scripts for dev, build, DB, and testing |
| **Deployment** | Where to deploy, which platforms to avoid, required env vars |

## Key Opinions

### 1. SQLite is a Real Database for SaaS

SQLite gets dismissed because it's "just a file." That's the feature. No network latency, no connection pooling, no "pg_hba.conf" headaches. For a SaaS with <10K concurrent users, SQLite is probably faster than PostgreSQL.

The tradeoff: you need a deployment platform with persistent disk (Railway, Fly.io), not ephemeral storage (Vercel Hobby).

### 2. Server Components by Default

Next.js App Router defaults to Server Components. We lean into this. If a component doesn't need interactivity, browser APIs, or real-time data, it stays on the server. Result: smaller JS bundles, faster landing pages, simpler code.

### 3. One Schema File Per Domain

Not one giant `schema.ts`. One file per domain (`users.ts`, `organizations.ts`, `subscriptions.ts`). This makes PRs smaller, reviews faster, and merge conflicts rare.

### 4. Migrations Are Sacred

We never touch the database manually in production. Every schema change is a migration. If you need a hotfix, you write a migration and ship it with the deploy.

### 5. Anti-patterns as Rules

We explicitly list what we DON'T do, with the better alternative:
- Don't build auth from scratch → use Lucia + Arctic
- Don't add Elasticsearch → use SQLite FTS5 (already built in)
- Don't use Context for server data → pass data as props
- Don't use `console.log` → use structured logging

## Usage

Copy `CLAUDE.md` to the root of a new Next.js 15 project. That's it.

```bash
# After creating your Next.js project:
cp claude-md-nextjs-sqlite/CLAUDE.md ./CLAUDE.md
```

The template assumes:
- `src/app` for App Router pages (Next.js 15 default)
- `pnpm` as package manager
- `better-sqlite3` + Drizzle ORM for database
- Tailwind CSS for styling

## Requirements Check

✅ Covers project structure  
✅ Covers naming conventions  
✅ Covers DB migration rules  
✅ Includes dev commands  
✅ Includes patterns to follow  
✅ Includes anti-patterns to avoid  
✅ Opinionated — every rule has a reason  
✅ Usable without modification on greenfield project  
✅ Stack & versions section  
✅ Folder structure section  
✅ SQL/migration conventions section  
✅ Component patterns section  
✅ What we don't do section  

## Contributing

Found a rule that's wrong for your use case? That's expected — this is an opinionated template. Fork it, remove the rules you disagree with, add the ones you've learned the hard way.

The goal is a template that encodes decisions so your team doesn't have to make the same 20 choices on every new project.

## Bounty

This template was created for [Issue #2](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2) in the claude-builders-bounty repo.

**Author:** lam1688  
**Wallet:** 0x4304329306B8Ab663888705818A0baAA8297f1E9  
**Bounty:** $75
