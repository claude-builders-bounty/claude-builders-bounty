# CLAUDE.md — Next.js 15 + SQLite SaaS

> Paste this file into the root of any greenfield Next.js 15 App Router + SQLite (better-sqlite3 or Turso) SaaS project. Claude Code will pick up the conventions automatically.

---

## Stack & Versions

| Layer       | Choice                         | Version  |
|-------------|--------------------------------|----------|
| Framework   | Next.js (App Router)           | 15.x     |
| Runtime     | Node.js                        | 20 LTS   |
| Language    | TypeScript (strict)            | 5.x      |
| Database    | better-sqlite3 (local) / Turso (prod) | latest |
| ORM         | Drizzle ORM                    | latest   |
| Auth        | NextAuth.js v5 (Auth.js)       | 5.x      |
| Styling     | Tailwind CSS                   | 4.x      |
| Validation  | Zod                            | 3.x      |
| Testing     | Vitest + React Testing Library | latest   |

---

## Commands

```bash
npm run dev          # Start dev server on :3000
npm run build        # Production build
npm run start        # Start production server
npm run db:push      # Push Drizzle schema to SQLite
npm run db:studio    # Open Drizzle Studio (local DB viewer)
npm run db:generate  # Generate SQL migration from schema changes
npm run db:migrate   # Run pending migrations
npm run test         # Run Vitest
npm run test:watch   # Run Vitest in watch mode
npm run lint         # ESLint
npm run typecheck    # tsc --noEmit
```

---

## Folder Structure

```
src/
├── app/                    # Next.js App Router pages & layouts
│   ├── (auth)/             # Auth route group (login, register)
│   ├── (dashboard)/        # Protected dashboard route group
│   ├── api/                # API route handlers
│   │   └── v1/             # Versioned API routes
│   ├── layout.tsx          # Root layout
│   └── page.tsx            # Landing page
├── components/
│   ├── ui/                 # Primitives: Button, Input, Card, Dialog
│   ├── forms/              # Form components with Zod + React Hook Form
│   └── layouts/            # Sidebar, Header, Shell
├── lib/
│   ├── db/                 # Drizzle schema, client, migrations
│   │   ├── schema.ts       # All table definitions (single file)
│   │   ├── client.ts       # DB connection (better-sqlite3 / Turso)
│   │   └── migrations/     # Generated SQL migration files
│   ├── auth.ts             # NextAuth config & helpers
│   ├── stripe.ts           # Stripe client & webhook helpers
│   └── utils.ts            # cn(), formatDate(), etc.
├── server/
│   ├── queries/            # Typed DB query functions (one per domain)
│   └── actions/            # Next.js Server Actions
├── hooks/                  # Custom React hooks
├── types/                  # Shared TypeScript types & Zod schemas
└── constants.ts            # App-wide constants
```

---

## SQL / Migration Conventions

- **Single schema file**: All tables live in `src/lib/db/schema.ts`. Split into separate files only when the file exceeds 300 lines.
- **Drizzle ORM only**: Never write raw SQL. Use Drizzle's query builder for all reads and writes.
- **Migrations are one-way**: Generate with `npm run db:generate`, apply with `npm run db:migrate`. Never edit migration files after generation.
- **Column naming**: `snake_case` in DB, mapped to `camelCase` in TypeScript via Drizzle's `cz` helpers.
- **Every table has**:
  - `id` — text primary key (use `nanoid()` or `cuid2`)
  - `created_at` — integer (Unix timestamp, not ISO string — SQLite has no native datetime type)
  - `updated_at` — integer (Unix timestamp)
- **Foreign keys**: Always declare with `references(() => table.id)` and `onDelete: "cascade"` where appropriate.
- **No ORM bypasses**: Never use `db.run()` or `db.all()` with raw SQL strings. If Drizzle can't express it, add a comment explaining why raw SQL is needed.

### Adding a new table

1. Define the table in `src/lib/db/schema.ts`
2. Run `npm run db:generate` to create the migration
3. Run `npm run db:push` (dev) or `npm run db:migrate` (prod)
4. Create a query file in `src/server/queries/<domain>.ts`

---

## Component Patterns

- **Server Components by default**: Every component is a Server Component unless it needs interactivity or browser APIs.
- **Client Component marker**: Add `"use client"` only when the component uses `useState`, `useEffect`, event handlers, or browser APIs.
- **Colocation**: Keep test files next to the component: `Button.tsx` → `Button.test.tsx`.
- **Props**: Use inline TypeScript types for props. Do not create separate `types.ts` files for component props.
  ```tsx
  // Good
  export function UserCard({ name, email }: { name: string; email: string }) { ... }
  ```
- **Server Actions**: Define in `src/server/actions/`. Always validate input with Zod. Return typed results.
  ```ts
  "use server"
  import { z } from "zod"
  const schema = z.object({ name: z.string().min(1) })
  export async function createUser(input: unknown) {
    const data = schema.parse(input)
    // ...
  }
  ```
- **Data fetching**: Use Server Components + `await db.query(...)` for reads. Use Server Actions for mutations. Never fetch data in Client Components when a Server Component can do it.
- **Loading states**: Use Next.js `loading.tsx` files with `<Skeleton />` components. Do not implement client-side loading spinners for server-rendered data.

---

## What We Don't Do (and Why)

| Anti-pattern                               | Why not                                         |
|--------------------------------------------|-------------------------------------------------|
| Prisma ORM                                 | Drizzle generates simpler SQL, works better with SQLite, and has zero runtime overhead |
| `getServerSideProps` / Pages Router        | App Router is the standard. Pages Router is legacy             |
| Client-side data fetching with `useEffect` | Server Components eliminate waterfalls and loading flicker     |
| `any` type                                 | Strict mode is on. Use `unknown` + Zod validation instead      |
| Stored procedures or DB triggers           | Business logic belongs in TypeScript, not SQLite               |
| Environment-based feature flags            | Use a config table or a simple `features` module              |
| Global state (Redux, Zustand)              | Server state via queries + URL state. Local UI state via `useState` only |
| CSS modules or styled-components           | Tailwind only. One styling system, no exceptions               |
| Custom auth implementation                 | Use NextAuth.js. Never roll your own session/JWT handling      |
| API routes for data fetching               | Server Components can query the DB directly. API routes are for webhooks and external integrations only |
| `fetch()` to own API routes                | Import the query function directly — skip the HTTP roundtrip  |

---

## Naming Conventions

- **Files**: `kebab-case.tsx` for components, `kebab-case.ts` for utilities
- **Components**: PascalCase exports, one component per file
- **Server Actions**: verb + noun: `createUser`, `deleteTeam`, `updateSettings`
- **DB Queries**: noun + verb: `userById`, `teamMembers`, `activeSubscriptions`
- **Route groups**: `(parentheses)` for grouping without URL impact
- **API routes**: `/api/v1/resource` — always versioned, always plural nouns

---

## Environment Variables

```bash
# Required
DATABASE_URL=file:./dev.db          # local: better-sqlite3 file path
# DATABASE_URL=libsql://xxx.turso.io  # prod: Turso connection
# DATABASE_AUTH_TOKEN=xxx             # prod: Turso auth token

NEXTAUTH_SECRET=xxx                  # Generate: openssl rand -hex 32
NEXTAUTH_URL=http://localhost:3000

STRIPE_SECRET_KEY=sk_test_xxx        # Stripe test key
STRIPE_WEBHOOK_SECRET=whsec_xxx      # From Stripe CLI

ANTHROPIC_API_KEY=xxx                # If using Claude API features
```

- Never commit `.env` files. `.env.local` is gitignored by default.
- Access env vars only in Server Components, Server Actions, or API routes — never in Client Components.
- Validate env vars at build time using `src/lib/env.ts` with Zod.

---

## Testing Conventions

- **Unit tests**: Vitest. Test pure functions and query functions.
- **Component tests**: React Testing Library + Vitest. Test user-facing behavior, not implementation details.
- **No E2E by default**: Only add Playwright when a critical user flow needs it.
- **DB tests**: Use a separate `test.db` SQLite file. Reset before each test suite.
- **Mocking**: Mock external APIs (Stripe, Claude). Never mock your own DB queries — use a test database.
