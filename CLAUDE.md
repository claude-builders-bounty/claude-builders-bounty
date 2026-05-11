# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack & Versions
- **Next.js 15 App Router** (React 19, TypeScript strict)
- **SQLite** via `better-sqlite3` (local dev / single-server) or `@libsql/client` (Turso for edge)
- **Auth:** lucia-auth v4 or NextAuth v5 with SQLite adapter
- **Styling:** Tailwind CSS v4
- **ORM:** Drizzle ORM (preferred) or raw SQL via better-sqlite3 prepared statements
- **Validation:** Zod
- **Testing:** Vitest + React Testing Library
- **Linting:** Biome (formatter + linter, replaces ESLint + Prettier)

## Project Structure
```
src/
  app/                 # App Router — routes are the file-system
    (auth)/            # Auth route group — login, signup, reset
    (dashboard)/       # Protected route group
    api/               # Route handlers
  components/
    ui/                # Primitive components (Button, Input, Modal)
    forms/             # Form components with Zod + server actions
    layouts/           # Layout components (Sidebar, Header)
  lib/
    db/
      schema.ts        # Drizzle schema definitions
      index.ts         # Database client singleton
    auth.ts            # Auth configuration
    utils.ts           # Shared utilities
  server/
    actions/           # Server actions (organized by domain)
    queries/           # Database queries (never in components)
  types/               # Shared TypeScript types
```

### Rules
- Server actions go in `src/server/actions/<domain>.ts`, never inline in components
- Database queries go in `src/server/queries/<domain>.ts`, imported by server actions
- `"use server"` only in server action files, never in component files
- Route handlers in `src/app/api/` return `NextResponse` — no magic strings

## Database Conventions

### Migrations
- Use Drizzle Kit: `npx drizzle-kit generate` → `npx drizzle-kit migrate`
- Never edit migration files manually
- Every schema change gets its own migration
- Run migrations in a transaction — if one fails, rollback

### Schema Rules
- All tables get `id TEXT PRIMARY KEY DEFAULT (uuid())`
- All tables get `created_at TEXT DEFAULT (datetime('now'))` and `updated_at TEXT DEFAULT (datetime('now'))`
- Use TEXT for all dates (ISO 8601), never INTEGER timestamps
- Foreign keys ON by default: `PRAGMA foreign_keys = ON` in connection setup
- Index every column used in WHERE clauses — SQLite is fast but needs indexes
- Never use `SELECT *` — list columns explicitly

### Query Pattern
```typescript
// Always paramaterize — never string interpolation
const rows = db.prepare('SELECT id, email FROM users WHERE email = ?').all(email);
```

## Component Patterns

### Server vs Client
- Default to Server Components — only add `"use client"` when you need hooks, state, or event handlers
- Pass data from server to client via props, not fetch
- Client components go in `src/components/` with a `.client.tsx` suffix if ambiguous

### Data Fetching
- Fetch data in the page/layout, pass down as props
- Use React `cache()` for deduping database calls per request
- Never await a query inside a component render — extract to a helper

### Forms
- Use server actions with Zod validation:
```typescript
const schema = z.object({ email: z.string().email() });
export async function submit(formData: FormData) {
  const parsed = schema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) return { error: parsed.error.flatten() };
  // persist...
  revalidatePath('/dashboard');
}
```
- Always return typed responses from server actions, never throw in production

## Dev Commands
```bash
npm run dev          # Next.js dev server
npm run build        # Production build
npm run lint         # Biome check
npm run lint:fix     # Biome fix
npm run test         # Vitest
npm run db:generate  # Generate Drizzle migrations
npm run db:migrate   # Apply pending migrations
npm run db:studio    # Drizzle Studio UI
```

## Patterns to Follow
- **Optimistic updates** — Update UI before server confirms, rollback on error
- **Error boundaries** — Wrap data-dependent sections, not the whole page
- **Suspense** — Wrap async components, provide meaningful fallbacks
- **revalidatePath** — Call inside server actions after mutations, never in GET handlers
- **CUID2 or UUIDv7** for primary keys — never auto-increment integers for user-facing IDs
- **Rate limiting** — Apply to auth routes and API endpoints via `@upstash/ratelimit` or middleware

## Anti-Patterns
- **Never** put database credentials in client code — all db access through server actions or route handlers
- **Never** use `any` — TypeScript strict mode is on, `unknown` + type guards instead
- **Never** store plaintext passwords — bcrypt via `bcryptjs` with salt rounds >= 12
- **Never** skip Zod validation because "the form already validates" — server actions must validate independently
- **Never** call the database from a Client Component — pass data as props or use a route handler
- **Never** use `useEffect` for data fetching — Next.js Server Components handle this
- **Never** commit `.env` files — use `.env.example` with dummy values
- **Never** use `localhost` URLs in production — use environment variables

## Testing
- Unit tests for utilities and server actions: `Vitest`
- Component tests for interactive UI: `@testing-library/react`
- Database tests: in-memory SQLite via `better-sqlite3` with `:memory:`
- E2E: Playwright targeting the dev server
- Test file naming: `*.test.ts` for unit, `*.spec.tsx` for component

## Deployment
- Target: Vercel (default) or Docker with persistent volume for SQLite
- If Turso/libsql: set `DATABASE_URL` and `DATABASE_AUTH_TOKEN` env vars
- If better-sqlite3: volume mount `/data` and set `DATABASE_PATH=/data/app.db`
- Build command: `npm run build` (runs `next build` + type checking)
- Start command: `npm start`
