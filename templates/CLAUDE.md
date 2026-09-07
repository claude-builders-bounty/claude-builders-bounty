# CLAUDE.md Template — Next.js 15 + SQLite SaaS Architecture & Engineering Guidelines

This document provides strict, opinionated architectural patterns, operational conventions, and rules for building production-grade SaaS applications with Next.js 15 (App Router) and SQLite (`better-sqlite3` / Turso).

---

## 🛠️ 1. Tech Stack & Canonical Versions

- **Framework:** Next.js 15 (App Router, React 19, Server Components by default)
- **Database:** SQLite via `better-sqlite3` (local/embedded) or `@libsql/client` (Turso edge-ready)
- **ORM / Query Builder:** Drizzle ORM (type-safe SQL, zero runtime bloat)
- **Authentication:** Lucia Auth or Auth.js v5 with SQLite session adapter
- **Styling:** Tailwind CSS v4 + Radix UI primitives
- **Validation:** Zod v3 (strict schema boundaries on server actions & API routes)
- **Package Manager:** `pnpm` (strict dependency resolution)

---

## 📁 2. Folder Structure

```
├── src/
│   ├── app/                    # Next.js App Router routes & layouts
│   │   ├── (auth)/             # Route group: login, register, reset-password
│   │   ├── (dashboard)/        # Route group: authenticated SaaS workspace
│   │   ├── api/                # Edge/Node API route handlers (webhooks only)
│   │   ├── layout.tsx          # Root layout with font & theme providers
│   │   └── page.tsx            # Marketing landing page
│   ├── components/             # Reusable UI components
│   │   ├── ui/                 # Atomic design primitives (Button, Input, Modal)
│   │   └── dashboard/          # Domain-specific dashboard widgets
│   ├── db/                     # Database layer
│   │   ├── schema/             # Drizzle table schemas (.ts files)
│   │   ├── migrations/         # Auto-generated SQL migration files
│   │   ├── index.ts            # Database client connection singleton
│   │   └── migrate.ts          # Migration runner script
│   ├── actions/                # Server Actions (mutations & form submissions)
│   ├── lib/                    # Shared utilities, auth, & environment validators
│   └── types/                  # Global domain types & Zod schemas
├── drizzle.config.ts           # Drizzle Kit configuration
├── next.config.ts              # Next.js build configuration
└── package.json
```

---

## 🗄️ 3. SQL & SQLite Conventions

1. **WAL Mode is Mandatory:** Always enable Write-Ahead Logging (`PRAGMA journal_mode = WAL;`) and synchronous normal (`PRAGMA synchronous = NORMAL;`) on connection initialization for high concurrent read throughput.
2. **Foreign Keys Always Active:** Execute `PRAGMA foreign_keys = ON;` immediately after opening any SQLite connection.
3. **Primary Keys:** Use `TEXT` primary keys with ULID / CUID2 (`cuid2` or `ulid()`) for distributed safety and sorted indexing. Avoid auto-incrementing integers for public IDs.
4. **Timestamps:** Store all timestamps as ISO 8601 UTC strings (`TEXT`, e.g. `2026-09-06T12:00:00.000Z`) or integer milliseconds (`INTEGER`). Never store local timezone strings.
5. **Prepared Statement Caching:** Reuse prepared statement instances for frequently executed hot queries to avoid statement compilation overhead.
6. **Migrations:** Never modify existing migration files. Always generate a new timestamped migration via `pnpm drizzle-kit generate` and apply via `pnpm db:migrate`.

---

## ⚡ 4. Next.js 15 & Server Component Patterns

1. **Server Components by Default:** Keep components as Server Components (`async function Component()`) unless client interactivity (state, event listeners, hooks) is explicitly required.
2. **Server Actions for Mutations:** Handle form submissions and state mutations via Server Actions placed in `src/actions/`.
   - Validate every action input with Zod (`schema.parse(input)`).
   - Check user session authorization inside the Server Action before executing DB queries.
   - Return `{ success: true, data }` or `{ success: false, error: string }`.
3. **Data Fetching:** Fetch data directly inside Server Components using DB queries. Do not create internal API routes (`/api/data`) just to fetch data from a Server Component.
4. **Optimistic UI:** Use `useOptimistic` and React 19 action hooks for instant feedback on user interactions.

---

## 🚫 5. What We DO NOT Do (And Why)

| Anti-Pattern | Why It Is Forbidden | Preferred Solution |
| :--- | :--- | :--- |
| **No Client-side DB Queries** | Severe security vulnerability; exposes secrets. | All database access lives exclusively in Server Components or Server Actions. |
| **No `any` Types in TypeScript** | Destroys type safety and leads to runtime crashes. | Use strict TypeScript with Zod schemas for inferred types (`z.infer<typeof schema>`). |
| **No Long-running Transactions** | SQLite locks the database file during writes, blocking concurrent mutations. | Keep write transactions short, atomic, and bounded (< 50ms). |
| **No Inline `fetch('/api/...')` in Pages** | Adds unnecessary HTTP overhead and network hops. | Query the database directly via Drizzle ORM in the Server Component. |
| **No Mutation in Route Handlers (GET)** | GET routes must be idempotent and safe. | Use Server Actions (POST) for all state-changing mutations. |

---

## 📜 6. Developer Commands

- `pnpm dev`: Start Next.js local development server on `http://localhost:3000`
- `pnpm build`: Build production bundle
- `pnpm db:generate`: Generate new Drizzle SQL migration from schema changes
- `pnpm db:migrate`: Apply pending migrations to SQLite database
- `pnpm db:studio`: Open Drizzle Studio web GUI for visual database management
- `pnpm lint`: Run ESLint checks
- `pnpm typecheck`: Run strict `tsc --noEmit` check

---

*Bounty Release / Payout Address:* `24p4kMYz26tZE487ZhPadPXXpip2GWtE2PSjsTEcBWBM`
