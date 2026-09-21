# Acceptance checklist (Bounty #2)

- [x] Opinionated `CLAUDE.md` for Next.js 15 App Router + Turso/SQLite SaaS
- [x] Explicit architecture: app routes, server actions, Drizzle schema sketch, multi-tenant notes
- [x] Security defaults called out (no secrets in client, env naming, CSRF/cookie notes)
- [x] `VERIFICATION.md` documents how a reviewer can spot-check the template
- [x] Keep scope to a reusable template (no unrelated repo churn)

## Reviewer quick path
1. Open `templates/nextjs-saas/CLAUDE.md`
2. Confirm sections cover stack, layout, data, auth/tenancy, and agent do/don't rules
3. Cross-check `VERIFICATION.md` against those sections
