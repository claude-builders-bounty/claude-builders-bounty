# SaaS Starter — Next.js 15 + SQLite

A production-ready SaaS starter with **Next.js 15** (App Router), **SQLite** via Drizzle ORM, authentication, and billing scaffolding. Opinionated. Zero-guesswork. Greenfield-friendly.

## 3-Step Setup

```bash
# 1. Clone and install
git clone <repo-url> my-saas && cd my-saas
pnpm install

# 2. Configure environment and bootstrap the database
cp .env.example .env.local
pnpm db:push && pnpm db:seed

# 3. Start developing
pnpm dev
```

Open [localhost:3000](http://localhost:3000). Sign in with the seeded demo account (see `.env.local` or seed output).

## Quick Reference

| Command | Purpose |
|---|---|
| `pnpm dev` | Start dev server |
| `pnpm db:generate` | Generate a migration |
| `pnpm db:migrate` | Apply migrations |
| `pnpm db:seed` | Seed demo data |
| `pnpm build` | Production build |
| `pnpm test` | Run unit/integration tests |

## What's Inside

- **Next.js 15** with React Server Components by default
- **SQLite** — single-file database, zero infrastructure
- **Drizzle ORM** — type-safe queries, auto-generated migrations
- **Authentication** — session-based (Lucia / NextAuth)
- **Validation** — Zod schemas shared between server and client
- **UI** — shadcn/ui components, Tailwind CSS
- **Secure by default** — NOT NULL timestamps, UUID v7 primary keys, soft deletes

## Docs

Full conventions, patterns, and anti-patterns are documented in **[CLAUDE.md](./CLAUDE.md)** — read it before writing any code.

## License

MIT
