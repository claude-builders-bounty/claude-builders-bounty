# CLAUDE.md — Next.js 15 App Router + SQLite SaaS Project Specification

This repository contains a production-grade, opinionated SaaS boilerplate built with Next.js 15 App Router, React 19, TypeScript, Tailwind CSS, and SQLite (`better-sqlite3` or Turso via LibSQL).

---

## 🏗️ 1. Stack & Versions
- **Framework:** Next.js 15 (App Router only, React Server Components by default)
- **Runtime / Language:** Node.js 20+ LTS, TypeScript 5.5+ (Strict mode: enabled)
- **Database:** SQLite with WAL mode (`better-sqlite3` for local/containerized, `@libsql/client` for Turso)
- **ORM / Query Builder:** Drizzle ORM (lightweight, zero-overhead, type-safe SQL)
- **Authentication:** Auth.js v5 (NextAuth) or Lucia Auth with SQLite adapter
- **Styling:** Tailwind CSS v3/v4 with `clsx` and `tailwind-merge`
- **Validation:** Zod v3.23+ for runtime schema validation (API inputs, server actions, env vars)

---

## 📁 2. Folder Structure
```text
├── src/
│   ├── app/                    # Next.js 15 App Router
│   │   ├── (auth)/             # Route group: login, register, callback
│   │   ├── (dashboard)/        # Route group: authenticated SaaS app pages
│   │   ├── (marketing)/        # Route group: landing page, pricing, blog
│   │   ├── api/                # Route handlers (webhooks, external integrations)
│   │   ├── layout.tsx          # Root layout
│   │   └── page.tsx            # Root landing
│   ├── components/             # Reusable UI components
│   │   ├── ui/                 # Primitives (Button, Modal, Input, Badge)
│   │   └── modules/            # Domain-specific components (BillingCard, UserMenu)
│   ├── db/                     # Database layer
│   │   ├── index.ts            # SQLite client instantiation & WAL configuration
│   │   ├── schema/             # Drizzle tables & relations per domain
│   │   │   ├── users.ts
│   │   │   ├── subscriptions.ts
│   │   │   └── audits.ts
│   │   └── migrations/         # Auto-generated SQL migration files
│   ├── actions/                # Server Actions ('use server')
│   ├── lib/                    # Shared utilities & configurations
│   │   ├── auth.ts             # Auth session helpers & middleware integration
│   │   ├── env.ts              # Type-safe environment variable parsing with Zod
│   │   └── utils.ts            # Formatting, cn() helper, math utilities
│   └── types/                  # Global shared TypeScript declarations
├── drizzle.config.ts           # Drizzle kit migration & push configuration
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

---

## 🗄️ 3. SQL & Migration Conventions
1. **WAL Mode is Mandatory:**
   - Every SQLite connection MUST enable WAL (Write-Ahead Logging) mode and busy timeout on boot:
     ```ts
     sqlite.pragma('journal_mode = WAL');
     sqlite.pragma('busy_timeout = 5000');
     sqlite.pragma('synchronous = NORMAL');
     ```
2. **Deterministic Primary Keys:**
   - Use prefixed sortable IDs (e.g. `usr_...`, `sub_...` with nanoid or ULID) or `INTEGER PRIMARY KEY AUTOINCREMENT`. Never use raw non-prefixed UUIDs without indexing.
3. **Explicit Foreign Keys:**
   - Always enforce foreign keys: `sqlite.pragma('foreign_keys = ON');`.
4. **Migration Rules:**
   - All schema changes MUST be generated via `pnpm db:generate` and committed as sequential `.sql` migration files in `src/db/migrations/`.
   - Never run raw untracked `ALTER TABLE` commands directly in production.

---

## ⚡ 4. Component & Server Action Patterns
1. **Server Components by Default:**
   - All components in `src/app/` are React Server Components unless interaction requires hooks (`useState`, `useEffect`, `useActionState`).
   - Add `'use client';` only to leaf interactive components (e.g. `src/components/ui/button.tsx`).
2. **Server Actions for Mutations:**
   - Every mutation is an async function in `src/actions/` prefixed with `'use server';`.
   - Always validate inputs using a Zod schema before executing DB operations:
     ```ts
     'use server';
     import { z } from 'zod';
     import { db } from '@/db';

     export async function updateProfile(rawInput: unknown) {
       const { name } = z.object({ name: z.string().min(2) }).parse(rawInput);
       // DB logic...
     }
     ```
3. **Optimistic UI:**
   - Use `useOptimistic` for instantaneous UI updates (e.g. toggles, upvotes) with rollback handling.

---

## 🛑 5. What We Don't Do (And Why)
1. **NO Client-Side DB Calls:**
   - *Why:* SQLite is a server-side embedded database. Never expose DB queries or raw credentials to client components.
2. **NO Unindexed Queries:**
   - *Why:* While SQLite is blazing fast in-memory, full-table scans degrade performance under high concurrent read loads. Every foreign key and lookup column (`email`, `tenant_id`) must have an index.
3. **NO Long Transactions in Write Operations:**
   - *Why:* SQLite allows multiple concurrent readers but only one active writer at a time. Keep write transactions small, atomic, and fast.
4. **NO Storing File Uploads as BLOBs in SQLite:**
   - *Why:* Storing large files causes database bloat and memory pressure. Store files in S3/R2/local disk and keep only the URL/path in SQLite.
5. **NO Skipping Zod Schema Validation:**
   - *Why:* TypeScript types are erased at runtime. Zod guarantees strict boundary safety for external webhook payloads and user inputs.

---

## 💻 6. Development Commands
- `pnpm dev`: Start Next.js local development server with Turbopack
- `pnpm build`: Create production build
- `pnpm db:generate`: Generate SQL migration from Drizzle schema
- `pnpm db:migrate`: Run pending migrations against SQLite database
- `pnpm db:studio`: Launch Drizzle Studio GUI for visual database management
- `pnpm lint`: Run ESLint and TypeScript typecheck
