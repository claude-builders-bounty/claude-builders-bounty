# Test report — Next.js 15 + SQLite SaaS CLAUDE.md

Bounty issue: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2

## Acceptance criteria coverage

- **Covers project structure:** yes — see `Expected folder structure` in `CLAUDE.md`.
- **Covers naming conventions:** yes — see `Naming conventions`.
- **Covers DB migration rules:** yes — see `SQL and migration conventions`.
- **Includes dev commands:** yes — see `Testing expectations`.
- **Includes patterns to follow:** yes — server/client boundaries, repository/service pattern, server actions, route handlers, auth, validation, tests.
- **Includes anti-patterns to avoid:** yes — see `What we do not do, and why`.
- **Opinionated, not generic:** yes — chooses explicit SQL, append-only migrations, server-only DB access, Zod boundaries, and no generic ORM by default.
- **Usable on a greenfield Next.js + SQLite project:** yes — copy `CLAUDE.md` into the project root before starting Claude Code.
- **Setup instructions in 3 steps or fewer:** yes — see `README.md`.

## Local validation performed

A temporary greenfield-style project was created under `/tmp/nextjs-sqlite-saas-claude-test` with this shape:

```text
/tmp/nextjs-sqlite-saas-claude-test/
  CLAUDE.md
  package.json
  src/
    app/
    components/
    features/
    lib/
    server/
      auth/
      db/
        migrations/
      repositories/
```

Validation checked that `CLAUDE.md` includes the sections and rules Claude Code needs before editing:

- stack and versions,
- expected folder structure,
- naming conventions,
- SQL and migration conventions,
- component patterns,
- server actions and route handlers,
- auth and authorization,
- testing expectations,
- explicit anti-patterns.

Validation output:

```text
VALIDATION OK
template bytes: 14122
sections checked: 9
phrases checked: 14
temp project: /tmp/nextjs-sqlite-saas-claude-test
```

## Claude Code context-readiness prompt

Use this prompt after copying the file into a new project root:

```text
Read CLAUDE.md and answer only with:
1. the stack,
2. where database code belongs,
3. how migrations should be handled,
4. whether client components may import src/server modules,
5. three anti-patterns to avoid.
Do not ask clarifying questions.
```

Expected behavior: Claude Code should answer directly from the template because the file provides stack, boundaries, migration policy, and anti-patterns without requiring additional project-specific context.

## Expected Claude Code answer shape

```text
1. Stack: Next.js 15 App Router, TypeScript, SQLite via better-sqlite3 or Turso/libSQL, Zod, Tailwind.
2. Database code belongs in server-only modules under src/server, especially src/server/db and src/server/repositories.
3. Migrations are append-only, numbered SQL files in src/server/db/migrations; committed migrations must not be edited.
4. No. Client components must not import src/server modules.
5. Avoid database calls in components, editing committed migrations, using any to bypass TypeScript, leaking secrets to client code, and putting business rules in JSX.
```

## Note

The container used for this submission had Node.js and npm available but did not have the interactive `claude` CLI installed. The validation therefore focuses on deterministic template completeness and a reproducible Claude Code prompt for maintainers to verify.
