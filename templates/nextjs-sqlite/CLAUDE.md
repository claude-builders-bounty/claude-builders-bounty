# CLAUDE.md — Next.js 15 (App Router) + SQLite (better-sqlite3) Architecture

> Production-ready agent instructions for building server-rendered SaaS applications with Next.js 15 App Router and local embedded or Turso SQLite.

---

## 1. Project Philosophy & Invariants

1. **Server-First by Default:** All routes, layouts, and components are React Server Components (RSC) unless interactive client-side hooks (`useState`, `useEffect`, event listeners) are strictly necessary. Mark client components with `"use client"` at the exact boundary.
2. **Synchronous, Low-Latency SQLite:** SQLite operates within the server process via `better-sqlite3`. Database access is synchronous, eliminating promise waterfall overhead on the server.
3. **No Database Calls in Client Components:** Database connection handles must never be imported into files with `"use client"`. All DB mutations occur via Server Actions (`actions/`) or Route Handlers (`app/api/`).
4. **Strict Schema Migration Discipline:** Never run raw schema modifications in runtime code. All tables, indexes, and migrations live in `db/migrations/` and execute via migration runner scripts.

---

## 2. Directory & Architectural Conventions

```text
├── app/
│   ├── (auth)/             # Route group for authentication flows
│   ├── (dashboard)/        # Authenticated customer workspace
│   ├── api/                # Webhooks, public API, and SSE routes only
│   ├── layout.tsx          # Root layout with fonts & metadata
│   └── page.tsx            # Marketing or landing root
├── actions/                # Next.js Server Actions ('use server')
│   ├── auth.ts
│   └── workspace.ts
├── db/
│   ├── schema.sql          # Source-of-truth DDL statements
│   ├── client.ts           # Singleton better-sqlite3 connection manager
│   ├── migrations/         # Sequential SQL migrations: 001_init.sql, 002_add_teams.sql
│   └── migrate.ts          # Migration executor script
├── lib/                    # Shared pure utility functions
│   ├── auth.ts             # Session cookies & password hashing (argon2/bcrypt)
│   └── validation.ts       # Zod schemas for forms and actions
├── components/
│   ├── ui/                 # Headless or Tailwind base primitives (buttons, modals)
│   └── forms/              # Client interactive forms with optimistic state
└── types/
    └── index.ts            # Global TypeScript interfaces & DB entity types
```

---

## 3. Database Singleton & Migration Rules

### Database Client Singleton (`db/client.ts`)
```typescript
import Database from "better-sqlite3";
import path from "path";

const DB_PATH = process.env.DATABASE_PATH || path.join(process.cwd(), "data", "saas.db");

// Prevent multiple connections during Next.js hot-reloading in development
declare global {
  var __dbInstance: Database.Database | undefined;
}

export const db: Database.Database =
  global.__dbInstance ||
  new Database(DB_PATH, {
    verbose: process.env.NODE_ENV === "development" ? console.log : undefined,
  });

// Enable WAL mode (Write-Ahead Logging) for concurrent reads & writes
db.pragma("journal_mode = WAL");
db.pragma("foreign_keys = ON");

if (process.env.NODE_ENV !== "production") {
  global.__dbInstance = db;
}
```

### Migration Execution
- All migrations must be idempotent.
- Run migrations before starting dev or build:
  ```bash
  npm run db:migrate
  ```

---

## 4. Developer Commands & Workflows

| Task | Command | Notes |
| :--- | :--- | :--- |
| **Start Development** | `npm run dev` | Runs Next.js at `localhost:3000` |
| **Execute Migrations** | `npm run db:migrate` | Applies pending migrations in `db/migrations/` |
| **Inspect SQLite DB** | `npm run db:studio` or `sqlite3 data/saas.db` | Interactive query shell |
| **Run Test Suite** | `npm test` | Executes unit & integration tests (`vitest` / `node:test`) |
| **Typecheck & Lint** | `npm run lint && tsc --noEmit` | Strict zero-warning verification |
| **Production Build** | `npm run build` | Compiles optimized server bundle |

---

## 5. Patterns to Follow

1. **Colocated Server Actions:**
   Validate all server action payloads using Zod before touching the database:
   ```typescript
   "use server";
   import { z } from "zod";
   import { db } from "@/db/client";
   import { revalidatePath } from "next/cache";

   const CreateProjectSchema = z.object({
     name: z.string().min(3).max(50),
   });

   export async function createProjectAction(formData: FormData) {
     const parsed = CreateProjectSchema.safeParse({
       name: formData.get("name"),
     });
     if (!parsed.success) {
       return { error: parsed.error.flatten().fieldErrors };
     }
     db.prepare("INSERT INTO projects (id, name, created_at) VALUES (?, ?, CURRENT_TIMESTAMP)").run(
       crypto.randomUUID(),
       parsed.data.name
     );
     revalidatePath("/dashboard");
     return { success: true };
   }
   ```

2. **Prepared Statement Caching:**
   Reuse prepared statements or declare them at module scope in query modules to minimize SQLite compilation overhead.

3. **Transaction Safety:**
   Wrap multi-table mutations inside `db.transaction()`:
   ```typescript
   const createAccountTx = db.transaction((user, org) => {
     db.prepare("INSERT INTO users ...").run(user);
     db.prepare("INSERT INTO orgs ...").run(org);
   });
   createAccountTx(userData, orgData);
   ```

---

## 6. Anti-Patterns to Avoid

- ❌ **DO NOT use raw asynchronous ORMs without need:** SQLite in Node is naturally synchronous. Async wrappers add unnecessary microtask latency.
- ❌ **DO NOT commit the `.db` or `.db-wal` files to git:** Ensure `data/*.db*` is strictly listed in `.gitignore`.
- ❌ **DO NOT perform database reads inside Client Components:** Never import `@/db/client` into a component marked `"use client"`.
- ❌ **DO NOT bypass foreign key constraints:** Always leave `PRAGMA foreign_keys = ON;` enabled.
- ❌ **DO NOT concatenate user inputs into SQL strings:** Always use parameterized queries (`?` or named parameters `@param`).
