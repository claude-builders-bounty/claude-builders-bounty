# Claude Code Context — Next.js 15 + SQLite SaaS

## Stack & versions
- Next.js 15 App Router (React 19, TypeScript 5)
- SQLite via `better-sqlite3` (local dev) / Turso (production)
- Drizzle ORM for type-safe migrations and queries
- Tailwind CSS v4 for styling
- Zod for validation

Why: Next.js 15 gives us server components, streaming, and partial prerendering. SQLite avoids the complexity of running a separate database server — single file, zero config, perfect for SaaS MVPs. Drizzle is lighter than Prisma and uses SQL-like syntax. Tailwind v4 eliminates config files.

## Folder structure
```
src/
├── app/              # Next.js App Router pages
│   ├── (auth)/       # Auth-grouped routes (login, signup)
│   ├── (dashboard)/  # Authenticated dashboard routes
│   └── api/          # Route handlers
├── db/
│   ├── schema.ts     # Drizzle schema definitions
│   ├── migrations/   # Auto-generated migration files
│   └── index.ts      # Database client singleton
├── lib/
│   ├── auth.ts       # Auth helpers (sessions, middleware)
│   └── utils.ts      # Shared utilities
└── components/
    ├── ui/           # Generic UI primitives (Button, Input, Card)
    └── features/     # Domain-specific components (BillingForm, TeamList)
```

Why: `(auth)` and `(dashboard)` route groups keep layouts separate without affecting URLs. `db/` isolates all data access — never import `better-sqlite3` or Drizzle outside this folder. `lib/` is for pure functions with no JSX. `components/features/` prevents the `ui/` folder from becoming a dumping ground.

## SQL / migration conventions

```
drizzle-kit generate  # After editing schema.ts
drizzle-kit migrate   # Apply to database
```

Rules:
- Every column gets an explicit name (never rely on inference)
- Foreign keys always reference `id` with `onDelete: cascade` or `restrict` — be explicit
- `createdAt` and `updatedAt` are required on every table
- Migration files are committed — never edit them manually, always generate fresh
- Never use raw SQL unless Drizzle doesn't support the operation (add a comment explaining why)

Why: Explicit column names prevent silent mismatches. Committed migrations enable rollbacks and team sync. Raw SQL bypasses type safety — only use as last resort.

## Component patterns

**Server components by default, client only when needed.**

```tsx
// Server component — can be async, reads DB directly
export default async function TeamList() {
  const teams = await db.query.teams.findMany()
  return <ul>{teams.map(t => <li key={t.id}>{t.name}</li>)}</ul>
}

// Client component — only when you need interactivity
"use client"
export function CreateTeamButton() {
  const [open, setOpen] = useState(false)
  return <button onClick={() => setOpen(true)}>New Team</button>
}
```

Rules:
- One component per file. File name matches export name.
- Props types are inline (not separate files) unless shared across 3+ components
- Async data fetching happens in the server component, not in `useEffect`
- Forms use Server Actions (not API routes for mutations)

Why: Server components reduce JS bundle size. One-component-per-file prevents scrolling through 500-line files. Server Actions eliminate the API-route boilerplate for form submissions.

## Dev commands
```bash
pnpm dev              # Next.js dev server
pnpm build            # Production build
pnpm db:generate      # Generate Drizzle migration
pnpm db:migrate       # Apply migration
pnpm db:studio        # Drizzle Studio (GUI for DB)
pnpm lint             # ESLint + TypeScript check
pnpm test             # Vitest
```

## What we don't do (and why)

- **No API routes for mutations** — use Server Actions instead. API routes add indirection; Server Actions are colocated with the component that triggers them.
- **No `any` types** — if you're fighting the type system, the design is wrong, not the types. Use `unknown` and narrow.
- **No client-side data fetching with `useEffect`** — server components can be async. Client fetches cause waterfalls and flash-of-empty states.
- **No environment variables in client code without `NEXT_PUBLIC_` prefix** — Next.js enforces this for a reason. If you need a secret, it stays on the server.
- **No Prisma** — for SQLite projects, Drizzle is 10x smaller, has zero code generation latency, and its SQL-like API is easier to reason about. Prisma adds a runtime engine that's overkill for single-file databases.
- **No barrel exports (`index.ts` that re-exports everything)** — they create circular dependency risks and make tree-shaking harder. Import directly from the source file.
