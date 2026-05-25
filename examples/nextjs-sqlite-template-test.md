# Template Test Notes

Tested against a greenfield Next.js 15 + SQLite SaaS skeleton by checking that
the template gives Claude Code enough context to answer without follow-up
questions for these prompts:

1. Add a billing settings route that reads the current organization from SQLite.
2. Add a Drizzle migration for storing Stripe customer IDs.
3. Explain where a server action for updating an organization name should live.

Expected behavior: Claude can point to `(app)` routes, `db/schema.ts`,
`db/migrations/`, `features/organizations`, Server Actions, Zod validation,
and the anti-patterns around client-side data writes.

This note is included as the PR evidence requested by bounty #2.
