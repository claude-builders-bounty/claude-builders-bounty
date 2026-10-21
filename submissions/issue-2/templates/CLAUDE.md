# CLAUDE.md — Next.js 15 App Router + SQLite (Turso / better-sqlite3)

This is an opinionated, production-ready specification for a greenfield SaaS project.
Follow these rules strictly. Every rule exists to prevent state desync, hydration errors, or SQL deadlocks.

---

## 1. Stack & Pinned Versions
- **Framework:** Next.js 15 (App Router with async request APIs)
- **Language:** TypeScript 5.5+ (Strict mode, no `any`)
- **Database:** SQLite via `@libsql/client` (Turso) or `better-sqlite3` with WAL mode
- **ORM / Query Builder:** Drizzle ORM (`drizzle-orm`, `drizzle-kit`)
- **Styling:** Tailwind CSS v3 / v4 + Lucide Icons
- **Validation:** Zod v3 for all API inputs and env vars

---

## 2. Directory Structure
```
├── src/
│   ├── app/                 # Next.js 15 App Router
│   │   ├── (auth)/          # Route group: login, register
│   │   ├── (dashboard)/     # Route group: authenticated SaaS dashboard
│   │   ├── api/             # Edge/Node API route handlers
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/
│   │   ├── ui/              # Primitive atom components (buttons, inputs)
│   │   └── features/        # Business feature components
│   ├── db/
│   │   ├── schema/          # Drizzle table schemas (auth.ts, billing.ts, teams.ts)
│   │   ├── index.ts         # DB singleton connection (WAL mode enforced)
│   │   └── migrations/      # Auto-generated SQL migration files
│   ├── lib/                 # Core utilities, auth helpers, Stripe client
│   └── actions/             # Next.js Server Actions with Zod safe-parsing
├── drizzle.config.ts
└── package.json
```

---

## 3. SQLite & Migration Conventions
1. **Always Enable WAL Mode:** SQLite write concurrency requires Write-Ahead Logging (`PRAGMA journal_mode = WAL; PRAGMA busy_timeout = 5000;`).
2. **Deterministic Foreign Keys:** Always enforce `PRAGMA foreign_keys = ON;` upon connection instantiation.
3. **Primary Keys:** Use ULID or CUID2 (`text` column) for globally distributed, sortable IDs. Avoid autoincrement integer IDs for public-facing records.
4. **Migrations over Direct Alter:** All schema edits must be generated via `npm run db:generate` and committed to `src/db/migrations/`.

---

## 4. Component & Server Action Patterns
1. **Default to React Server Components (RSC):** Only mark a file with `'use client'` if it uses interactive hooks (`useState`, `useEffect`, `useRef`).
2. **Server Actions for Mutations:** Mutations live in `src/actions/*.ts` with `'use server'`.
   - Every action must validate arguments using a Zod schema (`actionSchema.safeParse(input)`).
   - Return structured results: `{ success: true, data } | { success: false, error: string }`.
3. **Async Request APIs in Next.js 15:** In Next.js 15, `params`, `searchParams`, `cookies()`, and `headers()` are promises. Always `await` them.

---

## 5. Development Commands
- `npm run dev` — Start Next.js local development server
- `npm run db:generate` — Generate Drizzle migration files from schemas
- `npm run db:migrate` — Apply pending migrations to SQLite database
- `npm run db:studio` — Open Drizzle Studio visual inspector
- `npm run build` — Verify TypeScript and generate production bundle

---

## 6. What We Don't Do (And Why)
1. **NO Client-Side SQL Queries:** Never expose DB queries or credentials in client components. All database access must execute inside Server Components, Server Actions, or API handlers.
2. **NO Barrel Exports (`index.ts` re-exporting everything):** Next.js treeshaking degrades with large barrel files. Import directly from the module.
3. **NO Unbounded Mutations Without Transactions:** Batch writes affecting multiple tables must wrap in `db.transaction(...)` to guarantee ACID atomicity in SQLite.
4. **NO Raw Strings for Enum Columns:** Use TypeScript const arrays or enums validated with Zod.
