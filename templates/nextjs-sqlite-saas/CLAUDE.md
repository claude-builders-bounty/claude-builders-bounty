# CLAUDE.md — Next.js 15 + SQLite SaaS Template

Opinionated guidelines, conventions, and architectural invariants for greenfield SaaS development with Next.js 15 and SQLite.

---

## 🛠️ Stack & Versions
- **Framework**: Next.js 15.0+ (App Router with Turbopack)
- **Language**: TypeScript 5.6+ (Strict mode enabled, `noImplicitAny: true`)
- **UI & Runtime**: React 19 (Server Components, Server Actions, `useActionState`)
- **Database**: SQLite (better-sqlite3 for local / Turso `@libsql/client` for edge)
- **ORM**: Drizzle ORM 0.35+ (`drizzle-kit` for schema migrations)
- **Validation**: Zod 3.23+
- **Styling**: Tailwind CSS v4, Lucide Icons

---

## 📂 Project Structure
```text
├── src/
│   ├── actions/          # Server Actions (mutations with Zod validation)
│   ├── app/              # Next.js App Router (pages, layouts, route handlers)
│   │   ├── (auth)/       # Route group: login, signup, verify
│   │   ├── (dashboard)/  # Route group: authenticated SaaS workspace
│   │   ├── api/          # Webhook & external integrations only
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/
│   │   ├── ui/           # Primitives (buttons, inputs, dialogs)
│   │   └── features/     # Feature-scoped composite components
│   ├── db/
│   │   ├── schema.ts     # Single source of truth for Drizzle tables
│   │   ├── index.ts      # Connection singleton & WAL pragmas
│   │   └── migrations/   # Drizzle migration files
│   └── lib/
│       ├── env.ts        # Typed environment variables validation
│       ├── utils.ts      # Pure utility helpers (cn, formatters)
│       └── auth.ts       # Session extraction & guards
├── drizzle.config.ts
└── CLAUDE.md
```

---

## 💻 Essential Development Commands
```bash
# Development
npm run dev                  # Start local dev server with Turbopack
npm run build                # Typecheck and production build
npm run test                 # Run vitest / unit test suite

# Database & Migrations
npm run db:generate          # Generate SQL migration from schema diff
npm run db:migrate           # Apply pending migrations to SQLite
npm run db:studio            # Open Drizzle visual database inspector
```

---

## 🗄️ SQL & Migration Conventions
1. **Schema Source of Truth**: All database schemas MUST be defined in `src/db/schema.ts` using Drizzle ORM.
2. **WAL Mode Enforced**: SQLite connection initialization MUST set:
   ```typescript
   db.pragma('journal_mode = WAL');
   db.pragma('synchronous = NORMAL');
   db.pragma('foreign_keys = ON');
   ```
3. **Foreign Keys**: Explicit foreign keys with `onDelete: 'cascade'` or `onDelete: 'restrict'` on all relationships.
4. **Primary Keys**: Use `text('id').primaryKey().$defaultFn(() => crypto.randomUUID())` or nanoid for collision-resistant identifiers.
5. **Migrations**: Never alter SQLite database directly in runtime; always generate migration scripts via `drizzle-kit generate`.

---

## 🧩 Component & Data Fetching Patterns
- **Server Components by Default**: Fetch database queries directly in Server Components using async/await.
- **Client Boundaries Leaf-Only**: Only mark leaf interactive elements (forms, toggles) with `'use client'`.
- **Server Action Mutations**: All write operations must live in `src/actions/` and return a standard envelope:
  ```typescript
  export type ActionResult<T> =
    | { success: true; data: T }
    | { success: false; error: string; fieldErrors?: Record<string, string[]> };
  ```
- **Zod Input Enforcement**: Every Server Action MUST parse its arguments with a Zod schema before accessing database.

---

## 🚫 What We Don't Do (And Why)
- **NO `useEffect` for initial data fetching**: Causes network waterfalls and layout shifts. Fetch directly on the server.
- **NO default exports**: Except for Next.js route pages and layouts (`page.tsx`, `layout.tsx`). Use named exports everywhere else to ensure rename refactorability.
- **NO untyped `any` or `@ts-ignore`**: Compromises end-to-end type safety between SQLite schema, actions, and UI.
- **NO raw unparameterized SQL strings**: Always use Drizzle query builder or parameterized queries (`db.prepare(...)`) to prevent SQL injection.
- **NO client-side secrets**: Never import database drivers or secret environment variables in files containing `'use client'`.
