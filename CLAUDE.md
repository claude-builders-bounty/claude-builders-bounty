# Next.js 15 + SQLite SaaS — CLAUDE.md

## Project Architecture

```
project-root/
├── src/
│   ├── app/                 # Next.js 15 App Router
│   │   ├── (auth)/          # Auth-adjacent routes (login, register)
│   │   ├── (dashboard)/     # Authenticated app routes
│   │   ├── api/             # Route Handlers (API endpoints)
│   │   └── layout.tsx       # Root layout
│   ├── components/          # Shared UI components
│   │   ├── ui/              # Base UI primitives (button, input, card)
│   │   └── forms/           # Form components & react-hook-form wrappers
│   ├── db/                  # Database layer
│   │   ├── schema/          # Drizzle schema definitions
│   │   ├── migrations/      # Generated migration files
│   │   ├── index.ts         # DB client export
│   │   └── seed.ts          # Seed data
│   ├── lib/                 # Business logic, utilities
│   │   ├── auth.ts          # Auth.js (NextAuth) config
│   │   └── utils.ts         # Shared utilities
│   ├── actions/             # Server Actions (mutation logic)
│   └── styles/              # Global styles, Tailwind config
├── drizzle.config.ts        # Drizzle Kit configuration
├── next.config.ts           # Next.js configuration
├── vitest.config.ts         # Vitest configuration
├── tailwind.config.ts       # Tailwind CSS configuration
├── tsconfig.json            # TypeScript configuration
└── package.json
```

**Key decisions:**
- **Next.js 15 App Router** — All routes use `app/` directory. Pages are Server Components by default; add `"use client"` only when interactivity is needed.
- **SQLite via Drizzle ORM** — Database file at `data/sqlite.db` (gitignored). Schema defined in `src/db/schema/`.
- **Auth.js (NextAuth v5)** — Credentials provider + OAuth. Session stored in SQLite via Drizzle adapter.
- **Server Actions** for mutations; Route Handlers for webhooks & external API consumption.
- **React Hook Form + Zod** for form validation.

## Commands

```bash
npm run dev              # Start dev server (localhost:3000)
npm run build            # Production build
npm start                # Start production server
npm run db:generate      # Generate migration from schema changes
npm run db:migrate       # Apply pending migrations
npm run db:push          # Push schema directly (dev only)
npm run db:studio        # Open Drizzle Studio
npm run db:seed          # Seed the database
npm run lint             # ESLint
npm run format           # Prettier
npm run typecheck        # tsc --noEmit
npm run test             # Vitest (watch mode)
npm run test:run         # Vitest once (CI)
```

## Code Conventions

### TypeScript
- Strict mode enabled. Do not disable.
- Prefer `type` for props, `interface` for public API contracts.
- Avoid `any`. Use `unknown` and narrow with type guards.

### Naming
| Category          | Convention      | Example                 |
|-------------------|----------------|-------------------------|
| Files/Directories | kebab-case     | `user-profile.tsx`      |
| Components        | PascalCase     | `UserProfileCard`       |
| Functions         | camelCase      | `formatCurrency()`      |
| DB Tables         | snake_case     | `user_sessions`         |
| DB Columns        | snake_case     | `created_at`            |
| Env Vars          | UPPER_SNAKE    | `DATABASE_URL`          |

### Components
- One component per file, default export.
- Co-locate tests: `Component.test.tsx`.
- Keep under ~200 lines. Extract logic to hooks or lib/.
- Use `cn()` (clsx + tailwind-merge) for conditional classes.

### Imports Order
1. React / Next.js
2. Third-party libraries
3. Internal modules (@/db, @/lib, @/components)
4. Relative imports (./)
5. CSS / style imports

## Database Conventions

### Schema Design
- Each table gets its own file in `src/db/schema/`.
- Every table MUST have `id` (text, cuid2), `created_at`, `updated_at`.
- Use `text` for foreign keys (not `integer`).
- Define relations in `relations.ts`.
- Index foreign key columns and frequently queried columns.

```typescript
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";
import { createId } from "@paralleldrive/cuid2";

export const projects = sqliteTable("projects", {
  id: text("id").primaryKey().$defaultFn(createId),
  name: text("name").notNull(),
  userId: text("user_id").notNull().references(() => users.id),
  createdAt: integer("created_at", { mode: "timestamp" }).notNull().$defaultFn(() => new Date()),
  updatedAt: integer("updated_at", { mode: "timestamp" }).notNull().$onUpdateFn(() => new Date()),
});
```

### Migrations
- Never edit migration files manually. Regenerate with `db:generate`.
- Use `db:push` only in development. Use `db:migrate` in staging/production.
- Migration files are committed to version control.

## Testing

### Configuration
- Vitest with `@testing-library/react` for component tests.
- Integration tests use in-memory SQLite (`:memory:`).
- Mock external services (Stripe, Resend) with `msw`.

### What to Test
| Type       | Pattern                     | Focus                           |
|------------|-----------------------------|---------------------------------|
| Unit       | `utils.test.ts`             | Pure functions, formatting      |
| Component  | `Button.test.tsx`           | Rendering, interaction, a11y    |
| API Route  | `api/route.test.ts`         | Request/response, auth, errors  |
| Action     | `actions/*.test.ts`         | Mutation logic, permissions     |
| E2E        | `__e2e__/`                  | Critical user flows             |

## API Design

### Route Handlers
- `export async function GET/POST/PUT/DELETE` per file.
- Standard response shape:
```typescript
type ApiResponse<T> =
  | { success: true; data: T }
  | { success: false; error: string; code?: string };
```
- Auth: wrap with `withAuth` helper.
- Pagination: cursor-based (`?cursor=<id>&limit=50`). Default 50, max 200.
- Idempotency: POST mutations accept `Idempotency-Key` header.

### Server Actions
- `"use server"` at file or function level.
- Validate inputs with Zod before DB access.
- Revalidate with `revalidatePath()` / `revalidateTag()` after mutations.

## Deployment

- **Host:** Vercel (recommended) or Fly.io.
- **Production DB:** Turso (libsql) — Drizzle-compatible, edge-ready.
- **Build checks:** `typecheck && lint && test:run` must pass in CI.
- **Migrations on deploy:** Run `db:migrate` as build step.
- **Error monitoring:** Sentry.
- **Analytics:** PostHog or Plausible (self-hosted).

### Environment Variables (production)
```
DATABASE_URL           # libsql URL (Turso)
AUTH_SECRET            # Auth.js encryption secret
AUTH_GITHUB_ID         # GitHub OAuth client ID
AUTH_GITHUB_SECRET     # GitHub OAuth client secret
STRIPE_SECRET_KEY      # Stripe secret key
STRIPE_WEBHOOK_SECRET  # Stripe webhook signing secret
RESEND_API_KEY         # Transactional emails
```

## Git Workflow
- Branch naming: `feat/`, `fix/`, `chore/`, `refactor/` + kebab-case description.
- Commits follow Conventional Commits: `feat:`, `fix:`, `chore:`, `refactor:`, `docs:`, `test:`.
- One PR = one concern. Keep PRs small and focused.
