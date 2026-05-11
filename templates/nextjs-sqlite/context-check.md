# Greenfield Context Check

This is the validation scenario used for bounty #2.

## Project Setup

```bash
npx create-next-app@latest acme-saas --ts --app --eslint --src-dir false --import-alias "@/*"
cp templates/nextjs-sqlite/CLAUDE.md acme-saas/CLAUDE.md
```

Claude Code CLI was not available in this local environment, so the check below records the exact prompt and the expected context coverage the template provides without additional project-specific clarification.

## Prompt

```text
Add an organization settings page where an owner can rename the organization.
Include the SQLite migration, server action, validation, and tests.
```

## Context Coverage

- Route location is answered by `app/(dashboard)/settings/page.tsx`.
- Mutation location is answered by `server/organizations/mutations.ts`.
- Validation location is answered by `server/organizations/validators.ts`.
- Migration naming is answered by `db/migrations/NNNN_short_description.sql`.
- SQL style is answered by the parameterized SQL and forward-only migration rules.
- Authorization is answered by the requirement to check permissions inside mutations.
- Cache behavior is answered by the `revalidatePath` / `revalidateTag` rule.
- Test scope is answered by the domain validator, permission, migration, and Playwright guidance.
- Dev commands are answered by the command list in the template.

The template therefore gives Claude Code enough project context to start the implementation without asking where files belong, which database style to use, how migrations are named, or which tests should be added.
