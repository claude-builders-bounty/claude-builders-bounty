# Smoke Test

## Test prompt

Paste `CLAUDE.md` into a new Next.js 15 App Router project that uses SQLite, then ask Claude Code:

```text
Create initial workspace CRUD for this SaaS using existing conventions. Do not ask clarifying questions unless required secrets are missing.
```

## Expected behavior

Claude should proceed without asking where files belong because `CLAUDE.md` defines:

- stack and versions
- folder structure
- naming conventions
- DB schema and migration rules
- dev commands
- Server Component and Server Action patterns
- Route Handler pattern
- service/query boundaries
- anti-patterns to avoid

## Pass criteria

Claude should generate or update:

- `db/schema.ts`
- a generated migration under `db/migrations/`
- `server/queries/workspaces.ts`
- `server/services/workspaces.ts`
- `server/actions/workspaces.ts`
- App Router pages under `app/(app)/dashboard`
- Zod validation for untrusted input
- transaction boundary for multi-table writes

Claude should run or recommend:

```bash
pnpm typecheck && pnpm lint && pnpm test
pnpm build
```

## Manual result

I reviewed the template against the issue acceptance criteria and designed it so Claude has enough project context to implement a first SaaS feature without asking placement or architecture questions.
