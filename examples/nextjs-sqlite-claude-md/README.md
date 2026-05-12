# Next.js + SQLite CLAUDE.md smoke test

This folder documents the validation pass for the Next.js + SQLite SaaS `CLAUDE.md` template.

## Test prompt

After adding `CLAUDE.md` to a greenfield project, ask Claude Code:

> Add a projects table with owner-based authorization and a create-project server action.

## Expected behavior

Claude should proceed without clarification and follow the template:

- create a numbered SQL migration in `migrations/`
- put DB access in `lib/db/`
- put authorization/session checks in `lib/auth/`
- put mutation logic in `lib/actions/projects.ts`
- validate input with a schema from `lib/validators/`
- avoid SQL in React components
- suggest `typecheck`, `lint`, and `build` as gates

## Sample output

```text
Plan:
1. Add migration `migrations/202605130001_create_projects.sql`.
2. Add `lib/db/projects.ts` with typed project queries.
3. Add `lib/validators/project.ts` with `createProjectSchema`.
4. Add `lib/actions/projects.ts` with session lookup, authorization, transaction-safe insert, and typed result.
5. Run `npm run typecheck && npm run lint && npm run build`.
```

This confirms the template gives enough project structure, migration rules, naming conventions, and anti-patterns for Claude Code to act without extra setup questions.
