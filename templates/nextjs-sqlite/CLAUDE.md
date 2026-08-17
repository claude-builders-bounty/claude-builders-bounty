# Next.js 15 + SQLite SaaS Project Guidelines (CLAUDE.md)

> Production-ready, opinionated engineering guide for building SaaS applications with Next.js 15 App Router, React 19, TypeScript, and SQLite (better-sqlite3 / Turso / Drizzle).

---

## 1. Stack & Versions

- **Framework**: Next.js 15 (App Router only, React Server Components by default)
- **Runtime / Language**: Node.js 22 LTS, TypeScript 5.5+ (strict mode enabled)
- **Database**: SQLite 3 (`better-sqlite3` in local / container or `@libsql/client` for Turso distributed SQLite)
- **ORM & Migrations**: Drizzle ORM (`drizzle-kit` for schema declarations and migrations)
- **Styling**: Tailwind CSS 4 with CSS variables
- **Validation**: Zod 3.x for all input/output boundary schemas
- **Auth**: Auth.js / NextAuth v5 or Lucia Auth with SQLite adapter
- **Package Manager**: `pnpm` (required)

---

## 2. Standard Folder Structure

```text
├── app/                        # Next.js App Router routes & layouts
│   ├── (auth)/                 # Route group for authentication (login, register, forgot)
│   ├── (dashboard)/            # Route group for authenticated SaaS workspace
│   │   ├── layout.tsx          # Dashboard shell with sidebar & user nav
│   │   └── page.tsx            # Main workspace view
│   ├── api/                    # Webhook and external REST endpoints only
│   │   └── webhooks/           # Stripe / Paddle / GitHub webhook handlers
│   ├── globals.css             # Tailwind base and theme variables
│   └── layout.tsx              # Root layout (fonts, metadata, providers)
├── components/
│   ├── ui/                     # Primitives (Button, Input, Dialog, Table, Badge)
│   ├── forms/                  # Interactive form client components
│   └── layout/                 # Header, Sidebar, MobileNav, UserMenu
├── lib/
│   ├── db/
│   │   ├── index.ts            # SQLite connection pool & Drizzle instance (WAL mode)
│   │   ├── schema/             # Drizzle table schemas partitioned by domain
│   │   │   ├── users.ts        # Users, sessions, accounts
│   │   │   ├── teams.ts        # Organizations, memberships, invites
│   │   │   └── subscriptions.ts# Stripe subscriptions, tiers, invoices
│   │   └── migrations/         # Auto-generated SQL migration files
│   ├── actions/                # Server Actions (mutations with 'use server')
│   │   ├── auth.actions.ts     # Login, signup, logout actions
│   │   └── team.actions.ts     # Workspace management actions
│   └── utils/                  # Pure utility helpers (formatting, dates, crypto)
├── drizzle.config.ts           # Drizzle Kit configuration
├── tsconfig.json               # Strict TypeScript configuration
└── package.json
```

---

## 3. SQLite & Migration Conventions

1. **WAL Mode is Mandatory**: Always initialize local SQLite connections with `PRAGMA journal_mode = WAL; PRAGMA synchronous = NORMAL; PRAGMA foreign_keys = ON;` to ensure fast concurrent reads without locking writes.
2. **Schema Declarations**: Place all table definitions inside `lib/db/schema/*.ts`. Never write raw SQL `CREATE TABLE` strings manually.
3. **Migration Workflow**:
   - Update TypeScript schema in `lib/db/schema/`.
   - Run `pnpm db:generate` to generate timestamped SQL migration files.
   - Run `pnpm db:migrate` to execute pending migrations inside a single atomic transaction.
4. **Parameterization**: Always use parameterized prepared statements or Drizzle query builders (`db.select().from(...)`). Never concatenate raw strings into SQL queries.
5. **Foreign Key Integrity**: Always define cascading behavior explicitly (`onDelete: "cascade"` or `onDelete: "set null"`).

---

## 4. Component Patterns & Server Actions

1. **Server Components by Default**:
   - All components in `app/` are React Server Components (RSC) unless interactivity (useState, useEffect, event listeners) is strictly required.
   - Fetch data directly in Server Components using async/await and Drizzle queries.
2. **Client Components**:
   - Add `"use client";` at the very top line only for interactive islands (dialogs, toggles, forms).
   - Keep Client Components small and leaf-level in the component tree.
3. **Server Actions for Mutations**:
   - Define mutations inside `lib/actions/*.actions.ts` marked with `"use server";`.
   - Always validate payload inputs with `zod.parse()` or `safeParse()`.
   - Return structured results: `{ success: true, data: T } | { success: false, error: string }`.
   - Call `revalidatePath()` or `revalidateTag()` after successful database mutations.

---

## 5. Development Commands

```bash
# Start development server with Turbopack
pnpm dev

# Build for production with strict typecheck
pnpm build

# Generate Drizzle migration from schema changes
pnpm db:generate

# Apply pending SQL migrations to SQLite
pnpm db:migrate

# Open Drizzle Studio visual database inspector
pnpm db:studio

# Run automated test suite
pnpm test
```

---

## 6. What We DON'T Do (and Why)

| Anti-Pattern | Why We Avoid It | What We Do Instead |
|---|---|---|
| ❌ Heavy ORMs (Prisma / TypeORM) | High memory footprint, slow cold starts on serverless, redundant query layers over simple SQLite. | Use Drizzle ORM: lightweight, zero-overhead, direct SQL-to-TypeScript mapping. |
| ❌ Client-side Database Connections | Security vulnerability; exposes database files or credentials to browser bundles. | All database queries execute strictly inside React Server Components or Server Actions. |
| ❌ Barrel Files (`index.ts` re-exporting 50 files) | Degrades bundler tree-shaking performance and slows down hot module replacement (HMR). | Import directly from specific module paths (e.g. `import { Button } from "@/components/ui/button"`). |
| ❌ Untyped Server Actions | Causes runtime errors and security vulnerabilities from unexpected payloads. | Enforce strict Zod schema validation on every single Server Action input. |
| ❌ Raw `localStorage` for Auth State | Vulnerable to XSS token theft. | Use HTTP-only, Secure, SameSite cookies managed by the auth layer. |
