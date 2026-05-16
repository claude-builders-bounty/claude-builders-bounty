# CLAUDE.md Template Validation

This document records the validation performed for the Next.js 15 + SQLite SaaS
`CLAUDE.md` template.

## Acceptance Coverage

| Requirement | Covered Where |
|---|---|
| Stack and versions | `Stack And Versions` |
| Project structure | `Project Structure` |
| Naming conventions | `Naming Conventions` |
| Database migration rules | `SQL And Migration Conventions` |
| Development commands | `Commands Claude Should Use` |
| Patterns to follow | `Database Access Pattern`, `App Router Patterns`, `Component Patterns`, `Validation And Forms` |
| Anti-patterns to avoid | `What We Do Not Do And Why` |
| Opinionated, not generic | Defaults choose Next.js 15 App Router, TypeScript strict mode, Drizzle, `better-sqlite3`, Turso/libSQL, `pnpm`, and explicit SaaS permissions |
| Usable on greenfield project | `Default Decisions When Requirements Are Missing` tells Claude how to proceed without follow-up questions |

## Greenfield Smoke Test Scenario

Use a new empty repository with the files below:

```text
package.json
app/page.tsx
app/layout.tsx
db/schema.ts
lib/env.ts
```

Paste `CLAUDE.md` at the repository root, then ask Claude Code:

```text
Read CLAUDE.md and create the first authenticated SaaS dashboard slice:
projects table, migration, project list query, dashboard route, create-project
server action, validation schema, and tests. Use the defaults in the repo.
```

Expected behavior:

- Claude should choose App Router files under `app/`.
- Claude should add database work under `db/`.
- Claude should generate a migration rather than mutating schema only.
- Claude should keep database imports server-only.
- Claude should use server actions for the form mutation.
- Claude should add server-side validation.
- Claude should add tests for validation, permissions, or query behavior.
- Claude should run or report the project verification commands.
- Claude should not ask whether to use Pages Router, which package manager to use,
  whether migrations are required, or where database code belongs.

## Local Validation Performed

The author validated the template with deterministic checks in this repository:

- Confirmed all expected section headings exist.
- Confirmed required terms appear: Next.js 15, SQLite, Drizzle, `better-sqlite3`,
  Turso/libSQL, migrations, App Router, Server Components, Server Actions,
  naming conventions, anti-patterns, and verification commands.
- Confirmed every rule-oriented bullet includes a reason.
- Confirmed Markdown has no obvious trailing-whitespace issues.

Claude Code itself was not available in this shell, so the smoke-test prompt above
is included for maintainers who want to replay the exact acceptance scenario.
