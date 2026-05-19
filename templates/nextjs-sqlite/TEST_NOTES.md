# Test Notes — CLAUDE.md Template

## Objective
Validate that the template can be dropped into a greenfield Next.js + SQLite SaaS repo and provide enough context for Claude Code without clarifying questions.

## Quick Validation Flow

1. Create a fresh app:
   - `pnpm create next-app@latest saas-app --ts --app`
2. Add SQLite tooling:
   - `pnpm add better-sqlite3 zod`
3. Copy `CLAUDE.md` from this folder into the new repo root.
4. Ask Claude Code:
   - "Add workspace_members schema + migration + API route following this project rules."

## Observed Outcome

- Claude generated changes using feature-first layout.
- Proposed migration naming followed ordered convention.
- Domain logic stayed out of route file and into server module.
- SQL naming stayed snake_case/plural as instructed.

## Pass/Fail

- Pass: template provided sufficient architectural and operational guidance.
