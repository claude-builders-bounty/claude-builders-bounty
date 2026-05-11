# Validation Notes

## Acceptance Checklist

- Covers project structure, naming conventions, and database migration rules.
- Includes development commands, implementation patterns, and anti-patterns with reasons.
- Uses concrete defaults for Next.js 15 App Router, TypeScript, Server Components, server actions, and SQLite.
- Avoids generic advice by tying each rule to a small SaaS failure mode.
- Can be copied directly to a greenfield project root as `CLAUDE.md`.

## Smoke Test Scenario

Use a fresh project with this shape:

```text
src/app/(app)/dashboard/page.tsx
src/app/(marketing)/page.tsx
src/db/client.ts
src/db/migrations/
src/db/schema.ts
package.json
```

Paste `CLAUDE.md` into the project root, then ask Claude Code:

```text
Add a workspace invitations feature with a pending invite table, dashboard UI, and accept-invite server action.
```

Expected behavior:

- Creates a forward-only SQL migration under `src/db/migrations`.
- Adds tenant-scoped query functions under `src/db/queries`.
- Keeps initial data loading in Server Components.
- Uses a shallow Client Component only if interactive state is needed.
- Validates invite creation and acceptance inputs before writes.
- Mentions assumptions instead of asking for stack clarification already answered by `CLAUDE.md`.

## Review Result

The template contains explicit defaults for the stack, commands, folder layout, SQL rules, migration safety, component ownership, validation, auth, billing, and testing. The smoke-test prompt can be answered from the template without needing additional project-level clarification.
