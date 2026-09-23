# CLAUDE.md — Next.js 15 App Router + SQLite SaaS Blueprint

> **System Prompt & Coding Guidelines for Claude Code**
> Production-tested, zero-fluff blueprint optimized for high-performance SaaS applications with Next.js 15 (React 19 Server Components) and SQLite (`better-sqlite3` / Turso LibSQL).

---

## 🛠️ Stack & Verified Versions

- **Framework**: Next.js 15+ (App Router, Server Actions, React 19)
- **Language**: TypeScript 5.5+ (Strict mode, no `any`)
- **Database**: SQLite via `better-sqlite3` (local / embedded) or `@libsql/client` (Turso edge)
- **ORM / Query Builder**: Drizzle ORM / Kysely (typed, zero-overhead SQL)
- **Styling**: Tailwind CSS v4 + `shadcn/ui` (Radix UI primitives)
- **Authentication**: Lucia Auth or NextAuth v5 (Server-first sessions)
- **Validation**: Zod for schemas and action input validation

---

## 📁 Standard Folder Structure

```text
.
├── app/                        # Next.js App Router
│   ├── (auth)/                 # Route group: login, signup, verify
│   ├── (dashboard)/            # Route group: authenticated SaaS dashboard
│   │   ├── layout.tsx          # Dashboard shell with sidebar & user nav
│   │   └── page.tsx            # Analytics / metrics overview
│   ├── api/                    # Webhooks & public REST API endpoints
│   ├── layout.tsx              # Root layout (fonts, providers, toaster)
│   └── page.tsx                # Marketing landing page
├── components/
│   ├── ui/                     # Primitives (button, dialog, input via shadcn)
│   ├── forms/                  # State-managed client form components
│   └── shared/                 # Navbar, footer, user avatar, data tables
├── db/
│   ├── schema/                 # Drizzle / SQLite table definitions
│   │   ├── auth.ts             # Users, sessions, accounts
│   │   ├── billing.ts          # Subscriptions, customer IDs, usage
│   │   └── index.ts            # Consolidated schema export
│   ├── migrations/             # Timestamped SQL migration files
│   └── index.ts                # Database client connection pool (WAL mode)
├── lib/
│   ├── actions/                # Next.js Server Actions ('use server')
│   ├── auth/                   # Session verification & role guards
│   ├── utils.ts                # cn helper and date formatters
│   └── validations/            # Zod validation schemas
└── types/                      # Shared TypeScript domain types
```

---

## ⚡ Developer Commands

```bash
npm run dev           # Start Next.js dev server on http://localhost:3000
npm run build         # Production typecheck and build
npm run lint          # Run ESLint + Prettier check
npm run db:generate   # Generate SQLite SQL migration from schema diff
npm run db:migrate    # Apply pending SQL migrations
npm run db:studio     # Launch Drizzle Studio DB viewer
npm test              # Run Vitest unit & integration test suite
```

---

## 💾 SQLite & Database Rules

1. **WAL Mode is Mandatory**: Always enable `PRAGMA journal_mode = WAL;` and `PRAGMA busy_timeout = 5000;` on startup to support concurrent reads while writing.
2. **Foreign Keys Enforced**: Always execute `PRAGMA foreign_keys = ON;` upon initializing SQLite connections.
3. **Strict Migrations**: Never mutate existing migration files. Create new forward-only migration files for any schema change.
4. **Colocation of Schema**: Group related tables into modular schema files under `db/schema/`.

---

## 🧩 Architectural Patterns to Follow

- **Server-First by Default**: Keep components as React Server Components (RSC). Only add `'use client'` at the lowest possible leaf node (e.g., interactive buttons, forms).
- **Mutations via Server Actions**: Perform all mutations inside `lib/actions/*.ts` with `'use server'`, validating inputs with Zod before running queries.
- **Optimistic UI**: Use `useOptimistic` and `useTransition` for snappy client-side state updates.
- **Typed Response Envelope**: Return standard `{ success: boolean, data?: T, error?: string }` from all Server Actions.

---

## 🚫 Anti-Patterns & What We Avoid (And Why)

| Anti-Pattern | Why We Avoid It | Correct Alternative |
|---|---|---|
| **`useEffect` for data fetching** | Causes client waterfalls, SEO penalty, layout shifts | Fetch directly inside React Server Components |
| **`any` or `as unknown as T`** | Bypasses compiler safety, introduces runtime type crashes | Use strict Zod schema parsing (`schema.parse()`) |
| **Route Handlers (`/api/*`) for internal UI** | Adds unnecessary HTTP serialization overhead | Use Next.js Server Actions directly |
| **Blocking SQLite sync calls in edge workers** | Blocks event loop under high concurrent I/O | Use Turso LibSQL HTTP client for distributed edge |
| **Unindexed foreign key columns** | Degrades JOIN and cascade delete performance | Add explicit `.index()` on all foreign key ID fields |

---

## 🔒 Security & Defense Guidelines

- Sanitize all user-controlled rich text with DOMPurify before rendering.
- Rate-limit sensitive routes (login, password reset, checkout) using in-memory or Redis sliding window.
- Never expose server-side environment variables (`DATABASE_URL`, API secrets) with `NEXT_PUBLIC_` prefix.
