# CLAUDE.md - Next.js 15 + SQLite SaaS

This project is a greenfield SaaS application using Next.js 15 App Router, React 19, TypeScript strict mode, SQLite, Zod, and Tailwind CSS.

## Stack And Versions

- Next.js 15 App Router only. Reason: route groups, Server Components, Server Actions, and Route Handlers are the architectural baseline.
- React 19. Reason: match the Next.js 15 runtime and avoid legacy Pages Router assumptions.
- TypeScript strict mode. Reason: database rows, form input, and payment/auth state must be explicit.
- SQLite through `better-sqlite3` for local deployments or Turso/libSQL for hosted deployments. Reason: SQLite keeps early SaaS complexity low while still supporting real transactional workflows.
- Drizzle ORM for schema and migrations. Reason: it keeps SQL visible and typed without hiding migrations behind a heavy client.
- Zod at every external boundary. Reason: browser input, webhooks, and URL params are untrusted.
- Tailwind plus small feature components. Reason: keep UI changes local and avoid global CSS drift.

## Folder Structure

```text
app/
  (marketing)/
  (auth)/
  (dashboard)/
  api/
components/
  ui/
  forms/
  features/
server/
  actions/
  queries/
  services/
lib/
  db/
    schema.ts
    client.ts
    migrations/
  auth/
  env.ts
  validation/
tests/
  unit/
  integration/
```

Rules:

- Pages and layouts stay in `app/`. Reason: route ownership should follow URL structure.
- Business logic goes in `server/services/`. Reason: components render; services decide.
- Server Actions go in `server/actions/` and call services. Reason: actions are transport glue, not the business layer.
- Database reads go through `server/queries/`. Reason: read paths stay reusable across pages, actions, and tests.
- Database schema and migrations live only under `lib/db/`. Reason: one source of truth for persistence.

## Naming Conventions

- Route folders use kebab-case: `billing-settings`.
- Components use PascalCase: `InvoiceTable.tsx`.
- Server actions use verb-object names: `createInvoice`, `archiveWorkspace`.
- Database tables use snake_case plural names: `workspace_members`.
- Database columns use snake_case: `created_at`.
- TypeScript values use camelCase: `createdAt`.

Reason: predictable naming lets Claude infer intent from file paths and prevents mixed casing between SQL and TypeScript.

## SQL And Migration Rules

- Never hand-edit an applied migration. Reason: migration history must be replayable.
- Generate migrations after changing `schema.ts`, then review the SQL before applying it. Reason: generated SQL can still be destructive.
- Every user-owned table has `id`, `created_at`, `updated_at`, and nullable `deleted_at`. Reason: auditability and reversible deletion are default product requirements.
- Every foreign key explicitly states `onDelete`. Reason: silent cascade behavior is unacceptable.
- Use transactions for multi-table writes. Reason: SaaS workflows often update membership, billing, and audit rows together.
- Do not interpolate SQL strings. Use Drizzle builders or parameterized statements. Reason: SQL injection prevention belongs in the data layer.
- Prefer keyset pagination over `OFFSET`. Reason: offset pagination degrades as tables grow.

Migration workflow:

```bash
npm run db:generate
npm run db:migrate
npm run db:studio
```

## Component Patterns

- Server Components by default. Reason: they reduce client JavaScript and can read server data directly.
- Add `"use client"` only for browser state, event handlers, or browser APIs. Reason: client boundaries are expensive.
- Forms use React Hook Form plus Zod schemas shared with Server Actions. Reason: the client and server must agree on validation.
- Feature components live under `components/features/<domain>/`. Reason: domain UI should not leak into global UI primitives.
- `components/ui/` contains generic primitives only. Reason: reusable primitives should not know product concepts.

## Server Action Pattern

```ts
"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";
import { createWorkspace } from "@/server/services/workspaces";

const schema = z.object({
  name: z.string().min(2).max(80),
});

export async function createWorkspaceAction(input: unknown) {
  const parsed = schema.safeParse(input);
  if (!parsed.success) {
    return { ok: false, error: parsed.error.flatten() };
  }

  const workspace = await createWorkspace(parsed.data);
  revalidatePath("/dashboard");
  return { ok: true, data: workspace };
}
```

Reason: actions validate, call services, revalidate, and return typed envelopes. They do not contain SQL.

## API Route Pattern

Use Route Handlers only for external integrations, webhooks, and machine-to-machine APIs. Product mutations should usually be Server Actions.

```ts
export async function POST(request: Request) {
  const body = await request.json();
  const result = webhookSchema.safeParse(body);
  if (!result.success) {
    return Response.json({ ok: false, error: "invalid_payload" }, { status: 400 });
  }

  await handleWebhook(result.data);
  return Response.json({ ok: true });
}
```

Reason: route handlers are public boundaries and must parse untrusted input explicitly.

## Dev Commands

```bash
npm run dev          # local app
npm run build        # production build
npm run lint         # lint
npm run typecheck    # TypeScript without emit
npm run test         # unit and integration tests
npm run db:generate  # generate migration from schema
npm run db:migrate   # apply migrations
npm run db:studio    # inspect local database
```

## What We Do Not Do

- Do not add `pages/`. Reason: this is App Router only.
- Do not put SQL in React components. Reason: rendering and persistence are separate concerns.
- Do not use `any`. Reason: it hides schema drift and unsafe request parsing.
- Do not fetch data in `useEffect` when a Server Component can load it. Reason: avoids hydration races and duplicate loading states.
- Do not hard-delete user-owned rows by default. Reason: account recovery, audits, and support need history.
- Do not use `OFFSET` pagination for product lists. Reason: keyset pagination is more stable and scalable.
- Do not store secrets outside environment variables. Reason: leaked secrets cannot be reliably recovered.
- Do not swallow errors with empty `catch` blocks. Reason: failures must be observable.
- Do not create global providers for feature-local state. Reason: feature state should remain close to the feature.
- Do not invent migrations without changing `schema.ts`. Reason: schema and migrations must stay paired.

## First Task Checklist For Claude

Before editing code:

1. Identify whether the task changes UI, server action, query, service, schema, or migration.
2. Reuse the existing folder boundary above.
3. Add or update tests when changing validation, services, or database behavior.
4. Run typecheck and the narrowest relevant tests.
5. Summarize any migration risk in the final response.

