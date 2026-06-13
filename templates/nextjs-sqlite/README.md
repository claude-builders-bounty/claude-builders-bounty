# Next.js 15 + SQLite (better-sqlite3) SaaS Template

An opinionated, production-ready SaaS starter built around Next.js 15 App Router and SQLite via better-sqlite3 + Drizzle ORM.

## Quick Start

```bash
# 1. Create a new Next.js project
npx create-next-app@latest my-saas --typescript --tailwind --eslint --app --src-dir
cd my-saas

# 2. Install dependencies
pnpm add better-sqlite3 drizzle-orm zod
pnpm add -D @types/better-sqlite3 drizzle-kit tsx

# 3. Copy CLAUDE.md into your project root
cp path/to/CLAUDE.md ./CLAUDE.md

# 4. Create the data directory
mkdir -p data

# 5. Add to .gitignore
echo "data/*.db" >> .gitignore
echo "data/*.db-wal" >> .gitignore
echo "data/*.db-shm" >> .gitignore

# 6. Set up the DB singleton + schema + migration runner
# (see CLAUDE.md for the exact code to place in src/lib/db/)
```

## Key Architecture Decisions

| Decision               | Why                                                                 |
|------------------------|---------------------------------------------------------------------|
| Drizzle ORM > Prisma   | 10-50x faster with SQLite, zero-runtime, compiles to raw SQL        |
| Server Actions > API   | No HTTP overhead, no serialization, call DB directly                |
| Synchronous SQLite     | SQLite runs in-process; async adds microtask ticks for zero benefit |
| Append-only migrations | Linear, auditable, reviewable — ad-hoc pushes are not              |
| TEXT UUIDs > INTEGER   | Prevents ID enumeration in a multi-tenant SaaS                      |
| Biome > ESLint+Prettier| Single binary, 10x faster, one config file                          |

## Folder Layout

```
src/
├── app/          # Next.js App Router pages + layouts
├── actions/      # Server Actions (one file per domain)
├── components/   # React components (ui/, forms/, shared/)
├── lib/          # Pure logic (db, auth, validations, utils)
├── hooks/        # Client-side React hooks
└── types/        # Shared TypeScript types
```

## Package Scripts

```bash
pnpm dev              # Migrate + start dev server (Turbopack)
pnpm build            # Build for production
pnpm start            # Start production server
pnpm db:migrate       # Apply pending migrations
pnpm db:seed          # Seed dev data
pnpm db:reset         # Wipe DB, re-migrate, re-seed
pnpm lint             # Biome check
pnpm typecheck        # tsc --noEmit
pnpm test             # Vitest
```

## Deployment

**Use SQLite only if you self-host** (e.g. Railway, Fly.io, Docker VPS). SQLite is a file-based database and **does not work** on Vercel serverless functions (ephemeral filesystem, no shared state).

For serverless deployment, swap `better-sqlite3` for `@libsql/client` (Turso) — the Drizzle queries stay the same.

## Credits

This template was generated from the `claude-builders-bounty` repository's `templates/nextjs-sqlite/CLAUDE.md` — an opinionated CLAUDE.md designed to be copied into any greenfield Next.js + SQLite project.
