# CLAUDE.md Template — Next.js + SQLite SaaS

A production-ready `CLAUDE.md` template for greenfield SaaS projects built with **Next.js 15 App Router** and **SQLite** (Turso / better-sqlite3).

Drop it into any new project and Claude Code will understand your stack, conventions, and patterns from the first message.

---

## What's Inside

| Section | Covers |
|---------|--------|
| Stack & Versions | Pinned dependency choices with rationale |
| Folder Structure | App Router route groups, component organization, DB layout |
| Coding Standards | TypeScript rules, React patterns, API design, Server Actions |
| Database Conventions | Drizzle schema patterns, migration workflow, query guidelines |
| Testing Strategy | Unit / integration / E2E with specific tools and commands |
| Deployment | Env vars, CI pipeline, Vercel + Turso production setup |
| Common Commands | Copy-paste dev, DB, lint, test commands |
| Error Handling | Server Action, API route, and client error boundary patterns |
| Anti-patterns | What we never do — and why |

---

## Usage

### Option 1: Copy into a new project

```bash
# Create your Next.js project
pnpm create next-app@latest my-saas --typescript --tailwind --app --src-dir

# Copy the template
cp CLAUDE.md my-saas/

# Start Claude Code
cd my-saas && claude
```

### Option 2: Use as a reference

Browse `CLAUDE.md` and adapt sections to your own stack. The template is opinionated — change what doesn't fit your project:

- **Switch ORM?** Replace Drizzle section with Prisma/Kysely equivalents
- **Different auth?** Swap NextAuth for Clerk/Lucia patterns
- **Postgres instead of SQLite?** Update DB conventions (connection pooling, migrations)

---

## Dependencies

The template assumes these packages (install as needed):

```bash
# Core
pnpm add next@15 react@19 typescript@5

# Database
pnpm add drizzle-orm @paralleldrive/cuid2
pnpm add -D drizzle-kit better-sqlite3    # local dev
# or: pnpm add @libsql/client             # Turso in prod

# Auth
pnpm add next-auth@beta

# Validation
pnpm add zod

# UI
pnpm add tailwindcss @radix-ui/react-* class-variance-authority clsx tailwind-merge

# Testing
pnpm add -D vitest @testing-library/react @testing-library/jest-dom

# Dev tools
pnpm add -D eslint prettier lefthook
```

---

## Customization Guide

### If you're using Prisma instead of Drizzle

Replace the Schema/Migrations sections with:

```prisma
// prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "sqlite"
  url      = env("DATABASE_URL")
}
```

And update commands: `pnpm prisma migrate dev` / `pnpm prisma studio`.

### If you're using Clerk instead of NextAuth

Replace auth checks with Clerk's `auth()`:

```typescript
import { auth } from '@clerk/nextjs/server'
const { userId } = await auth()
```

### If you need Postgres in production

Keep SQLite for local dev (faster iteration), use Postgres via Vercel Postgres or Neon in prod. Update `DATABASE_URL` and driver accordingly.

---

## Design Decisions

Every rule in the template has a reason. Here are the big ones:

1. **CUID2 over UUID** — shorter, URL-safe, DB-index-friendly. No UUID v7 needed.
2. **Drizzle over Prisma** — lighter, SQL-like, no codegen step. Better for SQLite.
3. **Server Components default** — less JS shipped, faster TTFB, simpler mental model.
4. **Named exports only** — `grep` finds everything, refactoring doesn't break imports.
5. **No barrel files** — explicit imports > implicit re-exports. Fewer circular deps.
6. **Zod at every boundary** — trust nothing. Validate input at API/form/action entry points.
7. **pnpm over npm** — strict mode prevents phantom deps, faster installs, better monorepo support.

---

## License

MIT — use it however you want. If it helps, ⭐ the repo.
