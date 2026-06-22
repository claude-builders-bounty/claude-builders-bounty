# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack

| Layer | Choice | Why |
|---|---|---|
| Framework | Next.js 15 (App Router) | RSC, server actions, streaming |
| Language | TypeScript 5.x (strict) | Catch class of bugs at compile time |
| Database | SQLite via better-sqlite3 | Zero ops, fast local dev, easy backup |
| ORM | Drizzle ORM | Type-safe, SQL-like, no hidden N+1 |
| Auth | NextAuth.js v5 (Auth.js) | Built for App Router, adapter pattern |
| Styling | Tailwind CSS v4 | Utility-first, tiny prod bundle |
| UI Primitives | shadcn/ui | Copy-paste, fully customizable |
| Validation | Zod | Composable, inferred types |
| Testing | Vitest + Playwright | Fast unit tests, reliable e2e |

## Folder Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/            # Auth group (login, signup)
│   ├── (dashboard)/       # Authenticated routes
│   │   ├── settings/
│   │   └── [org]/
│   ├── api/               # Route handlers (REST endpoints)
│   └── layout.tsx         # Root layout
├── components/
│   ├── ui/                # shadcn/ui primitives
│   ├── forms/             # Form components with react-hook-form
│   └── shared/            # Shared app components
├── db/
│   ├── schema/            # Drizzle schema definitions
│   │   ├── users.ts
│   │   ├── orgs.ts
│   │   └── ...
│   ├── migrations/        # Generated SQL migrations
│   ├── queries/           # Reusable query functions
│   └── index.ts           # DB client singleton
├── lib/
│   ├── auth.ts            # Auth.js config
│   ├── utils.ts           # Utility functions
│   └── email.ts           # Email sending
└── types/
    └── index.ts           # Shared TypeScript types
```

**Why flat under `src/`:** Nesting beyond 2 levels hurts discoverability.
Colocate by domain, not by type. If a component grows beyond 300 lines,
extract into `components/shared/`.

## Naming Conventions

| What | Convention | Example |
|---|---|---|
| Components | PascalCase | `UserSettingsForm.tsx` |
| Hooks | `use` prefix, camelCase | `useCurrentOrg.ts` |
| Utils | camelCase | `formatDate.ts` |
| DB schemas | snake_case | `users.ts`, `org_members.ts` |
| DB columns | snake_case | `created_at`, `invited_by_id` |
| API routes | kebab-case | `route.ts` |
| Types/Interfaces | PascalCase | `type UserOrg` |
| Files (non-component) | camelCase | `sendEmail.ts` |

**Why snake_case for DB:** SQL convention. Drizzle maps to camelCase in TS
via `camelCase` config, so you write `user.createdAt` in code.

## SQL / Migration Rules

1. **Every migration must be reversible.** Include a `down` SQL comment.
2. **No raw SQL in app code.** All queries go through Drizzle.
3. **Index every foreign key.** SQLite needs explicit indexes.
4. **Use `TEXT` instead of `VARCHAR`.** SQLite treats them identically; TEXT is more portable.
5. **Timestamps:** always `created_at TEXT NOT NULL DEFAULT (datetime('now'))`.
6. **Soft deletes only** via `deleted_at TEXT`. Hard deletes break referential integrity.

```sql
-- Good migration
CREATE TABLE org_members (
  id        TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  org_id    TEXT NOT NULL REFERENCES orgs(id),
  user_id   TEXT NOT NULL REFERENCES users(id),
  role      TEXT NOT NULL DEFAULT 'member' CHECK(role IN ('admin','member')),
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  deleted_at TEXT
);
CREATE INDEX idx_org_members_org_id ON org_members(org_id);
-- down: DROP TABLE org_members;
```

## Component Patterns

### Server Component by Default
```tsx
// app/(dashboard)/orgs/page.tsx
export default async function OrgsPage() {
  const orgs = await getOrgsForUser(); // server-side query
  return <OrgList orgs={orgs} />;
}
```

### Client Component When Needed
```tsx
'use client';
// Only when: useState, useEffect, onClick, browser APIs
export function CreateOrgButton() { ... }
```

### Form Pattern
```tsx
'use server';
export async function createOrg(formData: FormData) {
  'use server';
  const data = createOrgSchema.parse(formData);
  await db.insert(orgs).values(data);
  revalidatePath('/orgs');
}
```

**Anti-pattern:** Fetching data in client components when server components work.

## Auth Pattern

```tsx
// lib/auth.ts
export const { handlers, signIn, signOut, auth } = NextAuth({
  adapter: DrizzleAdapter(db),
  session: { strategy: 'database' }, // SQLite-friendly
  providers: [GitHub, Google, Resend],
});

// In layouts:
const session = await auth();
if (!session) redirect('/login');
```

## Dev Commands

```bash
npm run dev          # Next.js dev server
npm run db:generate  # Generate migration from schema changes
npm run db:push      # Push migration to local SQLite
npm run db:studio    # Drizzle Studio (GUI)
npm run test         # Vitest unit tests
npm run test:e2e     # Playwright e2e
npm run lint         # Biome / ESLint
npm run typecheck    # tsc --noEmit
npm run build        # Production build
```

## What We Don't Do (And Why)

| Don't | Why |
|---|---|
| Prisma | Heavy binary, slow `prisma generate`, no SQLite `CHECK` constraints |
| tRPC | Overkill for server actions + RSC. Use server actions directly. |
| Redux/Zustand | RSC + URL state covers 95% of cases. Pass props. |
| Monorepo (turborepo) | Premature for a SaaS. Start monolith, extract later. |
| GraphQL | REST + server actions are simpler. GraphQL adds schema complexity. |
| Barrel exports | Cause circular deps and tree-shaking issues. Import directly. |
| `any` type | Use `unknown` + narrowing, or `z.infer`. `any` disables type-checking. |

## File Size Limits

- **Component:** max 300 lines. Split into smaller files.
- **Route handler:** max 100 lines. Move logic to `lib/`.
- **DB query:** max 80 lines. If longer, split into multiple queries.

## Testing Requirements

- Every server action needs a **unit test** (Vitest).
- Every API route needs an **integration test**.
- Every critical user flow (signup, payment, invite) needs an **e2e test**.
- Mock DB in unit tests using `better-sqlite3:memory:`.

## Git Conventions

| Prefix | Use Case |
|---|---|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `db:` | Migration or schema change |
| `refactor:` | Code restructuring |
| `docs:` | Documentation |
| `perf:` | Performance improvement |
