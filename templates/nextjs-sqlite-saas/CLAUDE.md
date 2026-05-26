# CLAUDE.md — Next.js 15 + SQLite SaaS (App Router)

You are working on a **multi-tenant B2B SaaS** using **Next.js 15 App Router**, **TypeScript strict**, **Tailwind CSS 4**, **Drizzle ORM**, and **SQLite**.

This file is authoritative. Do not introduce patterns from the Pages Router, Prisma, MongoDB, or REST route handlers for mutations unless explicitly asked.

---

## Stack and versions

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | Next.js 15.x, App Router only | RSC-first, built-in streaming, `app/` conventions |
| Language | TypeScript `strict: true` | Catch data-shape bugs at compile time |
| Styling | Tailwind CSS 4 | Utility-first, no CSS-in-JS runtime |
| Database | SQLite via **Drizzle** | One schema for local file DB and Turso |
| Local dev DB | `better-sqlite3` + file `var/dev.sqlite` | Fast, zero network, full SQL in tests |
| Production DB | Turso (`@libsql/client`) | Edge-compatible, managed backups |
| Validation | Zod 3 | Shared schemas for forms + server actions |
| Auth | Auth.js v5 (NextAuth) | Session in Server Components / actions |
| Package manager | pnpm | Lockfile discipline, workspace-ready |

**Runtime rule:** `better-sqlite3` runs only in **Node.js** route handlers, Server Actions, and scripts — never in Edge middleware or `export const runtime = 'edge'`.

---

## Commands

```bash
pnpm dev              # next dev --turbopack
pnpm build            # production build
pnpm lint             # eslint
pnpm test             # vitest
pnpm db:generate      # drizzle-kit generate
pnpm db:migrate       # drizzle-kit migrate (applies journal)
pnpm db:studio        # drizzle-kit studio
pnpm db:seed          # tsx scripts/seed.ts
```

Environment (`.env.local`, never commit secrets):

- `DATABASE_URL` — `file:./var/dev.sqlite` locally; Turso URL in prod
- `TURSO_AUTH_TOKEN` — production only
- `AUTH_SECRET` — Auth.js
- `NEXT_PUBLIC_APP_URL` — canonical origin for redirects

---

## Folder structure

```
src/
  app/
    (marketing)/          # Public site, no auth
    (app)/                # Authenticated product shell
      layout.tsx          # Loads session, sidebar
      dashboard/
        page.tsx
        loading.tsx
        error.tsx
    api/
      health/route.ts     # GET liveness only
    layout.tsx
    globals.css
  components/
    ui/                   # shadcn primitives (client when needed)
    *.tsx                 # Shared presentational components
  lib/
    db/
      client.ts           # Drizzle singleton (libsql | better-sqlite3)
      schema.ts           # All tables
      migrations/         # Generated SQL — commit to git
    actions/              # Server Actions ("use server" per file)
    auth/
      config.ts
      session.ts          # getSession(), requireUser()
    validators/           # Zod schemas
    utils/
  hooks/                  # Client-only hooks ("use client" files)
scripts/
  seed.ts
drizzle.config.ts
```

**Naming**

- Routes: `kebab-case` folders (`billing-settings/page.tsx`)
- React components: `PascalCase` files exporting one primary component
- Server actions: `verbNoun` (`createProject`, `archiveInvoice`)
- DB tables: `snake_case` plural (`workspace_members`)
- Zod schemas: `camelCase` + suffix `Schema` (`createProjectSchema`)

---

## Database and migrations

1. **Single source of truth:** `src/lib/db/schema.ts` — no raw DDL outside Drizzle migrations.
2. **Generate, don't hand-edit:** After schema changes run `pnpm db:generate`. Commit both `schema.ts` and new files under `src/lib/db/migrations/`.
3. **Never** run `drizzle-kit push` against production; use `migrate` in CI/deploy.
4. **IDs:** `text` primary keys with `crypto.randomUUID()` default — avoids auto-increment leaks across tenants.
5. **Timestamps:** every table has `created_at` / `updated_at` as integer Unix ms or `timestamp` mode — be consistent project-wide.
6. **Tenant isolation:** every tenant-owned row includes `workspace_id` with a foreign key; queries in actions must filter by session workspace unless the row is global.
7. **Local vs prod client** (`src/lib/db/client.ts`):

```ts
// Pseudocode — implement once, import everywhere
import { drizzle } from "drizzle-orm/better-sqlite3"; // dev
import { drizzle as drizzleLibsql } from "drizzle-orm/libsql"; // prod
```

Use `process.env.DATABASE_URL.startsWith("file:")` to pick the driver.

---

## Rendering and data fetching

- **Default:** Server Components. No `useEffect` for initial data.
- **`"use client"`** only for: forms with instant feedback, drag-and-drop, browser APIs, or third-party widgets without RSC support.
- **Fetch in Server Components** with async `page.tsx` / `layout.tsx`. Pass plain serializable props to children.
- **Mutations:** Server Actions in `src/lib/actions/*.ts` — top of file `"use server"`, not inline in components.
- **No** `pages/`, `getServerSideProps`, `getStaticProps`, or API `POST` routes for CRUD that actions can handle.
- **Caching:** prefer `export const dynamic = "force-dynamic"` on authenticated `(app)` routes; do not cache per-user HTML at the CDN.

---

## Component patterns

```tsx
// src/app/(app)/projects/page.tsx — Server Component
import { requireUser } from "@/lib/auth/session";
import { listProjects } from "@/lib/actions/projects";

export default async function ProjectsPage() {
  const user = await requireUser();
  const projects = await listProjects(user.workspaceId);
  return <ProjectList projects={projects} />;
}
```

```ts
// src/lib/actions/projects.ts
"use server";

import { revalidatePath } from "next/cache";
import { requireUser } from "@/lib/auth/session";
import { db } from "@/lib/db/client";
import { createProjectSchema } from "@/lib/validators/project";

export async function createProject(input: unknown) {
  const user = await requireUser();
  const data = createProjectSchema.parse(input);
  // insert with workspace_id = user.workspaceId
  revalidatePath("/projects");
}
```

- Colocate route-specific UI under `app/...`; cross-route UI in `components/`.
- Use `loading.tsx` + `error.tsx` beside `page.tsx` for each slow segment.
- Forms: `<form action={createProject}>` or `useActionState` on client; always re-validate with Zod on the server.

---

## What we do not do (and why)

| Anti-pattern | Why we avoid it |
|--------------|-----------------|
| Pages Router | Conflicts with RSC defaults; doubles routing mental model |
| Prisma / raw SQL strings in components | Drizzle keeps schema typed end-to-end |
| `better-sqlite3` in Edge | Native module; breaks middleware/edge routes |
| API routes for every mutation | Server Actions reduce boilerplate and CSRF surface |
| `any` or `@ts-ignore` | Strict TS is non-negotiable |
| Global client stores for server data | Use RSC + cache revalidation |
| `drizzle-kit push` in prod | Unreviewed schema drift |
| Sharing DB files between dev machines | `var/dev.sqlite` is gitignored; use seed script |

---

## Security checklist (every PR)

- [ ] Session checked in every Server Action (`requireUser`)
- [ ] `workspace_id` enforced on reads/writes
- [ ] Zod parse on all external input
- [ ] No secrets in `NEXT_PUBLIC_*`
- [ ] No logging of tokens or session cookies

---

## When unsure

1. Prefer Server Component + Server Action.
2. Ask one clarifying question only if the choice blocks implementation (auth scope, migration, or tenant model).
3. Match existing files in `src/lib/db/schema.ts` and `src/lib/actions/` before inventing new folders.
