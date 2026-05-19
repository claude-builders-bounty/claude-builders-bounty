# CLAUDE.md — Next.js 15 + SQLite SaaS Project

## Stack & Versions
- **Framework**: Next.js 15 (App Router) — *Rationale: Stability, improved performance, and native support for React Server Components.*
- **Runtime**: Node.js 20+ — *Rationale: LTS version ensuring compatibility with modern dependencies.*
- **Database**: SQLite (via `better-sqlite3` for local, `Turso` for production) — *Rationale: Low latency, easy local development, and seamless scaling to the edge with Turso.*
- **ORM**: Drizzle ORM — *Rationale: Type-safe, lightweight, and specifically optimized for SQLite with a "SQL-like" feel.*
- **Styling**: Tailwind CSS — *Rationale: Rapid UI development and consistent design system through utility classes.*
- **Auth**: NextAuth.js or Clerk — *Rationale: Industry-standard security and ease of integration for SaaS.*

## Build & Dev Commands
- `npm run dev`: Start development server
- `npm run build`: Build production application
- `npm run lint`: Run ESLint checks
- `npm run db:push`: Push schema changes to SQLite (Drizzle)
- `npm run db:generate`: Generate migration files
- `npm run db:migrate`: Apply migrations to production
- `npm run db:studio`: Open Drizzle Studio for DB exploration

## Project Structure
- `app/`: Next.js App Router (Routes, Layouts, Server Actions) — *Rationale: Centralized routing and server-first architecture.*
- `components/`:
  - `ui/`: Base components (shadcn/ui pattern) — *Rationale: Separation of reusable primitives from domain logic.*
  - `features/`: Complex, domain-specific components — *Rationale: Encourages modularity and prevents component bloat.*
- `lib/`:
  - `db/`: Database client and schema definitions — *Rationale: Single source of truth for persistence logic.*
  - `actions/`: Shared Server Actions — *Rationale: Reusability across different routes.*
  - `utils.ts`: General helper functions
- `public/`: Static assets
- `styles/`: Global CSS

## Coding Standards
- **Naming**: 
  - Components: `PascalCase.tsx` — *Rationale: Standard React convention for easy identification.*
  - Logic/Hooks: `camelCase.ts` — *Rationale: Standard JavaScript convention.*
  - DB Tables: `snake_case` — *Rationale: SQL convention compatibility.*
- **TypeScript**: Strict mode enabled. No `any`. Use `zod` for runtime validation. — *Rationale: Maximizes type safety and prevents runtime errors.*
- **Server Components**: Default to Server Components. — *Rationale: Reduces client-side bundle size and improves SEO/Initial load.*
- **Data Fetching**: Use Server Components and direct DB calls. — *Rationale: Eliminates the need for internal API routes for same-project data access.*
- **State Management**: Prefer URL state (searchParams) for filters. — *Rationale: Ensures state is shareable and persistent across reloads.*

## SQL & Migration Conventions
- **Schema**: Define in `lib/db/schema.ts`. — *Rationale: Centralized type-safe schema definition.*
- **Migrations**: Use Drizzle Kit for automated migration generation. — *Rationale: Ensures database schema is always in sync with code.*
- **Local DB**: File stored at `db.sqlite` (gitignored). — *Rationale: Fast, file-based local development.*
- **Safety**: Always use parameterized queries. — *Rationale: Essential for preventing SQL injection (Drizzle handles this by default).*

## Anti-Patterns (What we don't do)
- **No manual SQL strings**: Use the ORM's query builder. — *Rationale: Guarantees type safety and prevents injection.*
- **No client-side DB access**: All database logic must reside in Server Components or Actions. — *Rationale: Prevents leaking database credentials and improves security.*
- **No barrels (index.ts)**: Prefer direct imports. — *Rationale: Improves tree-shaking and avoids circular dependencies in complex projects.*
- **No `any`**: Use `unknown` and a type guard if type is truly unknown. — *Rationale: Maintains the integrity of the type system.*

## Component Patterns
- Use **Server Actions** for all mutations. — *Rationale: Simplified form handling and automatic revalidation.*
- **Form Handling**: Use `react-hook-form` with `zod`. — *Rationale: Best-in-class validation and UX.*
- **Icons**: Use `lucide-react` exclusively. — *Rationale: Consistent iconography and tree-shakable assets.*
- **UI Components**: Use shadcn/ui. — *Rationale: Accessible, customizable, and widely adopted.*
- Wrap complex components in `ErrorBoundary` and `Suspense`. — *Rationale: Enhances resilience and provides better loading states.*

## Production & Security
- **Deployment**: Vercel (Frontend) + Turso (Database).
- **Environment Variables**: Use `.env.local` for development and Vercel dashboard for production. Never commit `.env` files.
- **Rate Limiting**: Implement at the Middleware layer for API routes and Server Actions.
- **CSP**: Strict Content Security Policy defined in `next.config.js`.
