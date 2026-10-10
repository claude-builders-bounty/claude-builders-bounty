# Next.js 15 + SQLite SaaS — CLAUDE.md template ($75 bounty)

Opinionated, production-ready `CLAUDE.md`. Drop it into any greenfield
Next.js 15 App Router + SQLite project with zero edits (fill in the 3
lines in §0 only).

## Use

```bash
# greenfield test (acceptance-criteria verification)
npx create-next-app@15 my-saas --typescript --tailwind --app --no-src-dir
cd my-saas
npm i drizzle-orm better-sqlite3 @libsql/client zod nanoid
npm i -D drizzle-kit tsx vitest @types/better-sqlite3
cp templates/nextjs-sqlite-saas/CLAUDE.md ./CLAUDE.md
mkdir -p app/actions components/ui "components/features" lib/validations db/schema tests
# paste the folder tree from CLAUDE.md §3, then open in Claude Code:
# expected: Claude scaffolds using Server Actions + Drizzle + lib/db.ts
# without asking "which ORM?", "pages or app router?", "where do actions live?"
```

## What it covers (acceptance criteria mapping)

- [x] Project structure → §3 folder tree + dependency-flow rule
- [x] Naming conventions → §4 table (files, components, actions, tables, schemas, tests)
- [x] DB migration rules → §5 (8 hard rules incl. SQLite expansion/contraction, tenant scoping, transactions)
- [x] Dev commands → §2 (`dev/build/lint/typecheck/db:*` + env files)
- [x] Patterns to follow → §6 (RSC fetch, Server Action + Zod + revalidate, forms, errors)
- [x] Anti-patterns → §7 ("What we DON'T do" table, 11 rows, each with reason + replacement)
- [x] Opinionated, every rule has a reason → every row/rule carries a `Why/Reason`
- [x] Expected sections: Stack & versions (§1), Folder structure (§3), SQL/migration conventions (§5), Component patterns (§6), What we don't do (§7)

## Key opinions (so reviewers see it's not generic)

- Drizzle over Prisma for SQLite (engine binary breaks edge/serverless).
- `better-sqlite3` local / Turso `libsql` prod behind one `lib/db.ts` switch.
- Mutations in `app/actions/`, not `api/` routes (except webhooks).
- `middleware.ts` redirects only — never DB (edge has no sqlite file).
- Text PKs + integer-ms timestamps; multi-tenant `user_id` filter is the security boundary (no RLS in SQLite).
- No React Query/SWR for server state; no barrel files except `db/schema/_root.ts`.
