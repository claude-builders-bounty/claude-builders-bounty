# Project: Next.js 15 + SQLite SaaS

## Stack

- **Framework:** Next.js 15 (App Router, React Server Components)
- **Database:** SQLite via `better-sqlite3` (single-file, zero-config)
- **ORM:** Drizzle ORM (type-safe, SQL-first, migration support)
- **Auth:** NextAuth.js v5 (OAuth + email, session stored in SQLite)
- **Styling:** Tailwind CSS 4 + shadcn/ui components
- **Language:** TypeScript (strict mode)
- **Runtime:** Node.js 20+ LTS

## Project Structure

```
src/
  app/                    # Next.js App Router pages
    (auth)/               # Auth route group (login, register)
    (dashboard)/          # Protected route group
    api/                  # API routes (Route Handlers)
    layout.tsx            # Root layout (providers, nav)
    page.tsx              # Landing page
  components/
    ui/                   # shadcn/ui primitives (Button, Input, etc.)
    forms/                # Form components with validation
    layouts/              # Page-level layouts (sidebar, header)
  lib/
    db/
      index.ts            # Database connection singleton
      schema.ts           # Drizzle schema definitions (single source of truth)
      migrations/         # SQL migration files (numbered, sequential)
    auth.ts               # NextAuth configuration
    utils.ts              # Pure utility functions
    validators.ts         # Zod schemas for input validation
  hooks/                  # Custom React hooks (client-side only)
  types/                  # Shared TypeScript types
db/
  sqlite.db               # SQLite database file (gitignored)
drizzle.config.ts         # Drizzle ORM configuration
```

**Why this structure:** App Router groups `(auth)` and `(dashboard)` separate public and protected routes without adding URL segments. The `lib/db/` directory keeps all database logic colocated. Components are split by purpose (ui/forms/layouts) not by feature — because in a SaaS, most components are shared across features.

## Naming Conventions

| What | Convention | Example | Why |
|------|-----------|---------|-----|
| Files & folders | `kebab-case` | `user-profile.tsx` | Next.js convention, avoids case-sensitivity issues on Linux |
| Components | `PascalCase` | `UserProfile` | React convention |
| Functions/hooks | `camelCase` | `useUserProfile` | JavaScript convention |
| Database tables | `snake_case` | `user_profiles` | SQL convention, avoids quoting issues |
| Database columns | `snake_case` | `created_at` | SQL convention |
| API routes | `kebab-case` | `/api/user-profile` | URL convention |
| Environment vars | `SCREAMING_SNAKE` | `DATABASE_URL` | Universal convention |
| Types/interfaces | `PascalCase` | `UserProfile` | TypeScript convention |
| Zod schemas | `camelCase` + Schema suffix | `userProfileSchema` | Distinguishes from types |

## Database & Migrations

### Schema definition (Drizzle)

All tables are defined in `lib/db/schema.ts`. This is the single source of truth:

```typescript
// lib/db/schema.ts
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";

export const users = sqliteTable("users", {
  id: text("id").primaryKey().$defaultFn(() => crypto.randomUUID()),
  email: text("email").notNull().unique(),
  name: text("name"),
  role: text("role", { enum: ["user", "admin"] }).notNull().default("user"),
  created_at: integer("created_at", { mode: "timestamp" }).$defaultFn(() => new Date()),
  updated_at: integer("updated_at", { mode: "timestamp" }).$defaultFn(() => new Date()),
});
```

**Why Drizzle:** It generates SQL you can read. No magic. The schema file IS the migration — `drizzle-kit push` applies it. For production, use `drizzle-kit generate` to create versioned SQL files.

### Migration rules

1. **Never edit an existing migration file.** Create a new one. Reason: other environments may have already applied it.
2. **Always add columns as nullable first**, then backfill, then add NOT NULL in a separate migration. Reason: SQLite locks the entire database during ALTER TABLE — keep it fast.
3. **Name migrations sequentially:** `0001_create_users.sql`, `0002_add_teams.sql`. Reason: execution order must be deterministic.
4. **No `DROP COLUMN` in SQLite.** SQLite doesn't support it. Instead: create new table → copy data → drop old → rename. Drizzle handles this automatically with `drizzle-kit push`.
5. **Always include `created_at` and `updated_at`** on every table. Reason: debugging production issues without timestamps is miserable.
6. **Use UUIDs for primary keys**, not auto-increment. Reason: safe for multi-device sync, no ID collision when merging databases.

### Database connection

```typescript
// lib/db/index.ts
import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";
import * as schema from "./schema";

const sqlite = new Database("db/sqlite.db");
sqlite.pragma("journal_mode = WAL");      // Concurrent reads during writes
sqlite.pragma("foreign_keys = ON");        // Enforce FK constraints
sqlite.pragma("busy_timeout = 5000");      // Wait 5s instead of failing on lock

export const db = drizzle(sqlite, { schema });
```

**Why WAL mode:** Without it, SQLite blocks all reads during a write. WAL allows concurrent readers, which matters for a web server handling multiple requests.

## Dev Commands

```bash
npm run dev              # Start Next.js dev server (port 3000)
npm run build            # Production build
npm run db:push          # Apply schema changes to SQLite (development)
npm run db:generate      # Generate SQL migration files (production)
npm run db:migrate       # Run pending migrations
npm run db:studio        # Open Drizzle Studio (visual DB browser)
npm run lint             # ESLint + TypeScript check
npm run test             # Run Vitest
```

## Component Patterns

### Server Components (default)

Every component is a Server Component unless you explicitly add `"use client"`. Server Components can:
- Fetch data directly (no API routes needed)
- Access the database directly
- Never ship JavaScript to the client

```typescript
// app/(dashboard)/projects/page.tsx — Server Component
import { db } from "@/lib/db";
import { projects } from "@/lib/db/schema";
import { eq } from "drizzle-orm";

export default async function ProjectsPage() {
  const allProjects = await db.select().from(projects);
  return <ProjectList projects={allProjects} />;
}
```

**Why:** Server Components reduce client bundle size. The database query above runs on the server — zero JavaScript sent to the browser.

### Client Components (opt-in)

Only use `"use client"` when you need: `useState`, `useEffect`, `onClick`, `onChange`, browser APIs.

```typescript
// components/forms/create-project-form.tsx
"use client";

import { useActionState } from "react";
import { createProject } from "@/app/actions";

export function CreateProjectForm() {
  const [state, formAction, pending] = useActionState(createProject, null);
  return (
    <form action={formAction}>
      <input name="name" required />
      <button disabled={pending}>Create</button>
      {state?.error && <p className="text-red-500">{state.error}</p>}
    </form>
  );
}
```

**Why `useActionState`:** It's Next.js 15's replacement for `useFormState`. Handles loading state, error state, and form submission in one hook — no manual `useState` + `fetch`.

### Server Actions (mutations)

```typescript
// app/actions.ts
"use server";

import { db } from "@/lib/db";
import { projects } from "@/lib/db/schema";
import { revalidatePath } from "next/cache";
import { projectSchema } from "@/lib/validators";

export async function createProject(prevState: any, formData: FormData) {
  const parsed = projectSchema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) return { error: parsed.error.flatten().fieldErrors };

  await db.insert(projects).values(parsed.data);
  revalidatePath("/projects");
  return { success: true };
}
```

**Why Server Actions over API routes:** Less boilerplate, automatic form data parsing, works with progressive enhancement (forms work even with JavaScript disabled).

## Anti-Patterns (What We Don't Do)

### 1. Don't use API routes for data fetching in Server Components

```typescript
// BAD — unnecessary network hop
export default async function Page() {
  const res = await fetch("/api/projects");
  const data = await res.json();
}

// GOOD — direct database access
export default async function Page() {
  const data = await db.select().from(projects);
}
```

**Why:** Server Components run on the server. Fetching from your own API adds latency and complexity for zero benefit.

### 2. Don't put `"use client"` at the top of page files

```typescript
// BAD — entire page is client-rendered
"use client";
export default function DashboardPage() { ... }

// GOOD — page is server, only interactive parts are client
export default async function DashboardPage() {
  const data = await db.select().from(projects);
  return <InteractiveWidget data={data} />;  // Only this is "use client"
}
```

**Why:** Making a page a Client Component means it can't fetch data on the server, can't access the database, and ships more JavaScript.

### 3. Don't use raw SQL strings

```typescript
// BAD — SQL injection risk, no type safety
db.run("SELECT * FROM users WHERE email = '" + email + "'");

// GOOD — parameterized via Drizzle
db.select().from(users).where(eq(users.email, email));
```

**Why:** SQL injection is the #1 web vulnerability (OWASP). Drizzle parameterizes automatically.

### 4. Don't store secrets in code

```typescript
// BAD
const SECRET = "sk_live_abc123";

// GOOD — use .env.local (gitignored by default in Next.js)
const SECRET = process.env.AUTH_SECRET;
```

**Why:** Secrets in code get committed to git and exposed in builds.

### 5. Don't create a new database connection per request

```typescript
// BAD — opens new connection every time
export async function GET() {
  const sqlite = new Database("db/sqlite.db");
  // ...
}

// GOOD — singleton in lib/db/index.ts (module-level)
import { db } from "@/lib/db";
```

**Why:** SQLite has a single-writer lock. Multiple connections cause "database is locked" errors under load.

### 6. Don't use `useEffect` for data fetching

```typescript
// BAD — client-side fetch, loading spinner, waterfall
"use client";
export default function Page() {
  const [data, setData] = useState(null);
  useEffect(() => { fetch("/api/data").then(...) }, []);
}

// GOOD — Server Component, data is ready on first render
export default async function Page() {
  const data = await db.select().from(projects);
  return <ProjectList projects={data} />;
}
```

**Why:** `useEffect` fetching causes loading spinners, layout shift, and waterfalls. Server Components render with data already loaded.

### 7. Don't mix Tailwind with CSS modules

Pick one. We use Tailwind. No `.module.css` files. Reason: mixing creates two mental models. Tailwind's utility classes are sufficient for any design.

### 8. Don't skip Zod validation on Server Actions

```typescript
// BAD — trusting form data
export async function createUser(formData: FormData) {
  const email = formData.get("email") as string;
  await db.insert(users).values({ email });
}

// GOOD — validate first
export async function createUser(prevState: any, formData: FormData) {
  const parsed = userSchema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) return { error: "Invalid input" };
  await db.insert(users).values(parsed.data);
}
```

**Why:** Form data can be tampered with. Zod catches invalid input before it hits the database.

### 9. Don't use `any` type

```typescript
// BAD
function processData(data: any) { ... }

// GOOD
function processData(data: UserProfile) { ... }
```

**Why:** `any` disables TypeScript's entire benefit. Use `unknown` if the type is truly unknown, then narrow with type guards.

### 10. Don't commit `sqlite.db` to git

Add to `.gitignore`:
```
db/*.db
db/*.db-journal
db/*.db-wal
```

**Why:** Binary files bloat the repo, cause merge conflicts, and may contain user data.

### 11. Don't use `next/router` (Pages Router)

```typescript
// BAD — Pages Router import
import { useRouter } from "next/router";

// GOOD — App Router import
import { useRouter } from "next/navigation";
```

**Why:** Next.js 15 uses App Router. The old `next/router` is for Pages Router and won't work.

### 12. Don't hardcode URLs

```typescript
// BAD
const API_URL = "http://localhost:3000/api";

// GOOD
const API_URL = process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";
```

**Why:** Breaks in production, staging, and when teammates use different ports.

## Environment Variables

```bash
# .env.local (gitignored)
DATABASE_URL="db/sqlite.db"
AUTH_SECRET="generate-with-openssl-rand-base64-32"
AUTH_GITHUB_ID="your-github-oauth-id"
AUTH_GITHUB_SECRET="your-github-oauth-secret"
NEXT_PUBLIC_APP_URL="http://localhost:3000"
```

**Prefix rule:** `NEXT_PUBLIC_` = accessible in browser. Without prefix = server-only. Never put secrets in `NEXT_PUBLIC_` variables.

## Performance Rules

1. **Use `loading.tsx`** for route-level Suspense boundaries. Reason: instant page transitions.
2. **Use `generateStaticParams`** for pages with known slugs. Reason: pre-render at build time.
3. **Colocate data fetching with the component that uses it.** Reason: parallel fetching, no request waterfalls.
4. **Use `unstable_cache`** or React `cache()` for expensive queries. Reason: SQLite is fast but caching is faster.
5. **Optimize images with `next/image`.** Always set `width`, `height`, and `alt`. Reason: prevents layout shift, serves WebP automatically.
