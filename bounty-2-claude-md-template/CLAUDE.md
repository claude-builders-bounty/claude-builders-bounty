# CLAUDE.md — Next.js 15 + SQLite SaaS

## Project Stack

- **Framework**: Next.js 15 (App Router only — no Pages Router)
- **Language**: TypeScript (strict mode)
- **Database**: SQLite via better-sqlite3 (single file, zero config)
- **ORM**: Drizzle ORM (type-safe, SQL-first)
- **Auth**: Auth.js v5 (NextAuth)
- **Styling**: Tailwind CSS v4
- **Package Manager**: pnpm

## Project Structure

```
src/
├── app/                    # App Router pages and layouts
│   ├── (auth)/             # Auth-related routes (login, register)
│   ├── (dashboard)/        # Protected routes
│   ├── api/                # API routes (Route Handlers only)
│   ├── layout.tsx          # Root layout
│   └── page.tsx            # Landing page
├── components/
│   ├── ui/                 # Reusable primitives (Button, Input, Card)
│   └── [feature]/          # Feature-specific components
├── db/
│   ├── schema.ts           # Drizzle schema (single source of truth)
│   ├── migrations/         # SQL migration files (never edit by hand)
│   ├── index.ts            # Database connection singleton
│   └── seed.ts             # Seed data for development
├── lib/
│   ├── actions/            # Server Actions (one file per domain)
│   └── utils.ts            # Shared helpers (keep small)
└── types/                  # Shared TypeScript types
```

## Commands

```bash
pnpm dev                    # Start dev server (localhost:3000)
pnpm build                  # Production build
pnpm db:generate            # Generate migration from schema changes
pnpm db:migrate             # Run pending migrations
pnpm db:studio              # Open Drizzle Studio (database browser)
pnpm db:seed                # Seed development data
pnpm lint                   # ESLint check
pnpm typecheck              # TypeScript check (tsc --noEmit)
```

## Naming Conventions

| Thing | Convention | Example |
|-------|-----------|---------|
| Files (components) | kebab-case | `user-avatar.tsx` |
| Files (utilities) | kebab-case | `format-date.ts` |
| Components | PascalCase | `UserAvatar` |
| Functions | camelCase | `formatDate` |
| Database tables | snake_case | `user_sessions` |
| Database columns | snake_case | `created_at` |
| API routes | kebab-case folders | `api/billing-webhook/route.ts` |
| Server Actions | camelCase, verb-first | `createProject`, `deleteUser` |
| Environment vars | SCREAMING_SNAKE | `DATABASE_URL` |
| CSS classes | Tailwind only | No custom CSS files |

## Database Rules

**Schema is the source of truth.** Never write raw SQL for schema changes.

1. Edit `src/db/schema.ts` first
2. Run `pnpm db:generate` — this creates a migration file
3. Run `pnpm db:migrate` — this applies it
4. Never edit migration files by hand
5. Never use `db.run()` with raw DDL statements

**SQLite-specific constraints:**
- No `ALTER COLUMN` — SQLite doesn't support it. To change a column, create a new table, copy data, drop old table (Drizzle handles this)
- No concurrent writes in production — use WAL mode (`PRAGMA journal_mode=WAL`) in `db/index.ts`
- No `ENUM` type — use `text` with TypeScript union types
- Boolean = integer (0/1) — Drizzle maps this automatically
- Dates = text (ISO 8601) or integer (unix timestamp) — pick one per project and stick with it

**Query patterns:**
```typescript
// Always use Drizzle query builder, never raw SQL
const user = await db.query.users.findFirst({
  where: eq(users.id, userId),
  with: { projects: true },
});

// Transactions for multi-step writes
await db.transaction(async (tx) => {
  await tx.insert(orders).values(order);
  await tx.update(inventory).set({ stock: sql`stock - 1` }).where(eq(inventory.id, itemId));
});
```

## Server Actions

**One file per domain:** `lib/actions/projects.ts`, `lib/actions/billing.ts`

```typescript
// Always: "use server" at top, validate input, return typed result
"use server";

import { z } from "zod";
import { actionClient } from "@/lib/safe-action";

const createProjectSchema = z.object({
  name: z.string().min(1).max(100),
});

export const createProject = actionClient
  .schema(createProjectSchema)
  .action(async ({ parsedInput: { name } }) => {
    const project = await db.insert(projects).values({ name }).returning();
    revalidatePath("/dashboard");
    return { project };
  });
```

**Rules:**
- Always validate input with Zod — never trust client data
- Always `revalidatePath()` or `revalidateTag()` after mutations
- Never import server actions in other server actions — extract shared logic to `lib/`
- Never use `try/catch` in actions — let `next-safe-action` handle errors

## API Routes

Use API routes only for:
- Webhooks (Stripe, auth callbacks)
- Third-party integrations
- File uploads

Everything else = Server Actions.

```typescript
// api/webhook/stripe/route.ts
export async function POST(req: Request) {
  const body = await req.text(); // raw body for signature verification
  const sig = req.headers.get("stripe-signature")!;
  // verify, process, return
  return Response.json({ received: true });
}
```

## Component Patterns

**Server Components by default.** Only add `"use client"` when you need:
- `useState`, `useEffect`, `useRef`
- Event handlers (`onClick`, `onChange`)
- Browser APIs (`window`, `localStorage`)

```typescript
// Server Component (default) — can directly query DB
export default async function ProjectList() {
  const projects = await db.query.projects.findMany();
  return <ul>{projects.map(p => <li key={p.id}>{p.name}</li>)}</ul>;
}

// Client Component — only when interactivity is needed
"use client";
export function DeleteButton({ id }: { id: string }) {
  return <button onClick={() => deleteProject({ id })}>Delete</button>;
}
```

**Anti-patterns to avoid:**
- `"use client"` on page-level components (kills SSR)
- Fetching data in client components when a server component works
- Using `useEffect` for data fetching (use server components or server actions)
- Prop drilling — use server components to fetch data close to where it's used

## Auth Patterns

```typescript
// Protecting server components
import { auth } from "@/lib/auth";
import { redirect } from "next/navigation";

export default async function DashboardPage() {
  const session = await auth();
  if (!session) redirect("/login");
  // ...
}

// Protecting server actions
export const createProject = actionClient
  .use(async ({ next }) => {
    const session = await auth();
    if (!session) throw new Error("Unauthorized");
    return next({ ctx: { userId: session.user.id } });
  })
  .schema(createProjectSchema)
  .action(async ({ parsedInput, ctx }) => {
    // ctx.userId is available and typed
  });
```

## Error Handling

- **Server Actions**: Let `next-safe-action` handle errors. Define error messages in the schema, not in catch blocks.
- **API Routes**: Return proper HTTP status codes. 400 for bad input, 401 for unauth, 500 for unexpected.
- **Components**: Use `error.tsx` boundaries per route segment. Never use generic try/catch in components.
- **Database**: Drizzle throws on constraint violations — catch at the action level only if you need a custom user message.

## Environment Variables

```
# .env.local (never commit)
DATABASE_URL=file:./data/app.db
AUTH_SECRET=<random-32-chars>
AUTH_GITHUB_ID=
AUTH_GITHUB_SECRET=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
```

Rule: Access env vars only in `lib/` or `db/` files. Never import `process.env` directly in components.

## Anti-Patterns (Do Not)

| Do Not | Do Instead |
|--------|-----------|
| Create `/utils/helpers.ts` junk drawers | One focused file per concern |
| Use Prisma | Use Drizzle (SQL-first, better SQLite support) |
| Use Pages Router (`/pages`) | Use App Router (`/app`) exclusively |
| Add an API route for form submissions | Use Server Actions |
| Install `axios` | Use native `fetch` |
| Add Redux/Zustand for server state | Use server components + server actions |
| Create `types/index.ts` barrel file | Co-locate types with their domain |
| Use `any` | Use `unknown` and narrow with type guards |
| Manual SQL migrations | Always use `pnpm db:generate` |
| Store files in SQLite BLOBs | Store on filesystem, reference path in DB |
