# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack (pin these versions)

- Next.js 15 (App Router) + React 19 (Server Components by default)
- TypeScript 5.6, strict mode ON
- better-sqlite3 (local) / @libsql/client (Turso) — one code path via `lib/db.ts`
- Tailwind CSS 4 + shadcn/ui (Radix primitives only, no component library churn)
- Auth.js v5 (credentials or OAuth, sessions in DB)
- Zod for every external boundary (forms, API handlers, webhooks)

Rule: never rely on implicit versions. If you touch library code, read the
installed package's types in `node_modules` before assuming an API exists.

## Folder structure

```
app/
  (marketing)/            # public routes, no auth layout
  (app)/                  # authenticated routes, layout checks session
    [workspace]/          # every resource is workspace-scoped
      page.tsx
  api/
    <resource>/route.ts   # thin handlers: parse → call service → respond
components/
  ui/                     # shadcn primitives (generated, do not hand-edit)
  <feature>/              # composed feature components
lib/
  db.ts                   # single DB entry point — no other file imports better-sqlite3
  migrations/             # NNN_name.sql, append-only
  services/               # all business logic lives here, not in route handlers or components
server/
  auth.ts                 # Auth.js config
  actions/                # 'use server' actions: validate (zod) → service → revalidate
```

Rule: if you need DB access outside `lib/services/`, stop. The rule exists so
SQL lives in one reviewable place.

## SQL & migration conventions

1. One migration file per change: `009_add_invites.sql`. Append-only — never
   edit a merged migration. Fix forward with a new file.
2. Every migration must be reversible in prose: add a `-- DOWN:` comment
   explaining the rollback, even if we don't automate it.
3. Every foreign key is `REFERENCES table(id) ON DELETE CASCADE`. Soft deletes
   need an explicit reason in the migration comment.
4. Every tenant-scoped table has `workspace_id TEXT NOT NULL` and an index on
   `(workspace_id, ...)` for the columns you filter by. Every query filters by
   `workspace_id` — a missing predicate is a bug, not a style issue.
5. Timestamps: `created_at TEXT NOT NULL DEFAULT (datetime('now'))` stored UTC.
   Format in the UI layer only. Never store local time.
6. Transactions: wrap multi-table writes in `db.transaction(...)`. If you're
   writing two tables and not in a transaction, say why.
7. `better-sqlite3` is synchronous by design. No `async` wrappers, no pool.

## Component patterns

1. Server Components by default. Add `'use client'` only for: event handlers,
   hooks, browser APIs. If a component only renders data, it stays a server
   component even if its parent is a client component (pass as children).
2. Data fetching: fetch in the server component or route handler. No
   `useEffect` + `fetch` for initial data — that's a client-side waterfall.
3. Forms: `useActionState` + server action + `useFormStatus`. Validate with the
   same Zod schema on both sides (`lib/schemas/`).
4. Revalidation: after any mutation, call `revalidatePath`/`revalidateTag` in
   the server action. Cache tags: `workspace-${id}`.
5. No prop drilling more than 2 levels. Use a typed context or restructure.
6. Server-only modules: `import 'server-only'` at the top of anything touching
   secrets or the DB.

## What we do NOT do (and why)

- **No ORM unless told.** Raw SQL through `lib/db.ts` keeps type control and
  avoids N+1 surprises. Migrations stay readable.
- **No default exports in components.** Named exports make refactors and
  codemods reliable.
- **No `any`.** Unknown you can pass to `z.parse`; `any` silences the compiler
  and hides the bug.
- **No client-side fetching for first paint.** Use RSC or route handlers;
  SWR/TanStack only for polling/optimistic UI.
- **No CSS-in-JS, no styled-components.** Tailwind classes only.
- **No barrel files (`index.ts` re-exports) except for `components/ui`.**
  They bloat bundles and create circular imports.
- **No secrets in `NEXT_PUBLIC_*`.** Anything `NEXT_PUBLIC_` is public.
  Server secrets stay in env vars read only through `lib/env.ts`.
- **No `git push --force` to shared branches.** History is a review artifact.
- **No skipping `workspace_id` in queries.** Mass-assignment and IDOR come
  from exactly this shortcut.

## Dev commands

```bash
pnpm dev            # next dev
pnpm build          # prisma-less build; fails on type errors
pnpm db:migrate     # apply migrations in lib/migrations
pnpm db:reset       # drop + re-migrate + seed (local only)
pnpm test           # vitest unit/integration
pnpm test:e2e       # playwright
pnpm lint           # eslint --max-warnings 0
```

## Review checklist before you call a task done

- [ ] `pnpm lint` and `pnpm build` pass
- [ ] New tables have `workspace_id` + index + FK with cascade policy
- [ ] Migrations are append-only and numbered
- [ ] Every user input passes through Zod
- [ ] Mutations revalidate explicitly
- [ ] Tests added for the service layer, not the UI
