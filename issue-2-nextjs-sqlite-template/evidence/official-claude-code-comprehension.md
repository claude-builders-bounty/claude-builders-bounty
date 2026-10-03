## Context check
- Framework: Next.js 15 App Router with strict TypeScript and Server Components by default.
- Database: better-sqlite3 is for persistent single-node/local filesystems; Turso/libSQL is preferred for serverless, edge, or multi-region deployment.
- Client boundary: Client Components must not import lib/db, secrets, filesystem modules, or privileged services.
- Migrations: shipped migrations are immutable; destructive changes use backfill, compatibility window, then removal.
- Validation: Zod is required at every untrusted runtime boundary.
- Server Actions: authenticate/authorize internally, validate before DB access, and remain thin.
- Completion: run lint, typecheck, relevant tests, and migration checks when schema changes.
- Anti-pattern: do not place a local SQLite file on ephemeral serverless storage because writes may disappear or diverge.

## Implementation decision
For a new authenticated create-workspace mutation, I would keep the page as a Server Component, validate FormData with Zod, authorize inside a thin Server Action, call a lib/services use-case, and perform prepared SQL in lib/db inside the service transaction boundary. I would not ask for stack or folder clarification because CLAUDE.md already defines them.
