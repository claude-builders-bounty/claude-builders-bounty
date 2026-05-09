# Verification protocol — "paste it and ask"

Acceptance criterion #5 from issue #2:

> Tested: create a new project, paste the CLAUDE.md, confirm Claude Code understands the context without asking clarifying questions.

This file is the **test protocol** — a deterministic checklist a
reviewer can run in a fresh Claude Code session against an empty
directory containing only the bundled `CLAUDE.md` (and optionally
`.claude/commands/`). It defines the four representative prompts and,
for each, the exact behaviours the CLAUDE.md is engineered to produce.

A submission "passes" this verification when, in a fresh `claude code`
session, every "MUST" line below holds without the reviewer needing to
re-prompt.

## Setup

```bash
mkdir test-claude-md && cd test-claude-md
curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/templates/nextjs-sqlite-claude-md/CLAUDE.md -o CLAUDE.md
mkdir -p .claude/commands
curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/templates/nextjs-sqlite-claude-md/.claude/commands/add-route.md -o .claude/commands/add-route.md
curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/templates/nextjs-sqlite-claude-md/.claude/commands/db-migrate.md -o .claude/commands/db-migrate.md
claude
```

## Prompt 1 — "Add a route"

> **User:** Add a `/billing` route that shows the current user's
> subscription status.

The CLAUDE.md "Working with Claude Code on this project" section + the
`add-route` slash command are designed so the model **MUST**:

- Produce `app/(app)/billing/page.tsx` as a Server Component
- Produce `app/(app)/billing/loading.tsx` (Suspense fallback)
- Produce `app/(app)/billing/error.tsx` as a `"use client"` boundary with `reset()`
- Add or extend a query function in `lib/db/queries/billing.ts` (named, typed via Drizzle's `$inferSelect`)
- NOT ask "do you want loading/error UI?" — these must appear without prompting
- NOT suggest `react-query`, `swr`, or `useEffect` for data fetching
- NOT mark the page as `"use client"`

## Prompt 2 — "Add a column"

> **User:** Add a `trial_ends_at` column to the `subscriptions` table.

CLAUDE.md "Database conventions" + the `db-migrate` slash command
require that the model **MUST**:

- Edit `lib/db/schema.ts` to add `trialEndsAt: integer("trial_ends_at", { mode: "timestamp" })`
- State the next step as `pnpm db:generate` (NOT raw `ALTER TABLE`)
- Either run the generator (if instructed) or quote the SQL the generator would produce
- Update any query functions in `lib/db/queries/billing.ts` that select from `subscriptions` to include the new column
- NOT hand-write a migration SQL file
- NOT propose editing a previously-committed migration

## Prompt 3 — "Add interactivity"

> **User:** The billing page needs a "Cancel subscription" button that
> calls a Server Action and shows an optimistic UI.

CLAUDE.md "Component patterns" + "Data flow" require that the model
**MUST**:

- Keep `app/(app)/billing/page.tsx` as a Server Component
- Create `components/Billing/CancelSubscriptionButton.tsx` with `"use client"` and `useOptimistic`
- Pass server data into the client component as props (no fetching from the client)
- Create `server/actions/billing.ts` with `"use server"` directive
- Validate input with a Zod schema imported from `lib/db/zod/billing.ts`
- Return `{ ok: true, data } | { ok: false, error }` from the action
- Call `revalidatePath("/billing")` after success
- NOT mark the entire page as `"use client"`
- NOT throw across the client/server boundary

## Prompt 4 — Ambiguous request

> **User:** Add billing.

CLAUDE.md "Working with Claude Code on this project" specifies "ask
exactly one clarifying question" on ambiguous requests. The model
**MUST**:

- Ask one focused question covering the largest unknown (e.g. "Stripe
  Checkout vs Stripe Elements? Per-seat or flat-fee?" — bundled into a
  single response, not as 5 separate questions)
- NOT silently pick a path and start producing code
- NOT ask 5+ separate questions
- NOT ask "what database should we use?" — that's already answered by CLAUDE.md

## What this proves when it passes

The CLAUDE.md is internally consistent and produces stable, predictable
behaviour from Claude Code on the canonical SaaS shape (auth, DB,
billing, route additions). Anyone can paste it into a fresh project
and start shipping without a discovery round.

## Reproducibility

Reviewers (and bounty judges) are encouraged to run the four prompts
above against a fresh Claude Code session and either confirm the MUSTs
or open issues / suggest patches where the CLAUDE.md falls short. The
template is designed to be tightened iteratively — every gap surfaced
this way is a candidate for a new "What we don't do" row or a new
slash command.
