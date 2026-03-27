# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack

- **Framework**: Next.js 15 (App Router only — no Pages Router)
- **Runtime**: Node.js 22 LTS
- **Database**: SQLite via `better-sqlite3` (or Turso for edge)
- **ORM**: Drizzle ORM (not Prisma — Prisma is too heavy for SQLite)
- **Auth**: `better-auth` or `lucia-auth` (no NextAuth — too complex for SaaS MVP)
- **Styling**: Tailwind CSS 4 + `shadcn/ui`
- **Package manager**: pnpm (not npm, not yarn)
- **Language**: TypeScript (strict mode, no `any`)

## Project structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/             # Auth routes (login, register, forgot-password)
│   ├── (dashboard)/        # Protected SaaS routes
│   │   ├── layout.tsx      # Dashboard shell (sidebar, nav)
│   │   ├── page.tsx        # Dashboard home
│   │   └── settings/       # User/org settings
│   ├── api/                # Route handlers (REST-style)
│   │   └── v1/             # Versioned API
│   ├── layout.tsx          # Root layout (providers, fonts)
│   └── page.tsx            # Landing page
├── components/
│   ├── ui/                 # shadcn/ui primitives (button, input, dialog)
│   └── [feature]/          # Feature-specific components
├── db/
│   ├── schema.ts           # Drizzle schema (single source of truth)
│   ├── migrations/         # SQL migration files (numbered)
│   ├── migrate.ts          # Migration runner script
│   └── index.ts            # DB connection singleton
├── lib/
│   ├── auth.ts             # Auth config + helpers
│   ├── constants.ts        # App-wide constants
│   └── utils.ts            # Shared utilities (cn, formatDate, etc.)
├── hooks/                  # Custom React hooks
└── types/                  # Shared TypeScript types
```

## Dev commands

```bash
pnpm dev              # Start dev server (port 3000)
pnpm build            # Production build
pnpm db:generate      # Generate migration from schema changes
pnpm db:migrate       # Run pending migrations
pnpm db:studio        # Open Drizzle Studio (DB browser)
pnpm lint             # ESLint + type check
pnpm test             # Vitest
```

## Database conventions

### Schema rules
- Define all tables in `src/db/schema.ts` using Drizzle's `sqliteTable`
- Every table has: `id` (text, UUID default), `createdAt` (integer, Unix ms), `updatedAt` (integer, Unix ms)
- Use `text` for IDs, not `integer` — UUIDs prevent enumeration attacks
- Foreign keys always have `onDelete` specified (usually `cascade`)
- Boolean fields use `integer({ mode: 'boolean' })`

### Migration rules
- Never edit an existing migration file. Create a new one.
- Run `pnpm db:generate` after any schema change. Commit the generated SQL.
- Migration files are numbered: `0000_initial.sql`, `0001_add_teams.sql`
- Test migrations on a fresh database before committing.

### Query patterns
```typescript
// GOOD: Use Drizzle query builder
const users = await db.select().from(usersTable).where(eq(usersTable.email, email));

// GOOD: Transactions for multi-table writes
await db.transaction(async (tx) => {
  await tx.insert(teamsTable).values(team);
  await tx.insert(membersTable).values(member);
});

// BAD: Never use raw SQL unless Drizzle can't express it
// BAD: Never use db.run() for SELECT queries
```

## Component patterns

### File naming
- Components: `PascalCase.tsx` (e.g., `UserAvatar.tsx`)
- Hooks: `camelCase.ts` prefixed with `use` (e.g., `useUser.ts`)
- Utils/lib: `camelCase.ts` (e.g., `formatDate.ts`)
- Route files: `page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx` (Next.js convention)

### Component rules
- Server Components by default. Only add `"use client"` when you need interactivity.
- Props interfaces go in the same file, above the component. Name them `[Component]Props`.
- No barrel exports (`index.ts` that re-exports). Import directly from the file.
- Co-locate: component + its hook + its types in the same directory.

### Data fetching
```typescript
// GOOD: Server Component with direct DB access
export default async function DashboardPage() {
  const user = await getUser(); // Direct DB call, no API round-trip
  return <Dashboard user={user} />;
}

// GOOD: Server Action for mutations
"use server";
export async function updateProfile(formData: FormData) {
  // Validate, update DB, revalidate
}

// BAD: Don't create API routes for data that Server Components can fetch directly
// BAD: Don't use useEffect + fetch for initial data loading
```

### Form handling
- Use Server Actions for form submissions (not API routes)
- Validate with `zod` on both client and server
- Use `useActionState` for pending/error states
- Show inline errors next to the field, not toast-only

## Auth patterns

- Protect routes in `(dashboard)/layout.tsx` with a server-side auth check
- Redirect to `/login` if no session — never render a blank page
- Store session token in httpOnly cookie (not localStorage)
- Auth middleware runs in `middleware.ts` for edge-compatible checks
- Roles: `owner`, `admin`, `member` — check with `requireRole("admin")`

## API route conventions

- All API routes under `src/app/api/v1/`
- Return `NextResponse.json()` with consistent shape: `{ data, error, meta }`
- Validate request body with zod. Return 400 with `error` on failure.
- Auth: Extract session from cookie in every handler. Return 401 if missing.
- Rate limit: Use `upstash/ratelimit` or in-memory for dev

## Error handling

- Use Next.js `error.tsx` boundaries for route-level errors
- Server Actions return `{ success: boolean; error?: string }` — never throw
- Log errors server-side with structured JSON (`console.error` is fine for MVP)
- User-facing errors are friendly strings. Never expose stack traces.

## What we don't do (and why)

| Anti-pattern | Why |
|---|---|
| Prisma | Too heavy for SQLite. Drizzle is faster, lighter, and SQL-native. |
| NextAuth/Auth.js | Over-engineered for SaaS. `better-auth` or `lucia` gives more control. |
| `getServerSideProps` | Pages Router is dead. Use Server Components. |
| tRPC | Adds complexity. Server Actions + API routes cover all cases. |
| Global state (Redux, Zustand) | Server Components eliminate most client state. Use `useContext` if needed. |
| Barrel exports | Slow builds + circular dependency hell. Import directly. |
| `any` type | Breaks the point of TypeScript. Use `unknown` + type guards. |
| `.env.local` for secrets in prod | Use your hosting platform's secret manager. `.env.local` is dev-only. |
| ORM-generated IDs (autoincrement) | UUIDs prevent enumeration. Always `text` ID with `crypto.randomUUID()`. |
| Seeding in migrations | Migrations are schema-only. Seed in a separate `db:seed` script. |

## Testing

- **Unit**: Vitest for utils and pure functions
- **Component**: Vitest + Testing Library for interactive components
- **E2E**: Playwright for critical flows (signup, billing, core feature)
- Test files live next to source: `UserAvatar.test.tsx` beside `UserAvatar.tsx`

## Git conventions

- Branch: `feat/short-description`, `fix/short-description`
- Commits: Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`)
- PR title = commit message for squash merges
- Never commit `.env.local`, `*.db`, or `node_modules`
