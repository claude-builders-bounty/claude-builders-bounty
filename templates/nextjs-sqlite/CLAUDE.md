# CLAUDE.md — Next.js 15 + SQLite SaaS Project Guidelines

Opinionated, production-ready context rules for greenfield Next.js 15 (App Router) + SQLite (better-sqlite3 / Drizzle ORM / Turso) SaaS applications.

---

## 🛠️ Stack & Versions

- **Framework**: Next.js 15+ (App Router, Server Components by default, React 19)
- **Language**: TypeScript 5.x (`strict: true`, no `any`)
- **Database**: SQLite via `better-sqlite3` (local development/production) or `@libsql/client` (Turso edge replication)
- **ORM / Query Builder**: Drizzle ORM (`drizzle-orm` + `drizzle-kit` for migrations)
- **Styling**: Tailwind CSS v4 + `shadcn/ui` (Radix primitives)
- **State Management**: React Server Components + Server Actions (`zod` input validation)
- **Authentication**: Auth.js (NextAuth v5) or Clerk with SQLite session storage
- **Package Manager**: `pnpm` (strictly enforced via `pnpm-lock.yaml`)

---

## 📁 Folder Structure

```text
├── src/
│   ├── app/                    # Next.js App Router (pages & server actions)
│   │   ├── (auth)/             # Authentication route group
│   │   ├── (dashboard)/        # Main app dashboard route group
│   │   ├── api/                # REST/Webhook endpoints only
│   │   ├── layout.tsx          # Root layout
│   │   └── page.tsx            # Landing page
│   ├── components/             # UI Components
│   │   ├── ui/                 # Atomic shadcn components (primitives)
│   │   ├── dashboard/          # Feature-specific dashboard components
│   │   └── shared/             # Cross-cutting UI (headers, footers)
│   ├── db/                     # Database layer
│   │   ├── schema/             # Drizzle table schemas (modular per feature)
│   │   │   ├── users.ts
│   │   │   ├── subscriptions.ts
│   │   │   └── index.ts
│   │   ├── client.ts           # SQLite client connection singleton
│   │   └── migrate.ts          # Migration runner script
│   ├── lib/                    # Core utilities, validation schemas, API clients
│   │   ├── actions/            # Server Actions (Zod validated)
│   │   ├── auth.ts             # Auth configuration & session helpers
│   │   └── utils.ts            # Helper functions (cn, formatters)
│   └── types/                  # Shared TypeScript interfaces & types
├── drizzle/                    # Generated SQL migration files (.sql)
├── drizzle.config.ts           # Drizzle Kit configuration
└── tailwind.config.ts          # Tailwind CSS configuration
```

---

## 💻 Essential Developer Commands

- **Development Server**: `pnpm dev` (Runs Next.js dev server with Turbopack)
- **Build Production**: `pnpm build` (Strict typecheck + Next.js build)
- **Start Production**: `pnpm start`
- **Linting & Formatting**: `pnpm lint` && `pnpm format` (Biome or ESLint + Prettier)
- **Type Check**: `pnpm typecheck` (`tsc --noEmit`)
- **Database Generate Migration**: `pnpm db:generate` (`drizzle-kit generate`)
- **Database Push Schema**: `pnpm db:push` (`drizzle-kit push`)
- **Database Run Migrations**: `pnpm db:migrate` (`tsx src/db/migrate.ts`)
- **Database Studio**: `pnpm db:studio` (Drizzle Studio UI)
- **Run Unit Tests**: `pnpm test` (Vitest unit test runner)

---

## 🗄️ SQL & Migration Conventions

1. **WAL Mode Execution**: Always enable Write-Ahead Logging on SQLite initialization (`PRAGMA journal_mode = WAL;`) to prevent database locked errors during concurrent reads and writes.
2. **Foreign Key Enforcement**: Explicitly enable foreign keys on connection (`PRAGMA foreign_keys = ON;`). SQLite disables foreign key constraints by default.
3. **Primary Keys & Identifiers**: Use prefixed ULIDs or UUIDv4 for public string IDs (e.g. `usr_01H...` or `sub_01H...`), or auto-incrementing integer IDs for pure join tables.
4. **Timestamps**: Store all timestamps in UTC as ISO-8601 text strings (`YYYY-MM-DDTHH:mm:ss.sssZ`) or UNIX timestamps in integer format (`created_at INTEGER DEFAULT (unixepoch()) NOT NULL`).
5. **Drizzle Migration Flow**:
   - Never modify table schemas directly in SQLite via manual `ALTER TABLE` CLI commands.
   - Edit the typescript definition in `src/db/schema/*.ts`.
   - Run `pnpm db:generate` to produce a versioned SQL file in `./drizzle/`.
   - Run `pnpm db:migrate` to apply pending migrations.

---

## 🧩 Component & Code Patterns

1. **Server Components First**: Make components React Server Components (`RSC`) by default. Add `'use client'` only at the leaf nodes that require event listeners, browser hooks (`useState`, `useEffect`), or DOM interaction.
2. **Server Actions with Zod Validation**:
   - Every mutating Server Action MUST validate incoming FormData or JSON arguments using a `zod` schema.
   - Return structured standard result type `{ success: true, data }` or `{ success: false, error: string }`.
3. **Data Fetching in RSC**: Fetch data directly inside Server Components using Drizzle queries. Do not fetch via internal HTTP fetch `/api/...` endpoints from Server Components.
4. **Optimistic UI & Transitions**: Use `useOptimistic` and `useTransition` when triggering Server Actions from client components for instant user feedback.

---

## 🚫 What We Don't Do (And Why)

1. **No Client-Side Direct Database Imports**: Never import `src/db/client.ts` or any node-native module into client components (`'use client'`). *Why*: SQLite native bindings (`better-sqlite3`) will break Webpack/Turbopack bundlers and leak database credentials.
2. **No API Routes for Internal Server Component Data Fetching**: Do not write `/api/users` REST endpoints solely to consume them in Server Components. *Why*: Creates unnecessary round-trip overhead and serialization costs; Server Components execute directly on the node runtime.
3. **No Unbounded SELECT Queries**: Never run `db.select().from(table)` without an explicit `.limit()` or pagination block. *Why*: Large result sets block SQLite thread execution and exhaust memory.
4. **No Raw SQL String Interpolation**: Never write raw string interpolation inside SQL queries (`db.execute("SELECT * FROM users WHERE name = '" + name + "'")`). *Why*: Eliminates SQL injection vulnerabilities; always use parameterized Drizzle queries or prepared statements.
5. **No `any` Types or Ignored Lint Rules**: Never bypass TypeScript checks with `// @ts-ignore` or `any`. *Why*: Type safety prevents silent runtime crashes when schema fields update.
