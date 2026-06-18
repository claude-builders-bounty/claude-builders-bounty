# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack & Versions

| Layer | Technology | Version Constraint |
|-------|-----------|-------------------|
| Framework | Next.js | 15.x (App Router only) |
| Database | SQLite via better-sqlite3 | ^11.x |
| ORM / Query | Drizzle ORM | ^0.38.x |
| Auth | NextAuth.js / Auth.js | ^5.x |
| CSS | Tailwind CSS | ^4.x |
| Language | TypeScript | ^5.x (strict mode) |
| Package Manager | pnpm | ^9.x |

## Folder Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── (auth)/             # Auth route group
│   ├── (dashboard)/        # Authenticated routes
│   ├── api/                # Route handlers (no separate server/)
│   │   └── trpc/           # tRPC endpoints (if used)
│   └── layout.tsx          # Root layout
├── components/
│   ├── ui/                 # Primitive UI (button, input, card, etc.)
│   ├── shared/             # Feature-specific shared components
│   └── forms/              # Form components (react-hook-form)
├── db/
│   ├── schema/             # Drizzle schema files (one per domain)
│   │   ├── users.ts
│   │   ├── projects.ts
│   │   └── subscriptions.ts
│   ├── migrations/         # Auto-generated Drizzle migrations
│   ├── index.ts            # DB client singleton
│   └── seed.ts             # Dev seed data
├── lib/
│   ├── auth.ts             # Auth.js config
│   ├── stripe.ts           # Payment helpers (if applicable)
│   └── email.ts            # Email sending (Resend / SendGrid)
├── hooks/                  # Shared React hooks
├── types/                  # Global TypeScript types
└── env.ts                  # Zod-validated env schema
```

## SQL / Migration Conventions

### Rules

1. **Every migration is reversible.** Write `down` SQL for every `up`. If a migration can't be reversed (e.g. destructive column drop), add a warning comment.
2. **Never modify a committed migration.** Create a new one. This is non-negotiable — team members may have already applied it.
3. **Foreign keys are explicit.** Always define `references()` in Drizzle schema. SQLite doesn't enforce FK by default — run `PRAGMA foreign_keys = ON` on connect.
4. **Timestamps are `TEXT` (ISO 8601).** SQLite has no native datetime type. Store as `TEXT` in UTC (`new Date().toISOString()`). No Unix integers, no `DATETIME` — consistency matters.
5. **Index every foreign key column.** SQLite doesn't auto-index FKs. If you query by `user_id`, it needs an index.

### Migration Workflow

```bash
pnpm drizzle-kit generate   # Generate migration from schema changes
pnpm drizzle-kit migrate    # Apply to local SQLite
```

## Component Patterns

### Server Components First

Every component starts as a Server Component. Only add `'use client'` when you need:
- Interactivity (onClick, onChange, etc.)
- Browser-only APIs (localStorage, navigator, etc.)
- React hooks (useState, useEffect, useContext)

### Data Fetching

```tsx
// ✅ Server Component: fetch in the component, not in a hook
export default async function ProjectPage({ params }: Props) {
  const project = await db.query.projects.findFirst({
    where: eq(projects.id, params.id),
  });
  return <ProjectDetail project={project} />;
}

// ❌ Don't: fetch in a client component with useEffect
```

### Server Actions for Mutations

```tsx
// ✅ Server Action in a `actions/` file
'use server';
export async function createProject(formData: FormData) {
  const data = createProjectSchema.parse(Object.fromEntries(formData));
  await db.insert(projects).values(data);
  revalidatePath('/dashboard');
}
```

## Dev Commands

```bash
pnpm dev              # Local dev
pnpm build            # Production build
pnpm test             # Vitest
pnpm lint             # Biome or ESLint
pnpm db:generate      # Drizzle migration generation
pnpm db:migrate       # Apply migrations
pnpm db:seed          # Seed development data
pnpm db:studio        # Drizzle Studio (GUI for local DB)
pnpm typecheck        # tsc --noEmit
```

## Anti-Patterns (What We Don't Do, And Why)

1. **No `server/` directory.** Next.js App Router route handlers go in `src/app/api/`. A separate `server/` dir creates confusion about where to put things. If you need shared server logic, it goes in `src/lib/`.

2. **No `services/` layer.** Business logic lives in server actions, Drizzle queries, or lib utilities. An extra abstraction layer adds indirection without enough benefit for a SaaS codebase this size.

3. **No raw SQL strings.** Use Drizzle ORM for everything. If Drizzle can't express the query (window functions, recursive CTEs), extract it to a typed helper in `src/lib/queries/`.

4. **No `any` or `as` casts.** TypeScript strict mode is on. If you're fighting the type system, fix the types — don't escape them.

5. **No `.env.local` in docs.** Document env vars in `env.ts` (Zod schema). The `.env.example` file should list keys only, no placeholder values.

6. **No `try/catch` swallowing.** Every caught error must either: (a) log and rethrow, (b) return a typed error response, or (c) show a user-facing toast. Empty `catch {}` is not allowed.

## Auth / Session Pattern

Auth.js v5 with the `database` strategy (SQLite adapter). Session is fetched once in the root layout and passed down. No `useSession()` in individual components unless they mutate auth state.

```tsx
// ✅ Root layout handles session
export default async function RootLayout({ children }: Props) {
  const session = await auth();
  return <SessionProvider session={session}>{children}</SessionProvider>;
}
```

## Error Handling

- **Route handlers:** Always wrap in `try/catch`, return `NextResponse.json({ error })` with appropriate status.
- **Server Actions:** Return `{ success: boolean, error?: string }` — never throw in server actions unless it's a redirect.
- **Client Components:** Use `error.tsx` (error boundary files) for each route segment.
- **Not found:** Use `notFound()` from `next/navigation`, not custom 404 pages per route.
