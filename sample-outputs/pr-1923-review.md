## 🤖 AI Code Review

**PR:** [[BOUNTY $75] TEMPLATE: CLAUDE.md for a Next.js + SQLite SaaS project](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1923)
**Files:** 1 — +148 / -0
**Reviewed by:** claude-review agent

---

### Summary

This PR adds a comprehensive CLAUDE.md guide for a Next.js 15 + SQLite SaaS project. It covers the full tech stack (Next.js App Router, TypeScript strict, Drizzle ORM, Lucia/NextAuth, Tailwind + shadcn/ui, Stripe), provides a clear project structure, documents dev commands, and establishes coding patterns and anti-patterns. The guide is opinionated and prescriptive — exactly what a CLAUDE.md should be to steer an AI agent effectively.

### Identified Risks

- **Single point of guidance:** The CLAUDE.md strongly recommends SQLite (via Turso) over Postgres with the reasoning "if you outgrow it, migrate." While valid for MVPs, this architectural decision buried in a config file could be overlooked by human developers who join later and assume Postgres is available.
- **Server Actions only approach:** The guide mandates "Server Actions only — no REST API routes for CRUD." This is excellent for internal apps but can become a bottleneck if a mobile app or external API consumer needs the same endpoints later — they'd need REST routes duplicated anyway.
- **No `.env.example` mentioned:** The guide is thorough on patterns but doesn't reference environment variable management. The Stripe webhook pattern mentions `stripe_events` table but doesn't note the `STRIPE_WEBHOOK_SECRET` env var setup.
- **Testing section thin on integration tests:** E2E is mentioned ("Playwright for critical paths") but there's no guidance on API integration tests or contract testing between server actions and the database layer.

### Improvement Suggestions

- **Add a "Getting Started" section** — a 5-step bootstrap checklist at the top of CLAUDE.md that the AI can follow when first setting up the project (clone → install deps → set up .env → db:migrate → dev). This dramatically reduces the friction of the first `claude` invocation.
- **Mention `drizzle-kit` CLI requirements** — the `pnpm db:generate` / `db:migrate` commands assume `drizzle-kit` is installed. A note about `pnpm add -D drizzle-kit` in the dev commands section would prevent a common first-run error.
- **Soft delete pattern could be more specific** — mention that queries should always include `.where(isNull(table.deletedAt))` with an example, since forgetting this filter is the #1 soft-delete bug.
- **Secrets section** — add a brief section listing all required env vars (`DATABASE_URL`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `AUTH_SECRET`, etc.) with a link to `.env.example`. This also helps the AI agent know what to prompt the user for.
- **Reference the "why" for Drizzle vs Prisma more strongly** — the anti-pattern section already says "Heavy binary, slow cold start," but adding that Prisma's SQLite support requires `libsql` and has migration compatibility issues with Turso would make the argument more concrete for developers who might push back.

### Confidence Score

**High** — The diff is a single new file with clear, idiomatic conventions. All observations are based on the content itself and my knowledge of the Next.js/Drizzle/Stripe ecosystem. No external dependencies or complex logic to verify.