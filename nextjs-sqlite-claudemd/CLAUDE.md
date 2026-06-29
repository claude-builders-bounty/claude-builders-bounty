# CLAUDE.md — Next.js 15 + SQLite SaaS

Opinionated conventions for a greenfield SaaS using Next.js 15 App Router, SQLite, Drizzle ORM, and server actions.

## Stack

- **Framework:** Next.js 15 (App Router, React Server Components by default)
- **Database:** SQLite via `better-sqlite3` or Turso libSQL
- **ORM:** Drizzle ORM with SQL migrations in `drizzle/`
- **Auth:** Auth.js v5 (`next-auth`) with credentials or OAuth
- **UI:** Tailwind CSS v4, shared components in `components/ui/`
- **Tests:** Vitest (unit), Playwright (e2e)

## Commands

```bash
pnpm dev          # local app
pnpm build        # production build
pnpm test         # vitest
pnpm db:generate  # drizzle-kit generate
pnpm db:migrate   # apply migrations
pnpm db:studio    # drizzle studio
```

## Project structure

```
app/
  (marketing)/     # public pages
  (app)/           # authenticated app shell
  api/             # route handlers only when RSC/actions are insufficient
actions/           # server actions (mutations)
components/        # shared UI
lib/db/            # drizzle client singleton
lib/validators/    # zod schemas shared by actions + forms
drizzle/           # migrations + schema.ts
```

## Naming

- React components: `PascalCase.tsx`
- Server actions: `kebab-case.ts` exporting named async functions
- DB tables/columns: `snake_case`
- Route segments: `kebab-case`

## Database rules

- Enable WAL + foreign keys on SQLite connections.
- One migration per logical change; never edit applied migration files.
- All writes go through server actions or route handlers — never from client components.
- Use transactions for multi-table mutations.

## Server action pattern

```ts
"use server";
import { z } from "zod";
import { db } from "@/lib/db";

const Input = z.object({ email: z.string().email() });

export async function createUser(raw: unknown) {
  const input = Input.parse(raw);
  // db insert...
  return { ok: true as const, data: { id } };
}
```

Return `{ ok: false, error: string }` for expected failures; throw only for unexpected errors.

## Component boundaries

- Default to Server Components.
- Add `"use client"` only for interactivity (forms with instant feedback, hooks, browser APIs).
- Never import `lib/db` from client components.

## What we do not do (and why)

- **No client-side data fetching libraries for mutations** — server actions keep secrets off the client.
- **No raw SQL in components** — Drizzle + shared queries stay in `lib/db/queries/`.
- **No `any` in action inputs** — validate with Zod at every boundary.
- **No force-push to `main`** — use PRs; migrations must be backward compatible within a release.
- **No env secrets in client bundles** — only `NEXT_PUBLIC_*` crosses the boundary.

## Environment variables

| Variable | Scope | Purpose |
|----------|-------|---------|
| `DATABASE_URL` | server | SQLite/Turso connection |
| `AUTH_SECRET` | server | Auth.js encryption |
| `NEXT_PUBLIC_APP_URL` | client | absolute URLs |

## Deployment checklist

- [ ] Run migrations before traffic switch
- [ ] Verify `AUTH_SECRET` and `DATABASE_URL` in prod
- [ ] Run `pnpm build && pnpm test`
- [ ] Confirm RSC routes do not leak server env to client bundles

## Common pitfalls

1. **Calling DB from `"use client"` files** → move logic to a server action.
2. **Editing old migrations** → create a new migration instead.
3. **Mixing marketing + app layouts** → keep route groups separate.
4. **Skipping Zod on form data** → always parse `unknown` at the action boundary.
5. **Using `useEffect` for initial data** → fetch in the Server Component instead.
