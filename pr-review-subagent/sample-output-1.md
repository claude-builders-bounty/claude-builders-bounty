# Sample PR Review Output 1

**PR:** CLAUDE.md template — Next.js 15 + SQLite SaaS (Bounty #2 - $75)
**URL:** https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1321

---

## Summary

A well-structured, opinionated CLAUDE.md template targeting Next.js 15 App Router + Drizzle + SQLite SaaS projects. The author demonstrates solid familiarity with modern Next.js patterns (Server Components by default, Server Actions, route groups for auth boundaries) and makes deliberate framework choices (Drizzle over Prisma, pnpm over npm, Vitest over Jest) with reasoned justifications. The template covers folder structure, conventions, migration rules, component patterns, auth flow, anti-patterns, and testing strategy. For a CLAUDE.md — designed to shape AI agent behavior on a project — it is above average in depth and specificity.

### Identified Risks

1. **`useActionState` import path not shown** — In React 19, this hook is exported from `react`, but many snippets still reference `react-dom` (RC era). AI agents may guess wrong. Add explicit import: `import { useActionState } from 'react'`.

2. **Missing `'use server'` directive** — Server Actions in separate files require `'use server'` at the top. AI agents reading this CLAUDE.md may omit it, producing broken builds.

3. **No runtime input validation for Server Actions** — Template says "Server Actions validate once on the server using your API types." TypeScript types are compile-time only. At minimum, show a `z.object(...).parse()` call.

4. **SQLite + Turso driver ambiguity** — Different client init and `drizzle.config.ts` setups for `better-sqlite3` vs `@libsql/client`. Without guidance, agents may configure mismatched drivers.

5. **`current_timestamp` is not strict ISO 8601** — SQLite's `CURRENT_TIMESTAMP` produces `2024-01-15 10:30:00` (missing 'T'), which breaks strict ISO 8601 parsers.

6. **Overstated claim about `ALTER TABLE` in SQLite** — SQLite supports `ADD COLUMN` for nullable columns. The real issue is lack of `IF NOT EXISTS` syntax.

7. **`utils/` ban may backfire** — Cross-cutting utilities (date formatting, type guards) need a home. `lib/helpers.ts` is just a junk drawer with a different name.

### Improvement Suggestions

8. **Add a `drizzle.config.ts` stub** — Most common Drizzle setup friction point.
9. **Add `server-only` import convention** — Prevents exposing server-only modules in client bundles.
10. **Include `loading.tsx` and `layout.tsx` conventions** — Critical for AI agent code generation.
11. **Version pinning** — Caret ranges risk pulling breaking changes.
12. **Path alias convention** — Use `@/` imports instead of relative paths.

### Confidence Score

**Medium-High — 7/10.** Well-researched template reflecting current Next.js 15 patterns. Two factual issues (missing `'use server'` directive, runtime validation confusion) are significant enough to cause real bugs in AI-generated code.
