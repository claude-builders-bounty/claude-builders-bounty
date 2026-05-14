# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

This file is the operating manual for Claude Code in this repository. Treat it as binding project context, not a suggestion list.

## 1. Stack and versions

- Framework: Next.js 15 App Router.
- Language: TypeScript in strict mode.
- Runtime split:
  - Server Components by default.
  - Client Components only for browser-only state, event handlers, optimistic UI, or third-party widgets.
  - Route Handlers and Server Actions for writes.
- Database: SQLite through either `better-sqlite3` for local/single-node deployments or Turso/libSQL for hosted edge-friendly SQLite.
- Styling: Tailwind CSS plus small component primitives. Avoid adding a UI framework unless the issue explicitly asks for it.
- Auth/billing/email/analytics: integrate behind local adapter modules. Do not scatter provider SDK calls through pages.

Reason: this stack is intentionally boring. The product should be easy to ship, inspect, back up, and migrate without a distributed-systems tax.

## 2. Folder structure

Use this structure for new code:

```text
app/
  (marketing)/             # public landing pages
  (app)/                   # authenticated product shell
  api/                     # route handlers for webhooks or external callers
  actions/                 # server actions grouped by domain
components/
  ui/                      # reusable primitives: Button, Dialog, EmptyState
  feature/                 # product-specific composed components
lib/
  db/                      # connection, schema helpers, migrations
  auth/                    # session/user helpers
  billing/                 # billing adapter boundary
  email/                   # email adapter boundary
  validators/              # zod schemas shared by actions and forms
  domain/                  # business rules with no React imports
migrations/                # numbered SQL files, append-only
scripts/                   # one-off maintenance and verification scripts
tests/                     # unit/integration tests; mirror lib/app domains
```

Rules:

- Do not put database queries inside React components. Put them in `lib/<domain>/queries.ts` or `lib/db/*`.
- Do not import from `app/` into `lib/`. `lib/` must remain framework-light and testable.
- Keep route handlers thin: parse input, call domain function, return response.
- Keep Server Actions thin: authorize, validate, call domain function, revalidate/redirect.

Reason: App Router projects rot when data access, validation, and UI are braided together. These boundaries keep changes reviewable.

## 3. Naming conventions

- Files and folders: kebab-case (`project-settings-form.tsx`).
- React components: PascalCase exports (`ProjectSettingsForm`).
- Server Actions: verb-noun with `Action` suffix (`updateWorkspaceAction`).
- DB functions: verb phrase describing the query (`getWorkspaceBySlug`, `insertAuditEvent`).
- Zod schemas: noun with `Schema` suffix (`UpdateWorkspaceSchema`).
- Migration files: `NNNN_short_description.sql`, zero-padded and append-only.

Reason: consistent names let Claude and humans find the correct layer without guessing.

## 4. Database and migration rules

SQLite is the source of truth. Treat schema changes as production events.

### Migration rules

- Every schema change gets a new file in `migrations/`.
- Never edit a committed migration. Add a new migration that moves the schema forward.
- Wrap multi-step migrations in a transaction when possible:

```sql
BEGIN;
-- changes
COMMIT;
```

- Use explicit constraints:
  - `NOT NULL` unless null is a real domain state.
  - `CHECK` for enums and numeric bounds.
  - `FOREIGN KEY ... ON DELETE ...` deliberately, not by habit.
- Add indexes with the query in mind. Do not add speculative indexes.
- Store timestamps as ISO-8601 UTC text (`created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP`) unless the project already standardizes on integer epoch.
- Use integer cents for money. Never store user-facing money as floating point.
- Turn on foreign keys for every SQLite connection:

```ts
db.pragma('foreign_keys = ON');
db.pragma('journal_mode = WAL');
```

Reason: SQLite will happily let you build footguns. Constraints and boring timestamp/money choices prevent silent corruption.

### Query rules

- Use parameterized queries only. Never concatenate user input into SQL.
- Keep SQL close to the domain function that owns it.
- Return plain objects, not driver-specific row objects.
- Validate all write inputs before opening a transaction.
- For write flows, emit an audit event in the same transaction if the domain action is user-visible or billing-relevant.

## 5. Server/client component patterns

Default to Server Components.

Use Client Components only when the file needs:

- `useState`, `useEffect`, or browser APIs.
- event handlers like `onClick` or `onSubmit`.
- optimistic interactions.
- client-only libraries.

Pattern:

```tsx
// app/(app)/workspaces/[slug]/page.tsx
import { getWorkspacePageData } from '@/lib/workspaces/queries';
import { WorkspaceSettingsForm } from '@/components/feature/workspace-settings-form';

export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const data = await getWorkspacePageData(slug);
  return <WorkspaceSettingsForm workspace={data.workspace} />;
}
```

Reason: Server Components reduce client bundle size and keep secrets/database access off the browser.

## 6. Server Actions and validation

All mutations follow this order:

1. Authenticate and authorize.
2. Parse with a schema.
3. Run domain function inside a transaction if multiple writes are involved.
4. Revalidate exact paths/tags.
5. Return a typed result or redirect.

Example shape:

```ts
'use server';

import { revalidatePath } from 'next/cache';
import { UpdateWorkspaceSchema } from '@/lib/validators/workspace';
import { requireUser } from '@/lib/auth/session';
import { updateWorkspace } from '@/lib/workspaces/mutations';

export async function updateWorkspaceAction(input: unknown) {
  const user = await requireUser();
  const parsed = UpdateWorkspaceSchema.safeParse(input);
  if (!parsed.success) {
    return { ok: false, error: 'Invalid workspace settings' } as const;
  }

  await updateWorkspace({ userId: user.id, ...parsed.data });
  revalidatePath('/settings/workspace');
  return { ok: true } as const;
}
```

Reason: this order prevents unauthenticated validation leaks, SQL mistakes, and stale UI after writes.

## 7. Component patterns

- Components in `components/ui` must be generic and domain-free.
- Components in `components/feature` may know product language but must not query the database.
- Prefer explicit props over global context. Context is for session/theme/product shell, not random data transport.
- Keep loading, empty, and error states next to the component that renders the data.
- Do not over-abstract forms. A duplicated 20-line form is better than a generic form engine nobody can reason about.

Reason: SaaS UI changes frequently. Local clarity beats premature DRY.

## 8. Dev commands

Use the package manager already present in the repo. If none exists, prefer `pnpm`.

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm db:migrate
pnpm db:studio
```

If a command does not exist, add it before relying on it in documentation or CI.

Reason: Claude must not invent commands that make the README look good but fail in a fresh clone.

## 9. Testing expectations

- Domain logic in `lib/domain` gets unit tests.
- Database mutations get integration tests against a temporary SQLite database.
- Server Actions get tests around auth, validation, and transaction behavior where the project test harness supports it.
- Avoid snapshot tests for business UI. Assert user-visible text and state transitions.
- Every bug fix starts with a failing test that reproduces the bug.

Reason: SQLite makes realistic integration tests cheap. Use that advantage.

## 10. Security and privacy rules

- Never log secrets, session tokens, webhook signatures, or raw payment payloads.
- Webhooks must verify signatures before parsing business fields.
- Rate-limit public write endpoints.
- Use authorization checks in domain functions, not only in pages.
- Do not expose internal IDs in public URLs when a slug exists.
- Treat CSV export, file upload, and rich text as attack surfaces.

Reason: small SaaS apps often fail at boundaries: webhooks, exports, uploads, and admin shortcuts.

## 11. What we do not do, and why

- No global ORM migration magic unless the repo already uses it. Reason: explicit SQL is easier to inspect and recover.
- No client-side database calls. Reason: secrets and authorization belong server-side.
- No `any` to silence TypeScript. Reason: it moves bugs from compile time to customers.
- No speculative abstraction layers. Reason: SaaS requirements change faster than abstractions stabilize.
- No editing old migrations. Reason: deployed databases cannot time travel.
- No hidden provider calls in UI components. Reason: billing/auth/email providers must be replaceable.
- No force-push instructions, destructive cleanup commands, or production DB resets in docs. Reason: Claude may execute what docs normalize.

## 12. Before finishing any task

Run the narrowest relevant checks first, then the project-level checks:

```bash
pnpm lint
pnpm typecheck
pnpm test
```

For DB changes, also run:

```bash
pnpm db:migrate
```

If a check cannot run because the command is missing or the repo is a fresh template, say that explicitly in the PR notes and do not claim it passed.

## 13. How Claude should behave in this repo

- Prefer small, reviewable commits.
- Explain tradeoffs in PR notes when touching schema, auth, billing, or data deletion.
- Ask for clarification only when the ambiguity changes the schema or user-facing behavior.
- Otherwise make the boring, reversible choice and document it.
- When adding a dependency, justify why project code cannot solve the problem simply.

Reason: the goal is a maintainable SaaS codebase, not a demo that only works once.
