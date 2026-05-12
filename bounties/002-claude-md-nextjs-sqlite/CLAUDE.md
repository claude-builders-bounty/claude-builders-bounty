# Next.js 15 + SQLite SaaS — Claude Code Project Guide

This project is a B2B SaaS app built with Next.js 15 App Router, TypeScript, SQLite (via Turso/libSQL), Drizzle ORM, and Tailwind CSS. Read this entire file before writing any code. These rules are opinionated—every restriction exists because we've seen the alternative cause bugs or drift.

## Stack

| Layer | Choice | Why this, not the alternative |
|-------|--------|-------------------------------|
| Framework | Next.js 15 App Router | RSC = zero client JS by default. Pages Router has no future. |
| Language | TypeScript `strict: true` | `strict` catches ~40% of real runtime bugs at compile time. No `any`. |
| Database | SQLite / Turso libSQL | Zero-latency local dev, edge-compatible, no connection pooling needed. Not Postgres—we'll migrate when we need concurrent writes at scale. |
| ORM | Drizzle ORM | Type-safe queries without runtime overhead. Explicit SQL, not magic. Not Prisma—Prisma's generated client is a black box and its migrations require network access. |
| Auth | Better Auth | Multi-tenant sessions, org switching, passkeys out of the box. Not NextAuth/Auth.js—Better Auth has first-class org support we'd have to rebuild from scratch. |
| Styling | Tailwind CSS + local `ui/` components | Copy-paste-ready components, no dependency tree. Not shadcn/ui as a package—we vendor the components we actually use into `src/components/ui/` so we can modify them freely. |
| Validation | Zod | Runtime + compile-time. Used at every system boundary: forms, Server Actions, API routes, env vars. Not Yup—Zod's TypeScript inference is superior. |
| Package manager | pnpm | Deterministic, fast, disk-efficient. Not npm or yarn. |
| Testing | Vitest (unit) + Playwright (E2E) | Vitest = Jest-compatible, faster. Playwright = real browser. No Jest—Vitest is a drop-in with better ESM support. |

## Dev Commands

```bash
pnpm install          # install dependencies
pnpm dev              # start dev server (localhost:3000)
pnpm build            # production build
pnpm lint             # ESLint
pnpm typecheck        # tsc --noEmit
pnpm test             # vitest run
pnpm test:e2e         # playwright test
pnpm db:generate      # drizzle-kit generate (after schema change)
pnpm db:migrate       # drizzle-kit migrate (apply migrations)
pnpm db:studio        # drizzle-kit studio (UI)
pnpm db:seed          # seed dev data
```

If a command doesn't exist yet, add it to `package.json` before using it. Never run raw `tsx` scripts in CI—everything goes through `package.json` scripts.

## Folder Structure

```
src/
  app/
    (marketing)/          # public pages: /, /pricing, /blog
    (app)/                # authenticated pages behind /app
      layout.tsx          # session + org context loader
      dashboard/
      settings/
    api/                  # Route Handlers ONLY for webhooks + OAuth callbacks
  auth/
    client.ts             # Better Auth browser client
    server.ts             # Better Auth server instance (singleton)
  components/
    ui/                   # vendored, modifiable UI primitives
    feature/              # domain-specific components (not ui/)
  db/
    client.ts             # single Drizzle + Turso client export
    schema.ts             # all table definitions in one file
    migrations/           # checked-in SQL migration files
    queries/              # feature-level query modules (see below)
  features/
    billing/              # Stripe, plans, usage
    organizations/        # org CRUD, membership, invites
    users/                # profile, preferences
  lib/
    env.ts                # Zod-parsed env vars (import this, not process.env)
    errors.ts             # typed error classes
  server/
    actions/              # Server Actions (one file per domain)
```

### Rules about this structure

- Pages coordinate layout and loading states. Business logic lives in `features/` or `server/actions/`.
- `src/db/queries/` contains one file per domain (e.g., `organizations.ts`, `billing.ts`). Pages and actions import from queries, not from `src/db/schema.ts` directly.
- Never import across feature boundaries at depth. `features/billing/` should not import from `features/organizations/` internals—use a well-defined function from `features/organizations/index.ts`.
- `lib/env.ts` is the single place that reads `process.env`. Everywhere else uses `import { env } from '~/lib/env'`.

## Naming Conventions

| Target | Convention | Example |
|--------|-----------|---------|
| Files and folders | kebab-case | `invite-member-form.tsx` |
| React components | PascalCase export | `InviteMemberForm` |
| Server Actions files | `*.action.ts` | `organizations.action.ts` |
| Query modules | `*.queries.ts` | `organizations.queries.ts` |
| Zod schemas | `*.schema.ts` | `invite-member.schema.ts` |
| DB table names | snake_case plural | `organization_members` |
| DB column names | snake_case | `created_at`, `org_id` |
| TypeScript domain types | PascalCase | `Organization`, `Member` |
| Env vars | SCREAMING_SNAKE | `DATABASE_URL`, `STRIPE_SECRET_KEY` |

Name things after business meaning, not implementation. `organizationMembers` not `userOrgJoinRows`. `InviteMemberForm` not `ModalForm2`.

## Server vs Client Components

Start every component as a Server Component. Add `"use client"` only when the component needs one of:
- `useState`, `useEffect`, `useRef`, `useReducer`
- Browser-only APIs (`window`, `localStorage`, `navigator`)
- Event handlers on interactive elements (click, submit, change)
- Third-party libs that require browser context

**Data fetching always happens in Server Components or server-side query functions.** Client Components receive already-shaped props and call Server Actions for mutations.

```tsx
// ✅ correct: data in server component, interactivity in client
async function MembersPage() {
  const members = await getOrgMembers(orgId);
  return <MembersTable members={members} />;  // MembersTable is "use client"
}

// ❌ wrong: fetching in a client component with useEffect
"use client";
function MembersPage() {
  const [members, setMembers] = useState([]);
  useEffect(() => { fetch('/api/members').then(...) }, []);
}
```

## Database Rules

### Schema

Every table must have:

```sql
id          TEXT PRIMARY KEY,           -- cuid2 from @paralleldrive/cuid2, not UUID, not autoincrement
created_at  INTEGER NOT NULL,           -- Unix ms timestamp (Date.now())
updated_at  INTEGER NOT NULL,
```

Money: store as integer cents. `amount_cents INTEGER NOT NULL`. Never `REAL` for money.

Timestamps: store as `INTEGER NOT NULL` (Unix milliseconds). Never ISO strings in DB columns.

Foreign keys: always declare them. Enable `PRAGMA foreign_keys = ON` in the DB client.

Indexes: add an index for every foreign key column and every column used in a WHERE clause beyond the primary key.

### Migrations

Migrations are append-only once shared with another developer. Never edit an existing migration file—create a new one.

```bash
# After editing src/db/schema.ts:
pnpm db:generate    # creates a new migration file
pnpm db:migrate     # applies it
```

Name migration files describe the change: `0003_add_org_members_index.sql`, not `0003_migration.sql`.

### Queries

All DB access goes through `src/db/queries/*.ts`. Pages and Server Actions call query functions—they never construct SQL inline.

```ts
// ✅ src/db/queries/organizations.ts
export async function getOrgById(orgId: string): Promise<Organization | null> {
  return db.select().from(organizations).where(eq(organizations.id, orgId)).get();
}

// ❌ wrong: inline query in a page
const org = await db.select().from(organizations).where(eq(organizations.id, orgId)).get();
```

Use transactions for any operation that touches more than one table:

```ts
await db.transaction(async (tx) => {
  const org = await createOrg(tx, input);
  await createAuditEvent(tx, { action: 'org.created', orgId: org.id });
});
```

## Server Actions

Server Actions are the mutation boundary. Use them for all form submissions and app-level writes. Route Handlers (`app/api/`) are only for external webhooks (Stripe, OAuth callbacks).

Every Server Action must:

1. Validate input with Zod before touching the DB
2. Check authentication (`const session = await auth.getSession()`)
3. Check authorization (does this user own this resource?)
4. Call query functions, not raw DB
5. Return a typed `{ success: true, data } | { success: false, error: string }` result
6. Call `revalidatePath` or `revalidateTag` with the smallest useful scope

```ts
// src/server/actions/organizations.action.ts
'use server';

export async function inviteMember(input: unknown) {
  const parsed = inviteMemberSchema.safeParse(input);
  if (!parsed.success) return { success: false, error: 'Invalid input' };

  const session = await auth.getSession();
  if (!session) return { success: false, error: 'Not authenticated' };

  const member = await getOrgMember(session.orgId, session.userId);
  if (member?.role !== 'admin') return { success: false, error: 'Forbidden' };

  await createInvite(parsed.data);
  revalidatePath('/app/settings/members');
  return { success: true };
}
```

**Never trust client-submitted org IDs, role values, or price IDs.** Always re-read those from the DB after authentication.

## Auth and Multi-Tenancy

Every authenticated request has two IDs: `userId` and `orgId`. Both must be present for any app-level action.

Tenant scoping: **every** database query in the `(app)/` route group must include `WHERE org_id = ?`. If you can write a query that returns data from a different org without adding a filter, that's a bug.

```ts
// ✅ tenant-scoped
export async function listProjects(orgId: string) {
  return db.select().from(projects).where(eq(projects.orgId, orgId)).all();
}

// ❌ missing tenant scope
export async function listProjects() {
  return db.select().from(projects).all();
}
```

Middleware at `src/middleware.ts` redirects unauthenticated users. It is **not** the authorization layer—server-side queries must enforce tenant scope even if middleware is bypassed.

## Component Patterns

Build small feature components. A page should read like a product flow, not an implementation:

```tsx
// ✅ readable page
export default async function ProjectsPage() {
  const projects = await listProjects(orgId);
  return (
    <PageShell title="Projects">
      <ProjectToolbar />
      <ProjectTable projects={projects} />
    </PageShell>
  );
}
```

Forms use Server Actions directly via `action=` prop or `useActionState` for optimistic UI.

Loading states use `<Suspense>` around slow data panels, not full-page skeletons.

Error boundaries wrap each major panel so one failing section doesn't kill the page.

## Environment Variables

All env vars are declared and validated in `src/lib/env.ts`:

```ts
import { z } from 'zod';

const envSchema = z.object({
  DATABASE_URL: z.string().url(),
  BETTER_AUTH_SECRET: z.string().min(32),
  STRIPE_SECRET_KEY: z.string().startsWith('sk_'),
  NEXT_PUBLIC_APP_URL: z.string().url(),
});

export const env = envSchema.parse(process.env);
```

Everywhere else: `import { env } from '~/lib/env'`. Never `process.env.FOO` outside this file. `NEXT_PUBLIC_` prefix only for values that must be available in the browser.

## What We Don't Do (and Why)

| What | Why not |
|------|---------|
| `any` in TypeScript | Disables the type system at that call site. Use `unknown` and narrow it. |
| Prisma | Generated client obscures SQL; migrations require network; schema changes are verbose. Drizzle is explicit. |
| `useEffect` for data fetching | Creates loading flickers and race conditions. Fetch in Server Components or use SWR/React Query only when client-side revalidation is genuinely needed. |
| Raw `process.env` outside `lib/env.ts` | Typos in env var names fail silently at runtime. Zod catches them at startup. |
| Inline SQL in pages or components | Untestable, unrefactorable. All SQL goes through `src/db/queries/`. |
| Floating-point money | `0.1 + 0.2 !== 0.3`. Always integer cents. |
| Auto-increment IDs | Leaks row counts to users. Enumerable. Use cuid2. |
| Global state managers (Redux, Zustand, Jotai) | We don't need them—RSC + Server Actions handle most state. Add one only when you have a specific cross-tree client state problem that can't be solved with URL params or RSC. |
| `export default` for anything except Next.js page/layout files | Named exports are refactorable with TypeScript tooling. Default exports are not. |
| Test mocks for the database | Mocks lie. Use a real in-memory SQLite instance in tests (`':memory:'`). |
| Direct Stripe API calls outside `features/billing/` | Stripe logic must be centralized so webhook handlers and Server Actions share the same domain model. |
| `console.log` in committed code | Use structured logging (`pino` or similar). `console.log` gets lost in production. |

## Checklist Before Opening a PR

- [ ] `pnpm typecheck` passes with zero errors
- [ ] `pnpm lint` passes
- [ ] `pnpm test` passes
- [ ] New DB columns have migrations; no migration edits to existing files
- [ ] All new queries are tenant-scoped where applicable
- [ ] Server Actions validate input with Zod and check auth before any DB write
- [ ] No new `any`, no new `process.env` outside `lib/env.ts`
