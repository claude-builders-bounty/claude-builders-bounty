# CLAUDE.md — Next.js 15 + SQLite SaaS Project

## Stack & Versions

| Layer       | Choice              | Version  |
|-------------|---------------------|----------|
| Framework   | Next.js App Router  | 15.x     |
| Language    | TypeScript          | 5.x      |
| Database    | better-sqlite3      | 11.x     |
| ORM         | Drizzle             | 0.38+    |
| Auth        | next-auth           | 5.x      |
| Styling     | Tailwind CSS        | 4.x      |
| Runtime     | Node.js             | 22 LTS   |

Use `better-sqlite3` for local dev and single-server deploy. If you need
edge/multi-region, switch to `@libsql/client` (Turso) — the Drizzle
schema stays identical; only the driver import changes.

## Folder Structure

```
src/
  app/                  # Next.js App Router pages
    (auth)/             # Route group: login, register
    (dashboard)/        # Route group: authenticated pages
    api/                # API route handlers
  components/           # React components
    ui/                 # Primitive UI (Button, Input, Dialog)
    forms/              # Form components with validation
    layout/             # Shell, Sidebar, Header
  lib/
    db/
      schema.ts         # Drizzle table definitions (single source of truth)
      index.ts          # Drizzle client initialization
      migrations/       # SQL migration files (numbered, never edited)
    auth.ts             # next-auth configuration
    validators.ts       # Zod schemas for all API inputs
    utils.ts            # Pure utility functions
  hooks/                # Custom React hooks
public/                 # Static assets
drizzle.config.ts       # Drizzle Kit config
```

Every file goes in exactly one place. If you're unsure, it goes in
`lib/`. Never create top-level directories outside this structure.

## Database Conventions

### Schema (`src/lib/db/schema.ts`)

All table definitions live in ONE file. This is intentional — SQLite
has a single-writer concurrency model, so a monolithic schema file
makes migrations predictable and reviewable.

```typescript
export const users = sqliteTable('users', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  email: text('email').notNull().unique(),
  name: text('name'),
  createdAt: integer('created_at', { mode: 'timestamp' })
    .notNull()
    .$defaultFn(() => new Date()),
});
```

### Rules

1. **Every column has a NOT NULL constraint** unless the field is
   genuinely optional (e.g., `name` vs `email`). Nullable columns are
   the exception, not the default.

2. **Timestamps are integers** (Unix epoch ms). Use `mode: 'timestamp'`
   in Drizzle for automatic JS Date conversion.

3. **Foreign keys are enforced.** Add `references: () => table.id` to
   every FK column. Never store relations without FK constraints.

4. **No ORM-level joins in hot paths.** Write raw SQL for complex
   queries (dashboards, aggregations). Drizzle's query builder is fine
   for CRUD.

5. **UUIDs only for public-facing IDs** (API params, URLs). Internal
   references use auto-increment integers.

### Migrations

```bash
npx drizzle-kit generate   # Generate migration after schema change
npx drizzle-kit migrate    # Apply pending migrations
```

Migration files are numbered automatically. They are append-only. A
migration that has been run on any environment (including CI) must never
be modified. If a migration is wrong, create a new migration that
reverses or fixes it.

## Component Patterns

### Server Components by Default

Every component is a Server Component unless it explicitly needs
interactivity. The `"use client"` directive is a deliberate choice, not
a default.

```typescript
// GOOD — Server Component, no directive needed
export default async function UserProfile({ userId }: Props) {
  const user = await db.select().from(users).where(eq(users.id, userId));
  return <div>{user.name}</div>;
}

// BAD — unnecessary client component
"use client";
export default function UserProfile({ userId }: Props) {
  const [user, setUser] = useState(null);
  useEffect(() => { fetchUser(userId).then(setUser); }, [userId]);
  return <div>{user?.name}</div>;
}
```

### Forms

All forms use React Hook Form + Zod. The Zod schema IS the validation
and the TypeScript type. Never define a type separately from its
validator.

```typescript
export const createUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
});
export type CreateUserInput = z.infer<typeof createUserSchema>;
```

### Data Fetching

Server Components fetch directly from the database. API routes fetch
from the database. Never fetch from internal API routes — that's a
network round-trip to yourself.

### Error Boundaries

Every route segment that does data fetching gets an `error.tsx`. No
exceptions.

## API Routes

Every API route validates input with Zod before touching the database.

```typescript
export async function POST(request: Request) {
  const body = createUserSchema.parse(await request.json());
  const [user] = await db.insert(users).values(body).returning();
  return Response.json(user, { status: 201 });
}
```

Error responses: `{ error: string; detail?: string }`

Status codes: 200 (OK), 201 (Created), 400 (Validation), 401
(Unauthorized), 403 (Forbidden), 404 (Not Found), 409 (Conflict),
500 (Server Error). Never invent custom status codes.

## Dev Commands

```bash
npm run dev           # Start dev server with hot reload
npm run build         # Type-check + build for production
npm run lint          # ESLint + Prettier check
npm run db:generate   # Generate migration from schema changes
npm run db:migrate    # Apply pending migrations
npm run db:studio     # Open Drizzle Studio (DB browser)
npm run test          # Run tests with Vitest
npm run test:e2e      # Run Playwright end-to-end tests
```

## What We Don't Do (and Why)

1. **No Prisma.** Drizzle is closer to SQL, has zero runtime overhead
   on SQLite, and generates smaller bundles.

2. **No tRPC or GraphQL.** For an SQLite-backed SaaS, REST API routes
   with Zod validation are simpler, debuggable, and sufficient.

3. **No global state management (Redux, Zustand).** Server Components
   + URL state + `useActionState` cover 95% of state needs.

4. **No CSS-in-JS.** Tailwind handles styling. One system, zero
   runtime cost.

5. **No barrel files (`index.ts` re-exports).** Import directly from
   the source file. Barrel files break tree-shaking.

6. **No `any` types.** If the type is unknown, use `unknown` and narrow
   it. `any` is a lint error.

7. **No environment-dependent branching in components.** Use
   `NEXT_PUBLIC_` env vars at build time. Never read `process.env`
   inside a Client Component at runtime.

## Anti-Patterns to Avoid

- **Waterfall fetches.** Use `Promise.all` for parallel data fetching.
- **Client-side auth checks.** Auth happens in middleware or Server
  Components. The client never decides if a user is logged in.
- **Prop drilling >2 levels.** Use Server Component data fetching at
  the leaf instead.
- **`useEffect` for data fetching.** Fetch on the server, pass as
  props. `useEffect` is for browser-only side effects.
- **Optimistic updates without error handling.** You MUST handle
  rollback when the server rejects.

## Naming Conventions

| What              | Convention            | Example                 |
|-------------------|-----------------------|-------------------------|
| Files/dirs        | kebab-case            | `user-profile.tsx`      |
| Components        | PascalCase            | `UserProfile`           |
| Hooks             | camelCase, `use` prefix | `useAuth`             |
| DB tables         | plural, snake_case    | `users`, `order_items`  |
| DB columns        | snake_case            | `created_at`            |
| API routes        | plural nouns          | `/api/users`            |
| Env vars          | UPPER_SNAKE_CASE     | `DATABASE_PATH`         |
| Types/interfaces  | PascalCase            | `CreateUserInput`       |
| Constants         | UPPER_SNAKE_CASE     | `MAX_RETRY_COUNT`       |
| Utility functions | camelCase             | `formatCurrency`        |

## Testing

- Unit tests: Vitest + `@testing-library/react`
- E2E tests: Playwright
- Database tests: Use in-memory SQLite (`:memory:`)
- Every API route gets at least one integration test
- Every Zod validator gets a positive and negative test

```typescript
import { describe, it, expect } from 'vitest';

describe('createUserSchema', () => {
  it('accepts valid input', () => {
    expect(createUserSchema.parse({ email: 'a@b.c', name: 'Test' }))
      .toBeDefined();
  });

  it('rejects invalid email', () => {
    expect(() => createUserSchema.parse({ email: 'not-email', name: 'Test' }))
      .toThrow();
  });
});
```

## Deployment

Single-server deployment. SQLite file at `./data/app.db`. Back it up
with `sqlite3 app.db ".backup backup.db"` on a cron. Do not put SQLite
on NFS or network storage.
