# CLAUDE.md — Next.js 15 + SQLite SaaS

This file is the operating manual for this SaaS project.
Every rule exists because we learned the hard way.

## Stack (why)

| Layer | Choice | Why not the alternative |
|-------|--------|------------------------|
| Framework | **Next.js 15 App Router** | Pages Router is legacy. Remix requires more routing boilerplate. |
| Language | **TypeScript strict** | `any` hides bugs until production. `strict: true` catches them in CI. |
| Database | **SQLite (Turso/libSQL or better-sqlite3)** | Postgres is overkill for single-region SaaS. SQLite is faster for colocated reads. |
| ORM | **Drizzle** | Prisma generates JS at build time (slow CI). Drizzle is SQL-first and type-safe at zero cost. |
| Auth | **Better Auth** | NextAuth v5 still experimental. Clerk is expensive. Better Auth is open-source and type-safe. |
| UI | **shadcn/ui + Tailwind v4** | MUI is heavy for SaaS. Radix primitives with Tailwind give us 90% of MUI at 10% of the bundle. |
| Validation | **Zod** | Yup is slower. Valibot is newer but less ecosystem. Zod is the standard. |
| Payments | **Stripe** | Paddle/Lemon Squeezy for global tax handling if EU customers exist. |
| Email | **Resend** | SendGrid has deliverability issues. AWS SES is painful to set up. Resend just works. |
| Testing | **Vitest + Testing Library** | Jest is slower and needs `jest.config`. Vitest is native ESM and faster. |
| Linting | **Biome** | ESLint + Prettier need 7 config files. Biome does both with one. |

## Directory structure

```
src/
  app/
    (marketing)/        # Public pages: landing, pricing, blog
    (dashboard)/        # Authenticated: requires session check
    api/                # Webhooks, third-party callbacks only
    (auth)/             # Login, register, password reset
    layout.tsx          # Root providers (ThemeProvider, SessionProvider)
    globals.css         # Tailwind directives
  components/
    ui/                 # shadcn components (npx shadcn add)
    forms/              # Form components bound to server actions
  db/
    schema/             # One file per table, singular snake_case
    migrations/         # drizzle-kit generated, never edit manually
    client.ts           # DB connection singleton
  lib/
    auth.ts             # Session helpers
    env.ts              # Validated env vars (never read process.env directly)
    stripe.ts           # Stripe SDK wrapper
    utils.ts            # cn(), formatDate(), etc.
  server/
    actions/            # Server actions by domain (billing, team, project)
    queries/            # Read-only data access
  tests/
    setup.ts            # DB cleanup, mocks
    actions/            # Server action integration tests
```

**Rule:** A file that imports from more than 3 levels deep (`../../../../`) means your structure is wrong.

## Naming

| What | Convention | Example |
|------|-----------|---------|
| Tables | `singular_snake_case` | `user`, `team_membership` |
| Columns | `snake_case` | `created_at`, `stripe_customer_id` |
| Server actions | `verbNounAction` | `createTeamAction`, `inviteMemberAction` |
| Queries | `nounByNoun` | `teamBySlug`, `membersByTeamId` |
| Components | `PascalCase.tsx` | `TeamSwitcher.tsx` |
| Utils | `camelCase.ts` | `formatDate.ts` |
| Zod schemas | `nounSchema` | `createTeamSchema` |

**Why:** Predictable names let Claude Code find the right file without guessing.

## Dev commands

```bash
npm install
npm run dev          # localhost:3000
npm run build        # typecheck + lint + build
npm run test         # vitest (watch)
npm run db:generate  # drizzle-kit generate
npm run db:migrate   # drizzle-kit migrate
npm run db:studio    # drizzle-kit studio (GUI)
```

Every command must exist in `package.json` before you document it.

## Database rules

1. **Every schema change needs a migration.** No raw SQL edits.
2. **Never edit an applied migration.** Create a new one.
3. **Additive migrations only.** Add nullable columns first, backfill, then enforce.
4. **Enable `PRAGMA foreign_keys = ON`** in the DB client.
5. **Timestamps as ISO strings.** Don't mix `Date`, `number`, and `string`.
6. **Use `cuid2` for IDs.** UUIDs are slow in SQLite. Auto-increment leaks info.
7. **Index columns used in `WHERE`, `JOIN`, and `ORDER BY`.** SQLite has no query planner magic.

```ts
// db/schema/users.ts — correct
export const users = sqliteTable("users", {
  id: text("id").primaryKey().$defaultFn(createId),
  email: text("email").notNull().unique(),
  name: text("name"),
  teamId: text("team_id").references(() => teams.id, { onDelete: "set null" }),
  createdAt: text("created_at").notNull().$defaultFn(() => new Date().toISOString()),
})
```

## Component rules

- **Server Component by default.** Add `"use client"` only for: browser APIs, `useState`, `useEffect`, event handlers, context.
- **Client components must be leaves.** Pass serializable props from the server parent. Never query inside a client component.
- **No barrel exports.** `index.ts` re-exports cause circular deps and slow HMR.
- **Compose, don't configure.** Prefer `children` over 15 props.

## Server actions

```ts
"use server"

export async function createTeamAction(formData: FormData) {
  const session = await auth()
  if (!session) throw new AuthError()

  const parsed = createTeamSchema.safeParse(Object.fromEntries(formData))
  if (!parsed.success) return { error: parsed.error.flatten().fieldErrors }

  const team = await db.insert(teams).values(parsed.data).returning()
  revalidatePath("/dashboard")
  return { team }
}
```

Rules:
- Validate input with Zod at the boundary.
- Check auth and authorization before writing.
- Return typed `{ error }` or `{ data }` — never throw for expected failures.
- `revalidatePath` the smallest scope needed.
- Keep actions idempotent. The same form submitted twice should not duplicate.

## Auth & authorization

- **Authentication = "who are you?"** — handled by the auth library.
- **Authorization = "can you do this?"** — checked in every server action and query.
- **Never check only auth for scoped data.** Always verify the user belongs to the team/org.

```ts
// Correct
const membership = await db
  .select()
  .from(teamMemberships)
  .where(and(eq(teamMemberships.userId, session.user.id), eq(teamMemberships.teamId, teamId)))
  .get()

if (!membership) throw new AuthError("Not a member of this team")
```

## Error handling

| Situation | Approach |
|-----------|----------|
| Validation failure | Return `{ error }` from server action |
| Not found | Return `{ error: "not_found" }` or `notFound()` |
| Not authorized | `redirect("/login")` or throw `AuthError` |
| System failure | Throw — caught by `error.tsx` boundary |
| Webhook failure | Log + return 500, let Stripe retry |

- Log server errors with enough context to debug. Never log secrets.
- User-facing errors must say what to do next, not what went wrong internally.

## Testing rules

- **Test server actions and queries.** These are where bugs cost money.
- **Use an in-memory SQLite DB for tests.** Do not mock Drizzle.
- **Mock external APIs (Stripe, Resend) at the service boundary.**
- **Clean the DB between tests.** No shared state.
- **Test auth failure paths.** If a server action doesn't check auth, it's a security bug.
- **No snapshot tests.** They break on every minor change and catch nothing valuable.

## What we don't do

| Don't | Because |
|-------|---------|
| Global state manager (Redux, Zustand) | Server state + URL state + React context cover 99% of cases |
| `useEffect` data fetching | Server Components and Server Actions exist |
| Manual migration edits | They make production rollbacks impossible |
| A second ORM | One ORM, one way to query |
| Business logic in components | Components are for rendering, not deciding |
| `process.env` in components | All env vars go through `lib/env.ts` for validation |
| Background jobs for sync writes | SQLite transactions are fast enough. Add jobs only when they're not. |
| `any` with a TODO to fix it | That TODO will never happen |

## PR checklist

Before opening a PR:

- [ ] `npm run build` passes
- [ ] `npm run test` passes
- [ ] New server actions have tests
- [ ] New DB columns have migrations
- [ ] Auth + authorization checked for every new mutation
- [ ] Screenshots included for UI changes
