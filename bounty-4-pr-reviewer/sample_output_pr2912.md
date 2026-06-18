## Claude Code PR Review

**PR:** https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2912  
**Model:** `claude-sonnet-4-20250514`

---

### Summary
This PR adds an opinionated `CLAUDE.md` template for Next.js 15 App Router + SQLite SaaS projects. It encodes a curated set of technology choices (Drizzle ORM, Tailwind 4, next-auth v5, Zod) along with folder structure conventions, component patterns, migration workflow, and an anti-patterns table. The file is documentation-only with no runtime code changes.

### Risks
- No automated tests can verify that Claude actually follows these instructions in practice — the effectiveness depends on future LLM behavior
- The Drizzle-over-Prisma preference is opinionated and may not suit all team setups; teams with existing Prisma migrations would need to migrate
- `better-sqlite3` + Turso dual setup adds complexity; the `.env` example doesn't show how to switch between them via a single env var

### Improvement Suggestions
- Add a note on how to extend the template for multi-tenant setups (the current structure assumes single-owner tables)
- The `hooks/` folder is listed for "client-side hooks only" — add an explicit example of `useOptimistic` with Server Actions since that's a common Next.js 15 pattern
- Consider adding a `pnpm db:seed` seed script example — it's listed in dev commands but the pattern isn't shown

### Confidence Score
**High**  
Rationale: The PR is a single documentation file with no executable code; risks are limited to opinion divergence rather than correctness bugs.
