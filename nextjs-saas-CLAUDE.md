# CLAUDE.md — Next.js 15 App Router + SQLite SaaS Stack

> Opinionated guide. Every rule has a reason.  
> Target: greenfield SaaS projects with Next.js 15, TypeScript, SQLite (Turso or better-sqlite3).

## Project Structure

```
src/
├── app/                  # Next.js App Router (file-based routing)
│   ├── (auth)/           # Route group: authenticated pages
│   │   ├── dashboard/
│   │   │   └── page.tsx
│   │   └── layout.tsx    # Auth layout (checks session)
│   ├── (public)/         # Route group: public pages
│   │   ├── page.tsx      # Landing page → /
│   │   ├── login/
│   │   └── signup/
│   ├── api/              # API routes (trpc or route handlers)
│   │   └── v1/
│   └── layout.tsx        # Root layout (fonts, metadata, providers)
├── components/
│   ├── ui/               # Generic UI primitives (Button, Input, Modal)
│   └── features/         # Feature-specific composed components
├── lib/
│   ├── db/               # Database layer
│   │   ├── schema.ts     # Drizzle ORM schema definitions
│   │   ├── migrations/   # Auto-generated SQL migrations
│   │   └── client.ts     # DB connection singleton
│   ├── auth/             # Auth logic (sessions, middleware)
│   ├── email/            # Transactional email templates
│   └── utils.ts          # Pure utility functions
├── hooks/                # Shared React hooks
├── server/               # Server-only code (never imported client-side)
│   ├── actions.ts        # Server Actions (form mutations)
│   └── queries.ts        # Server-side data queries
├── types/                # Shared TypeScript types
└── middleware.ts          # Next.js edge middleware (auth, redirects)
```

**Why**: Route groups `(auth)` and `(public)` separate concerns without affecting URLs. Server-only code lives in `server/` to prevent accidental client bundling. Feature components live next to each other, not spread across abstract folders.

## Naming Conventions

### Files
- **Pages & routes**: `kebab-case` — `user-settings/page.tsx`  
  *Why*: Next.js convention. URLs map to file paths. `userSettings` in a URL is ugly.
- **Components**: `PascalCase` — `UserAvatar.tsx`, `SignupForm.tsx`  
  *Why*: React convention. The component is `UserAvatar`, so the file is `UserAvatar.tsx`.
- **Utilities & libraries**: `camelCase` — `formatCurrency.ts`, `validateEmail.ts`  
  *Why*: These export functions, not components. File name = function name.
- **Types**: `camelCase` with `types` suffix — `userTypes.ts`, `apiTypes.ts`  
  *Why*: Avoids collision with component names. `types/user.ts` is ambiguous about what belongs.

### Database
- **Tables**: `snake_case` plural — `users`, `user_sessions`, `billing_events`  
  *Why*: SQL convention. Drizzle maps to camelCase objects automatically.
- **Columns**: `snake_case` — `created_at`, `updated_at`, `stripe_customer_id`  
  *Why*: SQL convention. Every table has `created_at` and `updated_at`. Period.
- **Foreign keys**: `<singular_table>_id` — `user_id`, `team_id`  
  *Why*: Predictable. No guessing whether it's `ownerId` or `user_id`.

### Variables & Functions
- **Server actions**: `verbNoun` — `createTeam`, `updateProfile`, `deleteAccount`  
  *Why*: Actions mutate state. The verb tells you what happens. No `handleSubmit`.
- **Database queries**: `getNoun` / `listNouns` — `getUser`, `listTeamsByOrg`  
  *Why*: `get` returns one or null. `list` returns an array. No `fetch` prefix.
- **React hooks**: `useNoun` — `useSession`, `useTeamMembers`  
  *Why*: React convention. The `use` prefix is the signal.

## Database Rules

### Migrations (Drizzle + Turso)
```bash
# 1. Edit schema in lib/db/schema.ts
# 2. Generate migration
pnpm db:generate          # drizzle-kit generate
# 3. Review the generated SQL in lib/db/migrations/
# 4. Apply
pnpm db:migrate           # drizzle-kit migrate
```

### Rules (non-negotiable)
1. **Never edit a migration after it's applied.**  
   *Why*: Applied migrations are immutable history. Create a new migration instead.
2. **Every table gets `created_at` and `updated_at`.**  
   *Why*: Debugging without timestamps is guessing. Two extra columns cost nothing.
3. **Foreign keys have indexes.**  
   *Why*: Unindexed FKs cause sequential scans on joins. N+1 queries kill SaaS at scale.
4. **Use Drizzle's relational queries, never raw SQL unless necessary.**  
   *Why*: Type safety catches schema mismatches at compile time. Raw SQL skips the guardrails.
5. **Soft-delete for user data. Hard-delete for everything else.**  
   *Why*: Users expect undo. System data is garbage. Don't mix the two.

## Dev Commands

```bash
pnpm dev              # Next.js dev server (localhost:3000)
pnpm build            # Production build
pnpm start            # Start production server
pnpm lint             # ESLint (flat config)
pnpm format           # Prettier check
pnpm format:fix       # Prettier write
pnpm typecheck        # tsc --noEmit
pnpm db:generate      # Generate Drizzle migration
pnpm db:migrate       # Apply Drizzle migration
pnpm db:studio        # Drizzle Studio (localhost:4983)
pnpm test             # vitest
pnpm test:e2e         # Playwright
```

**Command philosophy**: `lint` checks, `lint:fix` fixes. `format` checks, `format:fix` fixes. `test` runs unit, `test:e2e` runs browser. No ambiguity. No one-off script names like `validate` or `check-types`.

## Patterns to Follow

### 1. Server Components by Default
```tsx
// ✅ DO: Server Component (no 'use client')
import { listTeams } from '@/server/queries';

export default async function TeamsPage() {
  const teams = await listTeams();
  return <TeamList teams={teams} />;
}
```
*Why*: Server Components are free (no client JS). Only add `'use client'` when you need interactivity.

### 2. Server Actions for Mutations
```tsx
// ✅ DO: Server Action for form submission
// server/actions.ts
'use server';
export async function createTeam(data: CreateTeamInput) {
  const session = await getSession();
  if (!session) throw new Error('Unauthorized');
  return db.insert(teams).values({ ...data, ownerId: session.userId });
}
```
*Why*: No API route boilerplate. Progressive enhancement works by default. Errors surface automatically.

### 3. Data Access Layer
```tsx
// ✅ DO: Centralized queries
// server/queries.ts
export async function getUser(userId: string) {
  return db.query.users.findFirst({
    where: eq(users.id, userId),
    with: { teams: true },
  });
}
```
*Why*: One place to add caching, logging, or auth checks. Components don't know about the database.

### 4. Structured Error Handling
```tsx
// ✅ DO: Typed result objects
type ActionResult<T> = 
  | { success: true; data: T }
  | { success: false; error: string };

export async function safeDeleteTeam(teamId: string): Promise<ActionResult<void>> {
  try {
    await db.delete(teams).where(eq(teams.id, teamId));
    return { success: true, data: undefined };
  } catch (e) {
    return { success: false, error: e instanceof Error ? e.message : 'Unknown error' };
  }
}
```
*Why*: No uncaught exceptions in the UI. Every caller handles both paths explicitly.

## Anti-Patterns to Avoid

### ❌ `use client` on layout components
```tsx
// ❌ DON'T: Entire layout is client-side
'use client';
export default function DashboardLayout({ children }) { ... }

// ✅ DO: Extract interactive parts into leaf components
export default function DashboardLayout({ children }) {
  return (
    <div>
      <Sidebar />        {/* Server-rendered */}
      <ClientSearch />   {/* Only this is 'use client' */}
      {children}
    </div>
  );
}
```
*Why*: `use client` is a boundary marker. The closer to the leaf, the more code stays on the server.

### ❌ API routes when Server Actions would work
```tsx
// ❌ DON'T: Creating a route handler for a mutation
export async function POST(req: Request) {
  const body = await req.json();
  await db.insert(teams).values(body);
  return Response.json({ ok: true });
}

// ✅ DO: Use a Server Action instead (see Pattern #2)
```
*Why*: Server Actions are simpler, type-safe, and don't need manual fetch boilerplate.

### ❌ Raw SQL in components
```tsx
// ❌ DON'T
const users = await db.all('SELECT * FROM users WHERE team_id = ?', teamId);

// ✅ DO: Use Drizzle queries
const users = await db.query.users.findMany({
  where: eq(users.teamId, teamId),
});
```
*Why*: TypeScript can't check raw SQL. Drizzle's query API gives you autocomplete and compile-time validation.

### ❌ `any` in function signatures
```tsx
// ❌ DON'T
export async function updateUser(userId: string, data: any) { ... }

// ✅ DO
export async function updateUser(userId: string, data: UpdateUserInput) { ... }
```
*Why*: `any` disables type checking. Every `any` is a future runtime error you chose to postpone.

### ❌ Mixing concerns in pages
```tsx
// ❌ DON'T: Page does everything
export default async function TeamPage({ params }) {
  const team = await db.query.teams.findFirst(...);
  const members = await db.query.users.findMany(...);
  const billing = await stripe.subscriptions.retrieve(...);
  return <div>...</div>;
}

// ✅ DO: Page composes server queries, delegates to components
export default async function TeamPage({ params }) {
  return (
    <TeamDetail
      team={await getTeam(params.id)}
      members={await listTeamMembers(params.id)}
    />
  );
}
```
*Why*: Pages should assemble, not compute. Queries go in `server/queries.ts`. Components receive data as props.

## Environment & Configuration

```
.env.local          # Local development (git-ignored)
.env.example        # Template with dummy values (committed)
```

**Required env vars** (documented in `.env.example`):
```
DATABASE_URL=        # Turso or SQLite connection string
AUTH_SECRET=         # NextAuth.js/Auth.js secret (openssl rand -base64 32)
STRIPE_SECRET_KEY=   # Stripe API key
RESEND_API_KEY=      # Email (Resend)
NEXT_PUBLIC_APP_URL= # Canonical URL (http://localhost:3000 in dev)
```

*Why*: `.env.example` is the single source of truth for required config. No guessing. No onboarding docs that are out of date.

## Dependencies (locked versions)

| Package | Purpose | Why this one |
|---------|---------|-------------|
| `drizzle-orm` | ORM | Type-safe SQL. Better than Prisma for serverless/SQLite. No code generation step. |
| `@libsql/client` | SQLite driver | Turso-compatible. Better than better-sqlite3 for edge/serverless. |
| `next-auth` / `Auth.js` | Authentication | Battle-tested. Built-in OAuth, magic link, credentials. |
| `stripe` | Payments | Industry standard. No competitors with equivalent tooling. |
| `resend` | Transactional email | Modern API. React email templates. Better DX than SendGrid. |
| `tailwindcss` | Styling | Zero-runtime. Tree-shakes unused CSS. Co-locates styles with markup. |
| `zod` | Validation | Parse, don't validate. Share schemas between server actions and forms. |
| `vitest` | Testing | Vite-native. Faster than Jest. Same transform pipeline as Next.js. |

---

*Generated for [claude-builders-bounty #2](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2) — $75 Bounty*
