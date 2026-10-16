# Next.js 15 App Router + SQLite SaaS `CLAUDE.md` Template

Opinionated, zero-ambiguity `CLAUDE.md` configuration for multi-tenant SaaS applications built with **Next.js 15 (App Router)**, **React 19**, **SQLite (`better-sqlite3` / Turso)**, and **Drizzle ORM**.

## Quick Start

Copy [`CLAUDE.md`](./CLAUDE.md) into the root of any greenfield or existing Next.js 15 + SQLite project:

```bash
cp templates/nextjs-sqlite-saas/CLAUDE.md /path/to/your-saas-app/CLAUDE.md
```

## Greenfield Verification Test

Verified on a clean Next.js 15 + `better-sqlite3` project with the prompt:
> *"Add an API key management feature where organization admins can create and revoke API keys."*

With this `CLAUDE.md` in the project root, Claude Code immediately generated:
1. `src/db/schema/api-keys.ts` using `snake_case` columns, `organization_id` cascade FK + composite index `idx_api_keys_organization_id`, and integer `timestamp_ms` columns.
2. `src/server/queries/api-keys.ts` starting with `import "server-only"`, wrapped in React `cache()`, enforcing `requireOrgMember(orgSlug)`.
3. `src/server/actions/api-keys.ts` exporting `createApiKeyAction` and `revokeApiKeyAction` returning `ActionResult<T>`, running synchronous `db.transaction()` mutations without `await` inside the transaction.
4. `src/app/(dashboard)/[orgSlug]/settings/api-keys/page.tsx` awaiting Next.js 15 `params: Promise<{ orgSlug: string }>`.
5. Vitest integration test in `tests/integration/api-keys.test.ts` using an in-memory SQLite instance—all without asking a single clarifying question.
