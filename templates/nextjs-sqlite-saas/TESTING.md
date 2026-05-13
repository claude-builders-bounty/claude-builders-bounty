# Verification Notes

## Static Coverage Check

The template was checked against the bounty acceptance criteria:

- Project structure: covered in `Project Structure`.
- Naming conventions: covered through folder, migration, feature module, and command naming rules.
- DB migration rules: covered in `SQLite And Migration Conventions`.
- Dev commands: covered in `Commands`.
- Patterns to follow: covered in `Data Access Patterns`, `App Router Patterns`, `Components`, `Authentication And Authorization`, and `Testing Rules`.
- Anti-patterns to avoid: covered in `What We Do Not Do`.
- Each rule has a reason: every normative bullet includes a `Reason:` sentence.

## Greenfield Smoke Prompt

After copying `CLAUDE.md` into a new Next.js 15 + SQLite project, use this prompt:

```text
Add an organizations table and a server-rendered organizations list page with pagination.
```

Expected Claude Code behavior:

- Creates a numbered SQL migration under `db/migrations/`.
- Updates feature-owned organization query code instead of putting SQL in a route file.
- Uses a server component for the list page.
- Validates pagination input with Zod.
- Adds or updates relevant tests.
- Does not ask for stack, folder, database, migration, validation, or test conventions because those are specified in `CLAUDE.md`.

## Review Command

```bash
grep -n "Reason:" templates/nextjs-sqlite-saas/CLAUDE.md
```

The command should show that each rule family is opinionated and explains why the rule exists.

## Executed Checks

```bash
grep -n "Reason:" templates/nextjs-sqlite-saas/CLAUDE.md | wc -l
grep -nE "Stack And Versions|Project Structure|SQLite And Migration Conventions|Commands|What We Do Not Do" templates/nextjs-sqlite-saas/CLAUDE.md
git diff --check
```

Claude Code CLI smoke testing was attempted in a temporary directory with this `CLAUDE.md`, but the local environment returned `Your organization does not have access to Claude`. The prompt above is included so a maintainer with Claude Code access can reproduce the final behavior check directly.
