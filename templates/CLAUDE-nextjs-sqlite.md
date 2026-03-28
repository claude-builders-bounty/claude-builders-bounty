# Project — Next.js 15 SaaS with SQLite

## Stack

- **Framework:** Next.js 15 (App Router, Server Components by default)
- **Language:** TypeScript 5, strict mode
- **Database:** SQLite via better-sqlite3 (dev/single-node) or Turso/libsql (production)
- **ORM:** Drizzle ORM with drizzle-kit migrations
- **Auth:** Auth.js v5 (next-auth)
- **Styling:** Tailwind CSS 4, shadcn/ui components
- **Package manager:** pnpm
- **Node:** 22 LTS

## Commands

```bash
pnpm dev              # Start dev server (port 3000)
pnpm build            # Production build
pnpm db:generate      # Generate migration from schema changes
pnpm db:migrate       # Run pending migrations
pnpm db:studio        # Open Drizzle Studio (DB browser)
pnpm lint             # ESLint + type check
pnpm test             # Vitest unit tests
pnpm test:e2e         # Playwright E2E tests
```

## Folder Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/             # Auth pages (login, register) — no sidebar
│   ├── (dashboard)/        # Authenticated pages — with sidebar
│   │   ├── layout.tsx      # Dashboard shell (sidebar, header)
│   │   ├── page.tsx        # /dashboard
│   │   └── settings/
│   ├── api/                # Route handlers (webhooks, external APIs only)
│   └── layout.tsx          # Root layout (providers, fonts)
├── actions/                # Server Actions (one file per domain)
│   ├── auth.ts
│   ├── projects.ts
│   └── billing.ts
├── components/
│   ├── ui/                 # shadcn/ui primitives (don't edit)
│   └── [domain]/           # Feature components (projects/, billing/)
├── db/
│   ├── schema.ts           # Drizzle schema (single file, all tables)
│   ├── index.ts            # DB connection singleton
│   ├── migrate.ts          # Migration runner
│   └── seed.ts             # Dev seed data
├── lib/                    # Shared utilities
│   ├── auth.ts             # Auth.js config
│   ├── constants.ts        # App constants (plans, limits)
│   └── utils.ts            # Pure helper functions
└── types/                  # Shared TypeScript types
    └── index.ts
drizzle/                    # Generated migrations (don't edit manually)
```

## Naming Conventions

- **Files:** kebab-case (`project-card.tsx`, `use-projects.ts`)
- **Components:** PascalCase exports (`export function ProjectCard`)
- **Server Actions:** camelCase, verb-first (`createProject`, `deleteTeamMember`)
- **DB tables:** snake_case plural (`user_projects`, `billing_events`)
- **DB columns:** snake_case (`created_at`, `stripe_customer_id`)
- **Env vars:** UPPER_SNAKE_CASE, prefixed (`DATABASE_URL`, `AUTH_SECRET`)
- **Route groups:** parenthesized by auth state (`(auth)`, `(dashboard)`, `(marketing)`)

## Database Rules

### Schema

All tables in `src/db/schema.ts`. Every table has:
```typescript
id: text("id").primaryKey().$defaultFn(() => createId()),
createdAt: integer("created_at", { mode: "timestamp" }).notNull().$defaultFn(() => new Date()),
updatedAt: integer("updated_at", { mode: "timestamp" }).notNull().$defaultFn(() => new Date()).$onUpdate(() => new Date()),
```

Use `text` for IDs (cuid2 via `@paralleldrive/cuid2`), not auto-increment integers. Reason: IDs appear in URLs and APIs — sequential integers leak information.

### Migrations

- Run `pnpm db:generate` after every schema change
- Never edit files in `drizzle/` manually
- Each migration runs in a transaction
- Backward-compatible only — no dropping columns in production. Add new column, migrate data, then remove old column in a follow-up

### Queries

- All DB access goes through Server Actions or Route Handlers. Never query in components directly.
- Use Drizzle query builder, not raw SQL
- Always scope queries by the authenticated user's `organizationId` — never trust client input for authorization

## Component Patterns

### Server Components (default)

Every component is a Server Component unless it needs interactivity. Data fetching happens at the page or layout level, passed as props.

```typescript
// app/(dashboard)/projects/page.tsx
export default async function ProjectsPage() {
  const projects = await getProjects();
  return <ProjectList projects={projects} />;
}
```

### Client Components

Add `"use client"` only when the component uses hooks, event handlers, or browser APIs. Keep them as leaf nodes — don't wrap large trees in `"use client"`.

### Forms

Use Server Actions with `useActionState` (React 19). No `useState` + `fetch` for mutations.

```typescript
// actions/projects.ts
"use server"
export async function createProject(prevState: ActionState, formData: FormData) {
  const name = formData.get("name") as string;
  // validate, insert, revalidate
  revalidatePath("/projects");
  return { success: true };
}
```

### Loading & Error States

Every route segment that fetches data has `loading.tsx` and `error.tsx` siblings. Use Suspense for granular loading states within a page.

## What We Don't Do (and Why)

| Don't | Why |
|-------|-----|
| `use client` at page level | Kills SSR, defeats the purpose of App Router |
| API routes for internal mutations | Server Actions are simpler, type-safe, and colocated |
| `useEffect` for data fetching | Server Components fetch on the server. Use `use()` or async components |
| Raw SQL strings | Drizzle prevents injection, gives type safety, handles migrations |
| `any` type | Use `unknown` + type guard, or define a proper type |
| Barrel exports (`index.ts` re-exports) | Breaks tree-shaking, slows builds, makes imports ambiguous |
| ORM models with methods | Drizzle schemas are plain declarations. Logic goes in Server Actions |
| Global error handling middleware | Use `error.tsx` per route segment. Granular, debuggable |
| Environment variables without validation | Validate with `zod` in `src/env.ts` at startup. Fail fast |
| Storing files in SQLite | Use object storage (S3/R2) for files, store URLs in DB |

## Auth Pattern

Auth.js v5 with database adapter. Session check via `auth()` in Server Components and `getServerSession()` in Server Actions.

```typescript
// In any Server Component or Action:
const session = await auth();
if (!session?.user) redirect("/login");
```

Protect route groups in layout:
```typescript
// app/(dashboard)/layout.tsx
export default async function DashboardLayout({ children }) {
  const session = await auth();
  if (!session) redirect("/login");
  return <Shell user={session.user}>{children}</Shell>;
}
```

## Error Handling

- Server Actions return `{ success: boolean, error?: string }`, never throw
- Use `error.tsx` for unexpected errors per route
- Log errors server-side with structured logging (pino)
- Show user-friendly messages in the UI, never stack traces

## Testing

- **Unit:** Vitest for utility functions and Server Actions (mock DB)
- **E2E:** Playwright for critical user flows (signup, create project, billing)
- **DB tests:** Use in-memory SQLite (`:memory:`) for fast isolated tests
- Test file lives next to source: `lib/utils.test.ts`
