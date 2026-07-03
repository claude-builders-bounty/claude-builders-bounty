# CLAUDE.md — Next.js 15 + SQLite SaaS

> Opinionated production guidelines for a SaaS project built with Next.js 15 App Router,
> SQLite (Turso / better-sqlite3), Drizzle ORM, and Tailwind CSS.

---

## Project Overview

This is a **multi-tenant SaaS platform** built on the modern Next.js stack. Every decision
below is deliberate — if something feels restrictive, there's a reason behind it.

| Concern               | Choice                          | Why                                                                 |
|-----------------------|---------------------------------|----------------------------------------------------------------------|
| Framework             | Next.js 15 (App Router)         | SSR, streaming, RSC — zero-config opinionated full-stack framework   |
| Database              | SQLite via Turso (prod) / better-sqlite3 (dev) | Serverless-friendly, zero ops, edge-replicated reads      |
| ORM                   | Drizzle ORM                     | Type-safe, SQL-like syntax, fast CLI, no hidden magic               |
| UI                    | Tailwind CSS v4 + shadcn/ui     | Utility-first, composable, tree-shakeable, accessible out of the box |
| Auth                  | NextAuth.js v5                  | Built for Next.js, supports credentials + OAuth, middleware-friendly |
| Language              | TypeScript (strict)             | Catch entire classes of bugs at compile time                         |
| Package Manager       | pnpm                            | Fast, disk-efficient, strict dependency resolution                   |
| Testing               | Vitest (unit) + Playwright (e2e)| Fast Vitest for unit/integration, Playwright for critical user flows |
| Validation            | Zod                             | Runtime + type safety in one schema definition                       |
| Payments              | Stripe                          | Industry standard for SaaS billing, webhooks, and subscription mgmt  |

---

## Tech Stack Reference

### Core

- **Runtime:** Node.js 20+ (LTS)
- **Framework:** Next.js 15 App Router (React 19, RSC, Server Actions, Streaming)
- **TypeScript:** strict mode — `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`

### Database

- **Local dev:** `better-sqlite3` via `drizzle-orm/better-sqlite3` driver
- **Production:** Turso (libsql) via `@libsql/client` — edge-ready, HTTP + WebSocket
- **Migrations:** Drizzle Kit — `drizzle-kit` CLI (generate, push, migrate, studio)
- **Schema:** Drizzle `pgTable`-style schema definitions in `src/db/schema/`

### UI & Styling

- **Tailwind CSS v4** — CSS-first config via `@tailwindcss/postcss`
- **shadcn/ui** — copy-paste components in `src/components/ui/`, customize via CSS variables
- **Lucide React** — icon set used by shadcn/ui

### Auth & Security

- **NextAuth.js v5** — `@auth/nextjs` with Database + OAuth adapters
- **bcryptjs** — password hashing (no native deps)
- **Zod** — input validation on API routes and Server Actions

### Developer Experience

- **Biome** — linter + formatter (faster than ESLint + Prettier)
- **Husky + lint-staged** — pre-commit hooks for linting and formatting
- **Drizzle Studio** — GUI database browser via `pnpm db:studio`

---

## Common Commands

```bash
# Development
pnpm dev              # Start dev server (localhost:3000)
pnpm dev --turbo      # Start with Turbopack (faster HMR)

# Build & Production
pnpm build            # Production build (validates types + lint)
pnpm start            # Start production server

# Linting & Formatting
pnpm lint             # Run Biome (lint + format checks)
pnpm format           # Auto-format code with Biome
pnpm typecheck        # Run tsc --noEmit for type checking

# Testing
pnpm test             # Run Vitest (unit/integration)
pnpm test --watch     # Watch mode for TDD
pnpm test:ui          # Vitest UI dashboard
pnpm test:e2e         # Run Playwright E2E tests
pnpm test:e2e --ui    # Playwright UI mode

# Database (Drizzle)
pnpm db:generate      # Generate migration from schema changes
pnpm db:migrate       # Apply pending migrations
pnpm db:push          # Push schema directly (dev only — no migration file)
pnpm db:studio        # Open Drizzle Studio (GUI DB browser)
pnpm db:seed          # Run seed script (src/db/seed.ts)
pnpm db:reset         # Drop DB + re-migrate + re-seed

# Other
pnpm clean            # Remove .next/, node_modules, and drizzle/
pnpm analyze          # Run @next/bundle-analyzer
```

---

## Architecture Patterns

### Server Components (Default)

Every component is a **Server Component** unless it needs interactivity. This is the default
in the App Router — you don't need to annotate it.

```tsx
// ✅ GOOD: Server Component — fetches data directly from DB
import { db } from '@/db';
import { posts } from '@/db/schema';
import { desc } from 'drizzle-orm';

export default async function PostList() {
  const allPosts = await db.select().from(posts).orderBy(desc(posts.createdAt));
  return (
    <ul>
      {allPosts.map(post => (
        <li key={post.id}>{post.title}</li>
      ))}
    </ul>
  );
}
```

**Rules:**
- Fetch data directly in Server Components — no `useEffect` or React Query for initial data
- Use `async` components for data fetching; Next.js streams the result
- Keep expensive computations in Server Components (they never ship to the client)
- **Never** import server-only modules (fs, DB, tokens) into client components

### Client Components

Mark with `'use client'` only when you genuinely need interactivity:

```tsx
'use client';

// ✅ GOOD: Only the interactive part is a client component
export function LikeButton({ postId }: { postId: string }) {
  const [liked, setLiked] = useState(false);
  return (
    <button onClick={() => setLiked(!liked)}>
      {liked ? '❤️' : '🤍'}
    </button>
  );
}
```

**When to use `'use client'`:**
- useState / useReducer / useRef
- useEffect or useLayoutEffect
- Event handlers (onClick, onSubmit, onChange)
- Browser-only APIs (localStorage, navigator, ResizeObserver)
- Third-party hooks or components that need browser APIs

**When NOT to use `'use client'`:**
- Pure presentational components that receive all data as props
- Components that only compose other components
- Layout components (they wrap server content)
- Data fetching — keep that in Server Components

### API Routes

Route handlers live in `src/app/api/[resource]/route.ts`:

```tsx
// src/app/api/posts/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/db';
import { posts, insertPostSchema } from '@/db/schema';
import { auth } from '@/lib/auth';

export async function GET(request: NextRequest) {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const searchParams = request.nextUrl.searchParams;
  const limit = Number(searchParams.get('limit')) || 20;

  const allPosts = await db.query.posts.findMany({
    limit,
    orderBy: (posts, { desc }) => [desc(posts.createdAt)],
    with: { author: true },
  });

  return NextResponse.json({ data: allPosts });
}

export async function POST(request: NextRequest) {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const body = await request.json();
  const parsed = insertPostSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 });
  }

  const [post] = await db.insert(posts).values({
    ...parsed.data,
    authorId: session.user.id,
  }).returning();

  return NextResponse.json({ data: post }, { status: 201 });
}
```

**Rules:**
- Validate all input with Zod before processing
- Always authenticate — use `auth()` from NextAuth.js
- Return consistent JSON shape: `{ data?, error?, message? }`
- Use HTTP status codes correctly (200, 201, 400, 401, 403, 404, 500)
- Rate-limit public endpoints (in-memory or Upstash)

### Server Actions

Prefer Server Actions over API routes for mutations tied to forms:

```tsx
// src/app/posts/actions.ts
'use server';

import { revalidatePath } from 'next/cache';
import { db } from '@/db';
import { posts } from '@/db/schema';
import { insertPostSchema } from '@/db/schema/posts';
import { auth } from '@/lib/auth';

export async function createPost(formData: FormData) {
  const session = await auth();
  if (!session?.user) throw new Error('Unauthorized');

  const parsed = insertPostSchema.safeParse({
    title: formData.get('title'),
    content: formData.get('content'),
  });
  if (!parsed.success) throw new Error(parsed.error.message);

  await db.insert(posts).values({ ...parsed.data, authorId: session.user.id });

  revalidatePath('/posts');
}
```

### Middleware

Use `src/middleware.ts` for auth checks, redirects, and header management:

```tsx
// src/middleware.ts
export { auth as middleware } from '@/lib/auth';

// Or custom middleware:
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Redirect /settings to /settings/profile
  if (pathname === '/settings') {
    return NextResponse.redirect(new URL('/settings/profile', request.url));
  }

  // Add security headers
  const response = NextResponse.next();
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('X-Content-Type-Options', 'nosniff');
  return response;
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
```

---

## Database & Migration Rules

### Schema-First Workflow

1. Edit table definitions in `src/db/schema/*.ts`
2. Run `pnpm db:generate` to produce a migration file in `drizzle/`
3. Run `pnpm db:migrate` to apply it
4. Commit **both** the schema change AND the migration file

### Schema Conventions

```ts
// src/db/schema/posts.ts
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';
import { createId } from '@paralleldrive/cuid2';
import { users } from './users';

export const posts = sqliteTable('posts', {
  id: text('id').primaryKey().$defaultFn(() => createId()),
  title: text('title').notNull(),
  slug: text('slug').notNull().unique(),
  content: text('content').notNull(),
  published: integer('published', { mode: 'boolean' }).default(false),
  authorId: text('author_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  createdAt: integer('created_at', { mode: 'timestamp' })
    .notNull()
    .$defaultFn(() => new Date()),
  updatedAt: integer('updated_at', { mode: 'timestamp' })
    .notNull()
    .$defaultFn(() => new Date())
    .$onUpdateFn(() => new Date()),
  deletedAt: integer('deleted_at', { mode: 'timestamp' }),  // soft delete
});

export type Post = typeof posts.$inferSelect;
export type NewPost = typeof posts.$inferInsert;
```

### Rules

| Rule | Detail |
|------|--------|
| **Timestamps** | Every table gets `createdAt` and `updatedAt` |
| **Soft deletes** | Add `deletedAt` column instead of hard deleting |
| **Foreign keys** | Always cascade on delete for user-owned rows |
| **IDs** | Use CUID2 (`createId()`) — no auto-increment, no UUID perf hit |
| **Migrations** | Never edit generated migration files — they are auto-generated |
| **One per feature** | Squash related schema changes into a single migration |
| **Raw SQL** | Only for performance-critical paths — prefer Drizzle query builders |

---

## Code Style Guidelines

### TypeScript

- **Strict mode** — `strict: true` in tsconfig.json, no exceptions
- **No `any`** — use `unknown` + type guards instead
- **Explicit returns** — annotate function return types on exported functions
- **Destructure early** — destructure props at the top of components
- **Named exports** — prefer named exports over default exports (better tree-shaking, refactoring)
- **Imports** — use `@/` path alias for all internal modules, group by: external → internal → type

### File Organization

```
src/
├── app/                 # Next.js App Router pages
│   ├── (auth)/          # Auth-required route group
│   ├── (marketing)/     # Public marketing pages
│   ├── api/             # API route handlers
│   ├── layout.tsx       # Root layout
│   └── page.tsx         # Home page
├── components/          # Shared React components
│   ├── ui/              # shadcn/ui primitives (button, input, dialog, etc.)
│   ├── forms/           # Form components (react-hook-form + zod)
│   └── layout/          # Layout components (header, sidebar, footer)
├── db/                  # Database layer
│   ├── schema/          # Drizzle table definitions
│   ├── queries/         # Reusable query functions
│   ├── index.ts         # DB client export
│   ├── seed.ts          # Seed script
│   └── migrate.ts       # Migration runner
├── lib/                 # Shared utilities
│   ├── auth.ts          # NextAuth.js configuration
│   ├── email.ts         # Email service (Resend / SendGrid)
│   ├── stripe.ts        # Stripe client
│   └── utils.ts         # General utilities (cn, formatDate, etc.)
├── config/              # Configuration & env validation
│   └── env.ts           # Zod-validated environment variables
└── styles/              # Global styles
    └── globals.css      # Tailwind imports + CSS variables
```

### React / JSX

- **Self-closing** — `<Button />` not `<Button></Button>`
- **Boolean props** — `<Button disabled>` not `<Button disabled={true}>`
- **Event handlers** — prefix with `handle`: `handleSubmit`, `handleClick`
- **Callback props** — prefix with `on`: `onSubmit`, `onClick`
- **Conditional rendering** — use ternary or `&&`, never `||` for display logic
- **Early returns** — guard clauses at the top of components for loading/empty/error states

### CSS

- **Tailwind utility classes** — prefer inline utilities over custom CSS
- **Custom styles** — use `@apply` in component files or CSS variables in `globals.css`
- **Animations** — use Tailwind's built-in `animate-*` utilities or `framer-motion`
- **Dark mode** — use `dark:` variant, driven by `class` strategy on `<html>`

---

## Environment Variables

### Validation Pattern

All environment variables are validated at startup using Zod:

```ts
// src/config/env.ts
import { z } from 'zod';

const envSchema = z.object({
  // App
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  APP_URL: z.string().url(),

  // Database
  DATABASE_URL: z.string().url(),
  DATABASE_AUTH_TOKEN: z.string().optional(),  // Turso only

  // Auth
  AUTH_SECRET: z.string().min(32),
  AUTH_GITHUB_ID: z.string().optional(),
  AUTH_GITHUB_SECRET: z.string().optional(),
  AUTH_GOOGLE_ID: z.string().optional(),
  AUTH_GOOGLE_SECRET: z.string().optional(),

  // Email
  RESEND_API_KEY: z.string().optional(),

  // Payments
  STRIPE_SECRET_KEY: z.string().optional(),
  STRIPE_WEBHOOK_SECRET: z.string().optional(),
  NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY: z.string().optional(),

  // Features
  NEXT_PUBLIC_POSTHOG_KEY: z.string().optional(),
  NEXT_PUBLIC_GA_ID: z.string().optional(),
});

export const env = envSchema.parse(process.env);
```

### Reference Table

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | SQLite DB path (dev) or libsql URL (prod/Turso) |
| `DATABASE_AUTH_TOKEN` | No | Turso auth token for production DB |
| `AUTH_SECRET` | Yes | NextAuth.js encryption secret (min 32 chars) |
| `AUTH_GITHUB_ID` | No | GitHub OAuth App client ID |
| `AUTH_GITHUB_SECRET` | No | GitHub OAuth App client secret |
| `AUTH_GOOGLE_ID` | No | Google OAuth client ID |
| `AUTH_GOOGLE_SECRET` | No | Google OAuth client secret |
| `RESEND_API_KEY` | No | Resend API key for transactional emails |
| `STRIPE_SECRET_KEY` | No | Stripe secret key (sk_live_*) |
| `STRIPE_WEBHOOK_SECRET` | No | Stripe webhook signing secret (whsec_*) |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | No | Stripe publishable key (pk_live_*) |
| `NEXT_PUBLIC_POSTHOG_KEY` | No | PostHog analytics API key |
| `NEXT_PUBLIC_GA_ID` | No | Google Analytics 4 measurement ID |

> ⚠️ Variables prefixed with `NEXT_PUBLIC_` are exposed to the browser.
> Never put secrets in `NEXT_PUBLIC_*` variables.

---

## Deployment Instructions (Vercel)

### Prerequisites

1. Push repo to GitHub
2. Create a Turso database: `turso db create myapp-prod`
3. Get the Turso URL and auth token: `turso db show myapp-prod` and `turso db tokens create myapp-prod`

### Vercel Setup

1. Import the GitHub repo into Vercel
2. Set framework preset to **Next.js**
3. Configure environment variables (see table above)
4. Deploy — Vercel detects `next.config.ts` automatically

### Build Settings

```json
{
  "installCommand": "pnpm install --frozen-lockfile",
  "buildCommand": "pnpm build",
  "outputDirectory": ".next"
}
```

### Post-Deploy

- Set `APP_URL` to the production URL (e.g., `https://myapp.vercel.app`)
- Configure custom domain in Vercel Dashboard > Domains
- Set up Stripe webhook endpoint → `https://myapp.vercel.app/api/webhooks/stripe`
- Enable Turso **edge-replicas** for fast global reads: `turso db locations add --all`

### Production Checklist

- [ ] DATABASE_AUTH_TOKEN set for Turso
- [ ] AUTH_SECRET regenerated (not the dev secret)
- [ ] Stripe webhook secret configured
- [ ] Custom domain set up with SSL
- [ ] Rate limiting enabled on public endpoints
- [ ] Analytics (PostHog / GA) configured
- [ ] Error monitoring (Sentry) configured
- [ ] Backup schedule configured in Turso

---

## Testing Patterns

### Unit Tests (Vitest)

```ts
// src/lib/__tests__/utils.test.ts
import { describe, it, expect } from 'vitest';
import { formatDate, cn } from '../utils';

describe('formatDate', () => {
  it('formats a date string correctly', () => {
    expect(formatDate('2026-01-15')).toBe('Jan 15, 2026');
  });

  it('handles ISO strings', () => {
    expect(formatDate('2026-06-07T10:30:00Z')).toBe('Jun 7, 2026');
  });
});

describe('cn', () => {
  it('merges class names', () => {
    expect(cn('px-4', 'py-2')).toBe('px-4 py-2');
  });

  it('resolves Tailwind conflicts', () => {
    expect(cn('px-4', 'px-6')).toBe('px-6');
  });
});
```

### Integration Tests (Vitest + MSW)

```ts
// src/app/api/posts/__tests__/route.test.ts
import { describe, it, expect, beforeAll } from 'vitest';
import { GET } from '../route';
import { db } from '@/db/testing';  // Test DB instance

describe('GET /api/posts', () => {
  beforeAll(async () => {
    // Seed test data
    await db.insert(posts).values({ title: 'Test', content: '...', authorId: 'user1' });
  });

  it('returns posts for authenticated users', async () => {
    const request = new Request('http://localhost:3000/api/posts');
    const response = await GET(request);
    expect(response.status).toBe(200);
    const body = await response.json();
    expect(body.data).toHaveLength(1);
  });
});
```

### E2E Tests (Playwright)

```ts
// e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test('user can sign up and access dashboard', async ({ page }) => {
  await page.goto('/signup');
  await page.fill('[name="email"]', 'test@example.com');
  await page.fill('[name="password"]', 'Password123!');
  await page.click('button[type="submit"]');

  await expect(page).toHaveURL('/dashboard');
  await expect(page.locator('h1')).toContainText('Dashboard');
});
```

### Testing Conventions

| Concern | Practice |
|---------|----------|
| **File location** | Co-locate with source: `Component.test.tsx` next to `Component.tsx` |
| **Test DB** | Use `better-sqlite3` in-memory database for integration tests |
| **Seeding** | Seed test data in `beforeAll` / `beforeEach`, clean up in `afterAll` |
| **Mocking** | Use MSW for HTTP mocking, `vi.mock()` for module mocking |
| **Auth** | Create test helper `createTestSession()` that returns a mock session |
| **Coverage** | Aim for >80% coverage on lib/ and db/; >60% on components/ |
| **CI** | Tests run on every PR via GitHub Actions |

---

## What We Don't Do (And Why)

| Anti-pattern | Reason |
|-------------|--------|
| `any` type | Defeats TypeScript. Use `unknown` with type guards |
| Direct SQL strings in components | Drizzle gives type-safe queries. Raw SQL only for perf-critical paths |
| Client-side data fetching as default | Server Components eliminate waterfall requests, reduce bundle size |
| `useEffect` for data fetching | React Query, Server Actions, or Server Components handle this better |
| Mixing ORMs / migration tools | Drizzle only — never Knex, Prisma, or raw SQL migrations |
| Hardcoded secrets | Always use validated `process.env.*` from `src/config/env.ts` |
| Default exports | Named exports are better for refactoring, tree-shaking, and IDE support |
| Barrel files (re-exports) | They cause circular dependencies and slow down HMR — import directly |
| Magic strings / numbers | Extract to named constants with clear intent |
| try/catch without error handling | Always log, report, and show user-friendly error messages |
| `any` in API responses | Define response types with Zod or TypeScript interfaces |
