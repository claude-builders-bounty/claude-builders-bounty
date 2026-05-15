## Proposed Changes

Adds a production-opinionated root `CLAUDE.md` for a greenfield Next.js 15 App Router + SQLite/Turso SaaS project.

The template covers:

- stack and version assumptions
- folder structure and ownership boundaries
- naming conventions
- development commands
- environment/config rules
- SQLite migration rules
- repository/data access patterns
- App Router, Server Action, and component patterns
- auth, authorization, validation, error handling, and testing expectations
- explicit anti-patterns with reasons
- completion checklist for Claude Code

/claim #2

## Validation

I checked the template against the issue acceptance criteria:

- Project structure: included with route groups, modules, db, shared components, and tests.
- Naming conventions: included with suffixes for actions, repos, schemas, and tests.
- DB migration rules: included with forward-only migrations, transaction guidance, FK/index rules, timestamp/id conventions.
- Dev commands: included with `pnpm dev`, lint, typecheck, tests, and db commands.
- Patterns to follow: included for server-first rendering, prepared SQL, route-local state, and cache invalidation.
- Anti-patterns to avoid: included with concrete reasons for each.
- Opinionated and greenfield-ready: uses one consistent set of defaults instead of generic alternatives.

## Notes

This is intentionally concise enough to be pasted into a new project while still giving Claude Code concrete implementation boundaries.
