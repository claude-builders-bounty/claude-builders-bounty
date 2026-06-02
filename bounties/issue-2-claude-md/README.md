# CLAUDE.md Next.js 15 + SQLite SaaS Template

> Opinionated CLAUDE.md for a production-ready Next.js 15 SaaS with SQLite + Drizzle.

## Whats included

- Stack Versions every choice explained alternatives listed with reasons
- Folder Structure opinionated layout with reasoning
- Naming Conventions table format for quick reference
- Database Migration Rules 7 hard rules never edit migrations Unix epoch timestamps etc
- Data Fetching Rules Server Components first zero useEffect data fetching
- Auth Pattern middleware + server session double-check
- Form Handling Server Action + Zod pattern with React 19 useActionState()
- Error Handling Hierarchy per-layer error strategy
- Anti-Patterns 10 explicit anti-patterns with reasons
- Dev Commands complete npm run reference
- Billing Subscription Pattern Stripe integration guide
- Performance Checklist 6 items to verify before shipping

## How to use

1. Copy CLAUDE.md to the root of any Next.js 15 + SQLite project
2. Review and adjust the folder structure to match your project
3. Claude Code will now understand your conventions without asking clarifying questions

## Key differentiators

| This template | Others |
|---|---|
| 10 anti-patterns with explicit why | Generic do this dont do that |
| Billing Stripe pattern included | Auth + fetching only |
| Unix epoch timestamps not ISO strings | Defaults to ISO strings |
| Performance checklist | No shipping checklist |
| Error handling hierarchy table | Single paragraph |

Closes #2
