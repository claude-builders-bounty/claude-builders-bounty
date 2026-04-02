# CLAUDE.md Template for Next.js + SQLite SaaS

A comprehensive, opinionated `CLAUDE.md` template that helps Claude Code (and other AI coding assistants) understand your Next.js + SQLite SaaS codebase instantly.

## What is CLAUDE.md?

`CLAUDE.md` is a convention file read automatically by Claude Code when it enters a repository. It gives Claude the context it needs to write correct, consistent code — your stack, your conventions, your patterns.

Think of it as onboarding docs for AI, except it actually gets read every time.

## Why this template?

Generic CLAUDE.md files are useless. "We use React" tells Claude nothing it couldn't infer. This template is **opinionated for the specific stack** most indie SaaS projects converge on:

- **Next.js 15** (App Router, Server Components, Server Actions)
- **SQLite** (via Drizzle ORM — file-based dev, Turso for prod)
- **Auth.js v5** (NextAuth)
- **Tailwind CSS + shadcn/ui**
- **Stripe** (webhooks-driven billing)
- **Vercel** (deployment)

If this isn't your stack, this template isn't for you — and that's the point. Specificity is what makes a CLAUDE.md useful.

## Quick Start

```bash
# 1. Copy the template to your repo root
cp CLAUDE.md /path/to/your/project/CLAUDE.md

# 2. Open it and fill in the project-specific sections
#    (every <!-- comment --> block tells you what to customize)

# 3. Delete the comment blocks when you're done

# 4. Commit it
cd /path/to/your/project
git add CLAUDE.md
git commit -m "Add CLAUDE.md for AI-assisted development"
```

## What's Covered

| Section | What Claude Learns |
|---|---|
| Project Overview | What the app does (so Claude doesn't guess) |
| Tech Stack | Exact versions and choices (no ambiguity) |
| Project Structure | Where every kind of file lives |
| Commands | How to dev, build, test, migrate |
| Environment Variables | Every env var and what it's for |
| Database Patterns | Schema conventions, query patterns, migration workflow |
| Auth Patterns | How to get sessions in every context (RSC, Client, Actions, API) |
| Server Actions | The 5-step mutation pattern (Auth → Validate → Authorize → Mutate → Revalidate) |
| Component Conventions | Server vs. Client, naming, data fetching |
| Styling Rules | Tailwind-only, cn() utility, dark mode |
| Stripe / Billing | Webhook-driven subscription lifecycle |
| Error Handling | Error boundaries, API error pattern |
| Testing Strategy | Vitest for unit, Playwright for E2E |
| Code Style | Import rules, type conventions, nullability |
| Common Gotchas | SQLite locking, edge runtime, revalidation |
| Deployment | Vercel + Turso setup |

## Customization Guide

### Must customize (template won't work without these)

1. **Project Overview** — Replace the placeholder with what your app actually does.
2. **Project Structure** — Adjust to match your actual directories. Remove routes that don't exist.
3. **Commands** — Match your `package.json` scripts exactly.
4. **Environment Variables** — List every env var your app uses.

### Should customize (makes it much better)

5. **Database Schema** — Replace the example schema with your actual tables.
6. **Domain-specific patterns** — Add sections for your domain (multi-tenancy, file uploads, real-time features, etc.).
7. **Server Actions** — Update the example action to match your actual entity.

### Customize if applicable

8. **Remove Stripe section** if you don't have billing yet.
9. **Add tRPC patterns** if you're using tRPC instead of raw Server Actions.
10. **Add multi-tenancy patterns** if your SaaS is team/org-based.

## Examples

See `examples/customized-example.md` for a fully customized version for a fictional invoicing SaaS called "InvoiceOwl."

## Tips for a Great CLAUDE.md

1. **Be specific, not aspirational.** Document what the code does today, not what you plan to build. Update CLAUDE.md as the project evolves.

2. **Show patterns, not APIs.** Claude knows the Next.js docs. What it doesn't know is *your* conventions — how *you* compose these tools.

3. **Include the "why."** `"We use Server Actions, not API routes, for mutations"` is good. `"We use Server Actions, not API routes, for mutations — because they support progressive enhancement and co-locate with the form"` is better.

4. **List the gotchas.** The most valuable part of any CLAUDE.md is the "things that will bite you" section. Every project has them.

5. **Keep it under 400 lines.** Claude has limited context. A 1000-line CLAUDE.md means Claude skips the end. Be concise.

## File Structure

```
├── CLAUDE.md                       # The template — copy this to your repo
├── README.md                       # You're reading this
└── examples/
    └── customized-example.md       # Fully filled-in example (InvoiceOwl SaaS)
```

## License

MIT — use it however you want.
