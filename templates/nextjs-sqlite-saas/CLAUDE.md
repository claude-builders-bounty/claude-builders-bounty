# CLAUDE.md — Next.js 15 + SQLite SaaS Template

Opinionated, production-ready guidelines for Claude Code on Next.js 15 (App Router) + SQLite (better-sqlite3 / Turso) + Drizzle ORM SaaS projects.

---

## 1. Stack & Versions

- **Framework**: Next.js 15+ (App Router, Server Actions, React 19)
- **Language**: TypeScript 5.x (Strict mode enabled)
- **Database**: SQLite (`better-sqlite3` for local dev, `@libsql/client` / Turso for production)
- **ORM**: Drizzle ORM (`drizzle-orm`, `drizzle-kit`)
- **Validation**: Zod (`zod`)
- **Styling**: Tailwind CSS v3/v4 + Lucide Icons (`lucide-react`)
- **Auth**: Auth.js / NextAuth v5 or Sessions via HTTP-only cookies

---

## 2. Directory Structure

```text
├── src/
│   ├── app/                    # Next.js 15 App Router pages & API routes
│   │   ├── (auth)/             # Auth route group (login, signup, callback)
│   │   ├── (dashboard)/        # Protected dashboard route group
│   │   ├── api/                # Public/Webhook API route handlers
│   │   ├── layout.tsx          # Root layout
│   │   └── page.tsx            # Landing page
│   ├── actions/                # Server Actions (Zod-validated, type-safe)
│   ├── components/             # UI components
│   │   ├── ui/                 # Atomic UI primitives (buttons, inputs, modals)
│   │   └── dashboard/          # Feature-specific components
│   ├── db/                     # Database schema, client setup & migrations
│   │   ├── migrations/         # Generated SQL migration files
│   │   ├── index.ts            # DB connection client singleton
│   │   └── schema.ts           # Drizzle table schemas & relations
│   └── lib/                    # Shared utilities, auth options, Zod schemas
│       ├── auth.ts             # Auth configuration & session helpers
│       └── utils.ts            # Helper functions (cn, formatters)
├── drizzle.config.ts           # Drizzle Kit configuration file
├── .env.example                # Environment variables template
├── next.config.js              # Next.js configuration
├── package.json
└── tsconfig.json
```

---

## 3. Dev Commands

```bash
# Core Development
npm run dev           # Start Next.js dev server on http://localhost:3000
npm run build         # Build production bundle
npm run start         # Start production server
npm run lint          # Run ESLint

# Database Operations (Drizzle + SQLite)
npm run db:generate   # Generate new SQL migration files from schema updates
npm run db:migrate    # Apply pending SQL migrations to local SQLite DB
npm run db:push       # Push schema changes directly to SQLite (Dev rapid prototyping)
npm run db:studio     # Open Drizzle Studio GUI on http://localhost:4983
```

---

## 4. Database & Migration Rules

1. **Single Schema File**: All tables, enums, and relations MUST be defined in `src/db/schema.ts`.
2. **Foreign Keys Enabled**: SQLite requires foreign key constraints to be explicitly enabled on connection (`PRAGMA foreign_keys = ON;`). Ensure `src/db/index.ts` executes this pragma.
3. **Migration Workflow**:
   - Modify `src/db/schema.ts`.
   - Run `npm run db:generate` to produce timestamped migration SQL files in `src/db/migrations/`.
   - Run `npm run db:migrate` to apply migrations safely.
4. **Data Types**:
   - IDs: Use text UUIDs (`text("id").primaryKey().$defaultFn(() => crypto.randomUUID())`) or integer auto-increments.
   - Timestamps: Store as integer Unix timestamps (`integer("created_at", { mode: "timestamp" })`) or ISO strings.
   - Booleans: Store as integers (`integer("is_active", { mode: "boolean" })`).

---

## 5. Server Component & Action Patterns

- **Server Components First**: All page and layout components are Server Components by default (`async function Page()`).
- **Use `'use client'` Sparingly**: Only add `'use client'` at the top of files that require browser event handlers, React hooks (`useState`, `useEffect`), or client-only libraries.
- **Server Actions for Mutations**: All database writes (insert, update, delete) MUST use Server Actions in `src/actions/`.
- **Validation Law**: Every Server Action MUST validate inputs using a Zod schema before querying the database:

```typescript
// Example: src/actions/project.ts
'use server'

import { db } from "@/db"
import { projects } from "@/db/schema"
import { z } from "zod"
import { revalidatePath } from "next/cache"

const CreateProjectSchema = z.object({
  name: z.string().min(2).max(50),
  description: z.string().optional(),
})

export async function createProject(formData: FormData) {
  const parsed = CreateProjectSchema.safeParse({
    name: formData.get("name"),
    description: formData.get("description"),
  })

  if (!parsed.success) {
    return { success: false, error: parsed.error.flatten().fieldErrors }
  }

  try {
    const [newProject] = await db.insert(projects).values(parsed.data).returning()
    revalidatePath("/dashboard")
    return { success: true, data: newProject }
  } catch (err) {
    return { success: false, error: "Database transaction failed" }
  }
}
```

---

## 6. What We Don't Do (and Why)

| Anti-Pattern | Why We Avoid It | What To Do Instead |
|---|---|---|
| **Raw SQL String Interpolation** | Vulnerable to SQL injection attacks | Use Drizzle ORM query builder or parametrized prepared statements |
| **Client-side DB Access** | SQLite is a server-side file database; exposing credentials or file path to client fails or leaks security | Run all DB operations inside Server Components, Route Handlers, or Server Actions |
| **Omitting Zod Validation** | Unvalidated user input leads to corrupted database state or unexpected runtime crashes | Validate all incoming request parameters, query params, and form inputs via Zod |
| **Mutating State in Render** | Causes infinite render loops and non-deterministic UI side-effects in React 19 | Perform mutations strictly within Server Actions or event handlers |
| **Hardcoding API Secrets** | Exposes private API keys, tokens, or encryption secrets in source control | Access environment variables exclusively via `process.env.SECRET_KEY` and populate `.env.local` |

---

## 7. Security & Production Preparedness

- **Database File Location**: Keep `sqlite.db` in a secured directory outside public web server roots (e.g. `./data/sqlite.db` or Turso cloud URL).
- **WAL Mode**: Enable Write-Ahead Logging (`PRAGMA journal_mode = WAL;`) for concurrent read/write performance under multi-threaded server execution.
- **CSRF & CORS**: Next.js Server Actions automatically verify Origin headers. Ensure public API routes in `src/app/api/` enforce proper CORS headers.
