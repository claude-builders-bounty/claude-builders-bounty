\# CLAUDE.md



Opinionated context guide for Claude Code tailored for a Next.js 15 App Router + SQLite SaaS stack.



\---



\## Stack \& Versions

\* \*\*Framework\*\*: Next.js 15 (App Router, React 19)

\* \*\*Language\*\*: TypeScript (strict mode, standard types)

\* \*\*Database\*\*: SQLite via `better-sqlite3` (local/dev) or `@libsql/client` (Turso edge setup)

\* \*\*ORM / Query Builder\*\*: Drizzle ORM

\* \*\*Styling\*\*: Tailwind CSS v4, `shadcn/ui` (Radix primitives)

\* \*\*State \& Forms\*\*: React Hook Form, Zod (schema validation), React Server Actions



\---



\## Development Commands

```bash

\# Development

pnpm dev              # Start local dev server with Turbopack

pnpm build            # Production build

pnpm start            # Run production build



\# Quality \& Verification

pnpm lint             # Run ESLint

pnpm typecheck        # Run TypeScript type check (tsc --noEmit)

pnpm test             # Run Vitest suite



\# Database Ops (Drizzle)

pnpm db:generate      # Generate SQL migrations from schema

pnpm db:migrate       # Apply pending migrations to SQLite DB

pnpm db:studio        # Open Drizzle Studio UI

