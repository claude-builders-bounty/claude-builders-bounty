# Project Instructions & Architecture Guide: Next.js 15 + SQLite SaaS

## 1. Stack & Versions
- **Framework**: Next.js 15+ (App Router only, React 19, Server Actions)
- **Language**: TypeScript 5.5+ (Strict mode enabled, zero `any`)
- **Database**: SQLite (local dev: `better-sqlite3` with WAL mode; production/serverless: `@libsql/client` / Turso)
- **ORM**: Drizzle ORM + Drizzle Kit (type-safe SQL, zero runtime schema bloat)
- **Styling**: Tailwind CSS v4 + `clsx` + `tailwind-merge`
- **Validation**: Zod v3.23+ (schemas at all network & database trust boundaries)
- **Package Manager**: `pnpm` (strictly enforced via `package.json` engines)

---

## 2. Standard Dev Commands
```bash
pnpm dev              # Start local dev server (port 3000)
pnpm build            # Production build & compile verification
pnpm lint             # Run ESLint (max warnings 0)
pnpm typecheck        # tsc --noEmit
pnpm test             # Run Vitest test runner

# Database Lifecycle (Drizzle + SQLite)
pnpm db:generate      # Generate SQL migration files from schema changes
pnpm db:migrate       # Apply pending SQL migrations to local SQLite DB
pnpm db:push          # Push schema directly to dev DB (rapid prototyping only)
pnpm db:studio        # Launch visual Drizzle Studio DB inspector
```

---

## 3. Folder Structure
```
├── src/
│   ├── app/                          # Next.js App Router
│   │   ├── (auth)/                   # Auth route group (login, register)
│   │   ├── (dashboard)/              # Protected SaaS workspace routes
│   │   │   ├── layout.tsx            # Authenticated shell layout (Server Component)
│   │   │   └── dashboard/page.tsx
│   │   ├── api/                      # Webhooks and public API endpoints only
│   │   ├── layout.tsx                # Root layout
│   │   └── page.tsx                  # Public marketing / landing page
│   ├── components/
│   │   ├── ui/                       # Reusable headless UI primitives (buttons, dialogs)
│   │   └── dashboard/                # Feature-scoped composite components
│   ├── db/
│   │   ├── index.ts                  # DB client singleton (WAL + PRAGMA setup)
│   │   ├── schema/                   # Drizzle schema definitions by domain
│   │   │   ├── users.ts
│   │   │   ├── organizations.ts
│   │   │   └── subscriptions.ts
│   │   └── migrations/               # Generated versioned SQL migrations
│   ├── lib/
│   │   ├── actions/                  # Server Actions (form mutations & business logic)
│   │   ├── auth/                     # Session & authentication helpers
│   │   └── validators/               # Zod validation schemas
│   └── types/                        # Global shared TypeScript types & inferred DB types
├── drizzle.config.ts                 # Drizzle Kit configuration
└── tsconfig.json
```

---

## 4. Naming Conventions
- **Files & Directories**: `kebab-case` everywhere (`user-profile.tsx`, `resolve-session.ts`).
- **React Components**: `PascalCase` matching export (`export function ProjectCard()`).
- **Server Actions**: `camelCase` starting with action verb (`createProjectAction`, `cancelSubscriptionAction`).
- **DB Tables**: `snake_case` pluralized (`users`, `organization_members`, `audit_logs`).
- **DB Columns**: `snake_case` (`created_at`, `stripe_customer_id`).
- **TypeScript Types/Interfaces**: `PascalCase` (`UserSelect`, `NewUserInsert`).

---

## 5. SQL & SQLite Migration Rules
1. **Always Enable WAL Mode & Foreign Keys**:
   Every SQLite connection pool initialization must run:
   ```sql
   PRAGMA journal_mode = WAL;
   PRAGMA foreign_keys = ON;
   PRAGMA busy_timeout = 5000;
   ```
   *Rationale*: Prevents database locks under concurrent HTTP requests and enforces relational integrity.
2. **Never Edit Existing Migrations**:
   Once committed, a migration in `src/db/migrations/` is immutable. Alterations require a new `pnpm db:generate`.
3. **No Automatic Destructive Drops**:
   Never drop columns with data in production migrations without a 2-step deprecation cycle.
4. **Colocation of Schema**:
   Group tables by bounded context in `src/db/schema/` and re-export via `src/db/schema/index.ts`.

---

## 6. Component & Data Flow Patterns
1. **Server Components by Default**:
   All files in `src/app/` are Server Components unless explicitly requiring client-side event listeners (`onClick`, `useState`, `useEffect`).
2. **Never Add `'use client'` to Parent Layouts**:
   Keep layouts as Server Components for fast initial streaming and SEO. Push `'use client'` down to the leaf buttons or interactive inputs.
3. **Data Fetching in Server Components**:
   Fetch data directly using Drizzle queries inside Server Components:
   ```tsx
   // app/(dashboard)/dashboard/page.tsx
   import { db } from "@/db";
   import { projects } from "@/db/schema";
   
   export default async function DashboardPage() {
     const items = await db.select().from(projects);
     return <ProjectList items={items} />;
   }
   ```
4. **Mutations via Server Actions with Zod**:
   All state-mutating requests must be Server Actions returning structured result types:
   ```ts
   // lib/actions/create-project.ts
   "use server";
   import { z } from "zod";
   import { db } from "@/db";
   
   const schema = z.object({ name: z.string().min(2).max(50) });
   
   export async function createProjectAction(rawInput: unknown) {
     const parsed = schema.safeParse(rawInput);
     if (!parsed.success) {
       return { success: false, error: parsed.error.flatten().fieldErrors };
     }
     // execute DB insert...
     return { success: true };
   }
   ```

---

## 7. What We Don't Do (And Why)

| Anti-Pattern | Why We Forbid It | What To Do Instead |
|---|---|---|
| `useEffect` for data fetching | Causes client waterfalls, flashes of unstyled content, and SEO loss. | Fetch in Server Components or use React Cache. |
| API routes (`/api/...`) for form submissions | Adds unnecessary HTTP serialization overhead and boilerplate routes. | Use Next.js Server Actions with Zod validation. |
| Storing SQLite in volatile container storage | Ephemeral containers wipe DB on redeploy. | Store SQLite DB file on persistent volume mounts or use Turso libSQL. |
| `any` or `@ts-ignore` | Weakens type-safety across DB and UI boundaries. | Use Drizzle's `$inferSelect` and `$inferInsert` types. |
| Hardcoding raw IDs or secrets in frontend | Security breach and credential exposure. | Pass secrets exclusively via Server Actions or Server Components via `process.env`. |
| Unindexed Foreign Keys in SQLite | SQLite does not automatically index foreign keys, causing table scans on `JOIN`. | Always define explicit indexes on foreign key columns in Drizzle schemas. |
