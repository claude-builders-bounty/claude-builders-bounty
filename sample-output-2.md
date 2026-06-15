## PR Review

### Summary
This PR introduces a production-ready CLAUDE.md template for a Next.js 15 + SQLite SaaS project. It covers project structure, SQL conventions, component patterns, anti-patterns, and environment variables. The document is opinionated and provides reasoning for each convention.

### Identified Risks
- Drizzle ORM may not be the best choice for all Next.js + SQLite setups; Prisma has larger ecosystem
- The anti-pattern table could become outdated as the stack evolves
- No mention of error monitoring/logging service (Sentry, etc.)

### Improvement Suggestions
- Add a section on testing strategy (Vitest setup, e2e with Playwright)
- Include error boundary patterns for the App Router
- Document the CI/CD pipeline expectations

### Confidence Score
**Confidence: Medium**

### Files Changed (with line counts)
- CLAUDE.md (+115/-0)

### Key Observations
- Well-organized with clear section headings
- Anti-pattern table is valuable for team onboarding
- Environment variables template is practical
- No testing or CI/CD guidance included
