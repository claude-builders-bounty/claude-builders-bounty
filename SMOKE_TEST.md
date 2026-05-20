# Next.js SQLite CLAUDE.md Smoke Test

This smoke test documents how the template was checked for the bounty
acceptance criteria.

## Greenfield Prompt

```text
Create a new billing settings page for a Next.js 15 App Router SQLite SaaS.
It should let workspace owners update the billing email and list the latest
invoices.
```

## Expected Agent Behavior

- Choose `app/(app)/billing/page.tsx` as the route surface.
- Add or reuse a `workspace_id` scoped invoice query.
- Validate billing email input before writing to SQLite.
- Use a server action for the billing email update.
- Keep invoice display in a server component unless client interaction is
  required.
- Add a migration only if the billing email column does not exist.
- Run `pnpm lint`, `pnpm typecheck`, `pnpm test`, and `pnpm build`.

## Acceptance Mapping

- Project structure: covered by the `Folder Structure` section.
- Naming conventions: covered by the `Naming Conventions` section.
- Database migration rules: covered by `SQLite And Migration Conventions`.
- Dev commands: covered by `Default Dev Commands`.
- Patterns and anti-patterns: covered by the final operating sections, with a
  reason for each rule.
- Greenfield usability: the prompt above should be answerable without asking
  what router, database style, migration approach, or component boundary to use.
