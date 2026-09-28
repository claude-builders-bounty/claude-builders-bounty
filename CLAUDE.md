# CLAUDE.md — Next.js 15 + SQLite SaaS Template

## Working contract

Use these defaults on a greenfield project without asking the owner to choose a stack again. Read `package.json`, the lockfile, `tsconfig.json`, and existing database/auth configuration first. If a listed script or module does not exist, implement it before invoking/importing it; do not claim this Markdown installed anything. Preserve an existing compatible structure rather than creating a second app or database. Ask only about genuinely missing product requirements, secrets, destructive changes, or external deployments.

## Stack & Versions

- **Framework:** Next.js **15** App Router and React **19**. Keep the resolved patch versions in the lockfile; do not upgrade framework majors implicitly. Reason: reproducible behaviour and compatibility with this template's target.
- **Language:** TypeScript **5**, strict mode; use `unknown` and validation at boundaries rather than `any`. Reason: inputs are not trustworthy merely because the caller is TypeScript.
- **Default database:** `better-sqlite3` with Drizzle ORM in the **Node.js runtime**, on one application host with a persistent writable volume. Reason: a native SQLite file is not an Edge database or durable storage on an ephemeral serverless filesystem.
- **Turso alternative:** only use `@libsql/client` with Drizzle's libSQL adapter when the project already selects Turso. Await its asynchronous calls; do not apply local-file connection or WAL assumptions to a remote database. Reason: the two drivers are not interchangeable.
- **Styling:** Tailwind CSS **4**; keep installed shadcn/ui components when present. Do not import components that have not been generated. Reason: visual conventions must match real files.
- **Auth:** Better Auth with the configured SQLite/Drizzle adapter and **database-backed sessions**. Use its generated auth schema and matching-version documentation. Do not describe a cookie carrying a session token as a stateless session. Reason: session storage and revocation must be explicit.
- **Validation:** Zod **3** for this template's examples; respect an existing compatible schema library/version. Reason: avoid mixing APIs from different major versions.

## Greenfield setup and Development Commands

If no application exists, create a Next.js 15 TypeScript App Router app with ESLint, Tailwind and the `@/*` alias. `src/` is the default here; an existing root `app/` is equally valid. Do not move an existing application solely to match this layout.

For the default local SQLite stack, install `better-sqlite3`, `drizzle-orm`, `zod@3`, and `server-only`; development dependencies are `@types/better-sqlite3`, `drizzle-kit`, and `tsx`. Install/configure Better Auth before introducing protected routes. Until auth is configured, fail closed for protected data and mutations; do not add a mock authenticated user.

Use the following script contract. Add missing entries to `package.json` after creating the required configuration; preserve unrelated scripts:

```json
{
  "scripts": {
    "dev": "next dev --turbopack",
    "build": "next build",
    "start": "next start",
    "lint": "eslint .",
    "typecheck": "tsc --noEmit",
    "db:generate": "drizzle-kit generate",
    "db:migrate": "drizzle-kit migrate",
    "db:studio": "drizzle-kit studio"
  }
}
```

`npm run build` builds the app; it does **not** generate or apply database migrations. Run `npm run lint`, `npm run typecheck`, and `npm run build` as separate acceptance checks. Reason: deploy-time schema changes need review, and a build must not mutate a database.

Use `drizzle.config.ts` with `dialect: 'sqlite'`, `schema: './src/db/schema.ts'`, `out: './drizzle'`, and a `dbCredentials.url` pointing at `process.env.DB_FILE_NAME ?? './local.sqlite'`. For an existing root-level application, use `./db/schema.ts` instead. Runtime and migration tools must resolve the **same file path**. Keep `drizzle/` SQL and its metadata together in version control.

Keep the non-secret local default in `.env.example`; ignore `.env.local`, database files, and SQLite `-wal`/`-shm` sidecars. Configure production through the existing secret/deployment system, never by inventing credentials.

## Folder Structure

```text
src/                         # Omit this prefix for an existing root-level app
├── app/
│   ├── (auth)/               # Public sign-in/sign-up routes
│   ├── (dashboard)/          # Protected SaaS pages
│   ├── api/                  # Webhooks, external APIs, downloads
│   ├── layout.tsx            # Root layout; html/body, providers
│   └── page.tsx              # Public landing page
├── components/
│   ├── ui/                   # Generated reusable primitives
│   └── shared/               # App-specific reusable components
├── db/
│   ├── index.ts              # Server-only driver and Drizzle initialization
│   ├── schema.ts             # Schema source of truth
│   └── queries/              # Parameterized, tenant-scoped queries
├── lib/
│   ├── actions/              # Authorized and validated Server Actions
│   ├── auth.ts               # Real Better Auth server configuration
│   └── utils.ts              # Pure helpers
└── types/                    # Truly shared types only

drizzle/                     # Generated SQL migrations plus metadata
public/                      # Public assets; never secrets or databases
drizzle.config.ts
CLAUDE.md
```

## Naming Conventions

- **Files and directories:** `kebab-case`, including component files: `submit-button.tsx`. **Exported React components:** `PascalCase`, e.g. `SubmitButton`. Reason: consistent paths across case-sensitive and case-insensitive filesystems.
- **Functions and variables:** `camelCase`; hooks begin with `use`; types/interfaces use `PascalCase` without an `I` prefix. Valid examples: `type User = { id: string }` and `interface BillingProps { userId: string }`. Reason: a predictable distinction between values and types.
- **SQL tables:** plural `snake_case`; columns: `snake_case`. Keep the auth library's generated schema or explicitly configure mappings before renaming it. Reason: hand-renaming auth tables can break its adapter.
- **Domain data:** store monetary amounts as integer minor units plus currency; timestamps use a documented UTC representation and `updated_at` is explicitly maintained on writes. Reason: avoid float rounding and misleading audit records.

## SQL & Database Migration Rules

1. Import `server-only` in application database modules. Use `better-sqlite3` only from Node.js server code; initialize `PRAGMA foreign_keys = ON`, `PRAGMA journal_mode = WAL`, and a bounded `busy_timeout` per connection. Reuse the connection in the application process rather than opening one per request. Reason: foreign-key declarations are not enforcement by themselves, and SQLite serializes writers.
2. Put schema changes in `schema.ts`, run `db:generate`, review the generated SQL and metadata, then run `db:migrate` against a disposable database before applying an approved production migration. Never edit already-applied migrations or run `drizzle-kit push` against production. Reason: a repeatable migration history must match deployed state.
3. Back up production before an approved schema migration and test restoration; use expand/migrate/contract changes for destructive operations. Reason: rollback cannot recover deleted data without a backup. Do not perform that operation without owner approval.
4. Declare foreign keys and indexes for actual access paths. Choose `CASCADE`, `RESTRICT`, or `SET NULL` per relationship rather than cascading every deletion. Reason: dependent rows may require retention rather than deletion.
5. Keep writes in short transactions. Do not perform network calls inside SQLite transactions or hold a transaction across an `await` with the synchronous driver. Reason: long locks block other writers.
6. Use parameterized queries/Drizzle expressions. Never interpolate user input into SQL, even in a database module. Scope every tenant-owned lookup and mutation to the authenticated tenant. Reason: moving a string out of a component does not prevent injection or cross-tenant access.
7. Validate migration results on a new database and on a database containing the previous schema. Check foreign-key violations and representative queries. Reason: creating an empty database is not proof that upgrades preserve existing data.

## Component & Architecture Patterns

1. **Server Components by default.** Add `'use client'` only at interactive boundaries. Return only necessary serializable fields to clients, not database rows containing secrets. Reason: minimize browser code and data exposure.
2. **Server Actions for first-party mutations.** Put `'use server'` at the top of action modules. Authenticate, authorize the operation/tenant, and validate Zod input **inside every action**, not just in a layout. Return expected validation failures safely; revalidate affected paths/tags after successful writes. Reason: an action is an independently callable server endpoint.
3. **Route Handlers for external protocols.** Verify webhook signatures and enforce idempotency for externally retried operations. Reason: external senders need explicit HTTP contracts, not a UI-only action.
4. **Read data in Server Components/query modules.** Prefer this for initial page data; client-side libraries remain appropriate for live or interactive data. Do not use Server Actions as the default read-cache mechanism. Reason: distinguish reads, mutations, and browser interaction.
5. **Error boundaries.** `error.tsx` must be a Client Component with `'use client'`; use `global-error.tsx` when handling root-layout errors. Reason: a route boundary does not catch every parent layout failure.
6. **Next.js 15 request APIs.** Await `cookies()`, `headers()`, and promised route `params` where required. Mark authenticated database-backed pages appropriately dynamic; do not query production tenant data at build time. Reason: request data belongs to the request, not static generation.
7. **Colocate domain code** until it is reused. Reason: shared folders should not become unstructured dumping grounds.

## What We Don't Do (And Why)

- No implicit stack or database-driver switching. Reason: deployment and transaction semantics differ.
- No migration generation/application inside `next build` or ordinary web requests. Reason: multiple builds/workers must not race on schema changes.
- No real secrets, session tokens, customer data, payment details, or database files in commits, logs, prompts, public assets, or `NEXT_PUBLIC_` variables. Reason: those surfaces are not secret storage.
- No trusting a layout guard, client-provided tenant ID, or payment-success redirect as authorization/payment proof. Reason: validate server-side against the configured authoritative source.
- No unexplained dependency swaps or claims of zero overhead/instant startup. Reason: measure performance and keep the project coherent.
- No claims that tests, a production deployment, or Claude Code validation ran unless they actually ran. Report the commands, result, and any blocked acceptance item. Reason: reviewers need evidence rather than an assertion.

## Verification

Run lint, type checking, production build, the configured migration tests, and relevant behaviour/security tests. To check Claude Code context loading, start Claude Code in a disposable greenfield project containing this file and ask it to explain the stack, paths, migration workflow and action authorization rules without changing files. Record its actual output and whether it asked clarifying questions. This is a required validation procedure, **not a claim that Claude Code was executed**.
