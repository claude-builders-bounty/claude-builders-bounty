# Bounty 2 — CLAUDE.md for Next.js + SQLite SaaS

An opinionated, production-ready `CLAUDE.md` template for Next.js 15 App Router + SQLite projects.

## Setup (1 step)

1. Copy `CLAUDE.md` into the root of your Next.js project.

That's it. Claude Code will read it automatically.

## What it covers

| Section | What's inside |
|---------|--------------|
| **Stack & Versions** | Exact tools and versions with rationale for each choice |
| **Folder Structure** | Full project tree with naming conventions and why each convention exists |
| **Database & Migrations** | SQLite pragmas, Drizzle schema rules, migration workflow, Turso upgrade path |
| **Dev Commands** | Every `pnpm` script the project uses |
| **Component Patterns** | Server Components, server actions, data fetching, UI component template |
| **What We Don't Do** | Anti-patterns table — what to avoid and what to do instead |
| **Environment Variables** | `.env.example` template with security rules |
| **Testing Strategy** | Unit / integration / E2E split with tool choices |
| **Deployment Notes** | SQLite-compatible hosting options and backup strategy |

## Design decisions

**Why every rule has a reason:**
Claude Code (and human devs) follow rules better when they understand the "why". Arbitrary rules get ignored. Every entry in this template explains its rationale.

**Why SQLite:**
SQLite handles more traffic than most SaaS apps will ever see. It removes an entire service (Postgres/MySQL) from your stack, simplifies deployment, and makes backups trivial. The template includes an upgrade path to Turso (hosted SQLite) when you outgrow a single server.

**Why Drizzle over Prisma:**
Drizzle produces predictable SQL, has a smaller bundle, and doesn't require a binary engine. For SQLite especially, Drizzle's thin abstraction is a better fit.

**Why opinionated:**
An unopinionated CLAUDE.md is useless — it just describes what exists without guiding decisions. This template makes choices so Claude Code doesn't have to guess.

## Customization

The template is a starting point. Adapt these sections for your project:

- **Auth provider** — swap Auth.js for Clerk, Lucia, or your own
- **Payment provider** — swap Stripe references for Lemon Squeezy, Paddle, etc.
- **Styling** — if you use something other than Tailwind, update the component patterns
- **Testing** — adjust the testing strategy to match your team's practices
- **Deployment** — pick your platform and remove the others
