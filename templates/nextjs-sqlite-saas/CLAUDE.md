     1|# CLAUDE.md — Next.js 15 App Router + SQLite SaaS
     2|
     3|> Production-ready conventions for a greenfield SaaS. Every rule here exists because violating it has caused real bugs in real projects.
     4|
     5|---
     6|
     7|## Stack Lock-in
     8|
     9|| Layer | Choice | Why |
    10||-------|--------|-----|
    11|| Runtime | Node.js ≥ 22 LTS | Stable, native ESM support |
    12|| Framework | Next.js 15 App Router | RSC-first, server actions, streaming |
    13|| Language | TypeScript `strict: true` | Catch bugs at compile time, not in production |
    14|| Database | `better-sqlite3` (local) / Turso (prod) | Zero-config local dev, seamless prod migration |
    15|| Validation | Zod | Runtime type safety at every trust boundary |
    16|| Styling | Tailwind CSS 4 | Utility-first, no CSS-in-JS runtime cost |
    17|| Auth | `better-auth` or `next-auth` v5 | Session management without vendor lock-in |
    18|| Testing | Vitest + Testing Library | Fast, native ESM, great DX |
    19|
    20|**Never introduce a dependency not listed above without explicit user approval.**
    21|
    22|---
    23|
    24|## Project Structure
    25|
    26|```
    27|src/
    28|├── app/                    # Next.js App Router (pages + layouts)
    29|│   ├── (marketing)/        # Public routes (no auth)
    30|│   ├── (dashboard)/        # Authenticated routes
    31|│   │   ├── layout.tsx      # Auth check + sidebar shell
    32|│   │   └── page.tsx        # Dashboard home
    33|│   ├── api/                # Route handlers (thin — delegate to services)
    34|│   │   └── webhooks/       # Stripe, etc.
    35|│   ├── layout.tsx          # Root layout (fonts, metadata, providers)
    36|│   └── globals.css         # Tailwind imports only
    37|├── components/
    38|│   ├── ui/                 # Generic UI (Button, Input, Card) — no business logic
    39|│   └── features/           # Domain-specific (UserAvatar, InvoiceTable)
    40|├── lib/
    41|│   ├── db/
    42|│   │   ├── schema.ts       # Drizzle/better-sqlite3 table definitions
    43|│   │   ├── migrate.ts      # Migration runner
    44|│   │   └── index.ts        # DB client singleton
    45|│   ├── auth.ts             # Auth config
    46|│   ├── stripe.ts           # Stripe client
    47|│   └── utils.ts            # Pure utility functions (no side effects)
    48|├── services/               # Business logic (called by server actions & route handlers)
    49|│   ├── user.ts
    50|│   └── billing.ts
    51|├── types/                  # Shared TypeScript types & Zod schemas
    52|│   └── index.ts
    53|└── middleware.ts            # Auth redirects, rate limiting
    54|```
    55|
    56|**Rules:**
    57|- `app/` contains ONLY routing concerns (layouts, pages, route handlers).
    58|- `components/ui/` must be reusable — zero imports from `services/` or `lib/db/`.
    59|- `services/` contains pure business logic. It does NOT import from `next` — testable without Next.js.
    60|- Never put database queries directly in route handlers. Always go through `services/`.
    61|
    62|---
    63|
    64|## Database & Migrations
    65|
    66|```bash
    67|npm run db:migrate    # Apply pending migrations
    68|npm run db:studio     # Visual DB browser (optional)
    69|npm run db:reset      # Drop + recreate + seed (dev only!)
    70|```
    71|
    72|**Schema rules:**
    73|- Every table gets `id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16))))` — UUIDs, not auto-increment.
    74|- Every table gets `created_at TEXT DEFAULT (datetime('now'))` and `updated_at TEXT DEFAULT (datetime('now'))`.
    75|- Use a trigger for `updated_at`:
    76|  ```sql
    77|  CREATE TRIGGER update_{table}_updated_at
    78|  AFTER UPDATE ON {table}
    79|  BEGIN
    80|    UPDATE {table} SET updated_at = datetime('now') WHERE id = NEW.id;
    81|  END;
    82|  ```
    83|- Migration files: `migrations/0001_create_users.sql`, numbered, never edited after applied.
    84|- **Never** use `db.exec()` with string concatenation. Parameterized queries only.
    85|
    86|---
    87|
    88|## Server Actions vs Route Handlers
    89|
    90|| Use case | Pattern |
    91||----------|---------|
    92|| Form submissions from React components | Server Action (`"use server"`) |
    93|| Webhooks (Stripe, GitHub) | Route handler in `api/webhooks/` |
    94|| Client-side data fetching | Route handler returning JSON |
    95|| Mutations from client components | Server Action called via `useActionState` |
    96|
    97|**Server Action rules:**
    98|- Always validate input with Zod before touching the database.
    99|- Return `{ success: true, data }` or `{ success: false, error: string }` — never throw.
   100|- Revalidate paths with `revalidatePath()` after mutations.
   101|- Never call server actions from other server actions — use `services/` instead.
   102|
   103|```typescript
   104|// ✅ Correct
   105|"use server"
   106|export async function createUser(formData: FormData) {
   107|  const parsed = CreateUserSchema.safeParse(Object.fromEntries(formData));
   108|  if (!parsed.success) return { success: false, error: parsed.error.flatten() };
   109|  
   110|  const user = await userService.create(parsed.data);
   111|  revalidatePath("/dashboard/users");
   112|  return { success: true, data: user };
   113|}
   114|
   115|// ❌ Wrong — raw DB call in action, no validation
   116|"use server"
   117|export async function createUser(formData: FormData) {
   118|  const name = formData.get("name");
   119|  db.run(`INSERT INTO users (name) VALUES ('${name}')`); // SQL injection!
   120|}
   121|```
   122|
   123|---
   124|
   125|## Component Patterns
   126|
   127|### Server Components (default)
   128|```typescript
   129|// app/(dashboard)/users/page.tsx
   130|import { userService } from "@/services/user";
   131|
   132|export default async function UsersPage() {
   133|  const users = await userService.list();
   134|  return <UserTable users={users} />;
   135|}
   136|```
   137|
   138|### Client Components (only when needed)
   139|```typescript
   140|// components/features/user-form.tsx
   141|"use client";
   142|
   143|import { useActionState } from "react";
   144|import { createUser } from "@/app/(dashboard)/users/actions";
   145|
   146|export function UserForm() {
   147|  const [state, action, pending] = useActionState(createUser, null);
   148|  return (
   149|    <form action={action}>
   150|      {/* form fields */}
   151|      <button disabled={pending}>{pending ? "Creating..." : "Create"}</button>
   152|      {state?.error && <p className="text-red-500">{state.error}</p>}
   153|    </form>
   154|  );
   155|}
   156|```
   157|
   158|**Rules:**
   159|- Default to server components. Add `"use client"` only for: `useState`, `useEffect`, event handlers, browser APIs.
   160|- Never pass functions as props from server to client components. Use server actions.
   161|- Never pass `Date` objects from server to client — serialize as ISO string.
   162|
   163|---
   164|
   165|## Validation (Zod)
   166|
   167|Define schemas in `types/`, use them at every boundary:
   168|
   169|```typescript
   170|// types/index.ts
   171|import { z } from "zod";
   172|
   173|export const CreateUserSchema = z.object({
   174|  email: z.string().email().max(255),
   175|  name: z.string().min(1).max(100),
   176|  plan: z.enum(["free", "pro", "enterprise"]).default("free"),
   177|});
   178|
   179|export type CreateUserInput = z.infer<typeof CreateUserSchema>;
   180|```
   181|
   182|**Validate at:**
   183|- ✅ Server actions (form data)
   184|- ✅ Route handlers (request body, search params)
   185|- ✅ Environment variables (`z.string().min(1)` for required)
   186|- ❌ Never skip validation "because the client already validates"
   187|
   188|---
   189|
   190|## Error Handling
   191|
   192|```typescript
   193|// lib/errors.ts
   194|export class AppError extends Error {
   195|  constructor(
   196|    message: string,
   197|    public code: string,
   198|    public statusCode: number = 500,
   199|  ) {
   200|    super(message);
   201|  }
   202|}
   203|
   204|export class NotFoundError extends AppError {
   205|  constructor(entity: string, id: string) {
   206|    super(`${entity} ${id} not found`, "NOT_FOUND", 404);
   207|  }
   208|}
   209|
   210|export class ValidationError extends AppError {
   211|  constructor(public issues: z.ZodIssue[]) {
   212|    super("Validation failed", "VALIDATION_ERROR", 400);
   213|  }
   214|}
   215|```
   216|
   217|**Rules:**
   218|- Server actions return `{ success: false, error }` — never throw.
   219|- Route handlers catch errors and return proper HTTP responses.
   220|- Use `error.tsx` in route segments for UI error boundaries.
   221|- Log errors with context (user ID, request path) — not just the stack trace.
   222|
   223|---
   224|
   225|## Environment Variables
   226|
   227|```typescript
   228|// lib/env.ts
   229|import { z } from "zod";
   230|
   231|const envSchema = z.object({
   232|  DATABASE_URL: z.string().min(1),
   233|  AUTH_SECRET: z.string().min(32),
   234|  STRIPE_SECRET_KEY: z.string().startsWith("sk_"),
   235|  STRIPE_WEBHOOK_SECRET: z.string().startsWith("whsec_"),
   236|  NODE_ENV: z.enum(["development", "production", "test"]).default("development"),
   237|});
   238|
   239|export const env = envSchema.parse(process.env);
   240|```
   241|
   242|- Import `env` from `@/lib/env` — never use `process.env` directly.
   243|- `.env.local` for secrets, `.env` for defaults. Both in `.gitignore`.
   244|
   245|---
   246|
   247|## Testing
   248|
   249|```bash
   250|npm run test          # Unit tests (Vitest)
   251|npm run test:e2e      # E2E tests (Playwright, optional)
   252|npm run test:coverage # Coverage report
   253|```
   254|
   255|**Rules:**
   256|- Test `services/` thoroughly — they contain the business logic.
   257|- Test server actions with mocked `services/`.
   258|- Test components with Testing Library — test user-visible behavior, not implementation.
   259|- **Never** test database queries directly in unit tests — mock the service layer.
   260|- Coverage target: ≥80% for `services/`, ≥60% overall.
   261|
   262|---
   263|
   264|## Performance Rules
   265|
   266|- Use `React.cache()` for deduplicating data fetches within a single render.
   267|- Use `loading.tsx` for instant loading states (streaming).
   268|- Images: always use `next/image` with explicit `width`/`height`.
   269|- Fonts: use `next/font` — no external font requests.
   270|- **Never** block the whole page on a slow query. Use Suspense boundaries.
   271|- **Never** fetch the same data twice in a single request (use `React.cache()`).
   272|
   273|---
   274|
   275|## Anti-Patterns (will be rejected in PR review)
   276|
   277|| ❌ Anti-Pattern | ✅ Correct |
   278||----------------|-----------|
   279|| DB query in `page.tsx` | Query in `service/`, page calls service |
   280|| `useEffect` to fetch data on mount | Server component fetches, passes as props |
   281|| `any` type | Proper types or `unknown` with type guards |
   282|| `console.log` for debugging | Use structured logging or remove |
   283|| Inline styles | Tailwind classes |
   284|| `export default function` (unnamed) | Named exports only |
   285|| Magic numbers/strings | Constants or enums |
   286|| String concatenation in SQL | Parameterized queries |
   287|| Mutating props | Spread + override |
   288|| `use client` at layout level | Keep layouts as server components |
   289|
   290|---
   291|
   292|## Git Conventions
   293|
   294|- Branch: `feat/`, `fix/`, `chore/`, `docs/` prefix
   295|- Commit: Conventional Commits (`feat: add user creation`)
   296|- PR: Link issue, describe what/why, screenshot for UI changes
   297|- **Never** commit `.env.local`, `data/*.db`, or `node_modules/`
   298|
   299|---
   300|
   301|## Deployment Checklist
   302|
   303|- [ ] `npm run typecheck` passes
   304|- [ ] `npm run lint` passes
   305|- [ ] `npm run test` passes
   306|- [ ] Environment variables set in production
   307|- [ ] Database migrations applied
   308|- [ ] Stripe webhook endpoint configured
   309|- [ ] Error monitoring (Sentry) configured
   310|