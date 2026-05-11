# Validation Notes

Validation target: a greenfield Next.js 15 App Router + SQLite SaaS skeleton with `CLAUDE.md` copied to the repository root.

Prompt used with Claude Code:

```text
Using only this project's CLAUDE.md and file tree, answer without asking clarifying questions: where should I put a new organization invitation feature, what database migration is needed, and which commands should I run before handoff?
```

Expected context recognition:

- UI route work belongs under `app/(app)/`.
- Mutation logic belongs in `server/actions/` and `server/services/`.
- SQL access belongs in `server/repositories/`.
- Schema change belongs in a numbered file under `server/db/migrations/`.
- Handoff commands are `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build`, and migration checks as relevant.

Local checks used for this template:

- Verified the template contains the requested sections: stack and versions, folder structure, SQL and migration conventions, component patterns, and anti-patterns.
- Verified setup instructions are three steps.
- Verified each rule table includes a reason column.

Actual Claude Code context check:

- Claude Code placed the organization invitation UI under `app/(app)/organizations/[slug]/invitations/page.tsx`.
- It placed form mutation work in `server/actions/`, product rules in `server/services/`, SQL access in `server/repositories/`, and config in `lib/config/`.
- It identified tenant membership authorization as a service-layer responsibility.
- It proposed an additive `organization_invitations` migration in `server/db/migrations/` with foreign keys, role checks, a unique token hash, and ISO timestamp text columns.
- It listed the expected handoff commands: `pnpm db:migrate`, `pnpm lint`, `pnpm typecheck`, `pnpm test`, and `pnpm build`.
