# CLAUDE.md — Next.js 15 App Router + SQLite (Turso/better-sqlite3) SaaS

> Opinionated, production-ready. Every rule has a reason. Drop into any greenfield SaaS project.

## Project Identity

- **Stack**: Next.js 15 (App Router), TypeScript (strict), SQLite (Turso for prod, better-sqlite3 for dev), Tailwind CSS, Drizzle ORM, Clerk Auth, Stripe (payments), Vercel (hosting)
- **Package manager**: `pnpm` (strict lockfile, fast CI)
- **Lint/Format**: Biome (replaces ESLint + Prettier — one tool, zero config drift)
- **Testing**: Vitest (unit) + Playwright (e2e, critical paths only)

## Project Structure — Follow This

```
src/
  app/                  # Next.js App Router (route = folder)
    (marketing)/        # Route group: public pages (no layout inheritance from dashboard)
    (dashboard)/        # Route group: authenticated pages (protected by middleware)
      layout.tsx        # Dashboard shell (sidebar, header)
    api/                # Route handlers (REST endpoints under /api/*)
  components/
    ui/                 # shadcn/ui primitives (Button, Input, Dialog, etc.) — untouched
    dashboard/          # Feature components for dashboard area
    marketing/          # Feature components for public pages
  lib/
    db/
      schema.ts         # Drizzle schema (single source of truth)
      index.ts          # Drizzle client singleton
      migrate.ts        # Migration runner
    auth.ts             # Clerk server helpers (auth(), currentUser())
    stripe.ts           # Stripe client + webhook handler
    utils.ts            # cn() helper, formatters (NO business logic here)
  server/
    actions/            # Server Actions (use "use server" — call from client components)
    queries/            # Data access functions (export async function — NEVER in components)
  hooks/                # Client hooks (useXxx — keep thin, delegate to server actions)
  types/                # Shared types, Zod schemas
```

**Rules**:
- `src/` is the only source directory. No top-level clutter.
- Server Actions live in `src/server/actions/`, NEVER in component files.
- Database queries live in `src/server/queries/`, NEVER inline in components.
- Route handlers (`route.ts`) are thin — delegate to service functions.

## Naming Conventions

| Thing | Convention | Example | Why |
|---|---|---|---|
| Files | kebab-case | `user-profile.tsx` | Consistent with Next.js routing |
| Components | PascalCase | `UserProfile.tsx` | React standard |
| Functions | camelCase | `getUserById()` | TypeScript standard |
| DB tables | snake_case, plural | `user_profiles` | SQL convention; Drizzle maps to camelCase |
| DB columns | snake_case | `created_at` | SQL convention |
| Server actions | verbNoun | `createProject`, `deleteMember` | Self-documenting |
| Zod schemas | noun + `Schema` | `createProjectSchema` | Obvious purpose |
| Route params | kebab-case slugs | `[project-slug]` | URL-friendly |

## Database Rules — NEVER Break These

1. **Drizzle is the single source of truth.** No raw SQL in app code. Migrations only via `pnpm db:generate` / `pnpm db:migrate`.
2. **Migrations are immutable after deploy.** If you need to change a deployed migration, create a NEW migration. Never edit old ones.
3. **Foreign keys are required** for all relationships. Drizzle: `.references(() => table.id, { onDelete: "cascade" })`.
4. **Timestamps on every table**: `created_at` (default now), `updated_at` (auto-update via trigger or Drizzle hook).
5. **Soft deletes preferred** for user-facing data: `deleted_at` timestamp, filtered in every query. Hard deletes only for internal/transient data.
6. **Query in server, pass to client.** Never import `db` in client components. Server Actions → queries → return plain objects.

## Commands

```bash
pnpm dev              # Next.js dev server (Turbopack)
pnpm build            # Production build
pnpm db:generate      # Generate Drizzle migrations from schema changes
pnpm db:migrate       # Apply pending migrations
pnpm db:studio        # Drizzle Studio GUI (localhost:4983)
pnpm lint             # Biome lint + format check
pnpm format           # Biome format (auto-fix)
pnpm test             # Vitest unit tests
pnpm test:e2e         # Playwright (critical paths only)
pnpm stripe:listen    # Stripe webhook forwarding (for local dev)
pnpm typecheck        # tsc --noEmit (run before push, not on every save)
```

## Patterns to Follow

### Data Fetching
```typescript
// ✅ GOOD: Server component fetches own data
export default async function ProjectPage({ params }: { params: { slug: string } }) {
  const project = await getProjectBySlug(params.slug); // from src/server/queries/
  return <ProjectDetail project={project} />;
}

// ✅ GOOD: Mutations via Server Actions
// src/server/actions/projects.ts
"use server";
export async function createProject(input: CreateProjectInput) {
  const { userId } = await auth();
  if (!userId) throw new Error("Unauthorized");
  const parsed = createProjectSchema.parse(input);
  return await db.insert(projects).values({ ...parsed, ownerId: userId });
}
```

### Error Handling
```typescript
// ✅ GOOD: Typed errors, not raw throws
export type ActionResult<T> = { success: true; data: T } | { success: false; error: string };
export async function safeAction<T>(fn: () => Promise<T>): Promise<ActionResult<T>> {
  try { return { success: true, data: await fn() }; }
  catch (e) { return { success: false, error: e instanceof Error ? e.message : "Unknown error" }; }
}
```

### Auth Guards
```typescript
// ✅ GOOD: Middleware protects routes, not inline checks
// middleware.ts protects /dashboard/* — no manual auth() in every component

// ✅ GOOD: Server action auth is minimal
const { userId } = await auth();
if (!userId) redirect("/sign-in");
```

## Anti-Patterns — NEVER Do These

| ❌ Anti-Pattern | ✅ Instead |
|---|---|
| `useEffect` for data fetching | Server Components or React Query for client-side |
| Inline database queries in components | `src/server/queries/` functions |
| `any` type (without explicit eslint-disable) | Proper TypeScript types or `unknown` + narrowing |
| Secret keys in client code (`NEXT_PUBLIC_` abuse) | Only `NEXT_PUBLIC_` for truly public values |
| Passing entire DB rows to client | Pick only needed fields; strip sensitive columns |
| `fetch()` to own API routes from Server Components | Direct function calls to query layer |
| Large client bundles from barrel exports | Named imports: `import { Button } from "@/components/ui/button"` |
| `// @ts-ignore` | `// @ts-expect-error` with explanation comment |
| Environment variables without Zod validation | Validate `process.env` at startup, fail fast |
