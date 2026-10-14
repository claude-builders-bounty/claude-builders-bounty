# CLAUDE.md — Next.js 15 App Router + SQLite (Turso / Drizzle) SaaS Standards

This document establishes the non-negotiable architectural rules, conventions, and operational commands for this codebase. Every rule is motivated by production reliability and edge compatibility.

---

## 1. Core Stack Architecture
- **Framework:** Next.js 15 (App Router, Server Actions, React Server Components by default).
- **Runtime:** Node.js 20+ (LTS) or Cloudflare Workers / Edge where applicable.
- **Database:** SQLite via LibSQL / Turso (`@libsql/client`) for local & edge replication.
- **ORM:** Drizzle ORM (`drizzle-orm`) with `drizzle-kit` for type-safe schema & migrations.
- **Auth:** Auth.js v5 or Lucia Auth (cookie-based session stored in SQLite).
- **Styling & UI:** Tailwind CSS v4 + Radix UI primitives.

---

## 2. Project Directory Structure
```
├── src/
│   ├── app/                 # Next.js 15 App Router pages & server routes
│   │   ├── (auth)/          # Route group: login, register, forgot-password
│   │   ├── (dashboard)/     # Route group: protected customer dashboard
│   │   ├── api/             # API handlers (webhooks & public REST only)
│   │   └── layout.tsx       # Root layout (RSC)
│   ├── components/          # Reusable UI components
│   │   ├── ui/              # Primitive atom components (button, input, modal)
│   │   └── shared/          # Composite domain components
│   ├── db/                  # Database layer
│   │   ├── schema/          # Modular Drizzle schemas (users.ts, teams.ts, billing.ts)
│   │   ├── index.ts         # Client singleton with connection pooling guard
│   │   └── migrations/      # Versioned SQL migration files
│   ├── lib/                 # Core utilities, validation schemas (Zod), and auth config
│   └── actions/             # Next.js 15 Server Actions (mutations with zod validation)
```

---

## 3. Mandatory Development Commands
```bash
# Development
pnpm dev              # Start local dev server with Turbopack (http://localhost:3000)
pnpm build            # Production type-check & standalone build
pnpm lint             # ESLint + Prettier check

# Database (Drizzle + SQLite)
pnpm db:generate      # Generate SQL migrations from src/db/schema/*.ts
pnpm db:migrate       # Apply pending migrations to local/remote SQLite
pnpm db:studio        # Open Drizzle Studio visual inspector

# Testing
pnpm test             # Run Vitest test suite
pnpm test:e2e         # Run Playwright end-to-end tests
```

---

## 4. Coding Patterns & Conventions

### Server Components vs. Client Components
- **Default to RSC:** Every component in `app/` and `components/` is a Server Component unless interactive browser APIs (hooks, state, event listeners) are strictly needed.
- **Leaf Client Components:** Push `"use client"` down to the smallest possible leaf component. Never mark layout or page root as `"use client"`.

### Data Mutations (Server Actions)
- Always write mutations inside `src/actions/` with `"use server"`.
- Every action must validate input arguments with **Zod** before touching the database.
- Always wrap mutations in `revalidatePath()` or `revalidateTag()` to maintain cache freshness.

### SQLite Database Rules
- **No In-Memory DB in Prod:** Always persist SQLite files to a durable volume or Turso remote URL.
- **WAL Mode Required:** For local `better-sqlite3`, enforce `PRAGMA journal_mode = WAL;` and `PRAGMA busy_timeout = 5000;` on startup to prevent lock contention under concurrent read/write traffic.
- **Strict Migrations:** Never edit applied migration files in `src/db/migrations/`. Always generate a new migration with `pnpm db:generate`.

---

## 5. Anti-Patterns to Avoid
1. ❌ **Do NOT call `fetch()` to internal `/api` routes from Server Components:** Call the database or service function directly inside RSC. Internal HTTP calls create redundant TCP roundtrips.
2. ❌ **Do NOT leak database clients across Serverless invocations:** Use a module-level global singleton pattern to reuse the LibSQL client connection.
3. ❌ **Do NOT store secrets or financial keys in client bundles:** Keep all API keys in server-only modules (`import "server-only"`).
4. ❌ **Do NOT use raw SQL string interpolation:** Always use Drizzle parameter binding or SQL tagged template literals to eliminate SQL injection vulnerabilities.
