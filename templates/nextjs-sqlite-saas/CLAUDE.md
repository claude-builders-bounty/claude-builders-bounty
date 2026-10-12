# Project Guidelines: Next.js 15 + SQLite SaaS Template

## Stack & Target Versions
- **Framework**: Next.js 15 (App Router with React Server Components)
- **Language**: TypeScript (Strict mode enabled, zero `any` allowed)
- **Database**: SQLite (via `better-sqlite3` for local development / `libsql` for Turso cloud edge)
- **ORM / Migrations**: Drizzle ORM
- **Authentication**: Auth.js / NextAuth v5
- **Styling**: Tailwind CSS v3 with `class-variance-authority` (cva)

## Directory Structure
```
├── app/                  # Next.js 15 App Router routes
│   ├── (auth)/          # Authentication route group (login, register)
│   ├── (dashboard)/     # Authenticated SaaS user dashboard
│   ├── api/             # Edge and Node.js REST API routes
│   ├── layout.tsx       # Root layout
│   └── page.tsx         # Public marketing landing page
├── components/          # Reusable React components
│   ├── ui/              # Primitive atom components (buttons, dialogs)
│   └── shared/          # Composed feature widgets
├── db/                  # Database layer
│   ├── schema.ts        # Drizzle schema definitions
│   ├── index.ts         # SQLite connection singleton
│   └── migrations/      # Version-controlled SQL migrations
├── lib/                 # Utility functions, validators, and constants
│   ├── auth.ts          # Session helper functions
│   └── validators.ts    # Zod input schemas
└── types/               # Global TypeScript definitions
```

## SQL & Migration Conventions
- All table names use `snake_case` plural (e.g. `users`, `subscriptions`, `teams`, `invoices`).
- Primary keys must be `text` with ULID or CUID2 (never autoincrement integer IDs for public URLs).
- Migrations are generated via `pnpm drizzle-kit generate` and executed via `pnpm db:migrate`.
- NEVER write raw, unparameterized SQL strings. Always use Drizzle prepared statements or parameterized queries.

## Component Patterns
1. **Server Components by Default**:
   Keep pages and layout as React Server Components. Only add `'use client'` when using hooks (`useState`, `useEffect`) or browser event handlers.
2. **Server Actions for Mutations**:
   Handle forms and data mutations via Server Actions (`actions.ts`) with Zod schema validation.
3. **Optimistic UI**:
   Use `useOptimistic` for instantaneous user feedback on dashboard lists and toggles.

## Anti-Patterns: What We DON'T Do (and Why)
- ❌ **No `useEffect` for data fetching**: Fetch directly inside Server Components to eliminate waterfall requests and eliminate loading spinners.
- ❌ **No Client-side Database Connections**: SQLite must remain strictly on the server layer.
- ❌ **No In-memory Stateful Singletons**: Serverless lambdas will discard memory state; always persist state in SQLite.
- ❌ **No unvalidated `req.json()`**: Always pass request payloads through `schema.parse(body)`.

## Development Commands
- `pnpm dev`: Start local Next.js dev server on port 3000
- `pnpm db:generate`: Create new migration from schema.ts
- `pnpm db:push`: Push schema directly during prototype development
- `pnpm build`: Validate TypeScript and produce production bundle
