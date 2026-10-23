# CLAUDE.md — Next.js 15 (App Router) + SQLite SaaS Production Rules

> Opinionated, zero-ambiguity engineering guide for a multi-tenant SaaS built with Next.js 15 App Router, SQLite (`better-sqlite3` / Turso `@libsql/client`), Drizzle ORM, Tailwind CSS v4, and Stripe.

---

## 1. Stack & Pinned Versions
- **Runtime:** Node.js `>=22.0.0`
- **Framework:** `next@^15.1.0` (App Router only, React 19, Server Actions, Turbopack)
- **Database:** SQLite in WAL mode via `better-sqlite3@^11.x` (local/single-node VPS) or `@libsql/client@^0.14.x` (Turso edge replicas)
- **ORM & Migrations:** `drizzle-orm@^0.38.x` + `drizzle-kit@^0.30.x`
- **Authentication:** Session-based HTTP-only cookies stored in SQLite (`sessions` table) — no stateless JWTs
- **Validation:** `zod@^3.24.x` at every boundary (Server Actions, Route Handlers, env vars)
- **Payments:** `stripe@^17.x` with webhook idempotency persisted in SQLite
- **Testing:** `vitest` (unit/DB integration with in-memory SQLite) + `playwright` (E2E)

### Essential Commands
```bash
npm run dev            # next dev --turbopack (port 3000)
npm run build          # next build (strict typecheck + lint)
npm run db:generate    # drizzle-kit generate (creates SQL migration in ./drizzle)
npm run db:migrate     # tsx src/db/migrate.ts (applies pending migrations with WAL enabled)
npm run db:studio      # drizzle-kit studio
npm run test           # vitest run
```

---

## 2. Folder Structure & Naming Conventions
```text
src/
├── app/
│   ├── (marketing)/           # Public pages (pricing, terms, landing)
│   ├── (auth)/                # /login, /signup, /verify
│   ├── (app)/                 # Authenticated SaaS tenant workspace
│   │   ├── [orgSlug]/         # Every tenant route is scoped by orgSlug
│   │   └── layout.tsx         # Calls requireOrgMember() before rendering
│   └── api/
│       └── webhooks/stripe/route.ts  # Raw body Stripe webhook handler
├── components/
│   ├── ui/                    # Pure stateless primitives (kebab-case files: button.tsx)
│   └── features/              # Domain components grouped by feature (billing-card.tsx)
├── db/
│   ├── index.ts               # Singleton SQLite connection + PRAGMA initialization
│   ├── migrate.ts             # Programmatic migration runner
│   └── schema/                # One file per domain: users.ts, orgs.ts, billing.ts
├── server/
│   ├── dal/                   # Data Access Layer (enforces tenant orgId on every query)
│   └── actions/               # Server Actions (mutating operations only, suffix: .action.ts)
└── lib/
    ├── env.ts                 # Zod-validated process.env
    └── errors.ts              # Typed Result<T, AppError> helpers
```

### Naming Rules (Why: Predictable grepability & zero import collisions)
- **Files:** `kebab-case.ts` / `kebab-case.tsx` everywhere.
- **React Components:** `PascalCase` exports.
- **Server Actions:** Verb-first camelCase (`createProjectAction`, `cancelSubscriptionAction`) in `src/server/actions/*.action.ts`.
- **SQLite Tables & Columns:** `snake_case` plural table names (`organization_members`), `snake_case` columns (`created_at`, `stripe_customer_id`).

---

## 3. SQL & SQLite Migration Conventions
1. **Mandatory PRAGMAs on Connection Startup (`src/db/index.ts`):**
   Every SQLite connection MUST execute these pragmas immediately upon opening:
   ```sql
   PRAGMA journal_mode = WAL;          -- Allows concurrent reads while a write is in progress
   PRAGMA busy_timeout = 5000;         -- Waits 5s on write lock instead of throwing SQLITE_BUSY
   PRAGMA synchronous = NORMAL;        -- Safe durability in WAL mode with 3x faster fsync
   PRAGMA foreign_keys = ON;           -- SQLite disables FK enforcement by default!
   PRAGMA temp_store = MEMORY;
   ```
2. **Primary Keys & Timestamps:**
   - Use prefixed text ULIDs (`usr_01J...`, `org_01J...`) instead of `AUTOINCREMENT` integers so IDs are sortable by creation time and non-enumerable in URLs.
   - Store timestamps as Unix epoch milliseconds (`integer('created_at', { mode: 'timestamp_ms' }).notNull()`) — never localized date strings.
3. **Zero-Downtime Migration Rules:**
   - Never edit an existing `.sql` file in `./drizzle`. Always generate a new migration via `npm run db:generate`.
   - Because SQLite `ALTER TABLE` has limited support for dropping/modifying columns with foreign keys, additive changes (adding nullable columns or new tables) are preferred.
   - Wrap multi-table writes inside `db.transaction((tx) => { ... })`. Never await external HTTP calls (like Stripe or email APIs) *inside* a SQLite transaction, or you will lock the entire database file.

---

## 4. Component & Data Fetching Patterns
1. **Reads happen in Server Components via the DAL (\`src/server/dal/\`):**
   - Server Components call DAL functions directly (e.g., `await getOrgProjects(orgId)`).
   - Do NOT create `/api/...` GET routes just to fetch data for your own React pages.
2. **Writes happen in Server Actions (\`src/server/actions/\`):**
   - Every Server Action MUST follow this exact 4-step pipeline:
     1. Parse `FormData` or JSON input with a `zod` schema.
     2. Authenticate & authorize via `const session = await requireOrgRole(orgSlug, ['owner', 'admin'])`.
     3. Execute the SQLite mutation via `db.transaction`.
     4. Call `revalidatePath` and return `{ ok: true, data }` or `{ ok: false, error }`.
3. **Client Components (`"use client"`):**
   - Push `"use client"` as far down the component tree as possible (leaf interactive inputs, modals, charts).
   - Never import `src/db` or `src/server` inside a Client Component (enforced via `import 'server-only'` at the top of `src/db/index.ts`).

---

## 5. What We Don't Do (And Why)
- **NO Prisma on SQLite:** Prisma ships a heavy Rust query engine binary that adds cold-start overhead and struggles with fine-grained SQLite WAL pragma tuning. We use Drizzle + `better-sqlite3`.
- **NO `useEffect` for Data Fetching:** Causes client waterfalls, layout shift, and duplicates auth logic. Fetch in Server Components and pass promises or serialized props.
- **NO Raw `userId` or `orgId` Trusted from Client Payloads:** Every mutation resolves the active user from the HTTP-only session cookie on the server and verifies membership in `organization_members`.
- **NO External Network Calls Inside `db.transaction()`:** SQLite allows only one writer at a time. Holding a transaction open while awaiting Stripe or Resend blocks every other user on the SaaS.
- **NO Unbounded `SELECT *` Without `LIMIT`:** Every list query in `src/server/dal/` must enforce cursor pagination (`WHERE id < ? ORDER BY id DESC LIMIT ?`, max 100 rows).
