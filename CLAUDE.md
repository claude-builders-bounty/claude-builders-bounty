# CLAUDE.md — Next.js 15 + SQLite SaaS Project

## Stack & Versions

- **Framework**: Next.js 15 (App Router, React Server Components by default)
- **Database**: SQLite via `better-sqlite3` (synchronous, zero-config) or Turso (edge-compatible)
- **ORM**: Drizzle ORM (type-safe SQL, migration-first)
- **Styling**: Tailwind CSS v4 + shadcn/ui components
- **Validation**: Zod for all API inputs and form schemas
- **Auth**: Better Auth or Lucia (session-based, no JWT)
- **Node**: ≥20.x (required for native better-sqlite3)

## Folder Structure

```
src/
├── app/                  # App Router pages & layouts
│   ├── (marketing)/      # Public landing pages (grouped route)
│   ├── (dashboard)/      # Authenticated app pages
│   │   └── [orgId]/      # Multi-tenant org scope
│   ├── api/              # Route handlers (REST)
│   └── layout.tsx        # Root layout with providers
├── components/
│   ├── ui/               # shadcn primitives (Button, Input, etc.)
│   ├── forms/            # Form wrappers with react-hook-form + zod
│   └── features/         # Feature-specific composite components
├── db/
│   ├── schema.ts         # Drizzle table definitions (single source of truth)
│   ├── migrations/       # Generated SQL migration files
│   ├── seed.ts           # Dev/test seed data
│   └── index.ts          # DB connection singleton
├── lib/
│   ├── auth.ts           # Auth helpers & session validation
│   ├── utils.ts          # Pure utility functions
│   └── validators/       # Zod schemas co-located by domain
└── types/                # Shared TypeScript types (no .ts in here, only .d.ts or interfaces)
```

## Naming Conventions

- **Files**: kebab-case (`user-profile.tsx`, `create-org.ts`)
- **Components**: PascalCase export (`UserProfile`), file is kebab-case
- **DB tables**: snake_case plural (`users`, `org_memberships`)
- **DB columns**: snake_case (`created_at`, `org_id`)
- **API routes**: kebab-case nouns (`/api/orgs/[orgId]/members`)
- **Zod schemas**: `createUserSchema`, `updateOrgSchema` (verb + noun + Schema)
- **Server Actions**: `createUser`, `deleteOrg` (verb + noun, exported from `actions/`)

## Database & Migration Rules

1. **Never edit migration files manually**. Always modify `schema.ts` then run `drizzle-kit generate`.
2. **Every schema change requires a migration**. No implicit sync.
3. **Use transactions** for multi-table writes:
   ```ts
   await db.transaction(async (tx) => {
     await tx.insert(users).values(user);
     await tx.insert(orgMemberships).values(membership);
   });
   ```
4. **Always add indexes** on foreign keys and frequently queried columns.
5. **Soft deletes preferred**: add `deleted_at` column, filter in queries. Hard delete only for PII cleanup.
6. **Timestamps**: use `integer('created_at', { mode: 'timestamp' })` for SQLite compatibility.
7. **No raw SQL unless necessary**. If needed, use `sql` template tag from drizzle-orm.

## Component Patterns

### Server vs Client Components
- **Default to Server Components**. Only add `"use client"` when you need interactivity, hooks, or browser APIs.
- **Data fetching happens in Server Components**. Pass data as props to client components.
- **Never fetch in useEffect**. Use Server Components or Server Actions.

### Forms
- All forms use `react-hook-form` + `zod` + `@hookform/resolvers`.
- Validation schema lives in `lib/validators/`, shared between client and server.
- Server-side re-validation in Server Action or Route Handler. Never trust client-only validation.

### Error Handling
- Use `error.tsx` boundaries for page-level errors.
- API routes return structured JSON: `{ error: string; code: string }`.
- Never expose stack traces or internal details in production responses.

## Dev Commands

```bash
pnpm dev              # Start dev server (Turbopack)
pnpm build            # Production build
pnpm db:generate      # Generate new migration from schema changes
pnpm db:migrate       # Apply pending migrations
pnpm db:seed          # Run seed script
pnpm db:studio        # Open Drizzle Studio (DB GUI)
pnpm lint             # ESLint + Prettier check
pnpm typecheck        # tsc --noEmit
```

## Anti-Patterns (Don't Do These)

| ❌ Don't | ✅ Do Instead | Why |
|----------|--------------|-----|
| `any` type | Explicit types or Zod inference | Type safety prevents runtime bugs |
| `useEffect` for data fetching | Server Components / Server Actions | RSC eliminates waterfall requests |
| Global state for server data | React Query / SWR for client cache | Server data belongs on the server |
| Inline styles | Tailwind utility classes | Consistency, purgeable CSS |
| `console.log` in production code | Structured logger (pino/winston) | Observable, filterable logs |
| Direct `process.env` access | Typed env config in `lib/env.ts` | Validation at startup, not runtime |
| Barrel exports (`index.ts` re-exports) | Direct imports | Tree-shaking, faster builds |
| JWT tokens for sessions | Signed cookies / server sessions | Secure, revocable, no XSS token theft |
| `dangerouslySetInnerHTML` | Sanitized rendering or markdown parser | XSS prevention |
| Mutable global state | React context or Zustand (scoped) | Predictable renders, SSR safe |

## Testing

- **Unit tests**: Vitest for pure functions and utilities.
- **Component tests**: Testing Library for interactive components.
- **E2E**: Playwright for critical user flows (signup, billing, core feature).
- **DB tests**: Use in-memory SQLite (`:memory:`) with migrations applied per test.
- **Coverage threshold**: ≥80% for `lib/` and `db/`, ≥60% overall.

## Security Checklist

- [ ] All user input validated with Zod before processing
- [ ] SQL queries parameterized (Drizzle handles this automatically)
- [ ] Auth checked in middleware + per-route (defense in depth)
- [ ] CSRF protection enabled for state-changing requests
- [ ] Rate limiting on auth and public API endpoints
- [ ] Secrets in `.env.local`, never committed, validated at startup
