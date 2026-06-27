# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack

- **Framework**: Next.js 15 App Router (TypeScript, `"use client"` / `"use server"` split)
- **Database**: SQLite via `better-sqlite3` + **Drizzle ORM** for migrations and queries
- **Auth**: `next-auth` v5 (or `lucia-auth`) — email/password + GitHub OAuth
- **Styling**: Tailwind CSS v4
- **Testing**: Vitest (unit), Playwright (E2E)
- **Package manager**: pnpm (v9+)

## Commands

```bash
# Development
pnpm dev                     # start dev server (localhost:3000)
pnpm build && pnpm start     # production build + serve
pnpm lint                    # ESLint
pnpm typecheck               # tsc --noEmit
pnpm test                    # Vitest unit tests
pnpm test:e2e                # Playwright E2E (requires dev server)

# Database
pnpm db:migrate              # apply pending migrations
pnpm db:studio               # Drizzle Studio (browser DB explorer)
pnpm db:generate             # generate migration from schema changes
pnpm db:seed                 # seed development data
```

## Project structure

```
├── app/                     # Next.js App Router
│   ├── (auth)/              # Route group: login, register, forgot-password
│   ├── (dashboard)/         # Route group: authenticated pages
│   │   ├── layout.tsx       # Auth guard + sidebar shell
│   │   └── settings/
│   ├── api/                 # API Routes (Next.js Route Handlers)
│   │   └── webhooks/
│   └── layout.tsx           # Root layout (Providers, fonts)
├── components/
│   ├── ui/                  # Unstyled primitives (button, input, dialog)
│   └── [feature]/           # Feature-scoped components
├── lib/
│   ├── db/
│   │   ├── schema.ts        # Drizzle table definitions
│   │   ├── index.ts         # db singleton (better-sqlite3)
│   │   └── migrations/      # SQL migration files
│   ├── auth/
│   │   └── config.ts        # next-auth config
│   └── utils.ts             # shared pure utilities
├── server/
│   └── actions/             # Server Actions (validated with zod)
├── types/
│   └── index.ts             # Shared TypeScript types
├── drizzle.config.ts        # Drizzle config (SQLite path, migrations dir)
└── vitest.config.ts
```

## Conventions

### File naming
- Page/layout files: `page.tsx`, `layout.tsx` (Next.js convention)
- Components: `PascalCase.tsx` (e.g., `UserMenu.tsx`)
- Server actions: `kebab-case.ts` in `server/actions/` (e.g., `create-post.ts`)
- Utilities: `camelCase.ts` in `lib/`

### Database
- Define all tables in `lib/db/schema.ts` as Drizzle table objects
- Run `pnpm db:generate` after schema changes, commit the migration file
- NEVER edit generated migration files — create a new one instead
- Use `lib/db/index.ts` as the single DB connection singleton

```typescript
// lib/db/index.ts
import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";
import * as schema from "./schema";

const sqlite = new Database(process.env.DATABASE_URL ?? "data/app.db");
sqlite.pragma("journal_mode = WAL");
sqlite.pragma("foreign_keys = ON");

export const db = drizzle(sqlite, { schema });
```

### Server Actions
- All form mutations go through Server Actions in `server/actions/`
- Validate inputs with **Zod** before touching the database
- Return `{ success, error, data? }` shaped objects — never throw to the client

```typescript
// server/actions/create-post.ts
"use server";
import { z } from "zod";
import { db } from "@/lib/db";
import { posts } from "@/lib/db/schema";

const schema = z.object({ title: z.string().min(1), body: z.string() });

export async function createPost(raw: unknown) {
  const result = schema.safeParse(raw);
  if (!result.success) return { success: false, error: "Invalid input" };
  const post = db.insert(posts).values(result.data).returning().get();
  return { success: true, data: post };
}
```

### Authentication
- Protect pages via `auth()` in server components or `middleware.ts`
- Never trust `session.user.id` from the client — re-verify in server actions
- Use `next-auth` callbacks to persist additional user fields to the DB on sign-in

### Components
- Prefer **Server Components** by default; add `"use client"` only when needed
- Interactive UI that needs hooks or browser APIs → `"use client"`
- Data fetching → Server Component, pass data as props to client children
- Extract client-only slices into leaf components to keep server/client boundary tight

### Styling
- Use Tailwind utility classes; avoid custom CSS unless unavoidable
- Theme variables in `tailwind.config.ts` (brand colors, spacing scale)
- `cn()` helper from `lib/utils.ts` for conditional class merging

## Testing

### Unit tests (Vitest)
- Test Server Actions and `lib/` utilities in isolation
- Use an in-memory SQLite DB for action tests:

```typescript
// tests/setup.ts
import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";
import { migrate } from "drizzle-orm/better-sqlite3/migrator";
import * as schema from "@/lib/db/schema";

export function makeTestDb() {
  const sqlite = new Database(":memory:");
  const db = drizzle(sqlite, { schema });
  migrate(db, { migrationsFolder: "./lib/db/migrations" });
  return db;
}
```

### E2E tests (Playwright)
- Test critical user flows: sign up, create entity, update settings
- Store authenticated state via `storageState` to skip login on each test
- Run against `http://localhost:3000` — start the dev server before `pnpm test:e2e`

## Environment variables

```
DATABASE_URL=data/app.db          # relative path to SQLite file
NEXTAUTH_SECRET=<random-32-chars> # next-auth JWT signing key
NEXTAUTH_URL=http://localhost:3000
GITHUB_ID=                        # OAuth app Client ID
GITHUB_SECRET=                    # OAuth app Client Secret
```

Never commit `.env` — use `.env.example` with placeholder values.

## Deployment checklist

- [ ] Set `DATABASE_URL` to a persistent volume path (not `/tmp`)
- [ ] Set `NEXTAUTH_SECRET` to a cryptographically random value
- [ ] Enable WAL mode and foreign key checks (already in db singleton)
- [ ] Run `pnpm db:migrate` as part of the deploy script (before server start)
- [ ] Set `NODE_ENV=production` — Next.js disables dev overlay and enables caching
- [ ] Configure `NEXTAUTH_URL` to your production domain

## Common pitfalls

- **SQLite and concurrent writes**: better-sqlite3 is synchronous; avoid long-running transactions. WAL mode handles concurrent reads fine.
- **Server Action caching**: Server Actions are never cached. Data fetching in Server Components respects Next.js cache; use `revalidatePath()` or `revalidateTag()` after mutations.
- **`"use client"` in layouts**: Adding `"use client"` to a layout or page disables server-side data fetching for ALL children. Prefer adding it to leaf components only.
- **Migration state drift**: Drizzle tracks applied migrations in `__drizzle_migrations` table. If you manually edit the DB, re-run `pnpm db:migrate` to resync.
