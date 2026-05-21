# Test Notes

Acceptance criteria review for issue #2:

- Covers project structure: yes, see `Folder Structure`.
- Covers naming conventions: yes, see `Naming Conventions`.
- Covers DB migration rules: yes, see `SQL And Migration Conventions`.
- Includes dev commands: yes, see `Dev Commands`.
- Includes patterns to follow: yes, see server action, query, component, data model, and testing rules.
- Includes anti-patterns to avoid: yes, see `What We Do Not Do`.
- Opinionated and reasoned: every major section includes a `Reason:` line.
- Usable on a greenfield Next.js + SQLite project: yes, no project-specific paths outside the proposed layout.

Manual Claude Code smoke prompt used for review:

```text
Using this CLAUDE.md, add a workspace-scoped "projects" feature with a migration, queries, server action, and dashboard table. Before coding, list which files you would touch and why.
```

Expected behavior:

- Claude should identify a migration under `db/migrations/`.
- Claude should place SQL helpers under `db/queries/`.
- Claude should validate input before mutation.
- Claude should enforce workspace authorization at the server boundary.
- Claude should keep table UI separate from business logic.

This repository environment does not include an actual greenfield Next.js app, so the validation is limited to acceptance-criteria coverage and prompt-readiness review.
