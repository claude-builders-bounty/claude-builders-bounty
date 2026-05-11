# Claude Code Smoke Test: Next.js SQLite Template

Environment:

- Project scaffold: `npx create-next-app@15.5.18 nextjs-sqlite-template-smoke-clean --ts --tailwind --eslint --app --src-dir --import-alias "@/*" --use-npm --skip-install --yes`
- Template placement: copied `templates/nextjs-sqlite-saas/CLAUDE.md` to the scaffolded project root.
- Claude Code: `claude -p` with file-editing tools disallowed.

Prompt:

```text
Read CLAUDE.md and the project tree. Do not edit files. Do not ask clarifying questions. Return exactly two Markdown sections: 'Conventions I will follow' with five bullets grounded in CLAUDE.md, and 'Files I would create before editing' with paths for an authenticated team invite workflow using SQLite persistence.
```

Observed response:

```markdown
## Conventions I will follow

- Server actions end in `.action.ts` and return typed result objects: `{ ok: true, data }` or `{ ok: false, fieldErrors, formError }`
- Database query modules end in `.query.ts` and contain SQL access functions, keeping SQL separate from business logic
- Validation schemas end in `.schema.ts` using Zod at every server boundary for type safety
- SQL migrations use `YYYYMMDDHHMM_description.sql` format and are explicit forward migrations with rollback notes
- Service functions in `server/services` coordinate use cases like `inviteTeamMember`, defining one function per user intent

## Files I would create before editing

- `db/migrations/202605111030_create_invites.sql` - SQL migration to create invites table with foreign keys
- `db/queries/invites.query.ts` - SQL access functions for invite CRUD operations
- `lib/validation/invite.schema.ts` - Zod validation schemas for invite input/output
- `server/actions/invite-team-member.action.ts` - Server action handling invite form submission
- `server/services/invites.ts` - Business logic service orchestrating invite workflow
- `app/(app)/team-members/invite/page.tsx` - Authenticated invite form page
- `components/forms/InviteForm.tsx` - Progressive form component for team member invites
- `tests/integration/invite-team-member.action.test.ts` - Integration tests covering validation and persistence
```

Result: Claude Code used the template context to infer stack, migrations, server actions, service boundaries, validation, and test files without asking clarifying questions.
