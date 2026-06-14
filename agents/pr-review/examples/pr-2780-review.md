## 🤖 Claude Review: [BOUNTY $75] TEMPLATE: CLAUDE.md for Next.js + SQLite SaaS

### Summary
This PR adds `templates/nextjs-sqlite/CLAUDE.md`, an opinionated CLAUDE.md template for a Next.js 15 + SQLite SaaS project. It covers stack decisions, folder structure, conventions for Server Actions, database migrations, component patterns, and anti-patterns. The template is self-contained and ready to drop into a new project.

### Identified Risks
- **risk: Hardcoded preference for better-sqlite3** — The template chose `better-sqlite3` as the SQLite driver. This works great for single-server deployments but breaks on serverless platforms (Vercel Edge, Neon) where a persistent filesystem is unavailable. Turso or libsql would be more portable. This is a design opinion rather than a bug, but worth flagging for users deploying to serverless.
- **risk: Folder structure implies upfront organization** — The template shows a complete folder structure with `db/schema/*.ts` for each table. Teams that start with this often end up with circular dependencies or schema files that grow too large. Consider suggesting a single `schema.ts` for small projects and splitting only when needed.

### Improvement Suggestions
- **suggestion: Add a "Scaling" section** — The template currently covers the happy path for a greenfield project. Adding a brief section on how to scale (e.g., when to split into packages, when to add a queue) would make it more durable.
- **suggestion: Pin package versions** — The Stack table lists framework choices but no version ranges. Adding minimum/recommended versions prevents drift (e.g., "Next.js >=15.0", "Drizzle >=0.38")
- **suggestion: Add testing conventions** — The Commands section includes `pnpm test` but there are no testing conventions (Vitest patterns, Playwright page object model, test file naming). This is the most common area where teams waste time.

### Confidence Score
**High** — The template is thorough, opinionated with clear rationale, and covers the critical areas that teams need. The suggestions above are enhancements, not gaps in the acceptance criteria.
