# CLAUDE.md — Next.js 15 + SQLite SaaS

> Opinionated conventions for a production-ready SaaS built with the **Next.js 15 App Router** and **SQLite** (local `better-sqlite3` or remote Turso).  
> Every rule includes the technical rationale. Do not deviate without a stronger reason.

---

## 1. Stack & Versions

| Layer | Standard | Reason |
| --- | --- | --- |
| Framework | **Next.js 15 (App Router)** | React Server Components, stable Server Actions, `after()` hook, improved `fetch` caching. |
| Language | **TypeScript 5.5+ strict** | Strict null checks catch DB null-handling bugs at compile time. |
| Database | **SQLite via Drizzle ORM** | `better-sqlite3` for local dev; `@libsql/client` for Turso in production. Drizzle provides type-safe SQL without a code-generation binary. |
| Styling | **Tailwind CSS + CSS variables** | Utility-first styling keeps Server Components lean; CSS variables enable dynamic theming without client-side context. |
| Validation | **Zod** | Schema-first validation runs on the edge (Server Actions) and in route handlers. |
| Auth | **Auth.js (NextAuth) v5** | First-class App Router support, database adapter for SQLite. |
| Testing | **Vitest** (unit) + **Playwright** (e2e) | Vitest is faster than Jest for modern ESM projects; Playwright covers the signed-in user journey. |
| Package Manager | **pnpm** | Strict node_modules prevents phantom dependencies. |

---

## 2. Folder Structure

**Feature-first architecture.**  
Co-location keeps related UI, logic, and DB code together. This reduces cross-file jumping and makes deleting a feature a single-directory operation.

```text
├── src/
│   ├── app/                    # Next.js App Router entry points
│   │   ├── (auth)/             # Route group: sign-in, sign-up layouts
│   │   ├── (marketing)/        # Landing, pricing, about
│   │   ├── (app)/              # Authenticated product area
│   │   │   ├── dashboard/
│   │   │   ├── settings/
│   │   │   └── layout.tsx      # Auth guard + navigation shell
│   │   ├── api/                # Route handlers (webhooks, health, cron)
│   │   ├── layout.tsx          # Root layout: fonts, metadata, providers
│   │   └── page.tsx            # Homepage
│   ├── components/             # Shared presentational UI
│   │   ├── ui/                 # Primitive components (button, input)
│   │   └── layout/             # Header, footer, nav
│   ├── features/               # Domain modules (user, billing, project)
│   │   └── <feature>/
│   │       ├── actions.ts      # Server Actions (mutations)
│   │       ├── queries.ts      # Data fetching
│   │       ├── components/     # Feature-specific UI
│   │       ├── schemas.ts      # Zod schemas
│   │       ├── types.ts        # DTOs / interfaces
│   │       └── db.ts           # Feature-local DB helpers (if needed)
│   ├── lib/                    # Infrastructure adapters
│   │   ├── db/
│   │   │   ├── index.ts        # Drizzle client & connection
│   │   │   ├── schema.ts       # All Drizzle schemas
│   │   │   └── migrations/     # Generated SQL migrations
│   │   ├── auth.ts             # Auth.js config
│   │   ├── env.ts              # T3 Env validated environment variables
│   │   └── utils.ts            # `cn()`, formatters
│   └── styles/
│       └── globals.css         # Tailwind + CSS variables
├── drizzle.config.ts
├── next.config.ts
├── package.json
└── tsconfig.json
```

### Rules
* `src/app` is **routing-only**; business logic lives in `src/features`.  
  *Reason:* Prevents the App Router from becoming a dumping ground, keeping route segments declarative.
* Shared components go in `src/components`.  
  *Reason:* Anything used in two or more features must be extracted here to avoid circular imports between features.
* Never import a feature from another feature.  
  *Reason:* Enforces unidirectional dependency flow and prevents hidden coupling.

---

## 3. Naming Conventions

| Subject | Convention | Example / Reason |
| --- | --- | --- |
| Directories | **kebab-case** | `user-settings/` — matches URL segments and file-system standards. |
| Components | **PascalCase** | `UserAvatar.tsx` — distinguishes React components from utilities. |
| Non-component files | **camelCase** | `useUser.ts`, `stripeClient.ts` — aligns with JS/TS library norms. |
| Server Actions | **Verb-noun functions** | `createProject`, `inviteTeamMember` — reads like a command; avoids noun-only ambiguity. |
| Database tables | **snake_case plural** | `users`, `team_members` — Drizzle infers this; plural avoids reserved-word clashes (`user` is not a reserved word in SQLite but plural is safer). |
| DB columns | **snake_case** | `created_at`, `stripe_customer_id` — standard across SQL databases; Drizzle maps to camelCase in TS automatically. |
| Environment variables | **SCREAMING_SNAKE** | `DATABASE_URL`, `TURSO_AUTH_TOKEN` — shell-compatible. |
| Types / Interfaces | **PascalCase** | `UserDto`, `CreateProjectInput` — differentiates types from values. |

---

## 4. Database & Migrations

### 4.1 Connection & Runtime
- Local development uses **`better-sqlite3`** (`DATABASE_URL="file:./sqlite.db"`).  
  *Reason:* Zero network latency, synchronous API, battle-tested.
- Production uses **Turso** (`@libsql/client`).  
  *Reason:* Managed SQLite with edge replication, backups, and row-level security compatible with Drizzle.
- **Enable WAL mode** on local SQLite.  
  *Reason:* `journal_mode = WAL` allows concurrent readers and one writer, preventing `SQLITE_BUSY` during Next.js HMR.
- **Enable foreign keys** (`PRAGMA foreign_keys = ON`).  
  *Reason:* SQLite defaults to off; Drizzle does not override this per connection.

### 4.2 Schema Conventions (Drizzle)
```ts
export const users = sqliteTable('users', {
  id: text('id').primaryKey(),               // UUIDv7 string
  email: text('email').notNull().unique(),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull(),
  updatedAt: integer('updated_at', { mode: 'timestamp' }).notNull(),
});
```
- **Use UUIDv7 text IDs**, not integer auto-increment.  
  *Reason:* UUIDv7 is time-sortable (B-tree locality) and avoids enumeration attacks. Integer IDs leak record counts.
- **Store timestamps as integer Unix epoch** (`integer('col', { mode: 'timestamp' })`).  
  *Reason:* SQLite stores `TEXT` dates inconsistently; integers sort correctly and serialize cleanly to JSON.
- **Money fields as integer cents**.  
  *Reason:* Avoids floating-point rounding errors.
- **Avoid `json` columns** unless the data is truly unstructured.  
  *Reason:* SQLite JSON functions are slower than proper columns and lose type safety.

### 4.3 Migration Workflow
All schema changes flow through **Drizzle Kit**.

```bash
# 1. Update src/lib/db/schema.ts
# 2. Generate migration
pnpm db:generate
# 3. Apply to local DB
pnpm db:migrate
# 4. Commit the generated .sql files + schema.ts
```

- **Never hand-edit a generated migration file.**  
  *Reason:* Drizzle tracks hash checksums; manual edits break the chain.
- **Never edit `schema.ts` and migrate in the same commit.**  
  *Reason:* Keep the schema definition and its versioned SQL separate for easier rollbacks.
- **Production migrations run via CI**, not inside `next start`.  
  *Reason:* A failing migration must block the deploy, not crash the server process.

---

## 5. Development Commands

All scripts are defined in `package.json`. Use **pnpm**. Do not introduce `npm`/`yarn` lockfiles.

| Command | Purpose | Notes |
| --- | --- | --- |
| `pnpm dev` | Start dev server | Turbopack (`--turbo`) is default in Next.js 15. |
| `pnpm build` | Production build | Fails on TS errors and lint violations. |
| `pnpm start` | Start production build | Run only for QA, not in dev. |
| `pnpm lint` | ESLint | Enforces App Router rules (e.g. no async client components). |
| `pnpm typecheck` | `tsc --noEmit` | Run before commits. |
| `pnpm test` | Vitest unit tests | `pnpm test:watch` for TDD. |
| `pnpm db:generate` | Drizzle Kit generate | Reads `schema.ts`, writes SQL to `lib/db/migrations`. |
| `pnpm db:migrate` | Drizzle Kit migrate | Applies pending SQL to local/Turso DB. |
| `pnpm db:push` | Prototype only | Pushes schema without generating SQL. **Banned after v0.** |
| `pnpm db:studio` | Drizzle Studio | Local GUI to inspect data. |
| `pnpm seed` | Seed script | Populates demo data for local development. |

---

## 6. Patterns & Best Practices

### Data Fetching
- Server Components should fetch data **directly via Drizzle** in `async` functions.  
  *Reason:* Eliminates API round-trips, waterfalls, and client-side loading states.
- Use `React.cache()` to deduplicate identical queries within the same request.  
  *Reason:* Prevents N+1 when multiple components ask for the current user.

### Mutations
- Use **Server Actions** (`"use server"`) for every mutation.  
  *Reason:* Progressive enhancement, single-codebase validation, and pending UI via `useActionState`.
- Pair every Action with a **Zod schema** for input validation.  
  *Reason:* Server Actions are public HTTP endpoints; never trust client-side validation.
- Call `revalidatePath()` or `revalidateTag()` after mutations.  
  *Reason:* Keeps Suspense boundaries fresh without a full router refresh.

### Auth
- Protect routes in `layout.tsx` (middleware) **and** in the data layer (`auth()`).  
  *Reason:* Middleware is a UX hint; the data layer is the security boundary.

### Components
- Default to **Server Components**. Add `'use client'` only for interactivity (event handlers, browser APIs).  
  *Reason:* Keeps JS bundle small, removes hydration overhead.
- Pass **serializable data** from Server to Client Components.  
  *Reason:* Dates, class instances, and functions crash or silently break at the RSC boundary.

---

## 7. What We Don't Do (Anti-Patterns)

| Anti-Pattern | Why It's Forbidden |
| --- | --- |
| **Prisma or TypeORM** | These ORMs ship heavy Rust/JS engines and use code-generation incompatible with edge runtimes. Drizzle is plain SQL + TypeScript. |
| **Prisma `$queryRaw` everywhere** | Losing type-safety defeats the purpose of an ORM. |
| **Global state for server data** (Zustand/Redux for DB rows) | Duplicates server truth, causes stale UI, and doubles cache invalidation work. Use Server Components + `revalidatePath` instead. |
| **API Routes for standard CRUD** | Adds unnecessary HTTP layer. Server Actions provide type-safe RPC. |
| **Client-side `useEffect` fetching** | Creates waterfalls. Fetch in Server Components or via Route Handlers only when SWR is required. |
| **SQLite `AUTOINCREMENT`** | Wastes pages and leaks row counts. Use UUIDv7. |
| **String interpolation into SQL** | SQL injection vector. Drizzle parameterizes queries by default; never bypass it. |
| **Date strings in DB** | Lexicographic sorting breaks timezones. Store Unix timestamps. |
| **`any` in TS** | Hides runtime errors. Use `unknown` and validate with Zod. |
| **`next/navigation` redirect in Server Actions** | Middleware/response redirects are cleaner. Server Actions should return data and let the client navigate. |
| **Modifying `node_modules` to fix a bug** | Creates a phantom dependency. Fork and PR upstream. |

---

## 8. Testing

- **Unit tests** for utilities, Zod schemas, and pure functions (`*.test.ts` beside the source file).
- **Integration tests** for Server Actions using Vitest with a test database URL (`:memory:` or file).  
  *Reason:* Catches SQL syntax errors that TypeScript cannot.
- **E2E tests** in Playwright cover:  
  1. Sign-up → onboarding → dashboard  
  2. Happy-path CRUD for a core resource  
  3. Auth guard redirects (`/login` redirect for signed-out users)
- Run `pnpm build && pnpm start` locally before opening a PR on authentication or billing changes.

---

## 9. Environment Variables

Validate all env vars with `@t3-oss/env-nextjs`. Access via `env` object, not `process.env` directly.

```ts
DATABASE_URL=file:./sqlite.db        # Local
TURSO_DATABASE_URL=libsql://...      # Production
TURSO_AUTH_TOKEN=...
AUTH_SECRET=...                      # Auth.js secret
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

*Reason:* Schema validation fails the build on missing or malformed variables instead of causing cryptic runtime errors.

---

## 10. Deployment & Backups

- **Turso**: automatic point-in-time recovery (7 days).  
- **Local backup**: `sqlite3 sqlite.db ".backup 'backup.db'"` in CI nightly.  
  *Reason:* The `.backup` API is WAL-safe; plain `cp` on an active WAL-mode DB corrupts snapshots.

---

*Last updated: 2025-06-05. Bump this line when you change a rule.*
