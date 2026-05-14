# Project Context — Next.js 15 App Router + SQLite SaaS

## Stack
- **Framework:** Next.js 15 (App Router, RSC)
- **Runtime:** Node.js 20+
- **Database:** SQLite via better-sqlite3 (local) / Turso (production)
- **ORM:** Drizzle ORM
- **Styling:** Tailwind CSS
- **Auth:** NextAuth.js v5 with database sessions

---

## Project Structure

```
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── (auth)/            # Auth routes (login, register, reset-password)
│   │   ├── (dashboard)/       # Authenticated dashboard routes
│   │   ├── api/               # API route handlers
│   │   │   └── auth/          # NextAuth.js API routes
│   │   └── layout.tsx         # Root layout
│   ├── components/             # React components
│   │   ├── ui/                # Primitive UI components (Button, Input, Card)
│   │   └── [feature]/         # Feature-specific components
│   ├── lib/
│   │   ├── db/                # Database schema, migrations, client
│   │   ├── auth/              # Auth configuration
│   │   └── utils/             # Shared utilities
│   └── types/                 # TypeScript type definitions
├── drizzle/                   # Drizzle migration files
├── scripts/                   # Utility scripts (seed, migrate)
└── tests/                     # Test files (Vitest + Playwright)
```

---

## Naming Conventions

| Pattern | Convention | Example |
|---------|-----------|---------|
| Pages | kebab-case | `user-profile-settings.tsx` |
| Components | PascalCase | `UserProfileCard.tsx` |
| Server Actions | snake_case verb phrase | `update_user_profile.ts` |
| API Routes | snake_case | `update-user.ts` |
| Database tables | snake_case plural | `user_sessions` |
| Database columns | snake_case | `created_at` |
| CSS classes | Tailwind utility first | — |
| Environment vars | SCREAMING_SNAKE | `DATABASE_URL` |

---

## SQL / Migration Rules

### Schema Declaration
- All tables use `id` (TEXT, UUID) as primary key unless otherwise specified
- All tables include `created_at` and `updated_at` timestamps
- Use Drizzle schema syntax only — no raw SQL in schema files

```typescript
// ✅ CORRECT
export const users = pgTable('users', {
  id: text('id').primaryKey().defaultRandom(),
  email: text('email').notNull().unique(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
});

// ❌ WRONG — raw SQL in schema
export const users = pgTable('users', {
  id: text('id').primaryKey().default(sql`gen_random_uuid()`),
});
```

### Migrations
- One migration per feature/fix
- Never modify existing migration files
- Always migrate forward — no down migrations in production
- Test migrations on a local DB copy before committing

### Query Patterns
- Use parameterized queries only — never string concatenation
- Use transactions for multi-table writes
- Keep queries close to the feature that uses them

---

## Component Patterns

### File Structure
Each component gets its own directory:
```
components/UserProfileCard/
├── UserProfileCard.tsx      # Main component
├── UserProfileCard.test.tsx
└── index.ts                 # Re-export
```

### Server vs Client Components
- Default to **Server Components**
- Add `'use client'` only when needed: event handlers, useState, useEffect, browser APIs
- Pass data to client components via props, not context

### Error Handling
- Wrap async Server Components in `try/catch`
- Use `error.tsx` files in each route segment
- Never swallow errors — always log + surface to user

---

## What We Don't Do (And Why)

| Anti-pattern | Why Not | Instead |
|-------------|---------|---------|
| `any` types | Loses type safety | Define proper interfaces |
| Inline styles | Hard to maintain | Tailwind utilities |
| Mixed CSS-in-JS | Performance cost | Tailwind only |
| Raw SQL strings | SQL injection risk | Drizzle ORM |
| `console.log` | No log levels | Use `lib/logger.ts` |
| Default exports | Barrel file conflicts | Named exports |
| Non-deterministic DB ops | Race conditions | Use transactions |
| `await` in useEffect | Memory leaks | Use SWR or React Query |

---

## Development Commands

```bash
# Setup
npm install

# Local development
npm run dev

# Run migrations
npm run db:migrate

# Create migration (after schema change)
npm run db:generate

# Push schema to local DB
npm run db:push

# Seed database
npm run db:seed

# Run tests
npm run test

# Type check
npm run typecheck
```

---

## Architecture Decisions

### Authentication
- Use NextAuth.js v5 with database session strategy
- Sessions stored in SQLite `sessions` table
- CSRF protection enabled by default

### Data Fetching
- Server Components fetch data directly (no client-side fetching for initial load)
- Use `useQuery` (TanStack Query) only for client-side mutations and real-time updates
- Never fetch in Server Component render — use `async`/`await`

### API Design
- Use Next.js Route Handlers (`app/api/`) for external API access
- Use Server Actions (`actions/`) for form submissions and mutations
- Return typed responses — no untyped JSON

---

## Testing Strategy

- **Unit:** Vitest for lib/utils functions
- **Component:** React Testing Library
- **E2E:** Playwright for critical user flows
- Test file location: `tests/` mirrors `src/` structure

---

## Git Conventions

| Type | Format | Description |
|------|--------|-------------|
| feat | `feat: add user profile page` | New feature |
| fix | `fix: resolve login redirect loop` | Bug fix |
| refactor | `refactor: extract auth helper` | Code restructure |
| docs | `docs: update README` | Documentation |
| test | `test: add user registration flow` | Tests |
| chore | `chore: update dependencies` | Maintenance |

Commit message format: `<type>: <description>`

---

## Environment Variables

```env
# Database
DATABASE_URL=file:./local.db

# Auth
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=<generate with: openssl rand -base64 32>

# Optional
TURSO_DATABASE_URL=
TURSO_AUTH_TOKEN=
```

Never commit `.env` — use `.env.example` as template.
