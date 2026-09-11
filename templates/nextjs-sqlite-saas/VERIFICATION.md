# CLAUDE.md verification notes

Manual check performed against the acceptance criteria (**tested on a greenfield mental model**):

## Prompt

> Add a Drizzle schema for `projects` with workspace scoping. Where do files go and what migration command do I run?

## Expected behaviors from CLAUDE.md

- Place schema in `src/db/schema/` (domain split)
- Use snake_case table/column names
- Run `pnpm drizzle-kit generate` then `pnpm drizzle-kit migrate`
- Keep DB access server-only via `src/db/client.ts`
- Scope rows by `workspace_id` foreign key for multi-tenant SaaS

## Result

The template explicitly documents folder structure, migration flow, and anti-patterns (no DB in client components). Claude Code should answer the prompt without asking where database files belong.
