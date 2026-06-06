# Next.js 15 + SQLite SaaS CLAUDE.md (bounty #2)
Stack: Next.js 15 App Router, Drizzle, better-sqlite3/Turso, Auth.js.
Structure: `src/app/(app)/[tenantSlug]`, `src/db/migrations`, `src/lib/db.ts`.
Rules: tenant_id on all tables; server components default; migrations forward-only.
