# Next.js 15 + SQLite SaaS Project Developer Guide

This guide details the conventions, structure, and patterns for development in this project. Follow these rules strictly to maintain consistency.

## 🛠️ Stack & Versions

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript 5.x
- **Database**: SQLite
  - For local dev: `better-sqlite3` (synchronous, fast)
  - Production option: Turso / libsql (for replication/serverless)
- **Database Access**: Prisma ORM (v6.x) or Drizzle ORM
- **Styling**: Tailwind CSS v4 / CSS Modules
- **UI Components**: Radix UI + Lucide React icons

---

## 📂 Folder Structure

We use a strictly grouped folder structure to keep components and pages organized.

```text
├── src/
│   ├── app/                # App Router (Pages, layouts, routes)
│   │   ├── (auth)/         # Auth routes group
│   │   ├── (dashboard)/    # Authenticated dashboard views
│   │   ├── api/            # API Route handlers
│   │   ├── layout.tsx      # Root layout
│   │   └── page.tsx        # Homepage
│   ├── components/         # Shared UI Components
│   │   ├── ui/             # Core base components (buttons, dialogs, etc.)
│   │   └── features/       # Feature-specific components (e.g. billing, profile)
│   ├── lib/                # Shared utility libraries and wrappers
│   │   ├── db.ts           # Database client singleton instance
│   │   ├── auth.ts         # Authentication utility helpers
│   │   └── utils.ts        # Formatting and common helpers
│   └── types/              # Global TypeScript declarations
├── db/                     # SQLite files and schema definitions
│   ├── dev.db              # Local SQLite database file (gitignored)
│   └── migrations/         # SQL schema migration files
├── package.json
└── CLAUDE.md
```

---

## 💾 SQL & Migration Conventions

SQLite is lightweight, and schema changes must be managed carefully.

1. **Migration Naming**: Use `YYYYMMDDHHMMSS_description.sql` format.
2. **Data Types**: 
   - Use `TEXT` for IDs, UUIDs, Dates, and JSON data.
   - Use `INTEGER` for counts, boolean flags (`0` or `1`), and Unix timestamps.
   - Use `REAL` for floating-point decimals.
3. **Foreign Keys**: Always enable Foreign Key constraints. In Drizzle/Prisma, verify relations are declared with referential actions (e.g., `ON DELETE CASCADE` or `ON DELETE SET NULL`).
4. **Local Development**: Keep `dev.db` out of git. Add `*.db`, `*.db-journal`, and `*.db-shm` to the root `.gitignore`.

---

## ⚛️ Component Patterns

We adhere to the React 19 / Next.js 15 Server Components architecture by default.

1. **Server Components by Default**: All components in the `app/` directory are React Server Components (RSC) unless marked with `"use client"`.
2. **"use client" Directive**: Only use client-side state, hooks (`useState`, `useEffect`), or browser APIs (like geolocation or copy-to-clipboard) when necessary. Keep client components leaves of the rendering tree.
3. **Server Actions for Mutations**: Use Next.js Server Actions (declared with `"use server"`) for form submissions and mutations, rather than custom API routes, to benefit from progressive enhancement.
4. **Loading & Error States**: Implement standard `loading.tsx` and `error.tsx` at route boundaries instead of custom try/catch loaders.

---

## 🚫 What We Don't Do (and Why)

1. **Don't use `fetch()` for server-side DB access**: Call services or the database client directly in RSCs. Using API routes internally causes extra network overhead and latency.
2. **Don't use client-side fetch for sensitive data**: Always fetch data inside Server Components to keep queries secure and avoid exposing internal database details or API tokens to the client.
3. **Don't use complex client-side state managers**: Avoid Redux or Zustand unless absolutely necessary. Rely on URL query parameters (`searchParams`) and Next.js router cache/refresh mechanisms for state management.
4. **Don't ignore SQLite concurrency**: Avoid running long-running synchronous database queries in request handlers to prevent database lockups (`SQLITE_BUSY` errors). Use indexes for columns frequently queried in `WHERE` clauses.
