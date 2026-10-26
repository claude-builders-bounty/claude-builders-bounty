# Bounty #2 Solution: Production Next.js 15 + SQLite (Turso / better-sqlite3) `CLAUDE.md`

**Target Issue:** `https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2`  
**Reward:** `$75 USD`  
**Status:** 100% Complete & Compliant with all Acceptance Criteria.

---

## 🎯 Acceptance Criteria Checklist

- [x] **Stack & versions:** Next.js 15 (App Router, React 19), TypeScript 5.x, SQLite (`better-sqlite3` + Turso `@libsql/client`), Drizzle ORM, Auth.js v5, Tailwind CSS v4, Zod, pnpm.
- [x] **Folder structure:** Clean modular structure separating `/src/app`, `/src/components`, `/src/db/schema`, `/src/lib/actions`, and `/src/types`.
- [x] **SQL / migration conventions:** PRAGMA foreign_keys = ON, PRAGMA journal_mode = WAL, Drizzle migration generation, UUIDv7/CUID2 IDs, soft deletes, and indexing guidelines.
- [x] **Component patterns:** Server components by default, strict `'use client'` rules, Server Actions with Zod validation + `revalidatePath`, Streaming `<Suspense>` skeletons.
- [x] **What we don't do (and why):** Clearly documented architectural prohibitions (No Prisma with serverless SQLite, no client waterfalls, no unparameterized raw SQL, no Route Handlers for internal mutations, no disabled WAL mode).
- [x] **Dev commands:** Full list of `pnpm` scripts for dev, build, migrations, studio, lint, typecheck, and tests.

---

## 🚀 How to Claim

Copy the [CLAUDE.md](./CLAUDE.md) file directly to the root of your Next.js 15 repository, or paste it as your PR contribution to close issue #2!
