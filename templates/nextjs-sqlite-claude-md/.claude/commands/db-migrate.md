---
description: Generate and apply a Drizzle migration after editing lib/db/schema.ts
---

The user has changed `lib/db/schema.ts` and wants the migration generated, applied, and the affected query functions updated.

Steps:

1. Run `pnpm db:generate` to produce a new migration in `lib/db/migrations/`.
2. Show the user the generated SQL file path and quote the SQL changes verbatim (don't paraphrase).
3. Run `pnpm db:migrate` to apply the migration to the local dev DB.
4. Search for query functions in `lib/db/queries/` that touch the changed table(s). For each, propose the minimal edit needed to keep them type-correct, then apply the edits.
5. If the migration is destructive (DROP COLUMN, NOT NULL on an existing column without a default, RENAME), warn the user and confirm before applying.

Do **not**:
- Hand-write SQL — always use `drizzle-kit generate`.
- Edit a previously-deployed migration. Add a new one if the schema needs further changes.
- Leave the local DB in an inconsistent state (i.e., schema edited but migration not run).
