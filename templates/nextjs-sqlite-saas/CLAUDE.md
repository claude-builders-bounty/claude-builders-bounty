# CLAUDE.md — Next.js 15 + SQLite SaaS

> Opinionated, production-ready instructions for Claude Code.
> Drop this file into the root of any greenfield Next.js 15 + SQLite SaaS project.

---

## Stack & Versions

| Layer | Technology | Version | Why |
|-------|-----------|---------|-----|
| Framework | Next.js | 15.x (App Router) | RSC-first, streaming, layouts |
| Language | TypeScript | 5.x, strict mode | Catch errors before runtime |
| Database | SQLite via better-sqlite3 | latest | Zero-config, fast reads, single-file DB |
| ORM | Drizzle ORM | latest | Type-safe SQL, zero runtime overhead |
| Styling | Tailwind CSS | 4.x | Utility-first, design tokens |
| Auth | Auth.js (NextAuth v5) | 5.x | Credential + OAuth, edge-compatible |
| Validation | Zod | 3.x | Runtime schema validation |
| Package Manager | pnpm | latest | Fast, disk-efficient |

**Node version:** ≥ 20 LTS. Enforced via `.nvmrc`.

---

## Folder Structure

```
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── (auth)/             # Auth route group (login, register)
│   │   ├── (dashboard)/        # Authenticated route group
│   │   │   ├── layout.tsx      # Dashboard shell with sidebar
│   │   │   ├── page.tsx        # Dashboard home
│   │   │   └── settings/
│   │   ├── api/                # Route handlers only — no pages
│   │   │   └── webhooks/
│   │   ├── layout.tsx          # Root layout (html, body, providers)
│   │   ├── page.tsx            # Landing page
│   │   └── globals.css
│   ├── components/
│   │   ├── ui/                 # Primitive components (Button, Input, Card)
│   │   └── [feature]/          # Feature-scoped composed components
│   ├── db/
│   │   ├── index.ts            # DB connection singleton
│   │   ├── schema.ts           # Drizzle schema definitions
│   │   └── migrations/         # SQL migration files
│   ├── lib/
│   │   ├── auth.ts             # Auth.js config
│   │   ├── constants.ts        # App-wide constants
│   │   └── utils.ts            # Pure utility functions
│   ├── server/
│   │   ├── actions/            # Server Actions (mutations)
│   │   │   └── [entity].ts     # One file per entity
│   │   └── queries/            # Data fetching functions
│   │       └── [entity].ts     # One file per entity
│   └── types/
│       └── index.ts            # Shared TypeScript types
├── drizzle.config.ts
├── next.config.ts
├── .env.local
└── data/
    └── app.db                  # SQLite database file (gitignored)
```

**Rules:**
- Route groups `(auth)`, `(dashboard)` control layout nesting — never nest layouts deeper than 2 levels.
- `api/` is for webhooks and external integrations only. Internal mutations use Server Actions.
- One schema file. When it exceeds 300 lines, split into `schema/users.ts`, `schema/billing.ts`, etc., and re-export from `schema/index.ts`.

---

## Dev Commands

```bash
pnpm dev              # Start Next.js dev server (port 3000)
pnpm build            # Production build
pnpm db:generate      # Generate Drizzle migrations from schema changes
pnpm db:migrate       # Apply pending migrations
pnpm db:studio        # Open Drizzle Studio (GUI for SQLite)
pnpm lint             # ESLint + type check
pnpm test             # Run Vitest unit tests
pnpm test:e2e         # Run Playwright E2E tests
```

**Never run `pnpm db:migrate` in production without a backup.** SQLite doesn't support transactional DDL for all operations.

---

## Database & Migration Conventions

### Schema Rules
```typescript
// ✅ DO: Use explicit column types
export const users = sqliteTable("users", {
  id: text("id").primaryKey().$defaultFn(() => createId()), // cuid2
  email: text("email").notNull().unique(),
  name: text("name").notNull(),
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .$defaultFn(() => new Date()),
  updatedAt: integer("updated_at", { mode: "timestamp" })
    .notNull()
    .$defaultFn(() => new Date()),
});

// ❌ DON'T: Auto-increment integer IDs
// Reason: cuid2 text IDs are globally unique, safe in URLs, and don't leak row count.
```

### Migration Rules
1. **Always generate migrations** — never hand-write SQL migration files.
2. **One migration per change** — don't batch unrelated schema changes.
3. **Migrations are append-only** — never edit or delete a committed migration.
4. **Test migrations on a copy** — `cp data/app.db data/app.db.bak` before running.
5. **Name tables in snake_case, plural** — `user_sessions`, not `UserSession` or `session`.

### Query Patterns
```typescript
// ✅ DO: Queries go in server/queries/, return plain objects
// src/server/queries/users.ts
import { db } from "@/db";
import { users } from "@/db/schema";
import { eq } from "drizzle-orm";

export async function getUserById(id: string) {
  return db.select().from(users).where(eq(users.id, id)).get();
}

// ❌ DON'T: Import db or run queries in client components
// ❌ DON'T: Use raw SQL strings — always use Drizzle query builder
```

---

## Component Patterns

### Server vs Client Components
```typescript
// ✅ Default: Server Components (no directive needed)
// src/app/(dashboard)/page.tsx
import { getProjects } from "@/server/queries/projects";
import { ProjectList } from "@/components/dashboard/project-list";

export default async function DashboardPage() {
  const projects = await getProjects();
  return <ProjectList projects={projects} />;
}

// ✅ Client Components: Only when you need interactivity
// src/components/dashboard/project-list.tsx
"use client";
import { useState } from "react";

export function ProjectList({ projects }: { projects: Project[] }) {
  const [search, setSearch] = useState("");
  // ...
}
```

**Rules:**
- **Server Components by default.** Add `"use client"` only when you need `useState`, `useEffect`, event handlers, or browser APIs.
- **Push client boundaries down.** The interactive part is often a small child component — don't make the whole page a client component.
- **Never pass functions as props** from server to client components. Use Server Actions instead.

### Server Actions (Mutations)
```typescript
// src/server/actions/projects.ts
"use server";

import { z } from "zod";
import { db } from "@/db";
import { projects } from "@/db/schema";
import { revalidatePath } from "next/cache";
import { auth } from "@/lib/auth";

const CreateProjectSchema = z.object({
  name: z.string().min(1).max(100),
  description: z.string().max(500).optional(),
});

export async function createProject(formData: FormData) {
  const session = await auth();
  if (!session?.user) throw new Error("Unauthorized");

  const parsed = CreateProjectSchema.safeParse({
    name: formData.get("name"),
    description: formData.get("description"),
  });

  if (!parsed.success) {
    return { error: parsed.error.flatten().fieldErrors };
  }

  await db.insert(projects).values({
    ...parsed.data,
    userId: session.user.id,
  });

  revalidatePath("/dashboard");
}
```

**Rules:**
- **Always validate with Zod** — never trust client input.
- **Always check auth** — every mutation must verify the session.
- **Always revalidate** — call `revalidatePath` or `revalidateTag` after writes.
- **Return errors, don't throw** — return `{ error: ... }` for form validation errors.

### Naming Conventions
| Thing | Convention | Example |
|-------|-----------|---------|
| Files & folders | kebab-case | `project-list.tsx` |
| Components | PascalCase | `ProjectList` |
| Functions | camelCase | `getUserById` |
| Server Actions | camelCase, verb-first | `createProject`, `deleteUser` |
| DB tables | snake_case, plural | `user_sessions` |
| DB columns | snake_case | `created_at` |
| Env vars | SCREAMING_SNAKE | `DATABASE_URL` |
| CSS classes | Tailwind utilities only | No custom class names |
| Types/Interfaces | PascalCase, no `I` prefix | `User`, not `IUser` |

---

## What We Don't Do (and Why)

### ❌ No `getServerSideProps` or `getStaticProps`
**Why:** These are Pages Router APIs. We use App Router with React Server Components.

### ❌ No API routes for internal mutations
**Why:** Server Actions are simpler, type-safe, and colocated with the UI. API routes are only for external consumers (webhooks, mobile apps).

### ❌ No Prisma
**Why:** Prisma adds a heavy runtime engine. Drizzle ORM is zero-overhead, generates raw SQL, and has better SQLite support.

### ❌ No `useEffect` for data fetching
**Why:** Data fetching belongs in Server Components or Server Actions. `useEffect` causes waterfalls and loading jank.

### ❌ No barrel exports (`index.ts` that re-exports everything)
**Why:** They break tree-shaking and make imports slower. Import directly from the source file.

### ❌ No relative imports deeper than 2 levels
**Why:** Use `@/` path alias instead. `import { db } from "@/db"` not `import { db } from "../../../db"`.

### ❌ No `any` type
**Why:** Use `unknown` and narrow with type guards. `any` defeats the purpose of TypeScript.

### ❌ No `.env` committed to git
**Why:** Use `.env.local` (gitignored) for secrets. Commit `.env.example` with placeholder values.

### ❌ No `console.log` in production code
**Why:** Use a structured logger or remove before committing. Console statements in Server Components are logged server-side and can leak info.

### ❌ No storing files in the database
**Why:** SQLite blob storage is inefficient. Use local filesystem (`data/uploads/`) or S3-compatible storage.

---

## Error Handling

```typescript
// ✅ DO: Custom error types for expected errors
export class AppError extends Error {
  constructor(
    message: string,
    public code: "NOT_FOUND" | "UNAUTHORIZED" | "VALIDATION" | "CONFLICT",
    public status: number = 400
  ) {
    super(message);
  }
}

// ✅ DO: error.tsx for route-level error boundaries
// src/app/(dashboard)/error.tsx
"use client";
export default function DashboardError({ error, reset }: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div>
      <h2>Something went wrong</h2>
      <button onClick={reset}>Try again</button>
    </div>
  );
}

// ✅ DO: not-found.tsx for 404s
// src/app/(dashboard)/[id]/not-found.tsx
export default function NotFound() {
  return <div>Project not found</div>;
}
```

---

## Environment Variables

```bash
# .env.example (committed)
DATABASE_URL=file:./data/app.db
NEXTAUTH_SECRET=generate-with-openssl-rand-base64-32
NEXTAUTH_URL=http://localhost:3000
```

**Access rules:**
- Server-only vars: Access via `process.env.VAR_NAME` in server code only.
- Client vars: Prefix with `NEXT_PUBLIC_` — use sparingly, never for secrets.

---

## Performance Rules

1. **Use `loading.tsx`** for streaming — every route group should have one.
2. **Use `Suspense` boundaries** around slow data fetches in Server Components.
3. **Images: always use `next/image`** — never raw `<img>` tags.
4. **Fonts: use `next/font`** — never external font links.
5. **SQLite: use WAL mode** — set `PRAGMA journal_mode=WAL` on connection.
6. **SQLite: add indexes** for any column used in `WHERE` or `ORDER BY`.
