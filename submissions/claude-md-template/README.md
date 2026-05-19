# CLAUDE.md — Next.js 15 + SQLite SaaS Template

Production-ready, opinionated `CLAUDE.md` for greenfield SaaS projects.

## Quick Start (3 steps)

1. Copy `CLAUDE.md` to your Next.js project root
2. Run `npx create-next-app@latest my-saas --typescript --tailwind --app`
3. Claude Code now understands your stack, conventions, and anti-patterns without clarification

## What's Covered

- **Stack decisions** — Turso over better-sqlite3 (edge-compatible), Drizzle over Prisma (lighter), NextAuth v5 over v4 (App Router native)
- **Folder structure** — Feature-based organization with rationale for every directory
- **SQL conventions** — snake_case, timestamp columns, transaction patterns, indexing rules
- **Component patterns** — Server Components by default, minimal client boundaries, form validation with Zod
- **Anti-patterns** — `useEffect` for data fetching, `any` without comment, `export default` in utils, mixing Server Actions with lib

## Design Philosophy

Every rule has a **why**. This isn't a style preference document — it encodes production lessons:

- Webhook routes need raw body → don't nest under feature routes
- Drizzle needs `schema.ts` as single source of truth → don't split across files
- Server Actions = RPC layer, `lib/` = infrastructure → don't mix them (circular imports)
