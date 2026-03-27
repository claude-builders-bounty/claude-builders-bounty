# CLAUDE.md — Next.js + SQLite SaaS

## Stack

- Next.js 15 (App Router)
- TypeScript (strict mode)
- SQLite via better-sqlite3 (or Turso for production)
- Drizzle ORM for schema + migrations
- Tailwind CSS
- Auth: NextAuth.js v5

## Folder Structure

```
src/
├── app/                    # App Router pages and layouts
│   ├── (auth)/             # Auth-related routes (login, signup)
│   ├── (dashboard)/        # Protected dashboard routes
│   ├── api/                # API routes (minimize — prefer Server Actions)
│   └── layout.tsx          # Root layout with providers
├── actions/                # Server Actions ("use server")
├── components/
│   ├── ui/                 # Reusable primitives (Button, Input, Card)
│   └── features/           # Feature-specific components
├── db/
│   ├── schema.ts           # Drizzle schema (single source of truth)
│   ├── migrations/         # Generated migrations (never hand-edit)
│   ├── index.ts            # Database connection singleton
│   └── seed.ts             # Seed data for development
├── lib/
│   ├── auth.ts             # NextAuth config
│   ├── utils.ts            # Shared utilities
│   └── validations.ts      # Zod schemas for form/API validation
└── types/                  # Shared TypeScript types
```

## Commands

```bash
pnpm dev                    # Start dev server
pnpm build                  # Production build
pnpm db:generate            # Generate migration from schema changes
pnpm db:migrate             # Apply pending migrations
pnpm db:studio              # Open Drizzle Studio
pnpm db:seed                # Seed development data
pnpm lint                   # ESLint
pnpm typecheck              # tsc --noEmit
```

## Database Rules

- Schema lives in `db/schema.ts` — this is the single source of truth
- Always run `pnpm db:generate` after changing schema, then `pnpm db:migrate`
- Never hand-edit files in `db/migrations/`
- Use Drizzle query builder, not raw SQL
- Every table has `id` (text, primary key, nanoid), `createdAt`, `updatedAt`
- Use `text` for IDs (nanoid), not auto-increment integers
- Foreign keys reference the `id` column, named `{table}Id`
- Indexes on every foreign key column and any column used in WHERE clauses

```typescript
// Schema pattern
export const projects = sqliteTable("projects", {
  id: text("id").primaryKey().$defaultFn(() => nanoid()),
  name: text("name").notNull(),
  userId: text("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
  createdAt: integer("created_at", { mode: "timestamp" }).$defaultFn(() => new Date()),
  updatedAt: integer("updated_at", { mode: "timestamp" }).$defaultFn(() => new Date()),
});
```

## Server Actions Over API Routes

- Default to Server Actions for all data mutations
- API routes only for: webhooks, external integrations, file uploads
- Every Server Action starts with auth check

```typescript
"use server";

import { auth } from "@/lib/auth";
import { db } from "@/db";
import { projects } from "@/db/schema";
import { eq } from "drizzle-orm";
import { revalidatePath } from "next/cache";

export async function createProject(data: { name: string }) {
  const session = await auth();
  if (!session?.user?.id) throw new Error("Unauthorized");

  const [project] = await db
    .insert(projects)
    .values({ name: data.name, userId: session.user.id })
    .returning();

  revalidatePath("/dashboard");
  return project;
}
```

## Component Patterns

- Server Components by default. Add "use client" only when needed (interactivity, hooks, browser APIs)
- Colocate components with their routes when feature-specific
- Shared components go in `components/ui/`
- Props interfaces defined inline or colocated, not in separate type files
- No barrel exports (`index.ts` re-exporting everything)

## Naming Conventions

- Files: kebab-case (`create-project.tsx`, `user-settings.ts`)
- Components: PascalCase (`ProjectCard`, `UserAvatar`)
- Server Actions: camelCase verbs (`createProject`, `deleteUser`)
- Database tables: plural snake_case (`user_projects`, `team_members`)
- Database columns: snake_case (`created_at`, `user_id`)
- Env vars: SCREAMING_SNAKE (`DATABASE_URL`, `NEXTAUTH_SECRET`)

## Validation

- Zod for all form inputs and Server Action parameters
- Validate on the server even if client validates too
- Shared schemas in `lib/validations.ts`

```typescript
import { z } from "zod";

export const createProjectSchema = z.object({
  name: z.string().min(1).max(100),
});

// In Server Action:
const parsed = createProjectSchema.safeParse(data);
if (!parsed.success) throw new Error("Invalid input");
```

## What We Don't Do

- **No raw SQL** — Drizzle handles everything. Raw SQL bypasses type safety.
- **No API routes for CRUD** — Server Actions are simpler, type-safe, and colocated with UI.
- **No `any` types** — Use `unknown` and narrow, or define proper types.
- **No `useEffect` for data fetching** — Use Server Components or TanStack Query.
- **No barrel exports** — They break tree-shaking and obscure dependencies.
- **No ORM-generated IDs (auto-increment)** — nanoid text IDs are URL-safe and non-sequential.
- **No env vars without validation** — Use `@t3-oss/env-nextjs` or manual Zod validation.
- **No inline styles** — Tailwind only.
- **No `console.log` in production code** — Use a proper logger or remove before commit.
