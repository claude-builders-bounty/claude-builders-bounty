# CLAUDE.md — Next.js 15 + SQLite SaaS Project

> AI assistant context file for Claude Code / Cursor / Windsurf

## Stack and Versions

| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | Next.js (App Router) | 15.x |
| Language | TypeScript | 5.x |
| Styling | Tailwind CSS | 4.x |
| Database | SQLite (better-sqlite3) | 9.x |
| ORM | Drizzle ORM | 0.x |
| Auth | Auth.js (NextAuth v5) | 5.x |
| Validation | Zod | 3.x |
| Testing | Vitest + Testing Library | latest |
| Deployment | Vercel / Docker | latest |

## Folder Structure

```
project/
├── app/                    # Next.js App Router
│   ├── (auth)/            # Auth group route
│   │   ├── login/
│   │   └── register/
│   ├── (dashboard)/       # Protected group route
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── api/               # API routes
│   │   └── trpc/
│   ├── globals.css        # Tailwind v4: @import "tailwindcss"
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Landing page
├── components/            # Shared React components
│   ├── ui/               # Base UI primitives
│   └── features/         # Feature-specific components
├── lib/                   # Core utilities
│   ├── db.ts             # Database connection
│   ├── schema.ts         # Drizzle schema definitions
│   ├── auth.ts           # Auth.js v5 config (handlers, auth, signIn, signOut)
│   └── validators.ts     # Zod schemas
├── server/               # Server-only code
│   ├── trpc.ts           # tRPC setup
│   └── routers/          # tRPC routers
├── migrations/            # Drizzle migrations
├── public/               # Static assets
├── tests/                # Test files
├── CLAUDE.md             # This file
├── drizzle.config.ts     # Drizzle config
├── middleware.ts          # Auth.js v5 middleware (route protection)
├── next.config.ts        # Next.js 15 TypeScript config
└── tsconfig.json         # TypeScript config
```

## Coding Conventions

### General Rules
- Use TypeScript strict mode — no `any` types
- Prefer `const` over `let`; avoid `var`
- Use named exports; avoid default exports for components
- Keep components under 150 lines; extract sub-components
- Use early returns and guard clauses

### Component Patterns
- Server Components by default; add `"use client"` only when needed
- Use Server Actions (`"use server"`) for mutations instead of API routes where possible
- In Next.js 15, Server Actions are async functions with `"use server"` directive; use `useActionState` (formerly `useFormState`) for form handling with pending states
- Server Actions receive `FormData` or typed arguments; validate inputs with Zod before processing
- Colocate types with components using `interface Props {}`
- Use composition over prop drilling; reach for context sparingly

### Auth.js v5 Conventions
- Configure in `lib/auth.ts` using `NextAuth()` factory: `export const { handlers, auth, signIn, signOut } = NextAuth(config)`
- Route handlers in `app/api/auth/[...nextauth]/route.ts` re-export `handlers` from `lib/auth.ts`
- Middleware in `middleware.ts` uses `auth` export for route protection: `export default auth((req) => { ... })`
- Access session in Server Components via `auth()` (no `"use client"` needed)
- Access session in Client Components via `useSession()` hook from `next-auth/react`
- Next.js 15 async APIs: `auth()` returns a Promise — always `await auth()`
- Edge-compatible by default; avoid Node.js-specific APIs in auth config

### Tailwind CSS v4 Conventions
- No `tailwind.config.js` — v4 uses CSS-native configuration via `@import "tailwindcss"` in `app/globals.css`
- Customize theme with `@theme` directive in CSS: `@theme { --color-primary: #3b82f6; }`
- Use `@variant` for custom variants instead of JavaScript plugins
- Utility classes remain the same; only configuration approach changed
- Third-party plugins use `@plugin` directive instead of JS config

### Naming
- Files: `kebab-case.tsx` for components, `camelCase.ts` for utilities
- Components: PascalCase (`UserAvatar`)
- Hooks: camelCase prefixed with `use` (`useAuth`)
- Database columns: snake_case (`created_at`)
- API endpoints: kebab-case (`/api/user-profile`)

### Import Order
1. React / Next.js
2. Third-party libraries
3. Server-only imports (`@/server/`, `@/lib/db`)
4. Components (`@/components/`)
5. Utilities (`@/lib/`)
6. Types
7. Styles

## SQL / Migration Conventions

### Schema Rules
- Every table has `id` (integer primary key autoincrement), `created_at`, `updated_at`
- Use SQLite-compatible types: integer, text, real
- Foreign keys must have `onDelete` and `onUpdate` actions
- Add indexes for frequently queried columns

### Migration Workflow
```bash
npm run db:generate    # Generate migration from schema changes
npm run db:migrate     # Apply migration
npm run db:studio      # Open Drizzle Studio
```

### Query Patterns
- Always use parameterized queries via Drizzle
- Never construct SQL strings manually
- Use transactions for multi-table operations
- Fetch only needed columns with `.select({ ... })`

### SQLite-Specific Rules
- No `ALTER TABLE DROP COLUMN` (SQLite limitation) — create new table + migrate
- Use `strftime()` for date operations, not `DATE()`
- Enable WAL mode for concurrent reads: `PRAGMA journal_mode=WAL`
- Set busy timeout: `PRAGMA busy_timeout=5000`

## Dev Commands

```bash
npm run dev             # Start dev server on :3000
npm run build           # Production build
npm run start           # Start production server
npm run test            # Run all tests
npm run test:watch      # Run tests in watch mode
npm run test:coverage   # Run tests with coverage
npm run lint            # ESLint check
npm run lint:fix        # ESLint auto-fix
npm run typecheck       # TypeScript type checking
npm run db:generate     # Generate Drizzle migration
npm run db:migrate      # Apply migrations
npm run db:seed         # Seed database
npm run db:studio       # Drizzle Studio GUI
```

## Testing Strategy

### Unit Tests
- Test business logic in `lib/` and `server/routers/`
- Mock database calls with Vitest `vi.mock()`
- Use `describe/it` blocks grouped by feature
- Target 80%+ coverage on business logic

### Integration Tests
- Test API routes with `next/test/server`
- Test database operations with in-memory SQLite
- Verify authentication flows end-to-end

### Component Tests
- Use `@testing-library/react` with `render()`
- Test user interactions, not implementation details
- Prefer `screen.getByRole()` over `getByTestId()`

### E2E Tests
- Playwright for critical user flows
- Test: signup → login → dashboard → CRUD → logout

## Deployment

### Vercel
- Connect GitHub repo → auto-deploy on push
- Set environment variables in Vercel dashboard
- SQLite runs in `/tmp` on Vercel (ephemeral — use Turso for persistence)

### Docker
```bash
docker build -t my-saas .
docker run -p 3000:3000 -v ./data:/app/data my-saas
```
- Mount `/app/data` for persistent SQLite storage
- Use `docker-compose.yml` for local dev with services

## What We Don't Do

| Anti-pattern | Correct approach |
|-------------|-----------------|
| `any` types | Use `unknown` + type narrowing or Zod schemas |
| `SELECT *` | Explicit column selection via Drizzle |
| Client-side DB calls | Always through tRPC API routes |
| `fs` in components | Server Components only for file I/O |
| Hardcoded secrets | Environment variables + `.env.local` |
| `eval()` or `new Function()` | Never — security risk |
| Synchronous DB in API routes | better-sqlite3 is sync; keep API routes thin |
| `tailwind.config.js` | Tailwind v4 uses CSS-native `@theme` in `globals.css` |
| `next.config.js` | Next.js 15 prefers `next.config.ts` (TypeScript) |
| NextAuth v4 `[...nextauth].ts` | Auth.js v5 uses `route.ts` with `handlers` export |

## Architecture Decisions

- **App Router** over Pages Router for nested layouts and server components
- **Next.js 15** with async Request APIs and improved Server Actions as the default mutation pattern
- **Auth.js v5** over NextAuth v4 for native App Router middleware and edge-compatible sessions
- **Drizzle** over Prisma for SQLite performance and type safety
- **tRPC** over REST for type-safe client-server communication
- **Tailwind CSS v4** with CSS-native configuration over v3 JS config
- **Zod** for runtime validation at API boundaries
- **Vitest** over Jest for ESM compatibility and speed
- **SQLite** over Postgres for simplicity; migrate to Turso/LibSQL for scale

## Security Checklist

- [ ] All API routes validate input with Zod
- [ ] Auth required on protected routes via Auth.js middleware
- [ ] CSRF protection via Next.js built-in
- [ ] SQL injection impossible via Drizzle parameterized queries
- [ ] Rate limiting on auth endpoints
- [ ] Environment variables never in client bundles
- [ ] Content Security Policy headers set
- [ ] HTTPS enforced in production
- [ ] Dependencies audited with `npm audit`
