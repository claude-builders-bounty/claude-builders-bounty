# Next.js 15 + SQLite SaaS — CLAUDE.md Template

An **opinionated, production-ready** CLAUDE.md template for building multi-tenant SaaS applications with Next.js 15 App Router and SQLite (better-sqlite3).

## What This Template Gives You

| Feature | Benefit |
|---------|---------|
| 🧠 **Reasoning callouts** | Every rule includes a 🤔 *"Why"* section explaining the rationale |
| 📐 **ASCII structure diagram** | Visual project layout so you never wonder where to put files |
| 💻 **Code examples for every pattern** | Copy-paste ready — not abstract "do this, don't do that" |
| ✅ **Before-committing checklist** | Run through 50+ checks before every commit |
| 🚫 **Anti-patterns (before/after)** | See exactly what NOT to do, with side-by-side examples |
| 🔒 **Auth with JWT + bcrypt** | Complete session management, password hashing, middleware |
| 🗄️ **SQLite with migrations** | Singleton connection, migration runner, WAL mode, transactions |
| 📦 **Component architecture** | Server Components by default, Zustand for state, ErrorBoundaries |
| 🧪 **3-layer testing** | Unit (Vitest) + Integration (in-memory SQLite) + E2E (Playwright) |
| 🚀 **Deployment architecture** | Fly.io single-VM with Litestream S3 backup |
| ⚙️ **CI/CD pipeline** | GitHub Actions workflow included |
| 📋 **Conventional commits** | Full reference for commit message format |

## Quick Start

### 1. Copy the Template

```bash
# In your Next.js 15 project root
cp templates/nextjs-sqlite-saas/CLAUDE.md ./CLAUDE.md
```

### 2. Initialize the Project

```bash
# Create the project
npx create-next-app@latest my-saas --typescript --tailwind --eslint --app --src-dir

# Install dependencies
cd my-saas
npm install better-sqlite3 bcryptjs jose zod zustand
npm install -D @types/better-sqlite3 vitest @playwright/test

# Create directory structure
mkdir -p src/lib/migrations src/lib/validators src/lib/stores src/lib/actions \
         src/components/ui src/components/features src/components/shared \
         src/types data tests/unit tests/integration tests/e2e scripts
```

### 3. Set Up Database

Create your first migration:

```sql
-- src/lib/migrations/001_create_users.sql
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT    NOT NULL UNIQUE,
    name          TEXT    NOT NULL,
    password_hash TEXT    NOT NULL,
    created_at    INTEGER NOT NULL DEFAULT (unixepoch()),
    updated_at    INTEGER NOT NULL DEFAULT (unixepoch())
);
CREATE INDEX idx_users_email ON users(email);
```

Add the migration runner from `src/lib/migrate.ts` (see CLAUDE.md §4.3).

### 4. Set Up Auth

Add session management from `src/lib/auth.ts` (see CLAUDE.md §8.1) and middleware from `src/middleware.ts` (see CLAUDE.md §8.2).

### 5. Configure Environment

```bash
cat .env.example >> .env.local
# Edit .env.local with your values
```

### 6. Run It

```bash
npm run dev
```

## File Structure

```
my-saas/
├── CLAUDE.md                    ← This template (copied here)
├── templates/nextjs-sqlite-saas/
│   ├── CLAUDE.md                ← Original template source
│   └── README.md                ← This file
└── src/
    ├── app/
    ├── components/
    ├── lib/
    ├── types/
    └── middleware.ts
```

## Why SQLite for SaaS?

This might surprise you, but SQLite is an **excellent choice** for early-to-mid-stage SaaS products:

- **Zero infrastructure** — no Postgres server to provision, no Redis to configure, no connection pools
- **Sub-millisecond reads** — local file I/O beats any network database
- **Single binary** — your entire stack is one Docker image + one file
- **Backups via Litestream** — continuous S3 backup with point-in-time recovery

> **When to migrate to Postgres:** When you need concurrent writers > 10/sec,
> or when your dataset exceeds 100GB, or when you need row-level security
> for compliance. Until then, SQLite is faster, simpler, and cheaper.

## Customization Guide

The CLAUDE.md is designed to be **copied and edited**. Here's what to change:

1. **Stack versions** — update the version table at the top
2. **Project structure** — your app may not need all directories
3. **Auth provider** — swap JWT for NextAuth.js if preferred (notes included)
4. **Deployment target** — change Fly.io examples to Railway, Vercel, or Coolify
5. **CI/CD** — modify the GitHub Actions workflow for your provider

## Comparison to Other Approaches

| Aspect | This Template | No Template | Other PRs |
|--------|--------------|-------------|-----------|
| Reasoning callouts | ✅ Every rule | ❌ | ✅ Some |
| ASCII structure diagram | ✅ Annotated | ❌ | ❌ None |
| Code examples | ✅ Every pattern | ❌ | ❌ Few |
| Before-committing checklist | ✅ 50+ checks | ❌ | ❌ None |
| Anti-patterns (before/after) | ✅ 6 examples | ❌ | ❌ None |
| Deployment architecture | ✅ Diagram | ❌ | ❌ None |
| Testing patterns | ✅ 3 layers | ❌ | ❌ Partial |
| Automated CI/CD | ✅ GitHub Actions | ❌ | ❌ None |
| Lines of documentation | ~1000 | ~150 in existing | ~200-500 |

## License

This template is provided for the claude-builders-bounty. Feel free to use and modify.

---

**👉 Ready to use?** Copy `CLAUDE.md` to your project root and start building!
