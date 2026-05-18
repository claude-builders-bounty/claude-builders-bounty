# CLAUDE.md — Next.js 15 + SQLite SaaS

This bounty submission addresses issue #2: create an opinionated, production-ready CLAUDE.md for a Next.js 15 App Router + SQLite SaaS project.

## What is this
A single `CLAUDE.md` file that can be dropped into any greenfield Next.js 15 + SQLite project. It gives Claude Code enough context to generate code that matches our conventions without asking clarifying questions.

## Tested on
A fresh Next.js 15 project (`npx create-next-app@latest --typescript --tailwind --eslint --app --src-dir --no-turbopack`). Claude Code read this CLAUDE.md and generated:
- Folder structure matching the spec
- `lib/db/schema.sql` with `_migrations` tracking
- `scripts/migrate.ts` runner
- Server Action `createPost` with Zod validation
- `app/(dashboard)/posts/page.tsx` fetching posts via Server Component

All without follow-up questions.

## Key opinions (and why)
| Rule | Reason |
|------|--------|
| Raw SQL, no ORM | SQLite is simple. ORMs add abstraction without benefit. |
| Server Components default | Less client JS, faster pages. |
| Lucia not NextAuth | Edge-compatible, simpler session model. |
| No `any` | `noUncheckedIndexedAccess` catches bugs at build time. |
| Soft-delete only | Prevents accidental data loss, audit trail for free. |
| Suspense + `loading.tsx` | Route-level loading is cleaner than scattered skeletons. |

## File
- `CLAUDE.md` — the complete spec (≈200 lines)
