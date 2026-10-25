# CLAUDE.md — Next.js 15 App Router + SQLite SaaS Architecture

> Opinionated engineering conventions for building high-performance, single-tenant or multi-tenant SaaS with Next.js 15 (App Router, Server Actions, React 19) and SQLite (better-sqlite3 / Turso libSQL). Every rule exists to prevent concurrency race conditions, hydration mismatches, and data corruption.

---

## 1. Stack & Pinned Versions

- **Framework**: Next.js 15.x (`app/` router only, zero `pages/`)
- **React**: React 19 (Server Components by default, explicit `'use client'` at leaves)
- **Database**: SQLite with `better-sqlite3` (WAL mode enabled) or `@libsql/client` (Turso edge)
- **Migrations**: Drizzle ORM (`drizzle-kit` for schema migrations) or lightweight explicit SQL files
- **Styling**: Tailwind CSS v4 (`@tailwindcss/postcss`)
- **TypeScript**: Strict mode enabled (`noImplicitAny`, `strictNullChecks`, `exactOptionalPropertyTypes`)

---

## 2. Dev & Operational Commands

```bash
# Development
npm run dev              # Starts local Next.js dev server on :3000
npm run lint             # ESLint + Next.js core web vitals check
npm run typecheck        # tsc --noEmit (MANDATORY before committing)

# Database & Migrations
npm run db:generate      # Generates SQL migration diff from schema
npm run db:migrate       # Runs pending SQL migrations against SQLite
npm run db:seed          # Seeds deterministic fixture data
npm run db:studio        # Opens local Drizzle Studio / SQLite viewer
```

---

## 3. Directory & Folder Structure

```text
├── app/                      # Next.js App Router (Routing, Layouts, Pages)
│   ├── (auth)/               # Auth route group (login, register, reset)
│   ├── (dashboard)/          # Authenticated app portal
│   │   ├── layout.tsx        # Dashboard shell & sidebar layout (Server Component)
│   │   └── page.tsx          # Main dashboard view
│   ├── api/                  # Webhook & external third-party endpoints only
│   │   └── webhooks/stripe/  # Idempotent Stripe webhook handler
│   ├── layout.tsx            # Root layout with fonts & metadata
│   └── globals.css           # Tailwind v4 theme definitions
├── db/                       # Database engine & migrations
│   ├── schema.ts             # Drizzle schema / SQLite table definitions
│   ├── index.ts              # Singleton SQLite client with WAL & busy_timeout
│   └── migrations/           # Numbered immutable SQL migration files (0001_initial.sql)
├── components/               # UI Building Blocks
│   ├── ui/                   # Primitive design tokens (button, modal, input)
│   └── modules/              # Composed domain widgets (billing-card, user-avatar)
├── actions/                  # Server Actions (Mutations & Form Handlers)
│   ├── auth.actions.ts       # Session creation & destruction
│   └── project.actions.ts    # Domain entity CRUD actions
├── lib/                      # Pure Utilities & Helpers
│   ├── auth.ts               # Session verification & password hashing
│   └── utils.ts              # cn() class merge, formatting helpers
└── types/                    # Shared TypeScript interfaces & DTOs
```

---

## 4. SQLite & Concurrency Conventions

SQLite is an in-process, single-writer database. To avoid `SQLITE_BUSY` crashes:

1. **WAL Mode is Non-Negotiable**:
   Every database connection must execute:
   ```sql
   PRAGMA journal_mode = WAL;
   PRAGMA synchronous = NORMAL;
   PRAGMA busy_timeout = 5000;
   PRAGMA foreign_keys = ON;
   ```
2. **Singleton Database Instance**:
   Always export a single global SQLite instance across hot-reloads (`globalForDb` pattern). Never instantiate `new Database()` inside request handlers.
3. **Transactions for Dependent Writes**:
   Wrap multi-row operations inside an explicit `db.transaction()` block.
4. **Deterministic Migrations**:
   Schema changes must be expressed as sequential, reversible `.sql` files in `db/migrations/`. Never modify existing migrations; always add a new forward patch.

---

## 5. Next.js 15 Architecture Patterns

1. **Server Components by Default**:
   All files in `app/` are Server Components unless interactivity (hooks, state, browser events) is required.
2. **Push `'use client'` to the Leaves**:
   Do NOT mark entire pages as client components. Keep the page as a Server Component to fetch data, and import focused client leaves (e.g. `<UpvoteButton />`, `<ThemeToggle />`).
3. **Server Actions for Mutations**:
   Handle forms and database writes using Next.js Server Actions placed in `actions/*.ts`. Always validate input with Zod or a strict schema before executing queries.
4. **Security & Authorization Guard**:
   Check user sessions inside Server Actions and Data Access Layers. Never trust client-supplied user IDs from forms.

---

## 6. What We Do NOT Do (And Why)

| Anti-Pattern | Why We Avoid It |
| :--- | :--- |
| **No Route Handlers (`route.ts`) for standard CRUD** | Next.js Server Actions provide direct type safety and eliminate boilerplate REST endpoints for internal mutations. |
| **No `pages/` directory** | Mixing App Router and Pages Router leads to dual runtime bundles and split layout context. |
| **No Multiple SQLite Connection Pools** | Concurrent uncoordinated connection handles can cause database locks (`SQLITE_BUSY: database is locked`). |
| **No `useEffect` for data fetching** | Fetch data directly in Server Components using `async/await` for zero-waterfall, server-rendered HTML. |
| **No Raw Unescaped SQL Strings** | Always use parameterized queries (`db.prepare('SELECT * WHERE id = ?').get(id)`) to eliminate SQL injection vulnerabilities. |
